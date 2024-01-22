import dash
import dateutil
import ee

import dash_bootstrap_components as dbc
import pandas as pd
import ursa.heat_islands as ht
import ursa.plots.heat_islands as pht
import ursa.utils.date as du
import ursa.utils.geometry as ug
import ursa.utils.raster as ru
import ursa.world_cover as wc

from components.text import figureWithDescription, figureWithDescription_translation, figureWithDescription_translation2
from components.page import new_page_layout
from dash import html, dcc, callback, Input, Output, State
from datetime import datetime, timezone
from layouts.common import generate_drive_text, generate_drive_text_translation
from pathlib import Path
from shapely.geometry import shape

import json

# Traducciones
with open('./data/translations/suhi/translations_suhi.json', 'r', encoding='utf-8') as file:
    translations = json.load(file)
    
# Traducciones
with open('./data/translations/suhi/tab_translations_suhi.json', 'r', encoding='utf-8') as file:
    tab_translations = json.load(file)

start_time_suhi = None

SEASON = "Qall"
YEAR = 2022

path_fua = Path("./data/output/cities/")

dash.register_page(
    __name__,
    title="URSA",
)

WELCOME_CONTENT = [
    html.P(
        [
            html.Span(id="WELCOME_CONTENT_PART1"),
            html.Strong(id="WELCOME_CONTENT_PART2"),
            html.Span(id="WELCOME_CONTENT_PART3"),
            html.A(id="WELCOME_CONTENT_PART4", href="https://www.mdpi.com/2072-4292/11/1/48"),
            
            html.Span(id="WELCOME_CONTENT_PART5"),
        ]
    ),
    html.Hr(style={"width": "70%", "margin-left": "30%"}),
    html.P(
        (
            "Zhou, D., Xiao, J., Bonafoni, S., Berger, C., Deilami, K., "
            "Zhou, Y., ... & Sobrino, J. A. (2018). "
            "Satellite remote sensing of surface urban heat islands: "
            "Progress, challenges, and perspectives. Remote Sensing, "
            "11(1), 48."
        ),
        style={
            "fontStyle": "italic",
            "fontSize": "0.9rem",
            "textAlign": "right",
            "width": "70%",
            "margin-left": "30%",
        },
    ),
]


MAP_INTRO_TEXT = (
    "El mapa a continuación muestra la desviación de temperatura de cada "
    "píxel en la superficie construida de la ciudad con respecto a la "
    "temperatura rural con un código de colores en 7 categorías. "
    "El color rojo más oscuro corresponde a las zonas urbana con una "
    "temperatura registrada que tiene la mayor desviación respecto a "
    "la temperatura rural en la zona circundante a la zona de interés "
    "(más de 2.5 desviaciones estándar de la media rural). "
    "Estas zonas en un color más oscuro corresponden a las islas de "
    "calor en la ciudad. "
    "Esta metodología que compara las temperaturas rurales y urbanas "
    "en una misma región es la más apropiada y generalizable, ya que "
    "al restar la temperatura media rural a la de cada píxel, "
    "se remueven variaciones locales y se puede comparar la intensidad "
    "de las islas de calor de ciudades en distintas latitudes."
)

MAP_TEXT = (
    "La información del mapa de las islas de calor se desglosa en una "
    "serie de gráficos que comparan su incidencia contra el tipo de uso "
    "de suelo en la región."
)

HISTOGRAMA_TEXT = html.P(
    [
        html.Span(id="HISTOGRAM_TEXT"),  
        html.Ol(
            [
                html.Li(html.Span(id="categoria-muy-frio")),
                html.Li(html.Span(id="categoria-frio")),
                html.Li(html.Span(id="categoria-ligeramente-frio")),
                html.Li(html.Span(id="categoria-templado")),
                html.Li(html.Span(id="categoria-ligeramente-calido")),
                html.Li(html.Span(id="categoria-caliente")),
                html.Li(html.Span(id="categoria-muy-caliente")),
            ]
        ),
        html.Span(id="desviacion"), 
    ]
)


