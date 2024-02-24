import ee

import geemap.plotlymap as geemap
import geopandas as gpd
import pandas as pd
import plotly.express as px
import ursa.utils.date as du
import ursa.utils.raster as ru

from shapely.geometry import Polygon

class_dict = {
    "0": "Agua",
    "1": "Árboles",
    "2": "Césped/Pasto",
    "3": "Vegetación inundada",
    "4": "Cultivos",
    "5": "Arbusto y matorral",
    "6": "Urbanización",
    "7": "Descubierto",
    "8": "Nieve y hielo",
}

colors = {
    "Agua": "#419BDF",
    "Árboles": "#397D49",
    "Césped/Pasto": "#88B053",
    "Vegetación inundada": "#7A87C6",
    "Cultivos": "#E49635",
    "Arbusto y matorral": "#DFC35A",
    "Urbanización": "#C4281B",
    "Descubierto": "#A59B8F",
    "Nieve y hielo": "#B39FE1",
}

columns = list(class_dict.values())


def plot_map_season(bbox_latlon, fua_latlon_centroid, season, year, language='es'):
    """Plots Dynamic World temporal composite on map for year and season.

    Season can one of the four seasons or 'all' for a yearly aggregate.
    """
    
    category_translations = {
        "es": {
            "Agua": "Agua",
            "Árboles": "Árboles",
            "Césped/Pasto": "Césped/Pasto",
            "Vegetación inundada": "Vegetación inundada",
            "Cultivos": "Cultivos",
            "Arbusto y matorral": "Arbusto y matorral",
            "Urbanización": "Urbanización",
            "Descubierto": "Descubierto",
            "Nieve y hielo": "Nieve y hielo",
        },
        "en": {
            "Agua": "Water",
            "Árboles": "Trees",
            "Césped/Pasto": "Grass/Lawn",
            "Vegetación inundada": "Flooded Vegetation",
            "Cultivos": "Crops",
            "Arbusto y matorral": "Shrub and Scrub",
            "Urbanización": "Urbanization",
            "Descubierto": "Bare",
            "Nieve y hielo": "Snow and Ice",
        },
        "pt": {
            "Agua": "Água",
            "Árboles": "Árvores",
            "Césped/Pasto": "Grama/Relva",
            "Vegetación inundada": "Vegetação Alagada",
            "Cultivos": "Culturas",
            "Arbusto y matorral": "Arbusto e Mato",
            "Urbanización": "Urbanização",
            "Descubierto": "Descoberto",
            "Nieve y hielo": "Neve e Gelo",
        }
    }
    
    translated_colors = {category_translations[language][key]: value for key, value in colors.items()}

    assert season in ["Q1", "Q2", "Q3", "Q4", "Qall"]
    assert 2016 <= year <= 2023

    vis_params = {
        "min": 0,
        "max": 8,
        "palette": [
            colors["Agua"],
            colors["Árboles"],
            colors["Césped/Pasto"],
            colors["Vegetación inundada"],
            colors["Cultivos"],
            colors["Arbusto y matorral"],
            colors["Urbanización"],
            colors["Descubierto"],
            colors["Nieve y hielo"],
        ],
    }

    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = du.date_format(season, year)

    # Filter the Dynamic World NRT collection
    dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
    dw_col = dw_col.filterDate(start_date, end_date)
    dw_col = dw_col.filterBounds(bbox_ee)

    # Create a Mode Composite
    dw_lbl = dw_col.select("label")
    dw_lbl = dw_lbl.reduce(ee.Reducer.mode())

    # Create a Top-1 Probability Hillshade Visualization
    probability_bands = [
        "water",
        "trees",
        "grass",
        "flooded_vegetation",
        "crops",
        "shrub_and_scrub",
        "built",
        "bare",
        "snow_and_ice",
    ]

    # Select probability bands
    probability_col = dw_col.select(probability_bands)

    # Create a multi-band image with the average pixel-wise probability
    # for each band across the time-period
    mean_probability = probability_col.reduce(ee.Reducer.mean())

    # Composites have a default projection that is not suitable
    # for hillshade computation.
    # Set a EPSG:3857 projection with 10m scale
    projection = ee.Projection("EPSG:3857").atScale(10)
    mean_probability = mean_probability.setDefaultProjection(projection)

    # Create the Top1 Probability Hillshade.
    top1_probability = mean_probability.reduce(ee.Reducer.max())
    top1_confidence = top1_probability.multiply(100).int()
    hillshade = ee.Terrain.hillshade(top1_confidence).divide(255)
    rgb_image = dw_lbl.visualize(**vis_params).divide(255)
    probability_hillshade = rgb_image.multiply(hillshade)

    Map = geemap.Map(basemap="carto-positron")

    centroid = fua_latlon_centroid
    Map.set_center(centroid.y, centroid.x, zoom=10)

    Map.addLayer(
        probability_hillshade.clip(bbox_ee),
        {"min": 0, "max": 0.8},
        "Dynamic World",
        opacity=0.6,
    )
    Map.update_layout(height=600)

    # Crea una leyenda falsa usando GeoDataFrame
    poly = Polygon([(0, 0), (1e-3, 1e-3), (-1e-3, -1e-3)])
    gdf = gpd.GeoDataFrame(
        {"geometry": [poly] * 9, "Clases": list(translated_colors.keys())}, crs=4326
    ).reset_index()
    fig = px.choropleth_mapbox(
        gdf,
        geojson=gdf.geometry,
        locations="index",
        mapbox_style="carto-positron",
        color="Clases",
        color_discrete_map=translated_colors,
    )

    Map.add_traces(fig.data)

    Map.layout.mapbox.layers[0].sourceattribution = (
        "<a "
        'href="https://developers.google.com/earth-engine/'
        'datasets/catalog/GOOGLE_DYNAMICWORLD_V1#description">'
        "Dynamic World V1</a>"
        " | Google Earth Engine"
    )

    return Map


