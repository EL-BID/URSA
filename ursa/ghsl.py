import os

import geemap.plotlymap as geemap
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import rasterio as rio
import rioxarray as rxr
import tempfile
import ursa.utils.raster as ru

from PIL import Image, ImageOps
from shapely.geometry import shape

HEIGHT = 600
HIGH_RES = True

url_pop = "https://doi.org/10.2905/D6D86A90-4351-4508-99C1-CB074B022C4A"
url_built = "https://doi.org/10.2905/D07D81B4-7680-4D28-B896-583745C27085"
url_smod = "https://doi.org/10.2905/4606D58A-DC08-463C-86A9-D49EF461C47F"


def download_s3(
    bbox,
    ds,
    data_path=None,
    resolution=1000,
    s3_path="GHSL/",
    bucket="tec-expansion-urbana-p",
):
    """Downloads a GHSL windowed rasters for each available year.

    Takes a bounding box (bbox) and downloads the corresponding rasters from a
    the global COG stored on Amazon S3. Returns a single multiband raster,
    a band per year.

    Parameters
    ----------
    bbox : Polygon
        Shapely Polygon defining the bounding box.
    ds : str
        Data set to download, can be one of SMOD, BUILT_S, POP, or LAND.
    resolution : int
        Resolution of dataset to download, either 100 or 1000.
    data_path : Path
        Path to directory to store rasters.
        If none, don't write to disk.
    s3_dir : str
        Relative path to COGs on S3.
    bucket : str

    Returns
    -------
    raster : rioxarray.DataArray
        In memory raster.

    """

    assert ds in ["SMOD", "BUILT_S", "POP", "LAND"], "Data set not available."

    print(f"Downloading {ds} rasters ...")

    s3_path = f"{s3_path}/GHS_{ds}/"

    if ds == "LAND":
        year_list = [2018]
        fname = f"GHS_{ds}_E{{}}_GLOBE_R2022A_54009_{resolution}_V1_0.tif"
    else:
        fname = f"GHS_{ds}_E{{}}_GLOBE_R2023A_54009_{resolution}_V1_0.tif"
        year_list = list(range(1975, 2021, 5))

    array_list = []
    for year in year_list:
        subset, profile = ru.np_from_bbox_s3(
            s3_path + fname.format(year), bbox, bucket, nodata_to_zero=True
        )
        array_list.append(subset)
    ghs_full = np.concatenate(array_list)

    # Create rioxarray
    profile["count"] = ghs_full.shape[0]
    tmp_name = os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
    with rio.open(tmp_name, "w", **profile) as dst:
        dst.write(ghs_full)
    raster = rxr.open_rasterio(tmp_name)

    # Rename band dimension to reflect years
    raster.coords["band"] = year_list

    if data_path is not None:
        raster.rio.to_raster(data_path / f"GHS_{ds}_{resolution}.tif")

    print("Done.")

    return raster


def load_or_download(
    bbox,
    ds,
    data_path=None,
    resolution=1000,
    s3_path="GHSL/",
    bucket="tec-expansion-urbana-p",
):
    """Searches for a GHS dataset to load, if not available,
    downloads it from S3 and loads it.

    Parameters
    ----------
    bbox : Polygon
        Shapely Polygon defining the bounding box.
    ds : str
        Data set to download, can be one of SMOD, BUILT_S, POP, or LAND.
    resolution : int
        Resolution of dataset to download, either 100 or 1000.
    data_path : Path
        Path to directory to store rasters.
        If none, don't write to disk.
    s3_dir : str
        Relative path to COGs on S3.
    bucket : str

    Returns
    -------
    raster : rioxarray.DataArray
        In memory raster.

    """
    fpath = data_path / f"GHS_{ds}_{resolution}.tif"
    if fpath.exists():
        raster = rxr.open_rasterio(fpath)
        if ds != "LAND":
            raster.coords["band"] = list(range(1975, 2021, 5))
        else:
            raster.coords["band"] = [2018]
    else:
        raster = download_s3(bbox, ds, data_path, resolution, s3_path, bucket)

    return raster


def clip_dataset(ds, polygons):
    ds = ds.rio.set_nodata(0)
    ds = ds.rio.clip(polygons)
    return ds


