import ee
import json

import geopandas as gpd
import pandas as pd
import ursa.ghsl as ghsl
import ursa.sleuth_prep as sp
import ursa.utils.geometry as ug
import ursa.world_cover as wc

from typing import Tuple, List
from ursa.constants import TEMP_CAT_MAP, TEMP_NAMES
from ursa.utils.date import date_format
from ursa.utils.raster import bbox_to_ee

MAX_PIXELS = 1e10

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


def get_lst(bbox_ee, start_date, end_date):
    collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")

    filtered = collection.filterDate(start_date, end_date).filterBounds(bbox_ee)

    if filtered.size().getInfo() == 0:
        raise Exception("No measurements for given date and location found.")

    projection = filtered.first().projection()
    preped = filtered.map(prep_img)
    reduced = (
        preped.reduce(ee.Reducer.mean()).setDefaultProjection(projection).select([0], ["ST_B10"])
    )
    reduced = reduced.multiply(0.00341802).add(149 - 273.15)

    return reduced.clip(bbox_ee), projection


def get_temps(lst, masks):
    # We need mean and std for total, urban and rural temps
    t_dict = {}

    reducer = ee.Reducer.mean().combine(
        ee.Reducer.stdDev(),
        sharedInputs=True,
    )
    for nmask in ["total", "rural", "urban"]:
        if nmask == "total":
            lst_masked = lst
        else:
            lst_masked = lst.updateMask(masks[nmask])

        res = lst_masked.reduceRegion(
            reducer, bestEffort=True, maxPixels=MAX_PIXELS
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
        t_dict["rural_old"] = {}
        t_dict["rural_old"]["mean"] = rural_mean
        t_dict["rural"]["mean"] = res["ST_B10"]

    return t_dict


def load_or_get_temps(lst, masks, path_cache):
    fpath = path_cache / "temperatures.json"
    if fpath.exists():
        with open(fpath, "r") as f:
            temps = json.load(f)
    else:
        temps = get_temps(lst, masks)
        with open(path_cache / "temperatures.json", "w") as f:
            json.dump(temps, f)

    return temps


def get_cat_suhi(lst, masks, path_cache):
    print("Generating temperature discrete image ...")
    temps = load_or_get_temps(lst, masks, path_cache)

    rural_lst_mean = temps["rural"]["mean"]
    std = temps["total"]["std"]
    offsets = make_offsets(0, std)
    
    unwanted_mask = masks["unwanted"]

    img_suhi = lst.subtract(rural_lst_mean)
    img_suhi = img_suhi.updateMask(unwanted_mask)

    cat_img = ee.Image(0).setDefaultProjection(img_suhi.projection())
    cat_img = cat_img.where(img_suhi.lt(offsets[0][0]), 1)

    for i, (start, end) in enumerate(offsets):
        cat_img = cat_img.where(img_suhi.gte(start).And(img_suhi.lt(end)), i + 2)

    cat_img = cat_img.where(img_suhi.gte(offsets[-1][1]), i + 3)
    cat_img = cat_img.updateMask(cat_img.neq(0))

    print("Done.")

    return cat_img

def make_offsets(s_mean: float, s_std: float, n: int = 3) -> List[Tuple[float, float]]:
    offsets = [(1.0, 1.0)] * (2 * n - 1)
    for i in range(n - 1):
        offsets[n - i - 2] = (s_mean - (i + 1.5) * s_std, s_mean - (i + 0.5) * s_std)
        offsets[n + i] = (s_mean + (i + 0.5) * s_std, s_mean + (i + 1.5) * s_std)
    offsets[n - 1] = (s_mean - 0.5 * s_std, s_mean + 0.5 * s_std)

    return offsets


def get_temperature_areas(img_cat, masks, bbox):
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

    return df


def load_or_get_t_areas(bbox_ee, img_cat, masks, path_cache):
    fpath = path_cache / "temp_areas.csv"
    if fpath.exists():
        df = pd.read_csv(fpath, index_col="clase")
    else:
        df = get_temperature_areas(img_cat, masks, bbox_ee)
        df.to_csv(path_cache / "temp_areas.csv")
    return df


def get_land_usage_dataframe(bbox_ee, img_cat, lc):
    proj = img_cat.projection()

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

    return df


def load_or_get_land_usage_df(bbox_ee, img_cat, path_cache):
    fpath = path_cache / "land_cover_by_temp.csv"
    if fpath.exists():
        df = pd.read_csv(fpath)
    else:
        lc, _ = wc.get_cover_and_masks(bbox_ee, img_cat.projection())
        df = get_land_usage_dataframe(bbox_ee, img_cat, lc)
        df.to_csv(path_cache / "land_cover_by_temp.csv", index=False)
    return df


def make_donuts(proj, bbox_latlon, uc_latlon, width=100):
    # Set projection
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


def get_radial_f(bbox_latlon, uc_latlon, suhi):
    proj_str = suhi.projection().getInfo()["crs"]
    radii, donuts_ee = make_donuts(proj_str, bbox_latlon, uc_latlon)

    reduced = suhi.reduceRegions(
        donuts_ee,
        ee.Reducer.mean(),
    )
    reduced = reduced.aggregate_array("mean")
    reduced = reduced.getInfo()

    df = pd.DataFrame({"radius": radii, "reduced": reduced})

    return df


def get_radial_lc(bbox_latlon, uc_latlon, lc):
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
    df = df.pivot(index="x", columns="Land type", values="sum")

    return df


def load_or_get_radial_distributions(
    bbox_latlon, uc_latlon, start_date, end_date, path_cache, 
):
    fpath_f = path_cache / "radial_function.csv"
    fpath_lc = path_cache / "radial_lc.csv"

    if fpath_f.exists() and fpath_lc.exists():
        df_f = pd.read_csv(fpath_f)
        df_lc = pd.read_csv(fpath_lc, index_col="x")
    else:
        bbox_ee = bbox_to_ee(bbox_latlon)
        
        lst, proj = get_lst(bbox_ee, start_date, end_date)
        lc, masks = wc.get_cover_and_masks(bbox_ee, proj)

        temps = load_or_get_temps(lst, masks, path_cache)
        rural_lst_mean = temps["rural"]["mean"]

        unwanted_mask = masks["unwanted"]

        suhi = lst.subtract(rural_lst_mean)
        suhi = suhi.updateMask(unwanted_mask)
    
        df_lc = get_radial_lc(bbox_latlon, uc_latlon, lc)
        df_f = get_radial_f(bbox_latlon, uc_latlon, suhi)

        df_lc.to_csv(fpath_lc)
        df_f.to_csv(fpath_f)

    return df_f, df_lc


def get_urban_mean(bbox_latlon, season, year, path_cache):
    bbox_ee = bbox_to_ee(bbox_latlon)
    start_date, end_date = date_format(season, year)

    lst, proj = get_lst(bbox_ee, start_date, end_date)
    _, masks = wc.get_cover_and_masks(bbox_ee, proj)
    temps = load_or_get_temps(lst, masks, path_cache)
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
    cluster_ee = bbox_to_ee(cluster_latlon)

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
    edges = sp.load_roads_osm(bbox, path_cache).to_crs("EPSG:4326")
    pip = edges.within(cluster)

    total_lenght = edges[pip]["length"].sum() / 1000

    return total_lenght
