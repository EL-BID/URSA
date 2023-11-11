import geemap.plotlymap as geemap

import plotly.express as px
import plotly.graph_objects as go
import ursa.world_cover as wc

from ursa.constants import TEMP_COLORS

def plot_radial_temperature(df):
    fig = px.line(
        x=df["radius"].map(lambda x: round(x, 1)),
        y=df["reduced"].map(lambda x: round(x, 1)),
        labels={
            "x": "Radio (km)",
            "y": "Diferencia con respecto a la temperatura rural (°C)",
        },
    )

    return fig


def plot_radial_lc(df):
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


def plot_temp_areas(df_t_areas):
    fig = px.bar(
        df_t_areas.rename(columns={"total": "Area"}),
        x=[k for i, k in enumerate(TEMP_COLORS.keys()) if i + 1 in df_t_areas.index],
        y="Area",
        color=[k for i, k in enumerate(TEMP_COLORS.keys()) if i + 1 in df_t_areas.index],
        color_discrete_map=TEMP_COLORS,
    )

    fig.update_layout(
        # title="Plot Title",
        xaxis_title="Clase de temperatura",
        yaxis_title="Área (km²)",
        legend_title="Temperatura",
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


def plot_temp_by_lc(df):
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