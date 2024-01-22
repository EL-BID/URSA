from osgeo import gdal
import numpy as np
import geopandas as gpd
import rasterio as rio
from shapely.geometry import box, Polygon
import ee
from pathlib import Path
import rioxarray as rxr
import xarray as xr


def row2cell(row, res_xy):
    # Extract resolution for each dimension
    res_x, res_y = res_xy

    # XY Coordinates are centered on the pixel
    minX = row["x"] - (res_x / 2)
    maxX = row["x"] + (res_x / 2)
    minY = row["y"] + (res_y / 2)
    maxY = row["y"] - (res_y / 2)

    poly = box(minX, minY, maxX, maxY)

    return poly


def km_2_lat(d):
    # radius of the earth
    R = 6371
    # conversion
    lat = (180 / np.pi) * d / R

    return lat


def km_2_lon(d, lat):
    # radius of the earth
    R = 6371
    # conversion
    lat_rad = np.pi / 180 * lat
    lon_rad = d / (R * np.cos(lat_rad))

    return 180 / np.pi * lon_rad


def buffer_geometry(bounds, buff):
    delta_lat = bounds[3] - bounds[1]
    delta_lon = bounds[2] - bounds[0]

    mid_lat = (bounds[3] + bounds[1]) / 2
    mid_lon = (bounds[2] + bounds[0]) / 2

    buff_lat = km_2_lat(buff)
    delta_lat += 2 * buff_lat
    buff_lon = km_2_lon(buff, mid_lat)
    delta_lon += 2 * buff_lon

    lat_max = mid_lat + delta_lat / 2
    lat_min = mid_lat - delta_lat / 2
    lon_max = mid_lon + delta_lon / 2
    lon_min = mid_lon - delta_lon / 2

    bbox = Polygon(
        [(lon_min, lat_min), (lon_max, lat_min), (lon_max, lat_max), (lon_min, lat_max)]
    )
    bbox = gpd.GeoDataFrame(geometry=[bbox], crs="EPSG:4326")
    return bbox


def get_bboxes(city, country, data_path, buff=10, square=False):
    """Calculates a bounding box for city in country.

    This functions uses data from the GHSL's 2015 definition of urban
    centers to locate a city and obtains bounding box with a buffer arround
    the defintion of functional urban area.
    Return the bounding box in the desired projection, the default being
    Mollweide, the projection of the GHSL data.

    Parameters
    ----------
    city : str
        The city to search for.
    country : str
        The country the city belongs to.
    data_path : Path
        Path where data files are stored in a subdirectory
        output/cities/{file}
        This are geopackage files previously generated from GHSL data.
    buff : int or float
        Buffer in kilometers arround the functional urban area used to
        define the bounding box.
    proj: str
        Projection code for the desired projection of bbox.

    Returns
    -------
    bbox : Polygon
        Shapely polygon for the bounding box.
    uc : GeoDataFrame
        Single line GeoDataFrame with the urban center for city.
    fua : GeoDataFrame
        Single line GeoDataFrame with the functional urban area for city.

    """

    cities_uc = gpd.read_file(data_path / "cities_uc.gpkg")
    cities_fua = gpd.read_file(data_path / "cities_fua.gpkg")
    uc = cities_uc.loc[(cities_uc.country == country) & (cities_uc.city == city)]
    fua = cities_fua.loc[(cities_fua.country == country) & (cities_fua.city == city)]

    # Build the bounding box in the orignal lat lon projection
    poly = fua.geometry.values[0]
    bounds = poly.bounds

    bbox = buffer_geometry(bounds, buff)
    bbox = bbox.envelope.iloc[0]

    if square:
        centroid = bbox.centroid
        minx, miny, maxx, maxy = bbox.bounds
        delta = max((maxx - minx), (maxy - miny))
        bbox = centroid.buffer(delta/2, cap_style=3)

    return (
        bbox,
        uc.iloc[0]["geometry"],
        fua.iloc[0]["geometry"],
    )


