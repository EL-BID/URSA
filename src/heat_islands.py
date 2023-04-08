import ee
# import numpy as np
import geemap.plotlymap as geemap
import raster_utils as ru
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import plotly.express as px
import plotly.graph_objects as go
from typing import Tuple, List
import json
import world_cover as wc
import ghsl
from sleuth_prep import load_roads_osm

MAX_PIXELS = 1e10

colors = {
    'Muy frío': "#2166AC",
    'Frío': "#67A9CF",
    'Ligeramente frío': "#D1E5F0",
    'Templado': "#F7F7F7",
    'Ligeramente cálido': "#FDDBC7",
    'Caliente': "#EF8A62",
    'Muy caliente': "#B2182B",
}

TEMP_CAT_MAP = {i+1: n for i, n in enumerate(colors.keys())}

RdBu7 = ["#2166AC", "#67A9CF", "#D1E5F0", "#F7F7F7",
         "#FDDBC7", "#EF8A62", "#B2182B"]

RdBu7k = ["#2166AC", "#67A9CF", "#D1E5F0", "#808080",
          "#FDDBC7", "#EF8A62", "#B2182B"]

TEMP_NAMES = list(TEMP_CAT_MAP.values())

TEMP_PALETTE_MAP = {x: y for x, y in zip(TEMP_NAMES, RdBu7)}

TEMP_PALETTE_MAP_INV = {value: key for key, value in TEMP_PALETTE_MAP.items()}

TEMP_PALETTE_MAP_K = {x: y for x, y in zip(TEMP_NAMES, RdBu7k)}

TEMP_PALETTE_MAP_INV_K = {
    value: key for key, value in TEMP_PALETTE_MAP_K.items()
}


def date_format(season, year):
    sdict = {
        'Q1': [f'{year}-3-1', f'{year}-5-31'],
        'Q2': [f'{year}-6-1', f'{year}-8-31'],
        'Q3': [f'{year}-9-1', f'{year}-11-30'],
        'Q4': [f'{year}-12-1', f'{year + 1}-2-29'],
        'Qall': [f'{year}-1-1', f'{year}-12-31']
    }

    return sdict[season]


def fmask(image):
    qa = image.select('QA_PIXEL')

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
    img = img.set({'epsg': orig.projection().crs()})
    return img  # .resample("bicubic")


def get_lst(bbox_ee, start_date, end_date, reducer=None):

    if reducer is None:
        reducer = ee.Reducer.mean()

    collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")

    filtered = (
        collection
        .filterDate(start_date, end_date)
        .filterBounds(bbox_ee)
    )

    if filtered.size().getInfo() == 0:
        raise Exception("No measurements for given date and location found.")

    projection = filtered.first().projection()
    preped = filtered.map(prep_img)
    reduced = (
        preped.reduce(reducer)
        .setDefaultProjection(projection)
        .select([0], ['ST_B10'])
    )
    reduced = reduced.multiply(0.00341802).add(149 - 273.15)

    return reduced.clip(bbox_ee), projection


def get_temps(lst, masks, path_cache):
    # We need mean and std for total, urban and rural temps

    t_dict = {}

    for nmask in ['total', 'rural', 'urban']:
        if nmask == 'total':
            mask = None
        else:
            mask = masks[nmask]

        if mask is not None:
            lst_masked = lst.updateMask(mask)
        else:
            lst_masked = lst

        mean = lst_masked.reduceRegion(
            ee.Reducer.mean(),
            bestEffort=False,
            maxPixels=MAX_PIXELS
        ).getInfo()["ST_B10"]

        std = lst_masked.reduceRegion(
            ee.Reducer.stdDev(),
            bestEffort=False,
            maxPixels=MAX_PIXELS
        ).getInfo()["ST_B10"]

        t_dict[f'{nmask}_mean'] = mean
        t_dict[f'{nmask}_std'] = std

        t_df = pd.DataFrame(t_dict, index=[0])
        t_df.to_csv(path_cache / 'temperatures.csv', index=False)

    return t_df


def load_or_get_temps(bbox_ee, start_date, end_date, path_cache,
                      reducer=None, force=False):

    if reducer is None:
        reducer = ee.Reducer.mean()

    fpath = path_cache / 'temperatures.csv'
    if fpath.exists() and not force:
        df = pd.read_csv(fpath)
    else:
        lst, proj = get_lst(bbox_ee, start_date, end_date, reducer)
        lc, masks = wc.get_cover_and_masks(bbox_ee, proj)
        df = get_temps(lst, masks, path_cache)

    return df