def download_map_season(bbox_latlon, season, year):
    """Plots Dynamic World temporal composite on map for year and season.

    Season can one of the four seasons or 'all' for a yearly aggregate.
    """

    assert season in ["Q1", "Q2", "Q3", "Q4", "Qall"]
    assert 2016 <= year <= 2023

    vis_params = {
        "min": 0,
        "max": 8,
        "palette": [
            "#419BDF",
            "#397D49",
            "#88B053",
            "#7A87C6",
            "#E49635",
            "#DFC35A",
            "#C4281B",
            "#A59B8F",
            "#B39FE1",
        ],
    }
    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = du.date_format(season, year)

    # Filter the Dynamic World NRT collection
    dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
    dw_col = dw_col.filterDate(start_date, end_date)
    dw_col = dw_col.filterBounds(bbox_ee)

    # Create a Mode Composite
    dw_lbl = dw_col.select("label")
    dw_lbl = dw_lbl.reduce(ee.Reducer.mode())

    # Create a Top-1 Probability Hillshade Visualization
    probability_bands = [
        "water",
        "trees",
        "grass",
        "flooded_vegetation",
        "crops",
        "shrub_and_scrub",
        "built",
        "bare",
        "snow_and_ice",
    ]

    # Select probability bands
    probability_col = dw_col.select(probability_bands)

    # Create a multi-band image with the average pixel-wise probability
    # for each band across the time-period
    mean_probability = probability_col.reduce(ee.Reducer.mean())

    # Composites have a default projection that is not suitable
    # for hillshade computation.
    # Set a EPSG:3857 projection with 10m scale
    projection = ee.Projection("EPSG:3857").atScale(10)
    mean_probability = mean_probability.setDefaultProjection(projection)

    # Create the Top1 Probability Hillshade.
    top1_probability = mean_probability.reduce(ee.Reducer.max())
    top1_confidence = top1_probability.multiply(100).int()
    hillshade = ee.Terrain.hillshade(top1_confidence).divide(255)
    rgb_image = dw_lbl.visualize(**vis_params).divide(255)
    probability_hillshade = rgb_image.multiply(hillshade)

    task = ee.batch.Export.image.toDrive(
        image=probability_hillshade,
        description="dynamic_world_raster",
        scale=10,
        region=bbox_ee,
        crs=projection,
        maxPixels=1e10,
        fileFormat="GeoTIFF",
    )
    task.start()
    return task


def get_cover_df(bbox_latlon, path_cache):
    print("Downloading land cover time series from GEE ...")

    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    dict_list = []
    for year in range(2016, 2023):
        start_date = f"{year}-1-1"
        end_date = f"{year}-12-31"

        col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        col = col.filterDate(start_date, end_date).filterBounds(bbox_ee)

        projection = col.first().projection()

        img = col.select("label").reduce(ee.Reducer.mode())
        img = img.setDefaultProjection(projection)

        pixelCountStats = img.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram().unweighted(),
            geometry=bbox_ee,
            maxPixels=1e10,
        )

        pixelCounts = ee.Dictionary(pixelCountStats.get("label_mode"))
        pixelCounts = pixelCounts.getInfo()
        pixelCounts["year"] = year
        dict_list.append(pixelCounts)

    df = pd.DataFrame(dict_list).set_index("year").rename(columns=class_dict)
    df = df * 100 / 1e6
    df = df[columns]
    df.to_csv(path_cache / "land_cover.csv")

    print("Done.")

    return df


def load_or_get_lc_df(bbox_latlon, path_cache, force=False):
    fpath = path_cache / "land_cover.csv"
    if fpath.exists() and not force:
        df = pd.read_csv(fpath, index_col="year")
    else:
        df = get_cover_df(bbox_latlon, path_cache)
    return df