BARS_TEXT = (
    "Las barras verticales en este gráfico suman 1 (o 100%) cada una. "
    "Las barras desglosan la composición de la superficie por tipo de "
    "uso de suelo para cada una de las 7 categorías de temperatura. "
    "Se puede apreciar que las temperaturas más frías se asocian con "
    "superficie de manglares o coberturas verdes, "
    "mientras que las superficies más calientes se componen principalmente "
    "de suelo construido y praderas."
)

LINE_TEXT = (
    "Un aspecto interesante a considerar es la variación de la temperatura "
    "en la superficie conforme nos alejamos del centro de la ciudad. "
    "Se espera que las islas de calor disminuyan conforme nos alejamos "
    "del centro de la zona urbana, que típicamente tiene la mayor "
    "superficie construida. "
    "Para evaluar esto, generamos “donas” concéntricas con radios "
    "crecientes. Con esto, calculamos la media de la SUHII de todos los "
    "pixeles contenidos en cada dona, y la graficamos en esta imagen. "
    "El gráfico muestra el diferencial de temperatura en ese radio específico"
    "y no de forma acumulada"
    "Se puede apreciar el gradiente de disminución de la temperatura "
    "promedio conforme incrementamos el radio de las “donas”, "
    "esto es, conforme nos alejamos del centro de la zona urbana."
)

AREA_TEXT = (
    "Podemos utilizar las “donas” concéntricas del gráfico anterior "
    "para calcular el uso de suelo en cada radio conforme nos alejamos "
    "de la zona central. "
    "Típicamente, lo que ocurre es que cerca del centro de la ciudad, "
    "la gran mayoría del suelo está cubierto de suelo construido; "
    "entre más nos alejamos, más disminuye esta categoría y aumenta "
    "la fracción de cobertura verde."
    "Cabe destacar que la composición de uso de suelo en cada radio o distancia"
    "no es acumulada, sino que es específica para esa dona en particular. "
    "Finalmente, cerca de los bordes de la ciudad, podemos observar una "
    "mezcla de varias coberturas, como xsparte del proceso de urbanización."
)

MEAN_TEMPERATURE_STYLE = {"font-weight": "lighter", "font-size": "3rem"}

SUBTITLE_STYLE = {"font-size": "100"}

RESULT_STYLE = {"font-weight": "lighter"}

STRATEGIES = {
    "strat-vegetacion": {
        "title": "Reintroducción de vegetación",
        "description": (
            "Reintroducir vegetación a al menos 16% del área "
            "urbana a través de parques, jardines y camellones"
            " puede generar un enfriamiento de 1.07 °C promedio."
        ),
        "mitigation": 1.07,
        "area_fraction": 0.16,
    },
    "strat-techos-verdes": {
        "title": "Instalación de techos verdes",
        "description": (
            "Instalar techos verdes en 50% de la superficie "
            "de techo disponible reduce un promedio de 0.083°C"
        ),
        "mitigation": 0.083,
        "area_fraction": 0.5,
    },
    "strat-techos-frescos": {
        "title": "Instalación de techos frescos",
        "description": (
            "Incrementar el albedo a 0.5 en el 50% de los techos "
            "de la ciudad  por medio de materiales reflectores en "
            "los techos reduce la temperatura un promedio de "
            "0.078°C"
        ),
        "mitigation": 0.078,
        "area_fraction": 0.5,
    },
    "strat-pavimento-concreto": {
        "title": "Instalación de pavimentos de concreto",
        "description": (
            "Cambiar los pavimentos de asfalto por pavimentos "
            "de concreto tiene la capacidad de reducir un "
            "promedio de 0.39ºC."
        ),
        "mitigation": 0.39,
        "area_fraction": 1.0,
    },
    "strat-pavimento-reflector": {
        "title": "Instalación de pavimentos reflectores",
        "description": (
            "Incrementar el albedo en 0.2 en todos los "
            "pavimentos de la ciudad mediante materiales o "
            "pinturas reflectoras en tiene la capacidad de "
            "reducir la temperatura en 1.39 °C promedio"
        ),
        "mitigation": 1.39,
        "area_fraction": 1.0,
    },
}