def load_plot_datasets(bbox_mollweide, path_cache, clip=False):
    smod = load_or_download(
        bbox_mollweide,
        "SMOD",
        data_path=path_cache,
        resolution=1000,
    )
    built = load_or_download(
        bbox_mollweide,
        "BUILT_S",
        data_path=path_cache,
        resolution=100,
    )
    pop = load_or_download(
        bbox_mollweide,
        "POP",
        data_path=path_cache,
        resolution=100,
    )

    if clip:
        smod = clip_dataset(smod, [bbox_mollweide])
        built = clip_dataset(built, [bbox_mollweide])
        pop = clip_dataset(pop, [bbox_mollweide])

    return smod, built, pop


def smod_polygons(smod, centroid):
    """Find SMOD polygons for urban centers and urban clusters.

    Parameters
    ----------
    smod : xarray.DataArray
        DataArray with SMOD raster data.
    centroid : shapely.Point
        Polygons containing centroid will be identified as
        the principal urban center and cluster.
        Must be in Mollweide proyection.

    Returns
    -------
    smod_polygons : GeoDataFrame
        GeoDataFrame with polygons for urban clusters and centers.
    """

    # Get DoU lvl 1 representation (1: rural, 2: cluster, 3: center)
    smod_lvl_1 = smod // 10

    smod_centers = (smod_lvl_1 == 3).astype(smod.dtype)
    smod_clusters = (smod_lvl_1 > 1).astype(smod.dtype)

    transform = smod.rio.transform()

    dict_list = []
    for year in smod["band"].values:
        centers = rio.features.shapes(
            smod_centers.sel(band=year).values, connectivity=8, transform=transform
        )
        clusters = rio.features.shapes(
            smod_clusters.sel(band=year).values, connectivity=8, transform=transform
        )

        center_list = [shape(f[0]) for f in centers if f[1] > 0]
        cluster_list = [shape(f[0]) for f in clusters if f[1] > 0]

        center_dicts = [
            {
                "class": 3,
                "year": year,
                "is_main": centroid.within(center),
                "geometry": center,
            }
            for center in center_list
        ]
        cluster_dicts = [
            {
                "class": 2,
                "year": year,
                "is_main": centroid.within(cluster),
                "geometry": cluster,
            }
            for cluster in cluster_list
        ]
        dict_list += center_dicts
        dict_list += cluster_dicts

    smod_polygons = gpd.GeoDataFrame(dict_list, crs=smod.rio.crs)

    return smod_polygons


def built_s_polygons(built):
    """Returns a polygon per pixel for GHS BUILT rasters."""

    resolution = built.rio.resolution()
    pixel_area = abs(np.prod(resolution))

    built_df = built.to_dataframe(name="b_area").reset_index()
    built_df = built_df.rename(columns={"band": "year"})
    built_df = built_df.drop(columns="spatial_ref")

    built_df = built_df[built_df.b_area > 0].reset_index(drop=True)

    built_df["fraction"] = built_df.b_area / pixel_area
    built_df["geometry"] = built_df.apply(ru.row2cell, res_xy=resolution, axis=1)

    built_gdf = gpd.GeoDataFrame(built_df, crs=built.rio.crs).drop(columns=["x", "y"])

    return built_gdf


def plot_built_poly(built_gdf, bbox_latlon, year=2020):
    """Plots a map with built information for year with polygons.
    May be slow and memory heavy."""

    west, south, east, north = bbox_latlon.bounds

    Map = geemap.Map()

    gdf = built_gdf[built_gdf.year == year].to_crs(4326).reset_index(drop=True)
    gdf["id"] = list(gdf.index)
    fig = px.choropleth_mapbox(
        gdf,
        geojson=gdf.geometry,
        color="fraction",
        locations="id",
        color_continuous_scale="viridis",
        hover_data={"fraction": True, "id": False},
        opacity=0.5,
    )
    fig.update_traces(marker_line_width=0)
    Map.add_traces(fig.data)

    Map.update_layout(
        mapbox_bounds={"west": west, "east": east, "south": south, "north": north},
        height=HEIGHT,
    )

    return Map


