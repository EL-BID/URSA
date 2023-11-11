import ee
import json
import requests

import geopandas as gpd
import numpy as np
import osmnx as ox
import rioxarray as rxr
import ursa.degree_of_urbanization as dou
import ursa.ghsl as ghsl
import ursa.utils.geometry as ug
import ursa.utils.raster as ru
import xarray as xr

from geocube.api.core import make_geocube
from rasterio.enums import Resampling
from scipy.spatial import KDTree


def load_or_prep_rasters(bbox_mollweide, path_cache):
    all_exist = True
    for path in ["urban", "roads", "slope", "excluded", "years"]:
        full_path = path_cache / f"{path}.npy"
        all_exist &= full_path.exists()

    all_exist &= (path_cache / "attributes.json").exists()

    if not all_exist:
        prep_rasters(bbox_mollweide, path_cache)

    return True


def bbox_to_latlon(bbox_mollweide, crs):
    bbox_latlon = gpd.GeoSeries([bbox_mollweide], crs=crs)
    bbox_latlon = bbox_latlon.to_crs("EPSG:4326").envelope.buffer(0.05, join_style=2)[0]
    return bbox_latlon


def prep_rasters(bbox_mollweide, path_cache):
    """SLEUTH inputs are_
    - urban history
    - slope
    - water + protected areas = excluded
    - roads

    For calibration, the earliest urban year is used as the seed, and
    subsequent urban layers, or control years, are used to measure
    several statistical best fit values. For this reason, at least
    four urban layers are needed for calibration: one for
    initialization and three additional for a least-squares
    calculation.

    The expected values are 0: non-urbanized, 1: urbanized
    """

    # We also need a lat lon bbox that covers all the mollweide bbox
    # to get data from GEE

    bbox_latlon = bbox_to_latlon(bbox_mollweide, "ESRI:54009")
    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    # Historic urbanization, obtained from GHSL + DoU processing
    # Extract last 20 years or urbanization for 5 calibration points
    dou_xr = dou.load_or_process_dou(bbox_mollweide, path_cache)
    dou_xr = dou_xr.astype("int32")
    dou_xr.name = "urban"
    dou_xr = dou_xr.rename({"band": "year"})
    urban_years = dou_xr.coords["year"].values

    assert dou_xr.min() >= 0
    assert dou_xr.max() >= 1
    assert len(urban_years) >= 4

    # World Cover
    print("Loading WorldCover")
    load_worldcover(bbox_ee, path_cache, dou_xr)
    print("End Loading WorldCover")

    # Slope and protected areas are obtained from GEE
    slope_xr = load_slope(bbox_ee, path_cache, dou_xr)

    excluded_xr = load_excluded(bbox_ee, bbox_mollweide, path_cache, dou_xr)

    # The road network is downloaded from OSM and further processed
    # into a set of auxiliary arrays with precomputed distances.
    geocube = bbox_to_geocube(bbox_latlon, path_cache, dou_xr)
    roads, *_ = load_roads(geocube)

    np.save(path_cache / "years", urban_years)
    np.save(path_cache / "urban", dou_xr.values)
    np.save(path_cache / "roads", roads.values)
    np.save(path_cache / "slope", slope_xr.values)
    np.save(path_cache / "excluded", excluded_xr.values)

    attr_dict = dict(
        years=[int(year) for year in dou_xr.year.values],
        transform=list(dou_xr.rio.transform()),
        height=int(dou_xr.rio.height),
        width=int(dou_xr.rio.width),
        crs=dou_xr.rio.crs.to_string(),
    )

    with open(path_cache / "attributes.json", "w", encoding="utf8") as f:
        json.dump(attr_dict, f)


