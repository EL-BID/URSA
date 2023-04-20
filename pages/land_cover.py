import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from urllib.parse import unquote
from pathlib import Path

from caching_utils import make_cache_dir
from dynamic_world import plot_map_season, plot_lc_year, plot_lc_time_series
from components.text import figureWithDescription
from components.page import pageContent

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


def layout(country='', city=''):

    if not city or not country:
        return 'No city selected'

    country = unquote(country)
    city = unquote(city)
    path_cache : Path = make_cache_dir(f'./data/cache/{country}-{city}')

    # Load figures
    map1 = plot_map_season(country, city, path_fua,
                           season='Qall', year=2022)
    lines1 = plot_lc_year(country, city, path_fua, path_cache)
    lines2 = plot_lc_time_series(country, city, path_fua, path_cache)

    maps = figureWithDescription(
            dcc.Graph(figure=map1),
            html.P(
                "El mapa muestra la categoría mas común observada en 2022 "
                "para cada pixel de 10x10 metros. "
                "El relieve refleja la certeza del proceso de clasificación, "
                "una mayor altura refleja una mayor certidumbre de que el "
                "pixel pertnezca a la clase mostrada. "
                "Notese que los bordes entre clases presentan mayor "
                "incertidumbre."
            )
    )

    lines = html.Div([
        figureWithDescription(
            dcc.Graph(figure=lines1),
            html.P(
                "El gráfico de barras muestra las superficie en kilómetros "
                "cuadrados que le corresponde a cada clase de cobertura en "
                "el año 2022."
            )
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
            )
        ),
    ])

    alert = dbc.Alert(ALERT_TEXT, color='light')
    layout = pageContent(
        pageTitle='Cobertura de suelo',
        alerts=[alert],
        content=[
            maps,
            lines
        ]
    )

    return layout