def plot_built_agg_img(smod, built, bbox_mollweide, centroid_mollweide, thresh=0.2, language="es"):
    """Plots historic built using an image overlay."""

    translations = {
        "es": {
            "Year": "Año",
            "Peripheral Zones": "Zonas periféricas",
            "Central Zone": "Zona central",
            "Analysis Zone": "Zona de análisis",
        },
        "en": {
            "Year": "Year",
            "Peripheral Zones": "Peripheral Zones",
            "Central Zone": "Central Zone",
            "Analysis Zone": "Analysis Zone",
        },
        "pt": {
            "Year": "Ano",
            "Peripheral Zones": "Zonas periféricas",
            "Central Zone": "Zona central",
            "Analysis Zone": "Zona de análise",
        }
    }
    
    years = [
        "1975",
        "1980",
        "1985",
        "1990",
        "1995",
        "2000",
        "2005",
        "2010",
        "2015",
        "2020",
    ]
    years_uint8 = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype="uint8")

    resolution = built.rio.resolution()
    pixel_area = abs(np.prod(resolution))

    # Create a density array
    # Only densities can be safely reprojected
    built = built / pixel_area

    # Reproject
    built.rio.set_nodata(0)
    built = built.rio.reproject("EPSG:4623")

    # Create a yearly coded binary built array
    built_bin = (built > thresh).astype("uint8")
    built_bin *= years_uint8[:, None, None]
    built_bin.values[built_bin.values == 0] = 200

    # Aggregate yearly binary built data
    # Keep earliest year of observed urbanization
    built_bin_agg = np.min(built_bin, axis=0)
    built_bin_agg.values[built_bin_agg == 200] = 0

    # Create high resolution raster in lat-lon

    # Create array to hold colorized image
    built_img = np.zeros((*built_bin_agg.shape, 4), dtype="uint8")

    # Set colormap
    colors_rgba = [plt.cm.get_cmap("cividis", 10)(i) for i in range(10)]
    colors = (np.array(colors_rgba) * 255).astype("uint8")
    cmap = {y: c for y, c in zip(years_uint8, colors)}
    cmap_cat = {y: mpl.colors.rgb2hex(c) for y, c in zip(years, colors_rgba)}

    # Set colors manually on image array
    for year, color in cmap.items():
        mask = built_bin_agg == year
        built_img[mask] = color

    # Create image bounding box
    lonmin, latmin, lonmax, latmax = built_bin_agg.rio.bounds()
    coordinates = [
        [lonmin, latmin],
        [lonmax, latmin],
        [lonmax, latmax],
        [lonmin, latmax],
    ]

    # Create Image object (memory haevy)
    img = ImageOps.flip(Image.fromarray(built_img))

    # High res image
    if HIGH_RES:
        img = img.resize(
            [hw * 10 for hw in img.size], resample=Image.Resampling.NEAREST
        )

    dummy_df = pd.DataFrame({"lat": [0] * 10, "lon": [0] * 10, "Year": years})
    fig = px.scatter_mapbox(
        dummy_df,
        lat="lat",
        lon="lon",
        color="Year",
        color_discrete_map=cmap_cat,
        mapbox_style="carto-positron",
    )

    fig.update_layout(
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        height=HEIGHT,
        legend_title=translations[language]["Year"],
        legend_orientation="h",
        mapbox_center={"lat": (latmin + latmax) / 2, "lon": (lonmin + lonmax) / 2},
    )

    # Create polygons of urban clusters and centers
    smod_p = smod_polygons(smod, centroid_mollweide)
    clusters_2020 = smod_p[(smod_p.year == 2020) & (smod_p["class"] == 2)]
    clusters_2020 = clusters_2020.to_crs(4326)

    n_mains = 0
    n_other = 0
    for _, row in clusters_2020.iterrows():
        if row.is_main:
            name = translations[language]["Central Zone"]
            n_mains += 1
        else:
            name = translations[language]["Peripheral Zones"]
            n_other += 1

        linestring = row.geometry.exterior
        x, y = linestring.xy
        p_df = pd.DataFrame({"lats": y, "lons": x})
        p_fig = px.line_mapbox(
            p_df,
            lat="lats",
            lon="lons",
            color=[name] * len(x),
            color_discrete_map={
                translations[language]["Central Zone"]: "maroon",
                translations[language]["Peripheral Zones"]: "orange",
            },
        )

        p_fig.update_traces(hovertemplate=None, hoverinfo="skip")

        if row.is_main and n_mains > 1:
            p_fig.update_traces(showlegend=False)
        if not row.is_main and n_other > 1:
            p_fig.update_traces(showlegend=False)

        fig.add_traces(p_fig.data)

    # Add trace of bbox
    bbox_temp = (
        gpd.GeoDataFrame({"geometry": bbox_mollweide}, index=[0], crs="ESRI:54009")
        .to_crs(4326)
        .geometry.iloc[0]
    )
    x, y = bbox_temp.exterior.xy
    p_df = pd.DataFrame({"lats": y, "lons": x})
    p_fig = px.line_mapbox(
        p_df,
        lat="lats",
        lon="lons",
        color=[translations[language]["Analysis Zone"]] * len(x),
        color_discrete_map={translations[language]["Analysis Zone"]: "blue"},
    )
    p_fig.update_traces(hovertemplate=None, hoverinfo="skip")
    fig.add_traces(p_fig.data)

    fig.update_layout(
        mapbox_layers=[
            {
                "sourcetype": "image",
                "source": img,
                "coordinates": coordinates,
                "opacity": 0.7,
                "below": "traces",
            }
        ]
    )

    fig.add_annotation(
        text=f'Datos de: <a href="{url_built}"">GHS-BUILT-S</a>',
        showarrow=False,
        xref="paper",
        yref="paper",
        x=1,
        y=0,
    )

    return fig