def format_temp(temp):
    return f"{round(temp, 2)} °C"


impactView = html.Div(
    [
        html.H4(id = "impactView1", className="text-primary"),
        html.Div(id = "impactView2", style=SUBTITLE_STYLE),
        html.Div("", id="impact-result-degrees", style=RESULT_STYLE),
        html.Div(id = "impactView3", style=SUBTITLE_STYLE),
        html.Div(
            "",
            id="impact-mitigated-degrees",
            className="text-success",
            style=RESULT_STYLE,
        ),
        html.Div(id = "impactView4", style=SUBTITLE_STYLE),
        html.Div("", id="impact-result-square-kilometers", style=RESULT_STYLE),
        html.Div(id = "impactView5", style=SUBTITLE_STYLE),
        html.Div("", id="impact-result-kilometers", style=RESULT_STYLE),
    ]
)

strategyList = html.Div(
    [
        html.H4(id="strategyList1", className="text-primary"),
        html.P(html.Span(id="strategyList2")),
        html.Div(
            dcc.Checklist(
                options=[
                    {
                        "label": html.Div(
                            [
                                html.P(
                                    html.Span(id="strat-vegetacion-title"),
                                    #STRATEGIES["strat-vegetacion"]["title"],
                                    id="check-strat-vegetacion",
                                    style={"display": "inline"},
                                ),
                                dbc.Popover(
                                    dbc.PopoverBody(html.Span(id="strat-vegetacion-desc")),
                                    target="check-strat-vegetacion",
                                    trigger="hover",
                                ),
                            ],
                            style={"display": "inline"},
                        ),
                        "value": "strat-vegetacion",
                    },
                    {
                        "label": html.Div(
                            [
                                html.P(
                                    html.Span(id="strat-techos-verdes-title"),
                                    id="check-strat-techos-verdes",
                                    style={"display": "inline"},
                                ),
                                dbc.Popover(
                                    dbc.PopoverBody(html.Span(id="strat-techos-verdes-desc")),
                                    target="check-strat-techos-verdes",
                                    trigger="hover",
                                ),
                            ],
                            style={"display": "inline"},
                        ),
                        "value": "strat-techos-verdes",
                    },
                    {
                        "label": html.Div(
                            [
                                html.P(
                                    html.Span(id="strat-techos-frescos-title"),
                                    id="check-strat-techos-frescos",
                                    style={"display": "inline"},
                                ),
                                dbc.Popover(
                                    dbc.PopoverBody(html.Span(id="strat-techos-frescos-desc")),
                                    target="check-strat-techos-frescos",
                                    trigger="hover",
                                ),
                            ],
                            style={"display": "inline"},
                        ),
                        "value": "strat-techos-frescos",
                    },
                    {
                        "label": html.Div(
                            [
                                html.P(
                                    html.Span(id = "strat-pavimento-concreto-title"),
                                    id="check-strat-pavimento-concreto",
                                    style={"display": "inline"},
                                ),
                                dbc.Popover(
                                    dbc.PopoverBody(html.Span(id = "strat-pavimento-concreto-desc")),
                                    target="check-strat-pavimento-concreto",
                                    trigger="hover",
                                ),
                            ],
                            style={"display": "inline"},
                        ),
                        "value": "strat-pavimento-concreto",
                    },
                    {
                        "label": html.Div(
                            [
                                html.P(
                                    html.Span(id = "strat-pavimento-reflector-title"),
                                    id="check-strat-pavimento-reflector",
                                    style={"display": "inline"},
                                ),
                                dbc.Popover(
                                    dbc.PopoverBody(html.Span(id = "strat-pavimento-reflector-desc")),
                                    target="check-strat-pavimento-reflector",
                                    trigger="hover",
                                ),
                            ],
                            style={"display": "inline"},
                        ),
                        "value": "strat-pavimento-reflector",
                    },
                ],
                value=[],
                id="strategy-checklist",
                inputStyle={"margin-right": "10px"},
                labelStyle={"display": "block", "margin-bottom": "15px"},
            ),
        ),
    ]
)


