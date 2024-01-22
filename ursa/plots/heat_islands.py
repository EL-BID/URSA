import geemap.plotlymap as geemap

import plotly.express as px
import plotly.graph_objects as go
import ursa.world_cover as wc

from ursa.constants import TEMP_COLORS

def plot_radial_temperature(df, language='es'):
    
    translations = {
        "es": {
            "x_label": "Radio (km)",
            "y_label": "Diferencia con respecto a la temperatura rural (°C)"
        },
        "en": {
            "x_label": "Radius (km)",
            "y_label": "Difference from rural temperature (°C)"
        },
        "pt": {
            "x_label": "Raio (km)",
            "y_label": "Diferença em relação à temperatura rural (°C)"
        }
    }

    fig = px.line(
        x=df["radius"].map(lambda x: round(x, 1)),
        y=df["reduced"].map(lambda x: round(x, 1)),
        labels={
            "x": translations[language]["x_label"],
            "y": translations[language]["y_label"]
        }
    )

    return fig

def plot_radial_lc(df, language = "es"):
    df.round(1)
    colors = [wc.COVER_PALETTE_NAME_MAP[x] for x in df.columns]
    x = list(df.index)
    map(lambda x: round(x, 1), x)

    land_type_translations = {
        "es": {
            "Árboles": "Árboles",
            "Matorral": "Matorral",
            "Pradera": "Pradera",
            "Cultivos": "Cultivos",
            "Construido": "Construido",
            "Desnudo / Vegetación escasa": "Desnudo / Vegetación escasa",
            "Nieve y hielo": "Nieve y hielo",
            "Agua": "Agua",
            "Humedal herbaceo": "Humedal herbáceo",
            "Manglares": "Manglares",
            "Musgo y liquen": "Musgo y liquen"
        },
        "en": {
            "Árboles": "Trees",
            "Matorral": "Shrubland",
            "Pradera": "Grassland",
            "Cultivos": "Cropland",
            "Construido": "Built-up",
            "Desnudo / Vegetación escasa": "Bare / Sparse Vegetation",
            "Nieve y hielo": "Snow and Ice",
            "Agua": "Water",
            "Humedal herbaceo": "Herbaceous Wetland",
            "Manglares": "Mangroves",
            "Musgo y liquen": "Moss and Lichen"
        },
        "pt": {
            "Árboles": "Árvores",
            "Matorral": "Arbustos",
            "Pradera": "Pradaria",
            "Cultivos": "Cultivos",
            "Construido": "Construído",
            "Desnudo / Vegetación escasa": "Desnudo / Vegetação Escassa",
            "Nieve y hielo": "Neve e Gelo",
            "Agua": "Água",
            "Humedal herbaceo": "Pântano Herbáceo",
            "Manglares": "Manguezais",
            "Musgo y liquen": "Musgo e Líquen"
        }
    }
    
    df.rename(columns=land_type_translations[language], inplace=True)
    
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
        
    axis_titles = {
        "es": {"xaxis_title": "Radio (km)", "yaxis_title": "Porcentaje"},
        "en": {"xaxis_title":"Radius (km)", "yaxis_title": "Percentage"},
        "pt": {"xaxis_title": "Raio (km)", "yaxis_title": "Percentagem"}
        }
               
    fig.update_layout(
        xaxis_title=axis_titles[language]["xaxis_title"],
        yaxis_title=axis_titles[language]["yaxis_title"],
        yaxis_range=(0, 1),
        yaxis=dict(tickformat=".0%")
    )

    return fig

def plot_temp_areas(df_t_areas, language="es"):
    
    TEMP_COLORS_ES = {
        "Muy frío": "#2166AC",
        "Frío": "#67A9CF",
        "Ligeramente frío": "#D1E5F0",
        "Templado": "#F7F7F7",
        "Ligeramente cálido": "#FDDBC7",
        "Caliente": "#EF8A62",
        "Muy caliente": "#B2182B",
    }

    TEMP_COLORS_EN = {
        "Very Cold": "#2166AC",
        "Cold": "#67A9CF",
        "Slightly Cold": "#D1E5F0",
        "Temperate": "#F7F7F7",
        "Slightly Warm": "#FDDBC7",
        "Hot": "#EF8A62",
        "Very Hot": "#B2182B",
    }

    TEMP_COLORS_PT = {
        "Muito Frio": "#2166AC",
        "Frio": "#67A9CF",
        "Ligeiramente Frio": "#D1E5F0",
        "Temperado": "#F7F7F7",
        "Ligeiramente Quente": "#FDDBC7",
        "Quente": "#EF8A62",
        "Muito Quente": "#B2182B",
    }

    TEMP_COLORS = TEMP_COLORS_ES if language == "es" else TEMP_COLORS_EN if language == "en" else TEMP_COLORS_PT

    fig = px.bar(
        df_t_areas.rename(columns={"total": "Area"}),
        x=[k for i, k in enumerate(TEMP_COLORS.keys()) if i + 1 in df_t_areas.index],
        y="Area",
        color=[k for i, k in enumerate(TEMP_COLORS.keys()) if i + 1 in df_t_areas.index],
        color_discrete_map=TEMP_COLORS,
    )

    titles = {
        "es": {"xaxis_title": "Clase de temperatura", "yaxis_title": "Área (km²)", "legend_title": "Temperatura"},
        "en": {"xaxis_title": "Temperature Class", "yaxis_title": "Area (km²)", "legend_title": "Temperature"},
        "pt": {"xaxis_title": "Classe de Temperatura", "yaxis_title": "Área (km²)", "legend_title": "Temperatura"}
    }

    fig.update_layout(
        xaxis_title=titles[language]["xaxis_title"],
        yaxis_title=titles[language]["yaxis_title"],
        legend_title=titles[language]["legend_title"],
    )

    return fig