def plot_lc_year(bbox_latlon, path_cache, year=2022, language='es'):

    translations = {
        "x_axis_title": {
            "es": "Área (km²)",
            "en": "Area (km²)",
            "pt": "Área (km²)"
        },
        "y_axis_title": {
            "es": "Tipo de cobertura",
            "en": "Type of Coverage",
            "pt": "Tipo de Cobertura"
        }
    }
    
    category_translations = {
        "es": {
            "Agua": "Agua",
            "Árboles": "Árboles",
            "Césped/Pasto": "Césped/Pasto",
            "Vegetación inundada": "Vegetación inundada",
            "Cultivos": "Cultivos",
            "Arbusto y matorral": "Arbusto y matorral",
            "Urbanización": "Urbanización",
            "Descubierto": "Descubierto",
            "Nieve y hielo": "Nieve y hielo",
        },
        "en": {
            "Agua": "Water",
            "Árboles": "Trees",
            "Césped/Pasto": "Grass/Lawn",
            "Vegetación inundada": "Flooded Vegetation",
            "Cultivos": "Crops",
            "Arbusto y matorral": "Shrub and Scrub",
            "Urbanización": "Urbanization",
            "Descubierto": "Bare",
            "Nieve y hielo": "Snow and Ice",
        },
        "pt": {
            "Agua": "Água",
            "Árboles": "Árvores",
            "Césped/Pasto": "Grama/Relva",
            "Vegetación inundada": "Vegetação Alagada",
            "Cultivos": "Culturas",
            "Arbusto y matorral": "Arbusto e Mato",
            "Urbanización": "Urbanização",
            "Descubierto": "Descoberto",
            "Nieve y hielo": "Neve e Gelo",
        }
    }

    x_col = translations["x_axis_title"][language]
    y_col = translations["y_axis_title"][language]

    lc_df = load_or_get_lc_df(bbox_latlon, path_cache)

    lc_present = (
        lc_df[lc_df.index == year]
        .T.reset_index()
        .rename(columns={"index": y_col, year: x_col})
        .sort_values(x_col, ascending=False)
        .reset_index(drop=True)
    )

    lc_present[x_col] = round(lc_present[x_col]).astype(int)
    
    #
    lc_present[y_col] = lc_present[y_col].map(category_translations[language])

    fig = px.bar(
        lc_present,
        x=x_col,
        y=y_col,
        color=y_col,
        color_discrete_map=colors,
        text_auto=True,
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_title="")

    return fig


def plot_lc_time_series(bbox_latlon, path_cache, language = 'es'):
    
    category_translations = {
        "es": {
            "Agua": "Agua",
            "Árboles": "Árboles",
            "Césped/Pasto": "Césped/Pasto",
            "Vegetación inundada": "Vegetación inundada",
            "Cultivos": "Cultivos",
            "Arbusto y matorral": "Arbusto y matorral",
            "Urbanización": "Urbanización",
            "Descubierto": "Descubierto",
            "Nieve y hielo": "Nieve y hielo",
        },
        "en": {
            "Agua": "Water",
            "Árboles": "Trees",
            "Césped/Pasto": "Grass/Lawn",
            "Vegetación inundada": "Flooded Vegetation",
            "Cultivos": "Crops",
            "Arbusto y matorral": "Shrub and Scrub",
            "Urbanización": "Urbanization",
            "Descubierto": "Bare",
            "Nieve y hielo": "Snow and Ice",
        },
        "pt": {
            "Agua": "Água",
            "Árboles": "Árvores",
            "Césped/Pasto": "Grama/Relva",
            "Vegetación inundada": "Vegetação Alagada",
            "Cultivos": "Culturas",
            "Arbusto y matorral": "Arbusto e Mato",
            "Urbanización": "Urbanização",
            "Descubierto": "Descoberto",
            "Nieve y hielo": "Neve e Gelo",
        }
    }
    
    translations = {
        "y_axis_title": {
            "es": "Área (km²)",
            "en": "Area (km²)",
            "pt": "Área (km²)"
        },
        "x_axis_title": {
            "es": "Año",
            "en": "Year",
            "pt": "Ano"
        },
        "legend_title": {
            "es": "Tipo de cobertura",
            "en": "Type of Coverage",
            "pt": "Tipo de Cobertura"
        }
    }

    lc_df = load_or_get_lc_df(bbox_latlon, path_cache)

    fig = px.area(lc_df, color_discrete_map=colors, markers=True)

    fig.update_layout(
        yaxis_title=translations["y_axis_title"][language],
        xaxis_title=translations["x_axis_title"][language],
        legend_title=translations["legend_title"][language],
        hovermode="x",
    )

    fig.update_traces(hovertemplate="%{y:.0f}<extra></extra>")

    names = {}
    for col in lc_df.columns:
        c0 = lc_df[col].iloc[0]
        cf = lc_df[col].iloc[-1]
        delta = (cf - c0) / c0 * 100
        up_down = "▲" if delta > 0 else "▼"
        translated_col = category_translations[language].get(col, col)
        names[col] = f"{translated_col} {up_down} {delta:0.2f}%"

    fig.for_each_trace(lambda t: t.update(name=names[t.name]))

    return fig