def get_urb_growth_df(smod, built, pop, centroid_mollweide, path_cache):
    built.rio.set_nodata(0)
    pop.rio.set_nodata(0)

    smod_gdf = smod_polygons(smod, centroid_mollweide)
    smod_gdf["Area"] = smod_gdf.area

    clusters_gdf = smod_gdf[smod_gdf["class"] == 2]

    main_cluster = clusters_gdf[clusters_gdf.is_main]

    # Total built-up area and pop per year
    # Built raster contains squared meters
    total_built = built.sum(axis=(1, 2)).values
    total_pop = pop.sum(axis=(1, 2)).values

    # Built and pop within center and cluster
    years = smod.coords["band"].values
    cluster_built = []
    cluster_pop = []
    cluster_built_all = []
    cluster_pop_all = []

    for year in years:
        # Check if main cluster is empty
        if main_cluster[main_cluster.year == year].empty:
            cluster_built.append(0)
            cluster_pop.append(0)
            cluster_built_all.append(0)
            cluster_pop_all.append(0)
        else:
            # Main cluster and center
            cluster = main_cluster[main_cluster.year == year].geometry.iloc[0]

            # All clusters and centers
            cluster_all = clusters_gdf[clusters_gdf.year == year].geometry

            # Series for main cluster and center
            cluster_built.append(
                np.nansum(
                    built.sel(band=year)
                    .rio.set_nodata(0)
                    .rio.clip([cluster], crs=built.rio.crs)
                    .values
                )
            )

            cluster_pop.append(
                np.nansum(
                    pop.sel(band=year)
                    .rio.set_nodata(0)
                    .rio.clip([cluster], crs=pop.rio.crs)
                    .values
                )
            )

            # Series for ALL clusters and centers
            cluster_built_all.append(
                np.nansum(
                    built.sel(band=year)
                    .rio.set_nodata(0)
                    .rio.clip(cluster_all, crs=built.rio.crs)
                    .values
                )
            )

            cluster_pop_all.append(
                np.nansum(
                    pop.sel(band=year)
                    .rio.set_nodata(0)
                    .rio.clip(cluster_all, crs=pop.rio.crs)
                    .values
                )
            )

    cluster_built = np.array(cluster_built)
    cluster_pop = np.array(cluster_pop)
    cluster_built_all = np.array(cluster_built_all)
    cluster_pop_all = np.array(cluster_pop_all)

    # Identify year that are not in main, i.e. years without a main cluster
    years_not_int_main = set(years) - set(main_cluster.year.values)

    # Create dummy dataframe with years without a main cluster with 'Area' set to zero
    dummy_dataframe = pd.DataFrame(years_not_int_main, columns=["year"])
    dummy_dataframe["Area"] = 0

    # Complete clusters_gdf and main_cluster with dummy_dataframe
    clusters_gdf = pd.concat([clusters_gdf, dummy_dataframe], ignore_index=True)
    main_cluster = pd.concat([main_cluster, dummy_dataframe], ignore_index=True)

    # Urban area for main cluster and center
    cluster_area = main_cluster.sort_values("year").Area.values

    # Total cluster and center area
    t_cluster_area = clusters_gdf.groupby("year").Area.sum().values

    df = pd.DataFrame(
        {
            "year": smod.coords["band"].values,
            "built_all": total_built / 1e6,
            "built_cluster_main": cluster_built / 1e6,
            "built_cluster_all": cluster_built_all / 1e6,
            "built_cluster_other": (cluster_built_all - cluster_built) / 1e6,
            "built_rural": (total_built - cluster_built) / 1e6,
            "urban_cluster_all": t_cluster_area / 1e6,
            "urban_cluster_main": cluster_area / 1e6,
            "urban_cluster_other": (t_cluster_area - cluster_area) / 1e6,
            "pop_total": total_pop,
            "pop_cluster_main": cluster_pop,
            "pop_cluster_all": cluster_pop_all,
            "pop_cluster_other": (cluster_pop_all - cluster_pop),
            "pop_rural": (total_pop - cluster_pop_all) / 1e6,
            "built_density_cluster_main": cluster_built / cluster_area,
            "built_density_cluster_all": cluster_built_all / t_cluster_area,
            "built_density_cluster_other": (
                (cluster_built_all - cluster_built) / (t_cluster_area - cluster_area)
            ),
            "pop_density_cluster_main": cluster_pop / (cluster_area / 1e6),
            "pop_density_cluster_all": cluster_pop_all / (t_cluster_area / 1e6),
            "pop_density_cluster_other": (
                (cluster_pop_all - cluster_pop)
                / ((t_cluster_area - cluster_area) / 1e6)
            ),
            "pop_b_density_cluster_main": cluster_pop / (cluster_built / 1e6),
            "pop_b_density_cluster_all": (cluster_pop_all / (cluster_built_all / 1e6)),
            "pop_b_density_cluster_other": (
                (cluster_pop_all - cluster_pop)
                / ((cluster_built_all - cluster_built) / 1e6)
            ),
        }
    )

    df.to_csv(path_cache / "urban_growth.csv")

    return df