def plot_cat_map(bbox_ee, fua_latlon_centroid, img_cat):
    print("Generating temperature map ...")
    vis_params = {"min": 0, "max": 7, "palette": ["#000000"] + list(TEMP_COLORS.values())}

    Map = geemap.Map(basemap="carto-positron")
    Map.set_center(fua_latlon_centroid.y, fua_latlon_centroid.x, zoom=10)
    Map.addLayer(img_cat.clip(bbox_ee), vis_params, "SUHI", opacity=0.6)
    Map.layout.mapbox.layers[0].sourceattribution = "LandSat" " | Google Earth Engine"

    print("Done.")

    return Map


def plot_temp_by_lc(df, language="es"):
    
    COVER_NAMES_ES = [
        "Árboles",
        "Matorral",
        "Pradera",
        "Cultivos",
        "Construido",
        "Desnudo / Vegetación escasa",
        "Nieve y hielo",
        "Agua",
        "Humedal herbaceo",
        "Manglares",
        "Musgo y liquen",
    ]

    COVER_NAMES_EN = [
        "Trees",
        "Shrubland",
        "Grassland",
        "Cropland",
        "Built-up",
        "Bare / Sparse Vegetation",
        "Snow and Ice",
        "Water",
        "Herbaceous Wetland",
        "Mangroves",
        "Moss and Lichen",
    ]

    COVER_NAMES_PT = [
        "Árvores",
        "Arbustos",
        "Pradaria",
        "Cultivos",
        "Construído",
        "Desnudo / Vegetação Escassa",
        "Neve e Gelo",
        "Água",
        "Pântano Herbáceo",
        "Mangues",
        "Musgo e Líquen",
    ]

    COVER_PALETTE = [
        "#006400",
        "#FFBB22",
        "#FFFF4C",
        "#F096FF",
        "#FA0000",
        "#B4B4B4",
        "#F0F0F0",
        "#0064C8",
        "#0096A0",
        "#00CF75",
        "#FAE6A0",
    ]

    COVER_MAP_ES = {key: value for key, value in zip(COVER_NAMES_ES, COVER_PALETTE)}
    COVER_MAP_EN = {key: value for key, value in zip(COVER_NAMES_EN, COVER_PALETTE)}
    COVER_MAP_PT = {key: value for key, value in zip(COVER_NAMES_PT, COVER_PALETTE)}

    COVER_PALETTE_NAME_MAP = COVER_MAP_ES if language == "es" else COVER_MAP_EN if language == "en" else COVER_MAP_PT
    
    titles_translations = {
        "es": {"xaxis_title": "Clase de temperatura", "yaxis_title": "Fracción por cobertura", "legend_title": "Tipo de suelo", "usage_label": "Uso"},
        "en": {"xaxis_title": "Temperature Class", "yaxis_title": "Fraction by Coverage", "legend_title": "Land Type", "usage_label": "Usage"},
        "pt": {"xaxis_title": "Classe de Temperatura", "yaxis_title": "Fração por Cobertura", "legend_title": "Tipo de Solo", "usage_label": "Uso"}
    }
    
    temperature_translations = {
    "es": {
        "Muy frío": "Muy frío",
        "Frío": "Frío",
        "Ligeramente frío": "Ligeramente frío",
        "Templado": "Templado",
        "Ligeramente cálido": "Ligeramente cálido",
        "Caliente": "Caliente",
        "Muy caliente": "Muy caliente"
    },
    "en": {
        "Muy frío": "Very Cold",
        "Frío": "Cold",
        "Ligeramente frío": "Slightly Cold",
        "Templado": "Temperate",
        "Ligeramente cálido": "Slightly Warm",
        "Caliente": "Hot",
        "Muy caliente": "Very Hot"
    },
    "pt": {
        "Muy frío": "Muito Frio",
        "Frío": "Frio",
        "Ligeramente frío": "Ligeiramente Frio",
        "Templado": "Temperado",
        "Ligeramente cálido": "Ligeiramente Quente",
        "Caliente": "Quente",
        "Muy caliente": "Muito Quente"
    }
}


    land_type_translations = {
        "es": {
            "Árboles": "Árboles",
            "Matorral": "Matorral",
            "Pradera": "Pradera",
            "Cultivos": "Cultivos",
            "Construido": "Construido",
            "Desnudo / Vegetación escasa": "Desnudo / Vegetación escasa",
            "Humedal herbaceo": "Humedal herbaceo"
        },
        "en": {
            "Árboles": "Trees",
            "Matorral": "Shrubland",
            "Pradera": "Grassland",
            "Cultivos": "Cropland",
            "Construido": "Built-up",
            "Desnudo / Vegetación escasa": "Bare / Sparse Vegetation",
            "Humedal herbaceo": "Herbaceous Wetland"
        },
        "pt": {
            "Árboles": "Árvores",
            "Matorral": "Arbustos",
            "Pradera": "Pradaria",
            "Cultivos": "Cultivos",
            "Construido": "Construído",
            "Desnudo / Vegetación escasa": "Desnudo / Vegetação Escassa",
            "Humedal herbaceo": "Pântano Herbáceo"
        }
    }

    df['Land type'] = df['Land type'].map(land_type_translations[language])

    df['Temperature'] = df['Temperature'].map(temperature_translations[language])

    fig = px.bar(
        data_frame=df,
        x="Temperature",
        y="sum",
        color="Land type",
        color_discrete_map=COVER_PALETTE_NAME_MAP,
        labels={"sum": "Usage"},
    )

    fig.update_layout(
        xaxis_title=titles_translations[language]["xaxis_title"],
        yaxis_title=titles_translations[language]["yaxis_title"],
        legend_title=titles_translations[language]["legend_title"],
    )

    return fig