def get_suhi(bbox_ee, start_date, end_date, path_cache,
             reducer=None):

    if reducer is None:
        reducer = ee.Reducer.mean()

    lst, proj = get_lst(bbox_ee, start_date, end_date, reducer)
    lc, masks = wc.get_cover_and_masks(bbox_ee, proj)

    temps = load_or_get_temps(bbox_ee, start_date, end_date,
                              path_cache, reducer)
    rural_lst_mean = temps['rural_mean'].item()

    unwanted_mask = masks['unwanted']

    suhi = lst.subtract(rural_lst_mean)
    suhi = suhi.updateMask(unwanted_mask)

    return suhi


def get_cat_suhi(bbox_ee, start_date, end_date, path_cache,
                 reducer=None):

    print('Generatin temperature discrete image ...')

    if reducer is None:
        reducer = ee.Reducer.mean()

    img_suhi = get_suhi(bbox_ee, start_date, end_date, path_cache)

    cat_img = ee.Image(0).setDefaultProjection(img_suhi.projection())

    temps = load_or_get_temps(bbox_ee, start_date, end_date,
                              path_cache, reducer)
    std = temps['total_std'].item()

    offsets = make_offsets(0, std)

    cat_img = cat_img.where(img_suhi.lt(offsets[0][0]), 1)

    for i, (start, end) in enumerate(offsets):
        cat_img = cat_img.where(
            img_suhi.gte(start).And(img_suhi.lt(end)),
            i + 2
        )

    cat_img = cat_img.where(img_suhi.gte(offsets[-1][1]), i + 3)
    cat_img = cat_img.updateMask(cat_img.neq(0))

    print('Done.')

    return cat_img


def make_offsets(
        s_mean: float,
        s_std: float,
        n: int = 3) -> List[Tuple[float, float]]:

    offsets = [(1., 1.)] * (2 * n - 1)
    for i in range(n - 1):
        offsets[n - i - 2] = (
            s_mean - (i + 1.5) * s_std,
            s_mean - (i + 0.5) * s_std
        )
        offsets[n + i] = (
            s_mean + (i + 0.5) * s_std,
            s_mean + (i + 1.5) * s_std
        )
    offsets[n - 1] = (s_mean - 0.5 * s_std, s_mean + 0.5 * s_std)

    return offsets


def get_temperature_areas(img_cat, masks, bbox, path_cache):

    dict_list = {}
    for nmask in ['total', 'rural', 'urban']:
        if nmask == 'total':
            mask = None
        else:
            mask = masks[nmask]

        if mask is not None:
            img = img_cat.updateMask(mask)
        else:
            img = img_cat

        img_area = img.pixelArea().setDefaultProjection(img.projection())
        img_area = img_area.addBands(img)
        area = img_area.reduceRegion(
            ee.Reducer.sum().group(groupField=1),
            bestEffort=False,
            geometry=bbox,
            maxPixels=MAX_PIXELS,
        ).getInfo()["groups"]
        area = {x['group']: x["sum"]/1e6 for x in area}
        dict_list[nmask] = area

    df = pd.DataFrame(dict_list)
    df.index.name = 'clase'

    df.to_csv(path_cache / 'temp_areas.csv')

    return df


def load_or_get_t_areas(bbox_ee, start_date, end_date, path_cache,
                        force=False):

    fpath = path_cache / 'temp_areas.csv'
    if fpath.exists() and not force:
        df = pd.read_csv(fpath, index_col='clase')
    else:
        img_cat = get_cat_suhi(bbox_ee, start_date, end_date, path_cache)
        proj = img_cat.projection()
        lc, masks = wc.get_cover_and_masks(bbox_ee, proj)
        df = get_temperature_areas(img_cat, masks, bbox_ee, path_cache)

    return df


