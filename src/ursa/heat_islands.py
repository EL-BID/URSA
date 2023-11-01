import ee
import json

import geemap.plotlymap as geemap
import geopandas as gpd
import pandas as pd
import ursa.ghsl as ghsl
import ursa.utils.geometry as ug
import ursa.utils.raster as ru
import plotly.express as px
import plotly.graph_objects as go
import ursa.world_cover as wc

from typing import Tuple, List
from ursa.sleuth_prep import load_roads_osm

MAX_PIXELS = 1e10

colors = {
    "Muy frío": "#2166AC",
    "Frío": "#67A9CF",
    "Ligeramente frío": "#D1E5F0",
    "Templado": "#F7F7F7",
    "Ligeramente cálido": "#FDDBC7",
    "Caliente": "#EF8A62",
    "Muy caliente": "#B2182B",
}

TEMP_CAT_MAP = {i + 1: n for i, n in enumerate(colors.keys())}

RdBu7 = ["#2166AC", "#67A9CF", "#D1E5F0", "#F7F7F7", "#FDDBC7", "#EF8A62", "#B2182B"]

RdBu7k = ["#2166AC", "#67A9CF", "#D1E5F0", "#808080", "#FDDBC7", "#EF8A62", "#B2182B"]

TEMP_NAMES = list(TEMP_CAT_MAP.values())

TEMP_PALETTE_MAP = {x: y for x, y in zip(TEMP_NAMES, RdBu7)}

TEMP_PALETTE_MAP_INV = {value: key for key, value in TEMP_PALETTE_MAP.items()}

TEMP_PALETTE_MAP_K = {x: y for x, y in zip(TEMP_NAMES, RdBu7k)}

TEMP_PALETTE_MAP_INV_K = {value: key for key, value in TEMP_PALETTE_MAP_K.items()}


def date_format(season, year):
    sdict = {
        "Q1": [f"{year}-3-1", f"{year}-5-31"],
        "Q2": [f"{year}-6-1", f"{year}-8-31"],
        "Q3": [f"{year}-9-1", f"{year}-11-30"],
        "Q4": [f"{year}-12-1", f"{year + 1}-2-29"],
        "Qall": [f"{year}-1-1", f"{year}-12-31"],
    }

    return sdict[season]


def fmask(image):
    qa = image.select("QA_PIXEL")

    dilated_cloud_bit = 1
    cloud_bit = 3
    cloud_shadow_bit = 4

    mask = qa.bitwiseAnd(1 << dilated_cloud_bit).eq(0)
    mask = mask.And(qa.bitwiseAnd(1 << cloud_bit).eq(0))
    mask = mask.And(qa.bitwiseAnd(1 << cloud_shadow_bit).eq(0))

    return image.updateMask(mask)


def prep_img(img):
    orig = img
    img = fmask(img)
    img = img.select(["ST_B10"])
    img = ee.Image(img.copyProperties(orig, orig.propertyNames()))
    img = img.set({"epsg": orig.projection().crs()})
    return img  # .resample("bicubic")


def get_lst(bbox_ee, start_date, end_date, reducer=None):
    if reducer is None:
        reducer = ee.Reducer.mean()

    collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")

    filtered = collection.filterDate(start_date, end_date).filterBounds(bbox_ee)

    if filtered.size().getInfo() == 0:
        raise Exception("No measurements for given date and location found.")

    projection = filtered.first().projection()
    preped = filtered.map(prep_img)
    reduced = (
        preped.reduce(reducer).setDefaultProjection(projection).select([0], ["ST_B10"])
    )
    reduced = reduced.multiply(0.00341802).add(149 - 273.15)

    return reduced.clip(bbox_ee), projection


