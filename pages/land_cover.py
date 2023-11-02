import dash
import dateutil.parser
import ee

import dash_bootstrap_components as dbc
import ursa.dynamic_world as udw

from components.page import new_page_layout
from components.text import figureWithDescription
from dash import html, dcc, callback, Input, Output, State
from datetime import datetime, timezone
from layouts.common import generate_drive_text
from pathlib import Path
from shapely.geometry import shape

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

ADDITIONAL_TEXT = html.Div(
    [
        """En esta pestaña podrás explorar los tipos de cobertura de suelo "
    presentes en el área alrededor de tu ciudad.
    Estos datos de cobertura de suelo provienen del proyecto """,
        html.A("Dynamic World", href="https://dynamicworld.app"),
        " de Google.",
        html.Br(),
        """En Dynamic World, las imágenes satelitales Sentinel son
    procesadas usando un red neuronal para clasificar cada
    pixel en una de las 9 posibles categorías de suelo.
    Dynamic World posee datos de cobertura de suelo desde el
    año 2016.""",
        html.Br(),
        "Las correspondencias y colores canónicos de cada etiqueta pueden revisarse en el siguiente ",
        html.A(
            "enlace",
            href="https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1#bands",
        ),
        ":",
        html.Ul(
            [
                html.Li("0: Agua"),
                html.Li("1: Árboles"),
                html.Li("2: Pasto"),
                html.Li("3: Vegetación inundada"),
                html.Li("4: Cultivos"),
                html.Li("5: Arbustos y maleza"),
                html.Li("6: Construido"),
                html.Li("7: Baldío"),
                html.Li("8: Nieve y hielo"),
            ]
        ),
    ]
)

maps = html.Div(
    [
        dcc.Graph(style={"height": "100%"}, id="cover-map-1"),
    ],
    style={"height": "100%"},
)

lines = html.Div(
    [
        figureWithDescription(
            dcc.Graph(id="cover-lines-1"),
            html.P(
                "El gráfico de barras muestra las superficie en kilómetros "
                "cuadrados que le corresponde a cada clase de cobertura en "
                "el año 2022."
            ),
            "Superficie por Categoría de Uso de Suelo (Año 2022)",
        ),
        figureWithDescription(
            dcc.Graph(id="cover-lines-2"),
            html.P(
                "El gráfico de líneas muestra la evolución en el tiempo "
                "de la cantidad de superficie de cada clase de cobertura "
                "desde 2016 hasta el 2022. "
                "El gráfico es interactivo y se pueden seleccionar una "
                "o varias clases específicas para observar más claramente "
                "su comportamiento en el tiempo."
            ),
            "Cobertura de suelo",
        ),
    ],
    style={"overflow": "scroll", "height": "82vh"},
)

main_info = dbc.Card(
    dbc.CardBody(
        [
            html.H4(
                "Clasificación del Territorio por Categoría de Uso de Suelo (Año 2022)"
            ),
            MAIN_TEXT,
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
            generate_drive_text(
                how="La información procesada en la sección Cobertura de Suelo se realiza principalmente mediante de Google Earth Engine. De esta manera, la descarga de los datos empleados, debido a su tamaño, es a través del Google Drive de la cuenta empleada en la autenticación de Google Earth Engine.",
                where="La descarga del raster con nombre 'dynamic_world_raster.tif' se hará al directorio raíz del Google Drive de la cuenta empleada.",
            ),
            dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    "Descarga rasters",
                                    id="lc-btn-download-rasters",
                                    color="light",
                                    title="Descarga los archivos Raster a Google Drive. En este caso la información es procesada en Google Earth Engine y la única opción de descarga es al directorio raíz de tu Google Drive.",
                                ),
                                width=4,
                            ),
                            dbc.Col(
                                dbc.Button(
                                    "Cancelar ejecución",
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
    ),
]

layout = new_page_layout(
    maps,
    tabs,
    stores=[
        dcc.Store(id="lc-store-task-name"),
        dcc.Interval(id="lc-interval", interval=10000, n_intervals=0, disabled=True),
        dcc.Location(id="lc-location"),
    ],
)


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

    if state in ("UNSUBMITTED", "READY", "RUNNING", "CANCEL_REQUESTED"):
        return f"Status de la Descarga: {state}, Tiempo transcurrido: {int(time_elapsed)} segundos"
    elif state in ("COMPLETED", "FAILED", "CANCELLED"):
        return f"Status de la Descarga: {state}, Tiempo transcurrido: {int(time_elapsed)} segundos"


@callback(
    Output("cover-map-1", "figure"),
    Output("cover-lines-1", "figure"),
    Output("cover-lines-2", "figure"),
    Output("lc-location", "pathname"),
    Input("global-store-hash", "data"),
    Input("global-store-bbox-latlon", "data"),
    Input("global-store-fua-latlon", "data"),
)
def generate_plots(id_hash, bbox_latlon, fua_latlon):
    if id_hash is None:
        return [dash.no_update] * 3 + ["/"]

    path_cache = Path(f"./data/cache/{id_hash}")

    bbox_latlon = shape(bbox_latlon)
    fua_latlon = shape(fua_latlon)

    map1 = udw.plot_map_season(
        bbox_latlon, fua_latlon.centroid, season="Qall", year=2022
    )
    lines1 = udw.plot_lc_year(bbox_latlon, path_cache)
    lines2 = udw.plot_lc_time_series(bbox_latlon, path_cache)

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
