import dash
import dateutil
import ee

import dash_bootstrap_components as dbc
import pandas as pd
import ursa.heat_islands as ht
import ursa.utils.geometry as ug

from components.text import figureWithDescription
from components.page import new_page_layout
from dash import html, dcc, callback, Input, Output, State
from datetime import datetime, timezone
from layouts.common import generate_drive_text
from pathlib import Path
from shapely.geometry import shape


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
            "Este apartado muestra un análisis sobre ",
            html.Strong("islas de calor"),
            " y el potencial impacto de estrategias de mitigación. La ",
            html.A("metodología", href="https://www.mdpi.com/2072-4292/11/1/48"),
            (
                " (Zhou et al., 2018) para identificar islas de calor "
                "consiste en contrastar la temperatura promedio anual de un "
                "píxel urbano (100x100 metros) contra la temperatura "
                "promedio anual de los píxeles rurales en la misma zona "
                "geográfica de la ciudad. "
                "Cada píxel de la zona de interés se clasifica en rural "
                "o urbano, utilizando el conjunto de datos WorldCover de "
                "la Agencia Espacial Europea (ESA)."
            ),
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
        (
            "Este diagrama de barras muestra la superficie en kilómetros "
            "cuadrados del suelo que forma parte del área de análisis "
            "para cada una de las 7 categorías de temperatura, "
            "para el suelo tanto rural como urbano. "
            "Las categorías de temperatura se particionan de la siguiente "
            "forma:"
        ),
        html.Ol(
            [
                html.Li("Muy frío: < -2.5σ"),
                html.Li("Frío: ≥ -2.5σ, < -1.5σ"),
                html.Li("Ligeramente frío: ≥ -1.5σ, < -0.5σ"),
                html.Li("Templado: ≥ -0.5σ, < 0.5σ"),
                html.Li("Ligeramente cálido: ≥ 0.5σ, < 1.5σ"),
                html.Li("Caliente: ≥ 1.5σ, < 2.5σ"),
                html.Li("Muy caliente: ≥ 2.5σ"),
            ]
        ),
        "σ: desviación estándar",
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
        html.H4("Impacto", className="text-primary"),
        html.Div("Nueva temperatura promedio", style=SUBTITLE_STYLE),
        html.Div("", id="impact-result-degrees", style=RESULT_STYLE),
        html.Div("Promedio mitigados", style=SUBTITLE_STYLE),
        html.Div(
            "",
            id="impact-mitigated-degrees",
            className="text-success",
            style=RESULT_STYLE,
        ),
        html.Div("Área urbana intervenida", style=SUBTITLE_STYLE),
        html.Div("", id="impact-result-square-kilometers", style=RESULT_STYLE),
        html.Div("Caminos intervenidos", style=SUBTITLE_STYLE),
        html.Div("", id="impact-result-kilometers", style=RESULT_STYLE),
    ]
)

strategyList = html.Div(
    [
        html.H4("Estrategias de mitigación", className="text-primary"),
        html.P(
            "Selecciona las estrategias a implementar. "
            "Puedes encontrar más infomración de cada estrategia o "
            "seleccionar múltiples."
        ),
        html.Div(
            dcc.Checklist(
                [
                    {
                        "label": html.Div(
                            [
                                html.P(
                                    strategy["title"],
                                    id=f"check-{strategyId}",
                                    style={"display": "inline"},
                                ),
                                dbc.Popover(
                                    dbc.PopoverBody(strategy["description"]),
                                    target=f"check-{strategyId}",
                                    trigger="hover",
                                ),
                            ],
                            style={"display": "inline"},
                        ),
                        "value": strategyId,
                    }
                    for strategyId, strategy in STRATEGIES.items()
                ],
                [],
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
                        "backgroundColor": f"{value}",
                        "margin-right": "5px",
                    },
                ),
                html.Div(
                    key,
                    className="font-weight-light text-white",
                    style={"font-size": "13px"},
                ),
            ],
            className="d-flex align-items-center m-1",
        )
        for key, value in legend_colors.items()
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
                figureWithDescription(
                    dcc.Graph(id="suhi-graph-areas"),
                    HISTOGRAMA_TEXT,
                    "Frecuencia de la superficie (Km²) de análisis por categoría de temperatura",
                ),
                figureWithDescription(
                    dcc.Graph(id="suhi-graph-temp-lc"),
                    BARS_TEXT,
                    "Fracción de uso de suelo por categoría de temperatura",
                ),
                figureWithDescription(
                    dcc.Graph(id="suhi-graph-radial-temp"),
                    "",
                    "Temperatura en función de la distancia al centro urbano",
                ),
                figureWithDescription(
                    dcc.Graph(id="suhi-graph-radial-lc"),
                    "",
                    "Fracción de uso de suelo en función de la distancia al centro urbano",
                ),
            ],
            style={"overflow": "scroll", "height": "82vh"},
        ),
    ],
    id="plots",
)