legend_colors = {
    "Muy frío": "#2166AC",
    "Frío": "#67A9CF",
    "Ligeramente frío": "#D1E5F0",
    "Templado": "#F7F7F7",
    "Ligeramente cálido": "#FDDBC7",
    "Caliente": "#EF8A62",
    "Muy caliente": "#B2182B",
}

map_legend = html.Div(
    [
        html.Div(
            [
                html.Div(
                    "",
                    style={
                        "height": "10px",
                        "width": "10px",
                        "backgroundColor": legend_colors["Muy frío"],
                        "margin-right": "5px",
                    },
                ),
                html.Div(
                    html.Span(id="color-muy-frio"),
                    className="font-weight-light text-white",
                    style={"font-size": "13px"},
                ),
            ],
            className="d-flex align-items-center m-1",
        ),
        html.Div(
            [
                html.Div(
                    "",
                    style={
                        "height": "10px",
                        "width": "10px",
                        "backgroundColor": legend_colors["Frío"],
                        "margin-right": "5px",
                    },
                ),
                html.Div(
                    html.Span(id="color-frio"),
                    className="font-weight-light text-white",
                    style={"font-size": "13px"},
                ),
            ],
            className="d-flex align-items-center m-1",
        ),
        html.Div(
            [
                html.Div(
                    "",
                    style={
                        "height": "10px",
                        "width": "10px",
                        "backgroundColor": legend_colors["Ligeramente frío"],
                        "margin-right": "5px",
                    },
                ),
                html.Div(
                    html.Span(id="color-ligeramente-frio"),
                    className="font-weight-light text-white",
                    style={"font-size": "13px"},
                ),
            ],
            className="d-flex align-items-center m-1",
        ),
        html.Div(
            [
                html.Div(
                    "",
                    style={
                        "height": "10px",
                        "width": "10px",
                        "backgroundColor": legend_colors["Templado"],
                        "margin-right": "5px",
                    },
                ),
                html.Div(
                    html.Span(id="color-templado"),
                    className="font-weight-light text-white",
                    style={"font-size": "13px"},
                ),
            ],
            className="d-flex align-items-center m-1",
        ),
        html.Div(
            [
                html.Div(
                    "",
                    style={
                        "height": "10px",
                        "width": "10px",
                        "backgroundColor": legend_colors["Ligeramente cálido"],
                        "margin-right": "5px",
                    },
                ),
                html.Div(
                    html.Span(id="color-ligeramente-calido"),
                    className="font-weight-light text-white",
                    style={"font-size": "13px"},
                ),
            ],
            className="d-flex align-items-center m-1",
        ),
        html.Div(
            [
                html.Div(
                    "",
                    style={
                        "height": "10px",
                        "width": "10px",
                        "backgroundColor": legend_colors["Caliente"],
                        "margin-right": "5px",
                    },
                ),
                html.Div(
                    html.Span(id="color-caliente"),
                    className="font-weight-light text-white",
                    style={"font-size": "13px"},
                ),
            ],
            className="d-flex align-items-center m-1",
        ),
        html.Div(
            [
                html.Div(
                    "",
                    style={
                        "height": "10px",
                        "width": "10px",
                        "backgroundColor": legend_colors["Muy caliente"],
                        "margin-right": "5px",
                    },
                ),
                html.Div(
                    html.Span(id="color-muy-caliente"),
                    className="font-weight-light text-white",
                    style={"font-size": "13px"},
                ),
            ],
            className="d-flex align-items-center m-1",
        ),
    ],
    className="d-flex justify-content-around flex-column",
    style={"width": "fit-content", "backgroundColor": "rgba(0,0,0,0.35)"},
)