def get_temps(lst, masks, path_cache):
    # We need mean and std for total, urban and rural temps
    t_dict = {}

    reducer = ee.Reducer.mean().combine(
        ee.Reducer.stdDev(),
        sharedInputs=True,
    )

    for nmask in ["total", "rural", "urban"]:
        if nmask == "total":
            mask = None
            lst_masked = lst
        else:
            mask = masks[nmask]
            lst_masked = lst.updateMask(mask)

        res = lst_masked.reduceRegion(
            reducer, bestEffort=False, maxPixels=MAX_PIXELS
        ).getInfo()

        t_dict[nmask] = dict(
            mean=res["ST_B10_mean"],
            std=res["ST_B10_stdDev"],
        )

    urban_mean = t_dict["urban"]["mean"]
    rural_mean = t_dict["rural"]["mean"]

    if abs(rural_mean - urban_mean) < 0.5 or rural_mean > urban_mean:
        lst_masked = lst.updateMask(masks["urban"])
        res = lst_masked.reduceRegion(
            ee.Reducer.percentile([5]), bestEffort=False, maxPixels=MAX_PIXELS
        ).getInfo()
        t_dict["rural_old"]["mean"] = rural_mean
        t_dict["rural"]["mean"] = res["ST_B10"]

    with open(path_cache / "temperatures.json", "w") as f:
        json.dump(t_dict, f)

    return t_dict


def load_or_get_temps(
    bbox_ee, start_date, end_date, path_cache, reducer=None, force=False
):
    if reducer is None:
        reducer = ee.Reducer.mean()

    fpath = path_cache / "temperatures.json"
    if fpath.exists() and not force:
        with open(fpath, "r") as f:
            temps = json.load(f)
    else:
        lst, proj = get_lst(bbox_ee, start_date, end_date, reducer)
        _, masks = wc.get_cover_and_masks(bbox_ee, proj)
        temps = get_temps(lst, masks, path_cache)

    return temps


def get_suhi(bbox_ee, start_date, end_date, path_cache, reducer=None):
    if reducer is None:
        reducer = ee.Reducer.mean()

    lst, proj = get_lst(bbox_ee, start_date, end_date, reducer)
    _, masks = wc.get_cover_and_masks(bbox_ee, proj)

    temps = load_or_get_temps(bbox_ee, start_date, end_date, path_cache, reducer)
    rural_lst_mean = temps["rural"]["mean"]

    unwanted_mask = masks["unwanted"]

    suhi = lst.subtract(rural_lst_mean)
    suhi = suhi.updateMask(unwanted_mask)

    return suhi


def get_cat_suhi(bbox_ee, start_date, end_date, path_cache, reducer=None):
    print("Generating temperature discrete image ...")

    if reducer is None:
        reducer = ee.Reducer.mean()

    img_suhi = get_suhi(bbox_ee, start_date, end_date, path_cache)

    cat_img = ee.Image(0).setDefaultProjection(img_suhi.projection())

    temps = load_or_get_temps(bbox_ee, start_date, end_date, path_cache, reducer)
    std = temps["total"]["std"]

    offsets = make_offsets(0, std)

    cat_img = cat_img.where(img_suhi.lt(offsets[0][0]), 1)

    for i, (start, end) in enumerate(offsets):
        cat_img = cat_img.where(img_suhi.gte(start).And(img_suhi.lt(end)), i + 2)

    cat_img = cat_img.where(img_suhi.gte(offsets[-1][1]), i + 3)
    cat_img = cat_img.updateMask(cat_img.neq(0))

    print("Done.")

    return cat_img


def download_cat_suhi(bbox_latlon, path_cache, season, year):
    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = date_format(season, year)

    cat_img = get_cat_suhi(bbox_ee, start_date, end_date, path_cache)

    task = ee.batch.Export.image.toDrive(
        image=cat_img,
        description="suhi_raster",
        scale=cat_img.projection().nominalScale(),
        region=bbox_ee,
        crs=cat_img.projection(),
        fileFormat="GeoTIFF",
    )
    task.start()
    return task


