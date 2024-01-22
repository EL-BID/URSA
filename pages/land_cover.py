import dash
import dateutil.parser
import ee

import dash_bootstrap_components as dbc
import ursa.dynamic_world as udw

from components.page import new_page_layout
from components.text import figureWithDescription, figureWithDescription_translation
from dash import html, dcc, callback, Input, Output, State
from datetime import datetime, timezone
from layouts.common import generate_drive_text, generate_drive_text_translation, generate_drive_text_translation_land
from pathlib import Path
from shapely.geometry import shape

import json

# Traducciones
with open('./data/translations/land_cover/translations_land_cover.json', 'r', encoding='utf-8') as file:
    translations = json.load(file)
    
with open('./data/translations/land_cover/tab_translations_land_cover.json', 'r', encoding='utf-8') as file:
    tab_translations = json.load(file)

path_fua = Path("./data/output/cities/")

dash.register_page(
    __name__,
    title="URSA",
)

MAIN_TEXT = """El mapa muestra la categoría mas común observada en 2022
        para cada pixel de 10x10 metros.
        El relieve refleja la certeza del proceso de clasificación,
        una mayor altura refleja una mayor certidumbre de que el
        pixel pertnezca a la clase mostrada.
        Notese que los bordes entre clases presentan mayor
        incertidumbre. """

ADDITIONAL_TEXT = [
    html.Div(id='ADDITIONAL_TEXT_PART1'),
    html.A("Dynamic World", href="https://dynamicworld.app"),
    html.Div(id='ADDITIONAL_TEXT_PART2'),
    html.Br(),
    html.Div(id='ADDITIONAL_TEXT_PART3'),
    html.Br(),
    html.Div(id='ADDITIONAL_TEXT_PART4'),
    html.A(
        "enlace",
        href="https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1#bands",
    ),
    ":",
    html.Ul(
        [
            html.Li(id = "tipo-agua"),
            html.Li(id = "tipo-arboles"),
            html.Li(id = "tipo-pasto"),
            html.Li(id = "tipo-vegetacion"),
            html.Li(id = "tipo-cultivos"),
            html.Li(id = "tipo-arbustos"),
            html.Li(id = "tipo-construido"),
            html.Li(id = "tipo-baldio"),
            html.Li(id = "tipo-nieve"),
        ]
    ),
]

maps = html.Div(
    [
        dcc.Graph(style={"height": "100%"}, id="cover-map-1"),
    ],
    style={"height": "100%"},
)

lines = html.Div(
    [
        figureWithDescription_translation(
        dcc.Graph(id="cover-lines-1"),
        "DESC1",  # ID descripción
        "TITLE1"  # ID título
        ),
        
        figureWithDescription_translation(
        dcc.Graph(id="cover-lines-2"),
        "DESC2",  # ID descripción
        "TITLE2"  # ID título
        ),
    ],
    style={"overflow": "scroll", "height": "82vh"},
)

main_info = dbc.Card(
    dbc.CardBody(
        [
            html.H4(id="TITLE3"), 
            html.Div(id="MAIN_TEXT"),  
        ]
    ),
    class_name="main-info",
)

additional_info = dbc.Card(dbc.CardBody(ADDITIONAL_TEXT), class_name="supp-info")

tabs = [
    dbc.Tab(
        lines,
        label="Gráficas",
        id="tab-plots",
        tab_id="tabPlots",
    ),
    dbc.Tab(
        html.Div([main_info, additional_info]),
        label="Info",
        id="tab-info",
        tab_id="tabInfo",
    ),
    dbc.Tab(
        [
            generate_drive_text_translation_land(
                how="La información procesada en la sección Cobertura de Suelo se realiza principalmente mediante de Google Earth Engine. De esta manera, la descarga de los datos empleados, debido a su tamaño, es a través del Google Drive de la cuenta empleada en la autenticación de Google Earth Engine.",
                where="La descarga del raster con nombre 'dynamic_world_raster.tif' se hará al directorio raíz del Google Drive de la cuenta empleada.",
            ),
            dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    html.Span(id = "info-button1"),
                                    #"Descarga rasters",
                                    id="lc-btn-download-rasters",
                                    color="light",
                                    title="Descarga los archivos Raster a Google Drive. En este caso la información es procesada en Google Earth Engine y la única opción de descarga es al directorio raíz de tu Google Drive.",
                                    #html.Span(id = "info-button1"),
                                ),
                                width=4,
                            ),
                            dbc.Col(
                                dbc.Button(
                                    #"Cancelar ejecución",
                                    id="lc-btn-stop-task",
                                    color="danger",
                                    style={"display": "none"},
                                ),
                                width=4,
                            ),
                        ],
                        justify="center",
                    ),
                    dbc.Row(
                        dbc.Col(html.Span(id="lc-span-rasters-output"), width=3),
                        justify="center",
                    ),
                ],
            ),
        ],
        label="Descargables",
        id = "tabDownloadables",
        tab_id="tabDownloadables",
    ),
]