def plot_cat_map(country, city, path_fua, path_cache,
                 season, year):

    print('Generating temperature map ...')

    vis_params = {
        'min': 0,
        'max': 7,
        'palette': ['#000000'] + list(colors.values())
    }

    bbox_latlon, uc_latlon, fua_latlon = ru.get_bbox(
        city, country, path_fua,
        proj='EPSG:4326')
    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = date_format(season, year)

    img_cat = get_cat_suhi(bbox_ee, start_date, end_date, path_cache)

    Map = geemap.Map(basemap="carto-positron")

    centroid = fua_latlon.geometry.iloc[0].centroid
    Map.set_center(centroid.y, centroid.x, zoom=10)

    Map.addLayer(img_cat.clip(bbox_ee),
                 vis_params,
                 'SUHI',
                 opacity=0.6)
    # Map.update_layout(
    #     height=600)

    # Create dummy legend
    poly = Polygon([(0, 0), (1e-3, 1e-3), (-1e-3, -1e-3)])
    gdf = gpd.GeoDataFrame(
        {'geometry': [poly]*7,
         'Clases': colors.keys()},
        crs=4326).reset_index()
    fig = px.choropleth_mapbox(
        gdf,
        geojson=gdf.geometry,
        locations='index',
        mapbox_style='carto-positron',
        color='Clases',
        color_discrete_map=colors
    )

    Map.add_traces(fig.data)

    Map.layout.mapbox.layers[0].sourceattribution = (
        'LandSat'
        ' | Google Earth Engine')

    print('Done.')

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
            ee.Reducer
            .sum()
            .group(groupField=1, groupName="temperature_code")
            .group(groupField=2, groupName="land_code")
        ),
        bestEffort=False,
        geometry=bbox_ee,
        maxPixels=MAX_PIXELS
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
    df = df.groupby(
        "temperature_code",
        group_keys=False
    )["sum"].apply(lambda x: x/x.sum())
    df = df.reset_index()
    df["Temperature"] = df["temperature_code"].map(TEMP_CAT_MAP)
    df["Land type"] = df["land_code"].map(wc.COVER_MAP)

    temp = df.groupby("land_code")["sum"].max()
    temp = temp[temp > 0.01]
    names = set(temp.index)

    df = df[df["land_code"].isin(names)]
    df["Temperature"] = pd.Categorical(df["Temperature"], TEMP_NAMES)

    df.to_csv(path_cache / 'land_cover_by_temp.csv', index=False)

    return df


def load_or_get_land_usage_df(bbox_ee, start_date, end_date, path_cache,
                              force=False):

    fpath = path_cache / 'land_cover_by_temp.csv'
    if fpath.exists() and not force:
        df = pd.read_csv(fpath)
    else:
        df = get_land_usage_dataframe(
            bbox_ee, start_date, end_date, path_cache)

    return df


def plot_t_hist():
    # Skip This until we discuss if standard deviation steps is an appropriate
    # dicretization scheme
    pass


def plot_temp_by_lc(country, city, path_fua, path_cache,
                    season, year):

    bbox_latlon, uc_latlon, fua_latlon = ru.get_bbox(
        city, country, path_fua,
        proj='EPSG:4326')
    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = date_format(season, year)

    df = load_or_get_land_usage_df(bbox_ee, start_date, end_date, path_cache)

    fig = px.bar(
        data_frame=df,
        x='Temperature',
        y='sum',
        color='Land type',
        color_discrete_map=wc.COVER_PALETTE_NAME_MAP,
        labels={'sum': 'Usage'}
    )

    fig.update_layout(
        # title="Plot Title",
        xaxis_title="Clase de temperatura",
        yaxis_title="Fracción por cobertura",
        legend_title="Tipo de suelo",
    )

    return fig


def plot_temp_areas(country, city, path_fua, path_cache,
                    season, year):

    bbox_latlon, uc_latlon, fua_latlon = ru.get_bbox(
        city, country, path_fua,
        proj='EPSG:4326')
    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = date_format(season, year)

    df_t_areas = load_or_get_t_areas(bbox_ee, start_date, end_date, path_cache)

    fig = px.bar(
        df_t_areas.rename(columns={'urban': 'Urbana', 'rural': 'Rural'}),
        x=[k for i, k in enumerate(colors.keys()) if i+1 in df_t_areas.index],
        y=['Urbana', 'Rural'],
        color_discrete_sequence=['gray', 'green'])

    fig.update_layout(
        # title="Plot Title",
        xaxis_title="Clase de temperatura",
        yaxis_title="Área (km²)",
        legend_title="Región",
    )

    return fig


def make_donuts(bbox_ee, proj, bbox_latlon, uc_latlon, width=100):

    # Set projection
    bbox_utm = gpd.GeoSeries(bbox_latlon).set_crs(4326).to_crs(proj)
    uc_utm = uc_latlon.to_crs(proj)

    # Set center of disks as the center of the
    # 2015 urban center
    center = uc_utm.centroid
    radius = bbox_utm.exterior.distance(center, align=False).item()

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
    donuts_df = donuts_df.set_crs(proj)
    donuts_df = donuts_df.to_crs("EPSG:4326")

    donuts_ee = ee.FeatureCollection(json.loads(donuts_df.to_json()))

    return radii, donuts_ee