map = html.Div(
    [
        html.Div(map_legend, className="position-absolute fixed-bottom right-0"),
        dcc.Graph(style={"height": "100%"}, id="suhi-graph-temp-map"),
    ],
    className="position-relative",
    style={"height": "100%"},
)

plots = html.Div(
    [
        dbc.Row(
            [
                figureWithDescription_translation2( # Version modificada para HISTOGRAMA_TEXT
                    dcc.Graph(id="suhi-graph-areas"),
                    HISTOGRAMA_TEXT,
                    "title1"
                ),
                
                figureWithDescription_translation(
                    dcc.Graph(id="suhi-graph-temp-lc"),
                    "BARS_TEXT",
                    "title2",
                ),
                figureWithDescription_translation(
                    dcc.Graph(id="suhi-graph-radial-temp"),
                    "empty-desc1",
                    "title3",
                ),
                figureWithDescription_translation(
                    dcc.Graph(id="suhi-graph-radial-lc"),
                    "empty-desc2",
                    "title4",
                ),
            ],
            style={"overflow": "scroll", "height": "82vh"},
        ),
    ],
    id="plots",
)

welcomeAlert = dbc.Alert(WELCOME_CONTENT, color="secondary")
mapIntroAlert = dbc.Alert(id = "MAP_INTRO_TEXT", color="light")

tabs = [
    dbc.Tab(
        html.Div(
            [
                html.Div(
                    [
                        html.P(id = "temperature", style=SUBTITLE_STYLE),
                        html.P(
                            id="suhi-p-urban-temp",
                            style=MEAN_TEMPERATURE_STYLE,
                        ),
                        html.P(
                            [
                                html.Span(id="satellite_image_data"),
                                html.A(
                                    "USGS Landsat 8 Level 2, Collection 2, Tier 1",
                                    href=(
                                        "https://developers.google.com/earth-engine"
                                        "/datasets/catalog/LANDSAT_LC08_C02_T1_L2"
                                    ),
                                ),
                            ],
                            style={"fontSize": "0.8rem"},
                        ),
                    ],
                    style={"margin-bottom": "15px"},
                ),
                strategyList,
                impactView,
            ],
        ),
        label="Controles",
        id="tab-controls-suhi",
        tab_id="tabControls",
    ),
    dbc.Tab(
        plots,
        label="Gráficas",
        id="tab-plots-suhi",
        tab_id="tabPlots",
    ),
    dbc.Tab(
        html.Div([welcomeAlert, mapIntroAlert]),
        label="Info",
        id="tab-info-suhi",
        tab_id="tabInfo",
    ),
    dbc.Tab(
        [
            generate_drive_text_translation(
                how="La información procesada en la sección Islas de Calor se realiza incluyendo Google Earth Engine. De esta manera, la descarga de los datos empleados, debido a su tamaño, es a través del Google Drive de la cuenta empleada en la autenticación de Google Earth Engine en el caso del raster y al disco local en el caso de los datos tabulares para hacer la visualizaciones.",
                where="La descarga del raster con nombre 'suhi_raster.tif' se hará al directorio raíz del Google Drive de la cuenta empleada. Por otro lado, el archivo descargado a disco es 'city-country-suhi-data.csv', reemplazando 'city' por la ciudad y 'country' por el país analizado, respectivamente.",
            ),
            dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    #"Descargar rasters",
                                    id="suhi-btn-download-rasters",
                                    color="light",
                                    title="Descarga los archivos Raster a Google Drive. En este caso la información es procesada en Google Earth Engine y la única opción de descarga es al directorio raíz de tu Google Drive.",
                                ),
                                width=4,
                            ),
                            dbc.Col(
                                dbc.Button(
                                    #"Cancelar ejecución",
                                    id="suhi-btn-stop-task",
                                    color="danger",
                                    style={"display": "none"},
                                ),
                                width=4,
                            ),
                        ],
                        justify="center",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    #"Descargar CSV",
                                    id="suhi-btn-download-csv",
                                    color="light",
                                    title="Descarga el archivo .csv, que alimenta las visualizaciones, localmente en tu carpeta de Descargas.",
                                ),
                                width=4,
                            ),
                            dbc.Col(width=4),
                        ],
                        justify="center",
                    ),
                    dbc.Row(
                        dbc.Col(html.Span(id="suhi-span-rasters-output"), width=3),
                        justify="center",
                    ),
                ],
            ),
        ],
        label="Descargables",
        id = "tabDownloadables-suhi",
    ),
]