def load_excluded(bbox_ee, bbox_mollweide, path_cache, raster_to_match):
    """Loads rasters denoting excluded areas.

    The excluded image defines all locations that are resistant to
    urbanization. Areas where urban development is considered
    impossible, open water bodies or national parks for example, are
    given a value of 100 or greater. Locations that are available for
    urban development have a value of zero (0).

    Pixels may contain any value between (0-100) if the representation
    of partial exclusion of an area is desired - unprotected wetlands
    could be an example: Development is not likely, but there is no
    zoning to prevent it.

    Water raster refers to the fraction of the pixel occupied by water.
    Threshold water pixels to those with more than half content of water.
    """

    protected_xr = load_protected(bbox_ee, path_cache, raster_to_match)

    # Water is the complement of GHS LAND, on AWS bucket
    land_xr = ghsl.load_or_download(
        bbox_mollweide, "LAND", data_path=path_cache, resolution=100
    ).squeeze()
    cell_area = land_xr.rio.resolution()[0] ** 2
    land_xr = land_xr / cell_area
    water_xr = 1 - land_xr
    # Binarize at 50% trehsold
    water_xr = (water_xr > 0.5).astype("int32")

    # Build excluded by combining water +  protected
    excluded = np.logical_or(water_xr, protected_xr).astype("int32")

    orig_attrs = excluded["spatial_ref"].attrs
    excluded = xr.where(excluded == 0, excluded, 100, keep_attrs=True)
    excluded["spatial_ref"].attrs = orig_attrs
    excluded.name = "excluded"
    excluded.attrs["num_exc_pix"] = (excluded > 99).sum().item()
    excluded.attrs["num_nonexc_pix"] = (excluded == 0).sum().item()
    excluded.attrs["exc_percent"] = excluded.attrs["num_exc_pix"] / excluded.size

    # Validate
    assert excluded.min() >= 0
    assert excluded.attrs["num_nonexc_pix"] > 0

    return excluded


def load_worldcover(bbox, path_cache, raster_to_match):
    """Load raster with World Cover from ESA WorldCover Dataset.

    The World Cover is obtained in a unique band named Map with several values including:
    10 Tree Cover
    20 Shrubland
    30 Grassland
    40 Cropland
    50 Built-up
    60 Bare/Sparse Vegetation
    70 Snow and Ice
    80 Permanent water bodies
    90 Herbaceous wetlands
    95 Mangroves
    100 Moss and lichen
    Note: bbox should be on latlot because ESA World Cover is on
    """
    basename = "worldcover.tif"
    fpath = path_cache / basename

    if not fpath.exists():
        src_addrs = "ESA/WorldCover/v100"

        col = ee.ImageCollection(src_addrs)
        col = col.filterBounds(bbox)
        image = col.first()
        proj = image.projection().crs()
        image = image.select(["Map"]).clip(bbox)

        params = {
            "name": "worldcover.tif",
            "region": bbox,
            "crs": image.projection().crs(),  # .crs(),
            "format": "GEO_TIFF",
            "scale": 100,
        }
        try:
            url = image.getDownloadURL(params)
            print(url)
            r = requests.get(url, stream=True)

            if r.status_code != 200:
                print(f"An error occurred while downloading {basename} 2.")
                return

            with open(fpath, "wb") as fd:
                fd.write(r.content)
            print(f"Data downloaded to {fpath}")

        except Exception as e:
            print(f"An error occurred while downloading {basename} 3.")
            print(r.json()["error"]["message"])
            return

        print("Archivo de World Cover descargado y guardado.")

    print("Cargando el archivo de World Cover...")
    worldcover = rxr.open_rasterio(fpath, name="worldcover", nodata=0.0).squeeze()
    print("Archivo de World Cover cargado.")

    print("Reproyectando y guardando el archivo de World Cover...")
    worldcover = worldcover.rio.reproject_match(raster_to_match, Resampling.mode)
    worldcover.name = "worldcover"
    np.save(path_cache / "worldcover.npy", worldcover)
    print("Archivo de World Cover reproyectado y guardado.")