def make_offsets(s_mean: float, s_std: float, n: int = 3) -> List[Tuple[float, float]]:
    offsets = [(1.0, 1.0)] * (2 * n - 1)
    for i in range(n - 1):
        offsets[n - i - 2] = (s_mean - (i + 1.5) * s_std, s_mean - (i + 0.5) * s_std)
        offsets[n + i] = (s_mean + (i + 0.5) * s_std, s_mean + (i + 1.5) * s_std)
    offsets[n - 1] = (s_mean - 0.5 * s_std, s_mean + 0.5 * s_std)

    return offsets


def get_temperature_areas(img_cat, masks, bbox, path_cache):
    dict_list = {}
    for nmask in ["total", "rural", "urban"]:
        if nmask == "total":
            mask = None
            img = img_cat
        else:
            mask = masks[nmask]
            img = img_cat.updateMask(mask)

        img_area = img.pixelArea().setDefaultProjection(img.projection())
        img_area = img_area.addBands(img)
        area = img_area.reduceRegion(
            ee.Reducer.sum().group(groupField=1),
            bestEffort=False,
            geometry=bbox,
            maxPixels=MAX_PIXELS,
        ).getInfo()["groups"]
        area = {x["group"]: x["sum"] / 1e6 for x in area}
        dict_list[nmask] = area

    df = pd.DataFrame(dict_list)
    df.index.name = "clase"

    df.to_csv(path_cache / "temp_areas.csv")

    return df


def load_or_get_t_areas(bbox_ee, start_date, end_date, path_cache, force=False):
    fpath = path_cache / "temp_areas.csv"
    if fpath.exists() and not force:
        df = pd.read_csv(fpath, index_col="clase")
    else:
        img_cat = get_cat_suhi(bbox_ee, start_date, end_date, path_cache)
        proj = img_cat.projection()
        _, masks = wc.get_cover_and_masks(bbox_ee, proj)
        df = get_temperature_areas(img_cat, masks, bbox_ee, path_cache)

    return df


def plot_cat_map(bbox_latlon, fua_latlon_centroid, path_cache, season, year):
    print("Generating temperature map ...")

    vis_params = {"min": 0, "max": 7, "palette": ["#000000"] + list(colors.values())}

    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = date_format(season, year)

    img_cat = get_cat_suhi(bbox_ee, start_date, end_date, path_cache)

    Map = geemap.Map(basemap="carto-positron")

    Map.set_center(fua_latlon_centroid.y, fua_latlon_centroid.x, zoom=10)

    Map.addLayer(img_cat.clip(bbox_ee), vis_params, "SUHI", opacity=0.6)

    Map.layout.mapbox.layers[0].sourceattribution = "LandSat" " | Google Earth Engine"

    print("Done.")

    return Map


def get_land_usage_dataframe(bbox_ee, start_date, end_date, path_cache):
    img_cat = get_cat_suhi(bbox_ee, start_date, end_date, path_cache)
    proj = img_cat.projection()

    lc, masks = wc.get_cover_and_masks(bbox_ee, proj)

    img_area = img_cat.pixelArea()
    img_area = img_area.setDefaultProjection(proj)
    img_area = img_area.addBands(img_cat)
    img_area = img_area.addBands(lc)

    histograms = img_area.reduceRegion(
        (
            ee.Reducer.sum()
            .group(groupField=1, groupName="temperature_code")
            .group(groupField=2, groupName="land_code")
        ),
        bestEffort=False,
        geometry=bbox_ee,
        maxPixels=MAX_PIXELS,
    ).getInfo()

    hist_flat = []
    for cat in histograms["groups"]:
        # Each element corresponds to a land class
        cat = cat.copy()
        for row in cat["groups"]:
            # Each element corresponds to a temp class
            # Append land class to each temp class
            row["land_code"] = cat["land_code"]
            hist_flat.append(row)

    df = pd.DataFrame(hist_flat)
    df = df.set_index(["temperature_code", "land_code"])
    df = df.groupby("temperature_code", group_keys=False)["sum"].apply(
        lambda x: x / x.sum()
    )
    df = df.reset_index()
    df["Temperature"] = df["temperature_code"].map(TEMP_CAT_MAP)
    df["Land type"] = df["land_code"].map(wc.COVER_MAP)

    temp = df.groupby("land_code")["sum"].max()
    temp = temp[temp > 0.01]
    names = set(temp.index)

    df = df[df["land_code"].isin(names)]
    df["Temperature"] = pd.Categorical(df["Temperature"], TEMP_NAMES)

    df.to_csv(path_cache / "land_cover_by_temp.csv", index=False)

    return df