def get_radial_f(bbox_ee, suhi, bbox_latlon, uc_latlon, path_cache,
                 width=100):

    proj_str = suhi.projection().getInfo()['crs']
    radii, donuts_ee = make_donuts(bbox_ee, proj_str, bbox_latlon, uc_latlon)

    reduced = suhi.reduceRegions(
        donuts_ee,
        ee.Reducer.mean(),
    )
    reduced = reduced.aggregate_array('mean')
    reduced = reduced.getInfo()

    df = pd.DataFrame({'radius': radii, 'reduced': reduced})

    df.to_csv(path_cache / 'radial_function.csv', index=False)

    return df


def load_or_get_radial_f(bbox_ee, start_date, end_date, path_cache,
                         bbox_latlon, uc_latlon, force=False):

    fpath = path_cache / 'radial_function.csv'
    if fpath.exists() and not force:
        df = pd.read_csv(fpath)
    else:
        img_suhi = get_suhi(bbox_ee, start_date, end_date, path_cache)
        df = get_radial_f(
            bbox_ee, img_suhi, bbox_latlon, uc_latlon, path_cache)

    return df


def plot_radial_temperature(country, city, path_fua, path_cache,
                            season, year):

    bbox_latlon, uc_latlon, fua_latlon = ru.get_bbox(
        city, country, path_fua,
        proj='EPSG:4326')
    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = date_format(season, year)

    df = load_or_get_radial_f(bbox_ee, start_date, end_date, path_cache,
                              bbox_latlon, uc_latlon)

    fig = px.line(
        x=df["radius"],
        y=df["reduced"],
        labels={
            "x": "Radio (km)",
            "y": "Diferencia con respecto a la temperatura rural (°C)",
        }
    )

    return fig


def get_radial_lc(bbox_ee, lc, bbox_latlon, uc_latlon, path_cache,
                  width=100):

    proj = lc.projection()
    proj_str = proj.getInfo()['crs']
    radii, donuts_ee = make_donuts(bbox_ee, proj_str, bbox_latlon, uc_latlon)

    img_area = lc.pixelArea().setDefaultProjection(proj)
    img_area = img_area.addBands(lc)

    reduced = img_area.reduceRegions(
        donuts_ee,
        ee.Reducer.sum().group(groupField=1),
    )
    reduced = reduced.aggregate_array('groups')
    reduced = reduced.getInfo()

    reduced_land_flat = []
    for r, row in zip(radii, reduced):
        row = row.copy()
        for d in row:
            d["x"] = r
            reduced_land_flat.append(d)

    df = pd.DataFrame(reduced_land_flat)
    df = df.set_index(["group", "x"])
    df = df.groupby("x", group_keys=False).apply(lambda x: x/x.sum())
    df = df.reset_index()
    df["Land type"] = df["group"].map(wc.COVER_MAP)

    test = df.pivot(index="x", columns="Land type", values="sum")
    test.to_csv(path_cache / 'radial_lc.csv')

    return test


def load_or_get_radial_lc(bbox_ee, start_date, end_date, path_cache,
                          bbox_latlon, uc_latlon, force=False):

    fpath = path_cache / 'radial_lc.csv'
    if fpath.exists() and not force:
        df = pd.read_csv(fpath, index_col='x')
    else:
        suhi = get_suhi(bbox_ee, start_date, end_date, path_cache)
        lc, masks = wc.get_cover_and_masks(bbox_ee, suhi.projection())
        df = get_radial_lc(bbox_ee, lc, bbox_latlon, uc_latlon, path_cache,
                           width=100)

    return df


def plot_radial_lc(country, city, path_fua, path_cache,
                   season, year):

    bbox_latlon, uc_latlon, fua_latlon = ru.get_bbox(
        city, country, path_fua,
        proj='EPSG:4326')
    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = date_format(season, year)

    df = load_or_get_radial_lc(bbox_ee, start_date, end_date, path_cache,
                               bbox_latlon, uc_latlon)

    colors = [wc.COVER_PALETTE_NAME_MAP[x] for x in df.columns]
    x = list(df.index)

    fig = go.Figure()
    for col, color in zip(df.columns, colors):
        fig.add_trace(go.Scatter(
            x=x,
            y=df[col],
            stackgroup="one",
            line_color=color,
            hoveron="points",
            line_width=0,
            name=col,
            opacity=1
        ))
    fig.update_layout(
        xaxis_title="Radio (km)",
        yaxis_title="Porcentaje",
        yaxis_range=(0, 1),
        yaxis=dict(
            tickformat=".0%"
        )
    )

    return fig


