import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from urllib.parse import unquote
from pathlib import Path

from xarray.core.utils import K

from caching_utils import make_cache_dir
from dynamic_world import plot_map_season, plot_lc_year, plot_lc_time_series, download_map_season
from components.text import figureWithDescription
from components.page import newPageLayout

path_fua = Path('./data/output/cities/')

dash.register_page(
    __name__,
    title='URSA',
    path_template='land-cover/<country>/<city>'
)

ALERT_TEXT = html.Div(
    [
        (
            "En esta pestaña podrás explorar los tipos de cobertura de suelo "
            "presentes en el área alrededor de tu ciudad. "
            "Estos datos de cobertura de suelo provienen del proyecto "
        ),
        html.A(
            "Dynamic World",
            href="https://dynamicworld.app"
        ),
        (
            " de Google. "
            "En Dynamic World, las imágenes satelitales Sentinel son "
            "procesadas usando un red neuronal para clasificar cada "
            "pixel en una de las 9 posibles categorías de suelo. "
            "Dynamic World posee datos de cobertura de suelo desde el "
            "año 2016."
        ),
    ]
)

DRIVE_TEXT = html.Div(
        html.P([
            html.H4('Descarga de Datos'),
            html.H5('¿Cómo se realiza la descarga?'),
            "La información procesada en la sección Cobertura de Suelo se realiza principalmente mediante de Google Earth Engine. De esta manera, la descarga de los datos empleados, debido a su tamaño, es a través del Google Drive de la cuenta empleada en la autenticación de Google Earth Engine.",
            html.Br(),
            html.Br(),
            html.H5('¿Dónde se descarga el archivo?'),
            "La descarga del raster con nombre 'dynamic_world_raster.tif' se hará al directorio raíz del Google Drive de la cuenta empleada.",
            html.Br(),
            html.Br(),
            html.H5('¿Cuales son los estados de la descarga?'),
            "Los estados de la tarea de descarga son los siguientes:",
            html.Ul(
        [
            html.Li(
                "UNSUBMITTED, tarea pendiente en el cliente."
            ),
            html.Li(
                "READY, tarea en cola en el servidor."
            ),
            html.Li(
                "RUNNING, tarea en ejecución."
            ),
            html.Li(
                "COMPLETED, tarea completada exitosamente."
            ),
            html.Li(
                "FAILED, tarea completada con errores."
            ),
            html.Li(
                "CANCEL_REQUESTED, tarea ejecución pero se ha solicitado su cancelación."
            ),
            html.Li(
                "CANCELED, tarea cancelada."
            ),
        ]
            ),
            html.Br(),
            html.Br(),
            html.H5('¿Es posible hacer descargas simultáneas?'),
            "URSA únicamente permite la ejecución de una tarea de descarga a la vez. Espere a que se complete la tarea antes de crear una nueva. Esto puede tomar varios minutos."
        ]
        )
        )


globalCountry = ''
globalCity = ''
globalTask = None

def layout(country='', city=''):

    if not city or not country:
        return 'No city selected'

    global globalCountry
    global globalCity

    globalTask = None
    country = unquote(country)
    
    city = unquote(city)
    
    path_cache : Path = make_cache_dir(f'./data/cache/{country}-{city}')

    globalCountry = country
    globalCity = city

    # Load figures
    map1 = plot_map_season(country, city, path_fua,
                           season='Qall', year=2022)
    lines1 = plot_lc_year(country, city, path_fua, path_cache)
    lines2 = plot_lc_time_series(country, city, path_fua, path_cache)

    maps = html.Div([
        dcc.Graph(figure=map1, style={"height" : "100%"}),
    ], style={"height": "100%"})

    lines = html.Div([
        figureWithDescription(
            dcc.Graph(figure=lines1),
            html.P(
                "El gráfico de barras muestra las superficie en kilómetros "
                "cuadrados que le corresponde a cada clase de cobertura en "
                "el año 2022."
            ),
            'Superficie por Categoría de Uso de Suelo (Año 2022)'
        ),
        figureWithDescription(
            dcc.Graph(figure=lines2),
            html.P(
                "El gráfico de líneas muestra la evolución en el tiempo "
                "de la cantidad de superficie de cada clase de cobertura "
                "desde 2016 hasta el 2022. "
                "El gráfico es interactivo y se pueden seleccionar una "
                "o varias clases específicas para observar más claramente "
                "su comportamiento en el tiempo."
            ),
            'Cobertura de suelo'
        ),
    ], style={"overflow": "scroll", "height": "82vh"})

    map_info_alert = dbc.Alert([
        html.H4('Clasificación del Territorio por Categoría de Uso de Suelo (Año 2022)'),
        """El mapa muestra la categoría mas común observada en 2022
        para cada pixel de 10x10 metros.
                El relieve refleja la certeza del proceso de clasificación,
                una mayor altura refleja una mayor certidumbre de que el
                pixel pertnezca a la clase mostrada. "
                Notese que los bordes entre clases presentan mayor
                incertidumbre. """,
    ], color='secondary')
    
    alert = dbc.Alert(ALERT_TEXT, color='light')

    download_info = dbc.Alert(DRIVE_TEXT, color = 'secondary')

    download_button_rasters = html.Div([
            dbc.Button('Descarga a Google Drive',
                        id='btn-rasters',
                        color='light'),
            html.Span(id="btn-rasters-output", style={"verticalAlign": "middle"}),
            html.Span(
              "?",
              id="tooltip-target02",
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
                "Descarga los archivos Raster a Google Drive. En este caso la información es procesada en Google Earth Engine y la única opción de descarga es al directorio raíz de tu Google Drive.",
                target="tooltip-target02",
            )
    ])

    tabs = [
        dbc.Tab(
            lines,
            label="Gráficas",
            id="tab-plots",
            tab_id="tabPlots",
        ),
        dbc.Tab(
            html.Div([map_info_alert, alert]),
            label="Info",
            id="tab-info",
            tab_id="tabInfo",
        ),
        dbc.Tab(
            html.Div([download_info, download_button_rasters]),
            label="Descargables",
            id="tab-download",
            tab_id="tabDownload",
        )
    ]

    layout = newPageLayout(maps, tabs)

    return layout

@callback(
    Output('btn-rasters-output', 'children'),
    Input('btn-rasters', 'n_clicks'),
    prevent_initial_call=True
    )
def download_rasters(n_clicks):
    global globalTask

    if globalTask is None: 
        globalTask = download_map_season(globalCountry, globalCity, path_fua,'Qall', 2022)

    return "Status de la Descarga: {}".format(globalTask.status()["state"])