def load_or_get_land_usage_df(bbox_ee, start_date, end_date, path_cache, force=False):
    fpath = path_cache / "land_cover_by_temp.csv"
    if fpath.exists() and not force:
        df = pd.read_csv(fpath)
    else:
        df = get_land_usage_dataframe(bbox_ee, start_date, end_date, path_cache)

    return df


def plot_t_hist():
    # Skip This until we discuss if standard deviation steps is an appropriate
    # dicretization scheme
    pass


def plot_temp_by_lc(bbox_latlon, path_cache, season, year):
    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = date_format(season, year)

    df = load_or_get_land_usage_df(bbox_ee, start_date, end_date, path_cache)

    fig = px.bar(
        data_frame=df,
        x="Temperature",
        y="sum",
        color="Land type",
        color_discrete_map=wc.COVER_PALETTE_NAME_MAP,
        labels={"sum": "Usage"},
    )

    fig.update_layout(
        # title="Plot Title",
        xaxis_title="Clase de temperatura",
        yaxis_title="Fracción por cobertura",
        legend_title="Tipo de suelo",
    )

    return fig


def plot_temp_areas(bbox_latlon, path_cache, season, year):
    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = date_format(season, year)

    df_t_areas = load_or_get_t_areas(bbox_ee, start_date, end_date, path_cache)

    fig = px.bar(
        df_t_areas.rename(columns={"total": "Area"}),
        x=[k for i, k in enumerate(colors.keys()) if i + 1 in df_t_areas.index],
        y="Area",
        color=[k for i, k in enumerate(colors.keys()) if i + 1 in df_t_areas.index],
        color_discrete_map=colors,
    )

    fig.update_layout(
        # title="Plot Title",
        xaxis_title="Clase de temperatura",
        yaxis_title="Área (km²)",
        legend_title="Temperatura",
    )

    return fig


def make_donuts(proj, bbox_latlon, uc_latlon, width=100):
    # Set projection
    # bbox_utm = gpd.GeoSeries(bbox_latlon).set_crs("EPSG:4326").to_crs(proj)
    # uc_utm = uc_latlon.to_crs(proj)
    bbox_utm = ug.reproject_geometry(bbox_latlon, proj)
    uc_utm = ug.reproject_geometry(uc_latlon, proj)

    # Set center of disks as the center of the
    # 2015 urban center
    center = uc_utm.centroid
    radius = bbox_utm.exterior.distance(center)

    # Make donuts
    discs = []
    radii = []
    while radius >= width:
        inner_radius = radius - width
        outer_circ = center.buffer(radius)
        inner_circ = center.buffer(inner_radius)
        donut = outer_circ.difference(inner_circ)

        discs.append(donut)
        # Save radius in km
        radii.append(inner_radius / 2000)

        radius = inner_radius
    # Last centermost circle
    final_circ = center.buffer(radius)
    discs.append(final_circ)
    radii.append(0)

    donuts_df = gpd.GeoDataFrame(discs)
    donuts_df.columns = ["geometry"]
    donuts_df.set_geometry("geometry", inplace=True)
    donuts_df = donuts_df.set_crs(proj)
    donuts_df = donuts_df.to_crs("EPSG:4326")

    donuts_ee = ee.FeatureCollection(json.loads(donuts_df.to_json()))

    return radii, donuts_ee