def load_slope(bbox, path_cache, raster_to_match):
    """Loads raster with slope data into xarray.

    The slope is commonly derived from a digital elevation model
    (DEM), but other elevation source data may be used. Cell values
    must be in percent slope (0-100).
    """

    fpath = path_cache / "slope.tif"

    if not fpath.exists():
        src_addrs = "projects/sat-io/open-datasets/Geomorpho90m/slope"

        col = ee.ImageCollection(src_addrs)
        col = col.filterBounds(bbox)
        proj = col.first().projection()
        image = col.mosaic().setDefaultProjection(proj)
        image = image.select(["b1"]).clip(bbox)
        local_download(image, bbox, fpath)

    slope = rxr.open_rasterio(fpath, name="slope", nodata=0.0).squeeze()
    slope = slope.rio.reproject_match(raster_to_match, Resampling.average)
    slope.name = "slope"

    # Slope is must be reescaled to 0-100,
    # Type must be int, zero values have issues, so use ceil
    # Zero slope values have been reported to unrealistically
    # attract urbanization. (TODO: reference needed)
    slope = np.ceil((slope + 0.01) * 100 / 90).astype(np.int32)

    # Validate
    min_slope = slope.min().item()
    max_slope = slope.max().item()

    assert min_slope > 0
    assert max_slope < 99

    return slope


def load_protected(bbox, path_cache, raster_to_match):
    fpath = path_cache / "protected.tif"

    if not fpath.exists():
        col = (
            ee.FeatureCollection("WCMC/WDPA/current/polygons")
            .filterBounds(bbox)
            .filter(ee.Filter.eq("STATUS", "Designated"))
        )

        image = ee.FeatureCollection.reduceToImage(
            col, ["WDPAID"], ee.Reducer.anyNonZero()
        )

        image = image.reproject(crs="EPSG:4326", scale=100).select("any")

        local_download(image, bbox, fpath)

    protected_xr = rxr.open_rasterio(fpath, nodata=0).squeeze()

    protected_xr = protected_xr.rio.reproject_match(raster_to_match, Resampling.mode)
    protected_xr = protected_xr.astype("int32")

    return protected_xr


def local_download(img, bbox, fpath):
    basename = fpath.name

    if not isinstance(img, ee.Image):
        print("The ee_object must be an ee.Image.")
        return

    params = {
        "name": basename,
        "filePerBand": False,
        "region": bbox,
        "crs": img.projection(),  # .crs(),
        "crs_transform": img.projection().getInfo()["transform"],
        "format": "GEO_TIFF",
    }
    try:
        try:
            url = img.getDownloadURL(params)
        except Exception as e:
            print(f"An error occurred while downloading {basename} 1.")
            print(e)
            return
        # print(f"Downloading data from {url}\nPlease wait ...")

        r = requests.get(url, stream=True)
        if r.status_code != 200:
            print(f"An error occurred while downloading {basename} 2.")
            return

        with open(fpath, "wb") as fd:
            fd.write(r.content)
        print(f"Data downloaded to {fpath}")

    except Exception as e:
        print(f"An error occurred while downloading {basename} 3.")
        print(r.json()["error"]["message"])
        return


def bbox_to_geocube(bbox, path_cache, raster_to_match):
    edges = load_roads_osm(bbox, path_cache)

    # Filter local an residential roads
    edges = edges[edges["weight"] > 2]

    # Burn in roads into raster
    roads = make_geocube(
        vector_data=edges, measurements=["weight"], like=raster_to_match, fill=0
    )["weight"]
    roads = roads.astype("int32")
    return roads


def derive_auxiliary_roads(roads, d_metric=np.inf):
    roads = roads.copy()

    # Remove roads from border to avoid neighbor lookup out of bounds
    roads.values[0, :] = 0
    roads.values[:, 0] = 0
    roads.values[-1, :] = 0
    roads.values[:, -1] = 0

    # Create bands with nearest roads indices
    road_idx = np.column_stack(np.where(roads.values > 0))
    # KDtree for fast neighbor lookup
    tree = KDTree(road_idx)
    # Explicitly create raster grid
    I, J = roads.values.shape
    grid_i, grid_j = np.meshgrid(range(I), range(J), indexing="ij")
    # Get coordinate pairs (i,j) to loop over
    coords = np.column_stack([grid_i.ravel(), grid_j.ravel()])
    # Find nearest road for every lattice point
    # p=inf is chebyshev distance (moore neighborhood)
    dist, idxs = tree.query(coords, p=d_metric)
    # Create bands
    dist = dist.reshape(roads.shape).astype(np.int32)
    road_i = road_idx[:, 0][idxs].reshape(roads.shape).astype(np.int32)
    road_j = road_idx[:, 1][idxs].reshape(roads.shape).astype(np.int32)

    roads.name = "roads"
    road_i = roads.copy(data=road_i)
    road_i.name = "road_i"
    road_j = roads.copy(data=road_j)
    road_j.name = "road_j"
    road_dist = roads.copy(data=dist)
    road_dist.name = "dist"

    return roads, road_i, road_j, road_dist