def plot_smod_clusters(smod, bbox_latlon, feature="clusters", language='es'):
    
    translations = {
        "es": {"Year": "Año"},
        "en": {"Year": "Year"},
        "pt": {"Year": "Ano"}
    }
    
    if feature == "clusters":
        c_code = 2
    elif feature == "centers":
        c_code = 3
    else:
        print("Feature must be either clusters or centers.")
        assert False

    smod_lvl_1 = smod // 10

    smod_lvl_1_df = smod_lvl_1.to_dataframe(name="smod").reset_index()
    smod_lvl_1_df = smod_lvl_1_df.drop(columns="spatial_ref")

    df = smod_lvl_1_df[smod_lvl_1_df.smod >= c_code].drop(columns="smod")

    df = df.groupby(["x", "y"]).min().reset_index()
    df = df.rename(columns={"band": translations[language]["Year"]})
    df = df.sort_values(translations[language]["Year"]).reset_index(drop=True)

    df["geometry"] = df.apply(ru.row2cell, res_xy=smod.rio.resolution(), axis=1)

    gdf = gpd.GeoDataFrame(df.drop(columns=["x", "y"]), crs=smod.rio.crs)

    gdf[translations[language]["Year"]] = gdf[translations[language]["Year"]].astype(str)

    # Set colormap
    years = [
        "1975",
        "1980",
        "1985",
        "1990",
        "1995",
        "2000",
        "2005",
        "2010",
        "2015",
        "2020",
    ]
    colors_rgba = [plt.cm.get_cmap("cividis", 10)(i) for i in range(10)]
    cmap_cat = {y: mpl.colors.rgb2hex(c) for y, c in zip(years, colors_rgba)}

    gdf = gdf.to_crs(epsg=4326).reset_index()
    fig = px.choropleth_mapbox(
        gdf,
        geojson=gdf.geometry,
        color=translations[language]["Year"],
        locations="index",
        hover_name=None,
        hover_data={translations[language]["Year"]: True, "index": False},
        color_discrete_map=cmap_cat,
        opacity=0.5,
        mapbox_style="carto-positron",
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(
        mapbox_center={
            "lat": bbox_latlon.centroid.xy[1][0],
            "lon": bbox_latlon.centroid.xy[0][0],
        }
    )

    fig.add_annotation(
        text=f'Datos de: <a href="{url_smod}"">GHS-SMOD</a>',
        showarrow=False,
        xref="paper",
        yref="paper",
        x=1,
        y=0,
    )

    fig.update_layout(
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        height=HEIGHT,
        # width=600,
        legend_orientation="h",
    )

    # fig.write_html(f'fig_urban_{feature}_historic.html')

    return fig


def plot_built_year_img(
    smod, built, bbox_latlon, bbox_mollweide, centroid_mollweide, year=2020, language = "es"
):
    """Plots built for year using an image overlay."""

    translations = {
        "es": {
            "Year": "Año",
            "Fraction": "Fracción",
            "Of Construction": "de construcción",
            "Peripheral Zones": "Zonas periféricas",
            "Central Zone": "Zona central",
            "Analysis Zone": "Zona de análisis"
        },
        "en": {
            "Year": "Year",
            "Fraction": "Fraction",
            "Of Construction": "of construction",
            "Peripheral Zones": "Peripheral Zones",
            "Central Zone": "Central Zone",
            "Analysis Zone": "Analysis Zone"
        },
        "pt": {
            "Year": "Ano",
            "Fraction": "Fração",
            "Of Construction": "de construção",
            "Peripheral Zones": "Zonas periféricas",
            "Central Zone": "Zona central",
            "Analysis Zone": "Zona de análise"
        }
    }

    resolution = built.rio.resolution()
    pixel_area = abs(np.prod(resolution))

    # Select specific year and transform into density
    # Only densitities can be safely reprojected
    built = built.sel(band=year) / pixel_area
    built.rio.set_nodata(0)

    # Reprojecto to lat lon
    built = built.rio.reproject(dst_crs=4326)

    # Get colorized image.
    cmap = plt.get_cmap("cividis").copy()
    colorized = cmap(built)
    mask = built.values == 0
    colorized[mask] = (0, 0, 0, 0)
    colorized = np.uint8(colorized * 255)
    img = ImageOps.flip(Image.fromarray(colorized))

    # Create image bounding box
    lonmin, latmin, lonmax, latmax = built.rio.bounds()
    coordinates = [
        [lonmin, latmin],
        [lonmax, latmin],
        [lonmax, latmax],
        [lonmin, latmax],
    ]

    # Create figure
    west, south, east, north = bbox_latlon.bounds

    c_col = f"{translations[language]['Fraction']} <br> {translations[language]['Of Construction']} <br> {year}"

    dummy_df = pd.DataFrame({"lat": [0] * 2, "lon": [0] * 2, c_col: [0.0, 1.0]})
    fig = px.scatter_mapbox(
        dummy_df,
        lat="lat",
        lon="lon",
        color=c_col,
        color_continuous_scale="cividis",
        mapbox_style="carto-positron",
    )
    fig.update_layout(
        mapbox_center={"lat": (latmin + latmax) / 2, "lon": (lonmin + lonmax) / 2}
    )

    fig.update_layout(
        margin={"r": 0, "t": 30, "l": 0, "b": 0}, height=HEIGHT, legend_orientation="h"
    )

    # Create polygons of urban clusters and centers
    smod_p = smod_polygons(smod, centroid_mollweide)
    clusters_2020 = smod_p[(smod_p.year == 2020) & (smod_p["class"] == 2)]
    clusters_2020 = clusters_2020.to_crs(4326)

    n_mains = 0
    n_other = 0
    for i, row in clusters_2020.iterrows():
        if row.is_main:
            name = translations[language]["Central Zone"]
            n_mains += 1
        else:
            name = translations[language]["Peripheral Zones"]
            n_other += 1

        linestring = row.geometry.exterior
        x, y = linestring.xy
        p_df = pd.DataFrame({"lats": y, "lons": x})
        p_fig = px.line_mapbox(
            p_df,
            lat="lats",
            lon="lons",
            color=[name] * len(x),
            color_discrete_map={
                translations[language]["Central Zone"]: "maroon",
                translations[language]["Peripheral Zones"]: "orange",
            },
        )

        p_fig.update_traces(hovertemplate=None, hoverinfo="skip")

        if row.is_main and n_mains > 1:
            p_fig.update_traces(showlegend=False)
        if not row.is_main and n_other > 1:
            p_fig.update_traces(showlegend=False)

        fig.add_traces(p_fig.data)

    # Add trace of bbox
    bbox_temp = (
        gpd.GeoDataFrame({"geometry": bbox_mollweide}, index=[0], crs="ESRI:54009")
        .to_crs(4326)
        .geometry.iloc[0]
    )
    x, y = bbox_temp.exterior.xy
    p_df = pd.DataFrame({"lats": y, "lons": x})
    p_fig = px.line_mapbox(
        p_df,
        lat="lats",
        lon="lons",
        color=[translations[language]["Analysis Zone"]] * len(x),
        color_discrete_map={translations[language]["Analysis Zone"]: "blue"},
    )
    p_fig.update_traces(hovertemplate=None, hoverinfo="skip")
    fig.add_traces(p_fig.data)


    # High res image
    if HIGH_RES:
        img = img.resize(
            [hw * 10 for hw in img.size], resample=Image.Resampling.NEAREST
        )

    fig.update_layout(coloraxis_colorbar_orientation="h")
    fig.update_layout(
        mapbox_layers=[
            {
                "sourcetype": "image",
                "source": img,
                "coordinates": coordinates,
                "opacity": 0.7,
                "below": "traces",
            }
        ]
    )

    fig.add_annotation(
        text=f'Datos de: <a href="{url_built}"">GHS-BUILT-S</a>',
        showarrow=False,
        xref="paper",
        yref="paper",
        x=1,
        y=0,
    )

    return fig


def plot_pop_year_img(smod, pop, bbox_mollweide, centroid_mollweide, year=2020, language = "es"):
    
    translations = {
    "es": {
        "Population": "Población",
        "Central Zone": "Zona central",
        "Peripheral Zones": "Zonas periféricas",
        "Analysis Zone": "Zona de análisis"
    },
    "en": {
        "Population": "Population",
        "Central Zone": "Central Zone",
        "Peripheral Zones": "Peripheral Zones",
        "Analysis Zone": "Analysis Zone"
    },
    "pt": {
        "Population": "População",
        "Central Zone": "Zona central",
        "Peripheral Zones": "Zonas periféricas",
        "Analysis Zone": "Zona de análise"
    }
}
    
    resolution = pop.rio.resolution()
    pixel_area = abs(np.prod(resolution)) / 1e6

    # Select specific year and transform into density
    # Only densitities can be safely reprojected
    pop = pop.sel(band=year) / pixel_area
    pop.rio.set_nodata(0)

    # Reprojecto to lat lon
    pop = pop.rio.reproject(dst_crs=4326)

    # Get back counts
    pop = pop * ru.get_area_grid(pop, "km")

    # Normalize values for colormap
    n_classes = 7
    pop_min = np.unique(pop)[1]
    bounds = np.array(
        [-1, pop_min / 2.0, 5.5, 20.5, 100.5, 300.5, 500.5, 1000.5, 10000]
    )
    norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=n_classes + 1)
    pop_norm = norm(pop).data / n_classes

    # Get colorized image.
    cmap = plt.get_cmap("cividis").copy()
    colorized = cmap(pop_norm)
    mask = pop_norm == 0
    colorized[mask] = (0, 0, 0, 0)
    colorized = np.uint8(colorized * 255)
    img = ImageOps.flip(Image.fromarray(colorized))

    # Create image bounding box
    lonmin, latmin, lonmax, latmax = pop.rio.bounds()
    coordinates = [
        [lonmin, latmin],
        [lonmax, latmin],
        [lonmax, latmax],
        [lonmin, latmax],
    ]

    mid_vals = ["3", "10", "50", "200", "400", "750", "2000"]
    cls_names = [
        "0 - 5",
        "6 - 20",
        "21 - 100",
        "101 - 300",
        "301 - 500",
        "501 - 1,000",
        "1,001 - Max",
    ]
    names = {v: n for v, n in zip(mid_vals, cls_names)}
    colors_d = [mpl.colors.rgb2hex(c) for c in cmap([int(v) for v in mid_vals])]
    cmap_d = {v: c for v, c in zip(mid_vals, colors_d)}

    dummy_df = pd.DataFrame(
    {"lat": [0] * n_classes, "lon": [0] * n_classes, translations[language]["Population"]: mid_vals}
    )

    fig = px.scatter_mapbox(
        dummy_df,
        lat="lat",
        lon="lon",
        color=translations[language]["Population"],
        color_discrete_map=cmap_d,
        mapbox_style="carto-positron",
    )
    fig.update_layout(
        mapbox_center={"lat": (latmin + latmax) / 2, "lon": (lonmin + lonmax) / 2}
    )

    fig.for_each_trace(lambda t: t.update(name=names[t.name]))

    fig.update_layout(
        margin={"r": 0, "t": 30, "l": 0, "b": 0}, height=HEIGHT, legend_orientation="h"
    )

    # Create polygons of urban clusters and centers
    smod_p = smod_polygons(smod, centroid_mollweide)
    clusters_2020 = smod_p[(smod_p.year == 2020) & (smod_p["class"] == 2)]
    clusters_2020 = clusters_2020.to_crs(4326)

    n_mains = 0
    n_other = 0
    for i, row in clusters_2020.iterrows():
        if row.is_main:
            name = translations[language]["Central Zone"]
            n_mains += 1
        else:
            name = translations[language]["Peripheral Zones"]
            n_other += 1

        linestring = row.geometry.exterior
        x, y = linestring.xy
        p_df = pd.DataFrame({"lats": y, "lons": x})
        p_fig = px.line_mapbox(
            p_df,
            lat="lats",
            lon="lons",
            color=[name] * len(x),
            color_discrete_map={
                translations[language]["Central Zone"]: "maroon",
                translations[language]["Peripheral Zones"]: "orange",
            },
        )

        p_fig.update_traces(hovertemplate=None, hoverinfo="skip")

        if row.is_main and n_mains > 1:
            p_fig.update_traces(showlegend=False)
        if not row.is_main and n_other > 1:
            p_fig.update_traces(showlegend=False)

        fig.add_traces(p_fig.data)

    # Agregar traza del bbox
    bbox_temp = (
        gpd.GeoDataFrame({"geometry": bbox_mollweide}, index=[0], crs="ESRI:54009")
        .to_crs(4326)
        .geometry.iloc[0]
    )
    x, y = bbox_temp.exterior.xy
    p_df = pd.DataFrame({"lats": y, "lons": x})
    p_fig = px.line_mapbox(
        p_df,
        lat="lats",
        lon="lons",
        color=[translations[language]["Analysis Zone"]] * len(x),
        color_discrete_map={translations[language]["Analysis Zone"]: "blue"},
    )
    p_fig.update_traces(hovertemplate=None, hoverinfo="skip")
    fig.add_traces(p_fig.data)

    # High res image
    if HIGH_RES:
        img = img.resize(
            [hw * 10 for hw in img.size], resample=Image.Resampling.NEAREST
        )

    fig.update_layout(
        mapbox_layers=[
            {
                "sourcetype": "image",
                "source": img,
                "coordinates": coordinates,
                "opacity": 0.7,
                "below": "traces",
            }
        ]
    )

    fig.add_annotation(
        text=f'Datos de: <a href="{url_pop}"">GHS-POP</a>',
        showarrow=False,
        xref="paper",
        yref="paper",
        x=1,
        y=0,
    )

    return fig