def get_radial_f(suhi, bbox_latlon, uc_latlon, path_cache, width=100):
    proj_str = suhi.projection().getInfo()["crs"]
    radii, donuts_ee = make_donuts(proj_str, bbox_latlon, uc_latlon)

    reduced = suhi.reduceRegions(
        donuts_ee,
        ee.Reducer.mean(),
    )
    reduced = reduced.aggregate_array("mean")
    reduced = reduced.getInfo()

    df = pd.DataFrame({"radius": radii, "reduced": reduced})

    df.to_csv(path_cache / "radial_function.csv", index=False)

    return df


def load_or_get_radial_f(
    bbox_ee, start_date, end_date, path_cache, bbox_latlon, uc_latlon, force=False
):
    fpath = path_cache / "radial_function.csv"
    if fpath.exists() and not force:
        df = pd.read_csv(fpath)
    else:
        img_suhi = get_suhi(bbox_ee, start_date, end_date, path_cache)
        df = get_radial_f(img_suhi, bbox_latlon, uc_latlon, path_cache)

    return df


def plot_radial_temperature(bbox_latlon, uc_latlon, path_cache, season, year):
    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = date_format(season, year)

    df = load_or_get_radial_f(
        bbox_ee, start_date, end_date, path_cache, bbox_latlon, uc_latlon
    )

    fig = px.line(
        x=df["radius"].map(lambda x: round(x, 1)),
        y=df["reduced"].map(lambda x: round(x, 1)),
        labels={
            "x": "Radio (km)",
            "y": "Diferencia con respecto a la temperatura rural (°C)",
        },
    )

    return fig


def get_radial_lc(lc, bbox_latlon, uc_latlon, path_cache, width=100):
    proj = lc.projection()
    proj_str = proj.getInfo()["crs"]
    radii, donuts_ee = make_donuts(proj_str, bbox_latlon, uc_latlon)

    img_area = lc.pixelArea().setDefaultProjection(proj)
    img_area = img_area.addBands(lc)

    reduced = img_area.reduceRegions(
        donuts_ee,
        ee.Reducer.sum().group(groupField=1),
    )
    reduced = reduced.aggregate_array("groups")
    reduced = reduced.getInfo()

    reduced_land_flat = []
    for r, row in zip(radii, reduced):
        row = row.copy()
        for d in row:
            d["x"] = r
            reduced_land_flat.append(d)

    df = pd.DataFrame(reduced_land_flat)
    df = df.set_index(["group", "x"])
    df = df.groupby("x", group_keys=False).apply(lambda x: x / x.sum())
    df = df.reset_index()
    df["Land type"] = df["group"].map(wc.COVER_MAP)

    test = df.pivot(index="x", columns="Land type", values="sum")
    test.to_csv(path_cache / "radial_lc.csv")

    return test


def load_or_get_radial_lc(
    bbox_ee, start_date, end_date, path_cache, bbox_latlon, uc_latlon, force=False
):
    fpath = path_cache / "radial_lc.csv"
    if fpath.exists() and not force:
        df = pd.read_csv(fpath, index_col="x")
    else:
        suhi = get_suhi(bbox_ee, start_date, end_date, path_cache)
        lc, _ = wc.get_cover_and_masks(bbox_ee, suhi.projection())
        df = get_radial_lc(lc, bbox_latlon, uc_latlon, path_cache, width=100)

    return df


def plot_radial_lc(bbox_latlon, uc_latlon, path_cache, season, year):
    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = date_format(season, year)

    df = load_or_get_radial_lc(
        bbox_ee, start_date, end_date, path_cache, bbox_latlon, uc_latlon
    )

    df.round(1)
    colors = [wc.COVER_PALETTE_NAME_MAP[x] for x in df.columns]
    x = list(df.index)
    map(lambda x: round(x, 1), x)

    fig = go.Figure()
    for col, color in zip(df.columns, colors):
        fig.add_trace(
            go.Scatter(
                x=x,
                y=df[col],
                stackgroup="one",
                line_color=color,
                hoveron="points",
                line_width=0,
                name=col,
                opacity=1,
            )
        )
    fig.update_layout(
        xaxis_title="Radio (km)",
        yaxis_title="Porcentaje",
        yaxis_range=(0, 1),
        yaxis=dict(tickformat=".0%"),
    )

    return fig