def np_from_bbox_s3(
    s3_path, bbox, bucket="tec-expansion-urbana-p", nodata_to_zero=False
):
    """Downloads a windowed raster with bounds defined by bbox from an
    COG stored in an Amaxon S3 bucket and stores it in memory in a numpy array.

    Uses bbox to define a search window to download a portion of a raster from
    a Cloud Optimized Geotiff stored in a public bucket in Amazon S3
    in s3_path.
    Store the raster in memory in a Numpy array.

    Parameters
    ----------
    s3_path : str
        The relative path of the COG in S3.
    bbox : Polygon
        Shapely Polygon defining the raster's bounding box.
    bucket : str
        Name of the S3 bucket with the COG.
    nodata_to_zero : bool
        If True, sets the output raster's nodata attribute to 0.

    Returns
    -------
    subset : np.array
        Numpy array with raster data.
    profile : dict
        Dictionary with geographical properties of the raster.

    """

    gdal.PushErrorHandler("CPLQuietErrorHandler")

    url = f"http://{bucket}.s3.amazonaws.com/{s3_path}"

    with rio.open(url) as src:
        profile = src.profile.copy()
        transform = profile["transform"]
        window = rio.windows.from_bounds(*bbox.bounds, transform)
        window = window.round_lengths().round_offsets()
        # The transform is specified as (dx, rot_x, x_0 , rot_y, dy, y0)
        new_transform = src.window_transform(window)
        profile.update(
            {"height": window.height, "width": window.width, "transform": new_transform}
        )
        subset = src.read(window=window)
    if nodata_to_zero:
        subset[subset == profile["nodata"]] = 0

    return subset, profile


def tif_from_bbox_s3(
    s3_path, local_path, bbox, bucket="tec-expansion-urbana-p", nodata_to_zero=False
):
    """Downloads a windowed raster with bounds defined by bbox from an
    COG stored in an Amaxon S3 bucket and saves a local geotiff file.

    Uses bbox to define a search window to download a portion of a raster from
    a Cloud Optimized Geotiff stored in a public bucket in Amazon S3
    in s3_path.
    Saves the raster to a local geotiff file in local_path.

    Parameters
    ----------
    s3_path : str
        The relative path of the COG in S3.
    local_path : Path
        Path to local file to store raster.
    bbox : Polygon
        Shapely Polygon defining the raster's bounding box.
    bucket : str
        Name of the S3 bucket with the COG.
    nodata_to_zero : bool
        If True, sets the output raster's nodata attribute to 0.

    """

    subset, profile = np_from_bbox_s3(s3_path, bbox, bucket, nodata_to_zero)

    with rio.open(local_path, "w", **profile) as dst:
        dst.write(subset)


def lat_2_meter(lat, delta):
    """Converts from degrees of latitued to meters.

    Takes a given latitud and a small distance delta in degreed,
    and ouput that same delta in meters.
    Conversion formula is taken from:
    https://en.wikipedia.org/wiki/Latitude#Meridian_distance_on_the_ellipsoid


    Parameters
    ----------
    lat : float or np.array
        Latitude at which to perform conversion.
    delta : float
        Small distance delta in degrees.

    Returns
    -------
    delta_in_m : float
        Delta distance in meters.

    """
    lat_rad = np.pi / 180 * abs(lat)

    a = 6378137.0
    b = 6356752.3142
    e2 = (a**2 - b**2) / a**2

    lat_in_m = a * (1 - e2) / (1 - e2 * np.sin(lat_rad) ** 2) ** (3 / 2)
    lat_in_m *= np.pi / 180
    delta_in_m = lat_in_m * delta

    return delta_in_m


def lon_2_meter(lat, delta):
    """Converts from degrees of longitude to meters.

    Takes a given longitude and a small distance delta in degrees,
    and ouput that same delta in meters.
    Conversion formula is taken from:
    https://en.wikipedia.org/wiki/Longitude#Length_of_a_degree_of_longitude


    Parameters
    ----------
    lat : float or np.array
        Latitude at which to perform conversion.
    delta : float
        Small distance delta in degrees.

    Returns
    -------
    delta_in_m : float
        Delta distance in meters.

    """
    lat_rad = np.pi / 180 * abs(lat)

    a = 6378137.0
    b = 6356752.3142
    e2 = (a**2 - b**2) / a**2

    lon_in_m = a * np.cos(lat_rad) / np.sqrt(1 - e2 * np.sin(lat_rad) ** 2)
    lon_in_m *= np.pi / 180

    delta_in_m = lon_in_m * delta

    return delta_in_m