def plot_growth(growth_df, *, y_cols, title, ylabel, var_type="extensive", language = "es"):
    if var_type == "extensive":
        p_func = px.area
    elif var_type == "intensive":
        p_func = px.line

    fig = p_func(growth_df, x="year", y=y_cols, markers=True)

    translations_year = {
        "es": "Año",
        "en": "Year",
        "pt": "Ano"
    }
    
    fig.update_layout(
        yaxis_title=ylabel,
        yaxis_tickformat=",.3~f",
        xaxis_title=translations_year[language],
        legend_title=title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig.update_layout(hovermode="x")
    if "pop" in y_cols[0] or "urban" in y_cols[0]:
        fig.update_traces(hovertemplate="%{y:.0f}<extra></extra>")
    else:
        fig.update_traces(hovertemplate="%{y:.2f}<extra></extra>")

    name_dict = {
        "all": "Todas las zonas {} {:.2f}%",
        "main": "Zona central {} {:.2f}%",
        "other": "Zonas periféricas  {} {:.2f}%",
    }
    
    name_dict_translations = {
        "es": {
            "all": "Todas las zonas {} {:.2f}%",
            "main": "Zona central {} {:.2f}%",
            "other": "Zonas periféricas {} {:.2f}%",
        },
        "en": {
            "all": "All zones {} {:.2f}%",
            "main": "Central zone {} {:.2f}%",
            "other": "Peripheral zones {} {:.2f}%",
        },
        "pt": {
            "all": "Todas as zonas {} {:.2f}%",
            "main": "Zona central {} {:.2f}%",
            "other": "Zonas periféricas {} {:.2f}%",
        }
    }

    name_dict = name_dict_translations[language]
    
    color_dict = {"all": "black", "main": "maroon", "other": "orange"}
    options = ["all", "main", "other"]

    names = {}
    colors = {}

    for col in y_cols:
        i = 0
        c0 = growth_df[col].iloc[i]
        while np.isnan(c0):
            i += 1
            c0 = growth_df[col].iloc[i]

        cf = growth_df[col].iloc[-1]
        delta = (cf - c0) / c0 * 100
        if delta > 0:
            up_down = "▲"
        else:
            up_down = "▼"
        for option in options:
            if option in col:
                names[col] = name_dict[option].format(up_down, delta)
                colors[col] = color_dict[option]

    fig.for_each_trace(
        lambda t: t.update(line_color=colors[t.name], name=names[t.name])
    )

    return fig