def get_urban_mean(bbox_latlon, season, year, path_cache, reducer=None):
    if reducer is None:
        reducer = ee.Reducer.mean()

    bbox_ee = ru.bbox_to_ee(bbox_latlon)
    start_date, end_date = date_format(season, year)

    temps = load_or_get_temps(bbox_ee, start_date, end_date, path_cache, reducer)
    return temps["urban"]["mean"]


country_name_map = {
    "Bahamas": "The_Bahamas",
    "CostaRica": "Costa_Rica",
    "DominicanRepublic": "Dominican_Republic",
    "ElSalvador": "El_Salvador",
    "PuertoRico": "Puerto_Rico",
    "TrinidadandTobago": "Trinidad_and_Tobago",
    "UnitedStates": "US",
}


def add_area(feature):
    return feature.set({"area": feature.geometry().area()})


def get_mit_areas_df(bbox_latlon, bbox_mollweide, uc_mollweide_centroid, path_cache):
    smod = ghsl.load_or_download(
        bbox_mollweide, "SMOD", data_path=path_cache, resolution=1000
    )
    smod_gdf = ghsl.smod_polygons(smod, uc_mollweide_centroid)
    clusters_gdf = smod_gdf[smod_gdf["class"] == 2]
    main_cluster = clusters_gdf[clusters_gdf.is_main]

    cluster_mollweide = main_cluster[main_cluster.year == 2020]
    cluster_latlon = cluster_mollweide.to_crs("EPSG:4326").geometry.iloc[0]
    cluster_ee = ru.bbox_to_ee(cluster_latlon)

    roof_area = calculate_building_area(
        bbox_mollweide, path_cache, cluster_mollweide.geometry
    )
    print(f"Roofs: {roof_area}")
    urban_area = calculate_urban_area(cluster_ee)
    print(f"Urban: {urban_area}")
    road_lenght = calculate_road_area(bbox_latlon, path_cache, cluster_latlon)
    print(f"Roads: {road_lenght}")

    df = pd.DataFrame(
        {"roofs": roof_area, "urban": urban_area, "roads": road_lenght}, index=[0]
    )

    df.to_csv(path_cache / "mitigation_areas.csv", index=False)

    print("Done.")

    return df


def load_or_get_mit_areas_df(
    bbox_latlon, bbox_mollweide, uc_mollweide_centroid, path_cache, force=False
):
    fpath = path_cache / "mitigation_areas.csv"
    if fpath.exists() and not force:
        df = pd.read_csv(fpath)
    else:
        df = get_mit_areas_df(
            bbox_latlon, bbox_mollweide, uc_mollweide_centroid, path_cache
        )
    return df


def calculate_building_area(bbox_mollweide, path_cache, cluster):
    built = ghsl.load_or_download(
        bbox_mollweide, "BUILT_S", data_path=path_cache, resolution=100
    )

    b_2020 = built.sel(band=2020)

    b_2020.rio.set_nodata(0)

    area = b_2020.rio.clip(cluster.geometry).sum().item() / 1e6

    return area


def calculate_urban_area(bbox):
    _, masks = wc.get_cover_and_masks(bbox, None)

    urban_mask = masks["urban"]
    img = (
        urban_mask.pixelArea()
        .setDefaultProjection(urban_mask.projection())
        .updateMask(urban_mask)
    )

    area = img.reduceRegion(
        ee.Reducer.sum(),
        geometry=bbox,
        maxPixels=MAX_PIXELS,
    ).getInfo()
    area = area["area"] / 1e6

    return area


def calculate_road_area(bbox, path_cache, cluster):
    edges = load_roads_osm(bbox, path_cache).to_crs("EPSG:4326")
    pip = edges.within(cluster)

    total_lenght = edges[pip]["length"].sum() / 1000

    return total_lenght
