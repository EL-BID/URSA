import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from urllib.parse import unquote
from pathlib import Path
import pandas as pd

from caching_utils import make_cache_dir
import heat_islands as ht
import raster_utils as ru
from components.text import figureWithDescription
from components.page import newPageLayout

path_fua = Path("./data/output/cities/")

dash.register_page(
    __name__,
    title='URSA',
    path_template='suhi/<country>/<city>'
)

WELCOME_CONTENT = [
    html.P(
        [
            "Este apartado muestra un análisis sobre ",
            html.Strong("islas de calor"),
            " y el potencial impacto de estrategias de mitigación. La ",
            html.A(
                "metodología",
                href="https://www.mdpi.com/2072-4292/11/1/48"
            ),
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

MEAN_TEMPERATURE_STYLE = {
    'font-weight': 'lighter',
    'font-size': '3rem'
}

SUBTITLE_STYLE = {
    'font-size': '100'
}

RESULT_STYLE = {
    'font-weight': 'lighter'
}

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

globalCountry = ""
globalCity = ""
globalPathCache = Path()
globalUrbanMeanTemp = None
globalTask = None


def format_temp(temp):
    return f"{round(temp, 2)} °C"


def meanTempView(urban_mean_temperature):
    title = html.P("Temperatura promedio", style=SUBTITLE_STYLE)

    paragraph1 = html.P(
        f"{format_temp(urban_mean_temperature)}",
        id="urban_mean_temperature",
        style=MEAN_TEMPERATURE_STYLE,
    )

    paragraph2 = html.P(
        [
            ("* Datos obtenidos para el año 2022 a partir de " "la imagen satelital "),
            html.A(
                "USGS Landsat 8 Level 2, Collection 2, Tier 1",
                href=(
                    "https://developers.google.com/earth-engine"
                    "/datasets/catalog/LANDSAT_LC08_C02_T1_L2"
                ),
            ),
        ],
        style={"fontSize": "0.8rem"},
    )

    return html.Div(
        [
            title,
            paragraph1,
            paragraph2,
        ],
        style={"margin-bottom": "15px"},
    )


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


def right_side(urban_mean_temperature):
    return html.Div(
        [meanTempView(urban_mean_temperature), strategyList, impactView],
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


def layout(country="", city=""):
    if not city or not country:
        return "No city selected"

    country = unquote(country)
    city = unquote(city)
    path_cache: Path = make_cache_dir(f"./data/cache/{country}-{city}")

    global globalCity
    global globalCountry
    global globalPathCache
    global globalUrbanMeanTemp

    globalCountry = country
    globalCity = city
    globalPathCache = path_cache
    globalUrbanMeanTemp = ht.get_urban_mean(
        globalCity, globalCountry, path_fua, "Qall", 2022, globalPathCache
    )

    season = "Qall"
    year = 2022

    temp_map = ht.plot_cat_map(country, city, path_fua, path_cache, season, year)

    areas_plot = ht.plot_temp_areas(country, city, path_fua, path_cache, season, year)
    temps_by_lc_plot = ht.plot_temp_by_lc(
        country, city, path_fua, path_cache, season, year
    )
    # radial_temp_plot = ht.plot_radial_temperature(
    # country, city, path_fua, path_cache,
    # season, year)
    # radial_lc_plot = ht.plot_radial_lc(
    # country, city, path_fua, path_cache,
    # season, year)

    globalUrbanMeanTemp = ht.get_urban_mean(
        globalCity, globalCountry, path_fua, "Qall", 2022, globalPathCache
    )

    # map_and_checks = html.Div(
    # [
    # figureWithDescription(
    # dbc.Row(
    # [
    # dbc.Col(
    # [
    # map_legend,
    # dcc.Graph(figure=temp_map, style={"height": "95%"}),
    # ],
    # width=8,
    # ),
    # # dbc.Col(
    # # right_side(globalUrbanMeanTemp),
    # # width=4,
    # # style={"padding": "15px"},
    # # ),
    # ]
    # ),
    # MAP_TEXT,
    # "Categoría de temperatura en islas de calor",
    # ), ]
    # )

    map = html.Div(
        [
            html.Div(map_legend, className="position-absolute fixed-bottom right-0"),
            dcc.Graph(figure=temp_map, style={"height": "100%"}),
        ],
        className="position-relative",
        style={"height": "100%"},
    )

    plots = html.Div(
        [
            dbc.Row(
                [
                    figureWithDescription(
                        dcc.Graph(figure=areas_plot),
                        HISTOGRAMA_TEXT,
                        "Frecuencia de la superficie (Km²) de análisis por categoría de temperatura",
                    ),
                    figureWithDescription(
                        dcc.Graph(figure=temps_by_lc_plot),
                        BARS_TEXT,
                        "Fracción de uso de suelo por categoría de temperatura",
                    ),
                ],
                style={"overflow": "scroll", "height": "82vh"},
            ),
            # dbc.Row(
            # [
            # figureWithDescription(
            # dcc.Graph(figure=radial_temp_plot),
            # LINE_TEXT,
            # 'Diferencia entre la temperatura urbana y la rural promedio por anillo concéntrico respecto al centro de la ciudad'
            # ),
            # figureWithDescription(
            # dcc.Graph(figure=radial_lc_plot),
            # AREA_TEXT,
            # 'Tipo de uso de suelo por anillo concéntrico respecto al centro de la ciudad'
            # )
            # ]
            # ),
        ],
        id="plots",
    )

    welcomeAlert = dbc.Alert(WELCOME_CONTENT, color="secondary")
    mapIntroAlert = dbc.Alert(MAP_INTRO_TEXT, color="light")

    download_button = html.Div([
            dbc.Button('Descargar a disco',
                        id='btn-csv',
                        color='light'),
            dcc.Download(id="download-dataframe-csv"),
            html.Span(
              "?",
              id="tooltip-target03",
              style={
                     "textAlign": "center", 
                     "color": "white",
                     "height": 25,
                     "width": 25,
                     "background-color": "#bbb",
                     "border-radius": "50%",
                     "display": "inline-block"

              }),
            dbc.Tooltip(
                "Descarga el archivo .csv, que alimenta las visualizaciones, localmente en tu carpeta de Descargas.",
                target="tooltip-target03",
            )
    ])

    download_button_rasters = html.Div([
            dbc.Button('Descarga a Google Drive',
                        id='btn-rasters-suhi',
                        color='light'),
            html.Span(id="btn-rasters-suhi-output", style={"verticalAlign": "middle"}),
            html.Span(
              "?",
              id="tooltip-target04",
              style={
                     "textAlign": "center", 
                     "color": "white",
                     "height": 25,
                     "width": 25,
                     "background-color": "#bbb",
                     "border-radius": "50%",
                     "display": "inline-block"

              }),
            dbc.Tooltip(
                "Descarga los archivos Raster a tu Google Drive, en este caso la información es procesada en GGE y la única opción de descarga es a esta carpeta en el directorio raíz.",
                target="tooltip-target04",
            )
    ])

    tabs = [
        dbc.Tab(
            [right_side(globalUrbanMeanTemp)],
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
            html.Div([download_button, download_button_rasters]),
            label="Descargables",
            id="tab-download",
            tab_id="tabDownload",
        )
    ]

    layout = newPageLayout(map, tabs)

    return layout


@callback(
    Output("impact-result-square-kilometers", "children"),
    Output("impact-result-kilometers", "children"),
    Output("impact-result-degrees", "children"),
    Output("impact-mitigated-degrees", "children"),
    Input("strategy-checklist", "value"),
)
def update_mitigation_kilometers(values):
    global globalUrbanMeanTemp

    if globalUrbanMeanTemp is None:
        globalUrbanMeanTemp = ht.get_urban_mean(
            globalCity, globalCountry, path_fua, "Qall", 2022, globalPathCache
        )

    df = ht.load_or_get_mit_areas_df(
        globalCity, globalCountry, path_fua, globalPathCache
    )
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
        else:
            pass

    mitigatedUrbanTemperature = globalUrbanMeanTemp - mitigatedDegrees

    return (
        f"{int(round(impactedSquareKm, 0))} Km²",
        f"{int(round(impactedKm, 0))} Km",
        format_temp(mitigatedUrbanTemperature),
        format_temp(mitigatedDegrees),
    )


@callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-csv", "n_clicks"),
    prevent_initial_call=True,
)
def download_file(n_clicks):
    csv_path = globalPathCache / "land_cover_by_temp.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        return dcc.send_data_frame(
            df.to_csv, f"{globalCity}_{globalCountry}-suhi-data.csv"
        )


@callback(
    Output("btn-rasters-suhi-output", "children"),
    Input("btn-rasters-suhi", "n_clicks"),
    prevent_initial_call=True,
)
def download_rasters(n_clicks):
    global globalTask

    if globalTask is None:
        globalTask = ht.download_cat_suhi(
            globalCountry, globalCity, path_fua, globalPathCache, "Qall", 2022
        )

    return "Status de la Descarga: {}".format(globalTask.status()["state"])