def get_area_grid(raster_xr, units):
    """Takes an input raster in lat lon coordinates and outputs a corresponding
    grid with each pixel's area in {units}.

    Parameters
    ----------
    raster_xr : DataArray
        Input raster in lat-lon coordinates.
    units : str
        Area units of the output raster, either 'm', 'km', or 'ha'.

    Returns
    -------
    area_grid : np.array
        Numpy array with each pixels area in {units}.

    """

    c_factor = {"m": 1, "km": 1 / 1e6, "ha": 1 / 1e4}

    x_ar = raster_xr.coords["x"].values
    y_ar = raster_xr.coords["y"].values
    lon_grid, lat_grid = np.meshgrid(x_ar, y_ar)
    delta_x, delta_y = [abs(x) for x in raster_xr.rio.resolution()]

    area_grid = lat_2_meter(lat_grid, delta_y) * lon_2_meter(lat_grid, delta_x)
    area_grid *= c_factor[units]

    return area_grid


def bbox_to_ee(bbox):
    bbox_ee = ee.Geometry.Polygon([t for t in zip(*bbox.exterior.coords.xy)])

    return bbox_ee


def tif_from_bbox_local(raster_path, local_path, bbox, nodata_to_zero=False):
    """Downloads a windowed raster with bounds defined by bbox from a
    local COG and saves a local geotiff file.

    Parameters
    ----------
    raster_path : str
        The path of the COG.
    local_path : Path
        Path to local file to store raster.
    bbox : Polygon
        Shapely Polygon defining the raster's bounding box.
    nodata_to_zero : bool
        If True, sets the output raster's nodata attribute to 0.

    """
    subset, profile = np_from_bbox_local(raster_path, bbox, nodata_to_zero)

    with rio.open(local_path, "w", **profile) as dst:
        dst.write(subset)


def np_from_bbox_local(local_path, bbox, nodata_to_zero=False):
    """Downloads a windowed raster with bounds defined by bbox from a
    local COG and stores it in memory in a numpy array.

    Parameters
    ----------
    local_path : str
        The relative path of the COG.
    bbox : Polygon
        Shapely Polygon defining the raster's bounding box.
    nodata_to_zero : bool
        If True, sets the output raster's nodata attribute to 0.

    Returns
    -------
    subset : np.array
        Numpy array with raster data.
    profile : dict
        Dictionary with geographical properties of the raster.

    """

    with rio.open(local_path) as src:
        profile = src.profile.copy()
        transform = profile["transform"]
        window = rio.windows.from_bounds(*bbox.bounds, transform)
        window = window.round_lengths().round_offsets()
        # The transform is specified as (dx, rot_x, x_0 , rot_y, dy, y0)
        new_transform = src.window_transform(window)
        profile.update(
            {"height": window.height, "width": window.width, "transform": new_transform}
        )
        subset = src.read(window=window)
    if nodata_to_zero:
        subset[subset == profile["nodata"]] = 0

    return subset, profile


def pop_2_density(raster, units="ha", save=False):
    """Tranforms a populatiuon counts raster into a population density raster.

    Takes a raster in lat-lon with population counts as input
    and outputs a raster with population density in people per {units}^2.
    Takes into account pixel area variability in lat-lon coordinates.

    Parameters
    ----------
    raster : DataArray or Path
        Input raster in population counts in lat-lon.
    units : str
        Units of lenght to use when calculating areas.
        Can be 'm', 'km', or 'ha'.
    save : bool
        Wether to save a geotiff to disk.

    Returns
    -------
    density_xr : DataArray
        Raster array with population density.

    """

    # Load population raster
    if isinstance(raster, Path):
        pop_rxr = rxr.open_rasterio(raster)
    elif isinstance(raster, xr.DataArray):
        pop_rxr = raster
        save = False
    else:
        print("Input must be either path or DataArray.")
        return

    area_grid = get_area_grid(pop_rxr, units)

    density_ar = pop_rxr.values / area_grid
    density_xr = pop_rxr.copy(data=density_ar)
    if save:
        fname = f"{raster.stem}-density-{units}-{raster.suffix}"
        density_xr.rio.to_raster(raster.parent / fname)

    return density_xr