def derive_auxiliary_roads_numpy(roads, d_metric=np.inf):
    roads = roads.copy()

    # Remove roads from border to avoid neighbor lookup out of bounds
    roads[0, :] = 0
    roads[:, 0] = 0
    roads[-1, :] = 0
    roads[:, -1] = 0

    # Create bands with nearest roads indices
    road_idx = np.column_stack(np.where(roads > 0))
    # KDtree for fast neighbor lookup
    tree = KDTree(road_idx)
    # Explicitly create raster grid
    I, J = roads.shape
    grid_i, grid_j = np.meshgrid(range(I), range(J), indexing="ij")
    # Get coordinate pairs (i,j) to loop over
    coords = np.column_stack([grid_i.ravel(), grid_j.ravel()])
    # Find nearest road for every lattice point
    # p=inf is chebyshev distance (moore neighborhood)
    road_dist, idxs = tree.query(coords, p=d_metric)
    # Create bands
    road_dist = road_dist.reshape(roads.shape).astype(np.int32)
    road_i = road_idx[:, 0][idxs].reshape(roads.shape).astype(np.int32)
    road_j = road_idx[:, 1][idxs].reshape(roads.shape).astype(np.int32)

    return roads, road_i, road_j, road_dist


def load_roads(roads, d_metric=np.inf):
    """Loads preprocessed road rasters.

    The road influenced growth dynamic included in SLEUTH simulates the
    tendency of urban development to be attracted to locations of
    increased accessibility. A transportation network can have major
    influence upon how a region develops.

    Road information is a combination of 4 rasters: road pixes, i and
    j coordinates of the closes road and the distance to the closest
    road.

    In any region some transportation lines may have more affect upon
    urbanization than others. Through road weighting this type of
    influence may be incorporated into the model. The highest road
    weight will increase the probability of accepting urbanization.
    Weights are in the range (1-100).
    """
    roads, road_i, road_j, road_dist = derive_auxiliary_roads(roads, d_metric=d_metric)
    # Normalize road weights to  0-100
    # set values to avoid loosing attrs
    # Max road value is 7 (motorway)
    roads.values = (roads.values * 100 / 7).astype(roads.dtype)

    # Store metadata
    roads.attrs["num_road_pix"] = (roads > 0).sum().item()
    roads.attrs["num_nonroad_pix"] = (roads == 0).sum().item()
    roads.attrs["road_percent"] = roads.attrs["num_road_pix"] / roads.size
    # roads.attrs['histogram'] = Counter(roads.values.ravel())
    roads.attrs["min"] = roads.min().item()
    roads.attrs["max"] = roads.max().item()

    # Validate
    assert roads.min() >= 0
    assert roads.attrs["num_nonroad_pix"] > 0
    assert roads.attrs["num_road_pix"] > 0
    match_idxs = (roads.values[road_i.values.ravel(), road_j.values.ravel()] > 0).all()
    assert match_idxs
    assert roads.shape == road_i.shape
    assert roads.shape == road_j.shape
    assert roads.shape == road_dist.shape

    return roads, road_i, road_j, road_dist