welcomeAlert = dbc.Alert(WELCOME_CONTENT, color="secondary")
mapIntroAlert = dbc.Alert(MAP_INTRO_TEXT, color="light")

tabs = [
    dbc.Tab(
        html.Div(
            [
                html.Div(
                    [
                        html.P("Temperatura promedio", style=SUBTITLE_STYLE),
                        html.P(
                            id="suhi-p-urban-temp",
                            style=MEAN_TEMPERATURE_STYLE,
                        ),
                        html.P(
                            [
                                (
                                    "* Datos obtenidos para el año 2022 a partir de "
                                    "la imagen satelital "
                                ),
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
        id="tab-controls",
        tab_id="tabControls",
    ),
    dbc.Tab(
        plots,
        label="Gráficas",
        id="tab-plots",
        tab_id="tabPlots",
    ),
    dbc.Tab(
        html.Div([welcomeAlert, mapIntroAlert]),
        label="Info",
        id="tab-info",
        tab_id="tabInfo",
    ),
    dbc.Tab(
        [
            generate_drive_text(
                how="La información procesada en la sección Islas de Calor se realiza incluyendo Google Earth Engine. De esta manera, la descarga de los datos empleados, debido a su tamaño, es a través del Google Drive de la cuenta empleada en la autenticación de Google Earth Engine en el caso del raster y al disco local en el caso de los datos tabulares para hacer la visualizaciones.",
                where="La descarga del raster con nombre 'suhi_raster.tif' se hará al directorio raíz del Google Drive de la cuenta empleada. Por otro lado, el archivo descargado a disco es 'city-country-suhi-data.csv', reemplazando 'city' por la ciudad y 'country' por el país analizado, respectivamente.",
            ),
            dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    "Descargar rasters",
                                    id="suhi-btn-download-rasters",
                                    color="light",
                                    title="Descarga los archivos Raster a Google Drive. En este caso la información es procesada en Google Earth Engine y la única opción de descarga es al directorio raíz de tu Google Drive.",
                                ),
                                width=4,
                            ),
                            dbc.Col(
                                dbc.Button(
                                    "Cancelar ejecución",
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
                                    "Descargar CSV",
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
    ),
]

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
        bbox_latlon = shape(bbox_latlon)
        task = ht.download_cat_suhi(bbox_latlon, path_cache, "Qall", 2022)
        status = task.status()
        return (False, status["name"], {"display": "block"}, "Iniciando descarga")
    else:
        return (dash.no_update, dash.no_update, dash.no_update, dash.no_update)


@callback(
    Output("suhi-span-rasters-output", "children", allow_duplicate=True),
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

    if state in ("UNSUBMITTED", "READY", "RUNNING", "CANCEL_REQUESTED"):
        return f"Status de la Descarga: {state}, Tiempo transcurrido: {int(time_elapsed)} segundos"
    elif state in ("COMPLETED", "FAILED", "CANCELLED"):
        return f"Status de la Descarga: {state}, Tiempo transcurrido: {int(time_elapsed)} segundos"


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
)
def generate_maps(id_hash, bbox_latlon, fua_latlon, uc_latlon):
    if id_hash is None:
        return [dash.no_update] * 5

    path_cache = Path(f"./data/cache/{id_hash}")

    bbox_latlon = shape(bbox_latlon)
    fua_latlon = shape(fua_latlon)
    uc_latlon = shape(uc_latlon)

    try:
        temp_map = ht.plot_cat_map(
            bbox_latlon, fua_latlon.centroid, path_cache, SEASON, YEAR
        )
    except Exception:
        temp_map = dash.no_update

    try:
        areas_plot = ht.plot_temp_areas(bbox_latlon, path_cache, SEASON, YEAR)
    except Exception:
        areas_plot = dash.no_update

    try:
        temps_by_lc_plot = ht.plot_temp_by_lc(bbox_latlon, path_cache, SEASON, YEAR)
    except Exception:
        temps_by_lc_plot = dash.no_update

    radial_temp_plot = ht.plot_radial_temperature(
        bbox_latlon, uc_latlon, path_cache, SEASON, YEAR
    )

    radial_lc_plot = ht.plot_radial_lc(bbox_latlon, uc_latlon, path_cache, SEASON, YEAR)

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