def get_urban_mean(city, country, path_fua, season, year, path_cache,
                   reducer=None):
    if reducer is None:
        reducer = ee.Reducer.mean()

    bbox_latlon, uc_latlon, fua_latlon = ru.get_bbox(
        city, country, path_fua,
        proj='EPSG:4326')
    bbox_ee = ru.bbox_to_ee(bbox_latlon)
    start_date, end_date = date_format(season, year)

    temps = load_or_get_temps(bbox_ee, start_date, end_date,
                              path_cache, reducer)
    return temps['urban_mean'].item()


country_name_map = {
    "Bahamas": "The_Bahamas",
    "CostaRica": "Costa_Rica",
    "DominicanRepublic": "Dominican_Republic",
    "ElSalvador": "El_Salvador",
    "PuertoRico": "Puerto_Rico",
    "TrinidadandTobago": "Trinidad_and_Tobago",
    "UnitedStates": "US"
}


def add_area(feature):
    return feature.set(
        {"area": feature.geometry().area()}
    )


def get_mit_areas_df(city, country, path_fua, path_cache):
    print('Generating mitigation areas...')
    bbox_latlon, uc_latlon, fua_latlon = ru.get_bbox(
        city, country, path_fua,
        proj='EPSG:4326')
    bbox_mollweide, uc_mollweide, fua_mollweide = ru.get_bbox(
        city, country, path_fua,
        proj='ESRI:54009')

    # bbox_ee = ru.bbox_to_ee(bbox_latlon)

    smod = ghsl.load_or_download(bbox_mollweide, 'SMOD',
                                 data_path=path_cache, resolution=1000)
    smod_gdf = ghsl.smod_polygons(
        smod, uc_mollweide.iloc[0].geometry.centroid)#.to_crs('EPSG:4326')
    clusters_gdf = smod_gdf[smod_gdf['class'] == 2]
    main_cluster = clusters_gdf[clusters_gdf.is_main]

    cluster_mollweide = main_cluster[main_cluster.year == 2020]
    cluster_latlon = cluster_mollweide.to_crs('EPSG:4326').geometry.iloc[0]
    # main_cluster[main_cluster.year == 2020].geometry.iloc[0]
    cluster_ee = ru.bbox_to_ee(cluster_latlon)

    # roof_area = calculate_building_area(country, cluster_ee)
    roof_area = calculate_building_area(
        bbox_mollweide, path_cache, cluster_mollweide.geometry
    )
    print(f'Roofs: {roof_area}')
    urban_area = calculate_urban_area(cluster_ee)
    print(f'Urban: {urban_area}')
    road_lenght = calculate_road_area(bbox_latlon, path_cache, cluster_latlon)
    print(f'Roads: {road_lenght}')

    df = pd.DataFrame(
        {
            'roofs': roof_area,
            'urban': urban_area,
            'roads': road_lenght
        },
        index=[0]
    )

    df.to_csv(path_cache / 'mitigation_areas.csv', index=False)

    print('Done.')

    return df


def load_or_get_mit_areas_df(city, country, path_fua, path_cache,
                             force=False):

    fpath = path_cache / 'mitigation_areas.csv'
    if fpath.exists() and not force:
        df = pd.read_csv(fpath)
    else:
        df = get_mit_areas_df(city, country, path_fua, path_cache)

    return df


def calculate_building_area(bbox_mollweide, path_cache, cluster):

    built = ghsl.load_or_download(bbox_mollweide, 'BUILT_S',
                                  data_path=path_cache, resolution=100)

    b_2020 = built.sel(band=2020)

    b_2020.rio.set_nodata(0)

    area = b_2020.rio.clip(cluster.geometry).sum().item()/1e6

    return area


# def calculate_building_area(country, bbox):

#     if country in country_name_map:
#         country = country_name_map[country]

#     buildings = ee.FeatureCollection(
#         f"projects/sat-io/open-datasets/MSBuildings/{country}")
#     buildings = buildings.filterBounds(bbox)
#     buildings = buildings.map(add_area)

#     area = buildings.aggregate_sum("area")
#     area = area.getInfo()
#     area /= 1e6

#     return area


def calculate_urban_area(bbox):
    lc, masks = wc.get_cover_and_masks(bbox, None)

    urban_mask = masks['urban']
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

    edges = load_roads_osm(bbox, path_cache).to_crs('EPSG:4326')
    pip = edges.within(cluster)

    total_lenght = edges[pip]['length'].sum()/1000

    return total_lenght