# Traduccion

language_buttons = dbc.ButtonGroup(
    [
        dbc.Button("Español", id="btn-lang-es", n_clicks=0),
        dbc.Button("English", id="btn-lang-en", n_clicks=0),
        dbc.Button("Portuguese", id="btn-lang-pt", n_clicks=0),
    ],
    style={"position": "absolute", "top": "10px", "right": "10px", "z-index": "1"},
)

layout = new_page_layout(
    [map],
    tabs,
    stores=[
        dcc.Store("suhi-store-task-name"),
        dcc.Interval(id="suhi-interval", interval=10000, n_intervals=0, disabled=True),
        dcc.Download(id="download-dataframe-csv"),
        dcc.Location(id="suhi-location"),
    ],
    alerts=[
        dbc.Alert(
            "Algunas gráficas no pudieron ser generadas. Considere cambiar la bounding box de análisis.",
            id="suhi-alert",
            is_open=False,
            dismissable=True,
            color="warning",
        )
    ],
)

# ---
"""
layout = html.Div(
    [language_buttons, layout],
    style={"position": "relative"}
)
"""
@callback(
    [Output(key, 'children') for key in translations.keys()],
    [Input('current-language-store', 'data')]
)
def update_translated_content(language_data):
    language = language_data['language'] if language_data else 'es'
    updated_content = [translations[key][language] for key in translations.keys()]
    return updated_content

# ---