def load_roads_osm(bbox, path_cache, force_download=False):
    print("Loading road network from OSM...")

    # https://wiki.openstreetmap.org/wiki/Key:highway
    # https://wiki.openstreetmap.org/wiki/Highway:International_equivalence#References
    road_types_dict = {
        "motorway": 7,
        "trunk": 6,
        "primary": 5,
        "secondary": 4,
        "tertiary": 3,
        "unclassified": 2,
        "residential": 1,
        "living_street": 1,
        "unknown": 1,
    }

    def simplify_road_type(org_type):
        """Maps OSM road type to integer types in road_types_dict."""

        if not isinstance(org_type, list):
            org_type = [org_type]

        # Check if all types are link type
        # if not remove all link types
        is_link = ["link" in t for t in org_type]
        if sum(is_link) == len(org_type):
            org_type = [t.split("_link")[0] for t in org_type]
        else:
            org_type = [t for t in org_type if "link" not in t]

        # Remove all types not in dict
        org_type = [t if t in road_types_dict.keys() else "unknown" for t in org_type]
        assert len(org_type) > 0

        tp = max(org_type, key=lambda x: road_types_dict[x])

        return road_types_dict[tp]

    # Load the road graph
    G_path = path_cache / "road_network.graphml"
    edges_path = path_cache / "roads.gpkg"
    if not edges_path.is_file() or force_download:
        if not G_path.is_file():
            print("Downloading the graph...")
            # Download roads from OSM
            G = ox.graph_from_polygon(bbox, network_type="drive")
            G = ox.project_graph(G, to_crs="ESRI:54009")
            ox.save_graphml(G, G_path)
        else:
            print("Loading the graph...")
            G = ox.load_graphml(G_path)

        # Create vector geodataframe to burn in
        print("Creating edges gdf...")
        edges = ox.graph_to_gdfs(G, nodes=False)
        # Specify weight type, larger means more accessible
        edges["weight"] = edges.apply(lambda x: simplify_road_type(x.highway), axis=1)
        edges = edges[["length", "weight", "geometry"]]
        edges.to_file(path_cache / "roads.gpkg")
    else:
        print("Loading edges gdf...")
        edges = gpd.read_file(path_cache / "roads.gpkg")

    print("Done.")
    return edges


def create_scenario_file(
    path_cache,
    stop_year,
    scenario="calibration",
    optimizer="grid_search",
    diffusion=0,
    breed=0,
    spread=0,
    slope=0,
    road=0,
):
    # Create output dir if needed
    odir = path_cache / f"sleuth_output_{scenario}"
    odir.mkdir(exist_ok=True)

    if scenario == "calibration":
        # Coefficient values are initial values for
        # some optimizers
        mode = "calibrate"
    elif scenario == "inertial":
        # Calibrated coefficients are used as given
        mode = "predict"
    elif scenario == "fast":
        # Adjust coefficients
        pass
    elif scenario == "slow":
        # Adjust coefficients
        pass

    fpath = path_cache / f"sleuth_scenario_{scenario}.ini"
    f = open(fpath, "w")

    text = "\n".join(
        (
            "[DEFAULT]",
            f"MODE={mode}",
            f"INPUT_DIR={path_cache.absolute()}/",
            "INPUT_FILE=sleuth_inputs.nc",
            f"OUTPUT_DIR={odir.absolute()}/",
            "RANDOM_SEED=0",
            "MONTE_CARLO_ITERS=10",
            f"STOP_YEAR={stop_year}",
            "START_YEAR=2000",
            f"OPTIMIZER={optimizer}",
            "",
            "[COEFFICIENTS]",
            f"DIFFUSION={diffusion}",
            f"BREED={breed}",
            f"SPREAD={spread}",
            f"SLOPE={slope}",
            "CRITICAL_SLOPE=50.0",
            f"ROAD={road}",
            "",
            "[SELF MODIFICATION]",
            "SELF_MOD=false",
            "CRITICAL_LOW=0.97",
            "CRITICAL_HIGH=1.3",
            "BOOM=1.01",
            "BUST=0.9",
            "ROAD_SENS=0.01",
            "SLOPE_SENS=0.1",
            "",
            "[GRID SEARCH]",
            "# You may provide a list grid values or a tuple of (start, end, step)",
            "DIFFUSION=[1, 25, 50, 75, 100]",
            "BREED=[1, 25, 50, 75, 100]",
            "SPREAD=[1, 25, 50, 75, 100]",
            "SLOPE=[1, 25, 50, 75, 100]",
            "ROAD=[1, 25, 50, 75, 100]",
        )
    )
    f.write(text)
    f.close()

    return fpath