# Traducciones
language_buttons = dbc.ButtonGroup(
    [
        dbc.Button("Español", id="btn-lang-es", n_clicks=0),
        dbc.Button("English", id="btn-lang-en", n_clicks=0),
        dbc.Button("Portuguese", id="btn-lang-pt", n_clicks=0),
    ],
    style={"position": "absolute", "top": "10px", "right": "10px", "z-index": "1"},
)

layout = new_page_layout(
    maps,
    tabs,
    stores=[
        dcc.Store(id="lc-store-task-name"),
        dcc.Interval(id="lc-interval", interval=10000, n_intervals=0, disabled=True),
        dcc.Location(id="lc-location"),
    ],
)

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
    Output("lc-interval", "disabled", allow_duplicate=True),
    Output("lc-store-task-name", "data"),
    Output("lc-btn-stop-task", "style", allow_duplicate=True),
    Output("lc-span-rasters-output", "children", allow_duplicate=True),
    Input("lc-btn-download-rasters", "n_clicks"),
    State("global-store-bbox-latlon", "data"),
    State("lc-store-task-name", "data"),
    prevent_initial_call=True,
)
def start_download(n_clicks, bbox_latlon, task_name):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update

    if task_name is None:
        bbox_latlon = shape(bbox_latlon)
        task = udw.download_map_season(bbox_latlon, "Qall", 2022)
        status = task.status()
        return False, status["name"], {"display": "block"}, "Iniciando descarga"
    else:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update


@callback(
    Output("lc-span-rasters-output", "children", allow_duplicate=True),
    Output("lc-interval", "disabled", allow_duplicate=True),
    Input("lc-interval", "n_intervals"),
    State("lc-store-task-name", "data"),
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
    [Output("cover-map-1", "figure"),
     Output("cover-lines-1", "figure"),
     Output("cover-lines-2", "figure"),
     Output("lc-location", "pathname")],
    [Input("global-store-hash", "data"),
     Input("global-store-bbox-latlon", "data"),
     Input("global-store-fua-latlon", "data"),
     Input('btn-lang-es', 'n_clicks'),
     Input('btn-lang-en', 'n_clicks'),
     Input('btn-lang-pt', 'n_clicks')],
    [State('current-language-store', 'data')],
)
def generate_plots(id_hash, bbox_latlon, fua_latlon, btn_lang_es, btn_lang_en, btn_lang_pt, language_data):
    if id_hash is None:
        return [dash.no_update] * 3 + ["/"]
    
    ctx = dash.callback_context
    if not ctx.triggered:
        language = language_data['language'] if language_data else 'es'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        language = 'es' if button_id == 'btn-lang-es' else 'en' if button_id == 'btn-lang-en' else 'pt'

    path_cache = Path(f"./data/cache/{id_hash}")

    bbox_latlon = shape(bbox_latlon)
    fua_latlon = shape(fua_latlon)

    map1 = udw.plot_map_season(
        bbox_latlon, fua_latlon.centroid, season="Qall", year=2022, language=language
    )
    lines1 = udw.plot_lc_year(bbox_latlon, path_cache, year=2022, language=language)
    lines2 = udw.plot_lc_time_series(bbox_latlon, path_cache, language=language)


    return map1, lines1, lines2, dash.no_update

@callback(
    Output("lc-btn-stop-task", "style"),
    Output("lc-interval", "disabled"),
    Output("lc-span-rasters-output", "children"),
    Input("lc-btn-stop-task", "n_clicks"),
    State("lc-store-task-name", "data"),
    prevent_initial_call=True,
)
def stop_task(n_clicks, task_id):
    ee.data.cancelOperation(task_id)
    return {"display": "none"}, True, "Descarga cancelada"