@callback(
    [Output(key, 'label') for key in tab_translations.keys()],
    [Input('btn-lang-es', 'n_clicks'),
     Input('btn-lang-en', 'n_clicks'),
     Input('btn-lang-pt', 'n_clicks')],
    [State('current-language-store', 'data')],
)
def update_tab_labels(btn_lang_es, btn_lang_en, btn_lang_pt, language_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        language = language_data['language'] if language_data else 'es'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        language = 'es' if button_id == 'btn-lang-es' else 'en' if button_id == 'btn-lang-en' else 'pt'

    tab_labels = [tab_translations[key][language] for key in tab_translations.keys()]
    return tab_labels

# ---


@callback(
    Output("impact-result-square-kilometers", "children"),
    Output("impact-result-kilometers", "children"),
    Output("impact-result-degrees", "children"),
    Output("impact-mitigated-degrees", "children"),
    Output("suhi-p-urban-temp", "children"),
    Output("suhi-location", "pathname"),
    Output("suhi-alert", "is_open"),
    Input("strategy-checklist", "value"),
    State("global-store-hash", "data"),
    State("global-store-bbox-latlon", "data"),
    State("global-store-uc-latlon", "data"),
)
def update_mitigation_kilometers(values, id_hash, bbox_latlon, uc_latlon):
    if id_hash is None:
        return [dash.no_update] * 5 + ["/", dash.no_update]

    path_cache = Path(f"./data/cache/{id_hash}")

    bbox_latlon = shape(bbox_latlon)
    uc_latlon = shape(uc_latlon)

    bbox_mollweide = ug.reproject_geometry(bbox_latlon, "ESRI:54009")
    uc_mollweide = ug.reproject_geometry(uc_latlon, "ESRI:54009")

    try:
        df = ht.load_or_get_mit_areas_df(
            bbox_latlon, bbox_mollweide, uc_mollweide.centroid, path_cache
        )
    except Exception:
        return [dash.no_update] * 6 + [True]

    urban_mean_temp = ht.get_urban_mean(bbox_latlon, "Qall", 2022, path_cache)

    area_roofs = df.roofs.item()
    area_urban = df.urban.item()
    roads_distance = df.roads.item()

    mitigatedDegrees = 0
    impactedSquareKm = 0
    impactedKm = 0

    for strategyId in values:
        mitigatedDegrees += STRATEGIES[strategyId]["mitigation"]
        areaFraction = STRATEGIES[strategyId]["area_fraction"]
        if (
            strategyId == "strat-pavimento-concreto"
            or strategyId == "strat-pavimento-reflector"
        ):
            impactedKm += roads_distance
        elif (
            strategyId == "strat-techos-verdes" or strategyId == "strat-techos-frescos"
        ):
            impactedSquareKm += area_roofs * areaFraction
        elif strategyId == "strat-vegetacion":
            impactedSquareKm += area_urban * areaFraction

    mitigatedUrbanTemperature = urban_mean_temp - mitigatedDegrees

    return (
        f"{int(round(impactedSquareKm, 0))} Km²",
        f"{int(round(impactedKm, 0))} Km",
        format_temp(mitigatedUrbanTemperature),
        format_temp(mitigatedDegrees),
        format_temp(urban_mean_temp),
        dash.no_update,
        dash.no_update,
    )


@callback(
    Output("download-dataframe-csv", "data"),
    Input("suhi-btn-download-csv", "n_clicks"),
    State("global-store-hash", "data"),
    prevent_initial_call=True,
)
def download_file(n_clicks, id_hash):
    path_cache = Path(f"./data/cache/{id_hash}")
    csv_path = path_cache / "land_cover_by_temp.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        return dcc.send_data_frame(df.to_csv, "suhi_data.csv")


@callback(
    Output("suhi-interval", "disabled", allow_duplicate=True),
    Output("suhi-store-task-name", "data"),
    Output("suhi-btn-stop-task", "style", allow_duplicate=True),
    Output("suhi-span-rasters-output", "children", allow_duplicate=True),
    Input("suhi-btn-download-rasters", "n_clicks"),
    State("global-store-hash", "data"),
    State("global-store-bbox-latlon", "data"),
    State("suhi-store-task-name", "data"),
    prevent_initial_call=True,
)
def start_download(n_clicks, id_hash, bbox_latlon, task_name):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update

    path_cache = Path(f"./data/cache/{id_hash}")

    if task_name is None:
        start_date, end_date = du.date_format("Qall", 2022)

        bbox_latlon = shape(bbox_latlon)
        bbox_ee = ru.bbox_to_ee(bbox_latlon)
        
        lst, proj = ht.get_lst(bbox_ee, start_date, end_date)
        _, masks = wc.get_cover_and_masks(bbox_ee, proj)

        img_cat = ht.get_cat_suhi(lst, masks, path_cache)

        task = ee.batch.Export.image.toDrive(
            image=img_cat,
            description="suhi_raster",
            scale=img_cat.projection().nominalScale(),
            region=bbox_ee,
            crs=img_cat.projection(),
            fileFormat="GeoTIFF",
        )
        task.start()
        status = task.status()

        return (False, status["name"], {"display": "block"}, "Iniciando descarga")
    else:
        return (dash.no_update, dash.no_update, dash.no_update, dash.no_update)


@callback(
    Output("suhi-span-rasters-output", "children", allow_duplicate=True),
    Output("suhi-interval", "disabled", allow_duplicate=True),
    Input("suhi-interval", "n_intervals"),
    State("suhi-store-task-name", "data"),
    prevent_initial_call=True,
)
def download_rasters(n_intervals, task_name):
    task_metadata = ee.data.getOperation(task_name)["metadata"]
    state = task_metadata["state"]

    start_time = task_metadata["createTime"]
    start_time = dateutil.parser.isoparse(start_time)

    current_time = datetime.now(timezone.utc)
    time_elapsed = (current_time - start_time).total_seconds()

    if state in ("COMPLETED", "FAILED", "CANCELLED", "SUCCEEDED"):
        return [f"Status de la Descarga: {state}, Tiempo transcurrido: {int(time_elapsed)} segundos"], True
    
    return [f"Status de la Descarga: {state}, Tiempo transcurrido: {int(time_elapsed)} segundos"], False


@callback(
    Output("suhi-graph-temp-map", "figure"),
    Output("suhi-graph-areas", "figure"),
    Output("suhi-graph-temp-lc", "figure"),
    Output("suhi-graph-radial-temp", "figure"),
    Output("suhi-graph-radial-lc", "figure"),
    Input("global-store-hash", "data"),
    Input("global-store-bbox-latlon", "data"),
    Input("global-store-fua-latlon", "data"),
    Input("global-store-uc-latlon", "data"),
    Input('btn-lang-es', 'n_clicks'),
    Input('btn-lang-en', 'n_clicks'),
    Input('btn-lang-pt', 'n_clicks'),
    [State('current-language-store', 'data')],
)
def generate_maps(id_hash, bbox_latlon, fua_latlon, uc_latlon, btn_lang_es, btn_lang_en, btn_lang_pt, language_data):
    if id_hash is None:
        return [dash.no_update] * 5
    
    ctx = dash.callback_context
    if not ctx.triggered:
        language = language_data['language'] if language_data else 'es'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        language = 'es' if button_id == 'btn-lang-es' else 'en' if button_id == 'btn-lang-en' else 'pt'

    path_cache = Path(f"./data/cache/{id_hash}")

    bbox_latlon = shape(bbox_latlon)
    fua_latlon = shape(fua_latlon)
    uc_latlon = shape(uc_latlon)
    bbox_ee = ru.bbox_to_ee(bbox_latlon)

    start_date, end_date = ht.date_format(SEASON, YEAR)

    try:
        lst, proj = ht.get_lst(bbox_ee, start_date, end_date)

        _, masks = wc.get_cover_and_masks(bbox_ee, proj)

        img_cat = ht.get_cat_suhi(lst, masks, path_cache)
        df_t_areas = ht.load_or_get_t_areas(bbox_ee, img_cat, masks, path_cache)
        df_land_usage = ht.load_or_get_land_usage_df(bbox_ee, img_cat, path_cache)

        temp_map = pht.plot_cat_map(
            bbox_ee, fua_latlon.centroid, img_cat
        )
        areas_plot = pht.plot_temp_areas(df_t_areas, language=language) # 
        
        temps_by_lc_plot = pht.plot_temp_by_lc(df_land_usage, language=language) #
        
    except Exception as e:
        temp_map = dash.no_update
        areas_plot = dash.no_update
        temps_by_lc_plot = dash.no_update        

    df_f, df_lc = ht.load_or_get_radial_distributions(bbox_latlon, uc_latlon, start_date, end_date, path_cache)
    
    radial_temp_plot = pht.plot_radial_temperature(df_f, language=language) #
    radial_lc_plot = pht.plot_radial_lc(df_lc, language=language) #

    return temp_map, areas_plot, temps_by_lc_plot, radial_temp_plot, radial_lc_plot


@callback(
    Output("suhi-btn-stop-task", "style"),
    Output("suhi-interval", "disabled"),
    Output("suhi-span-rasters-output", "children"),
    Input("suhi-btn-stop-task", "n_clicks"),
    State("suhi-store-task-name", "data"),
    prevent_initial_call=True,
)
def stop_task(n_clicks, task_id):
    ee.data.cancelOperation(task_id)
    return {"display": "none"}, True, "Descarga cancelada"