import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from urllib.parse import unquote
from pathlib import Path

from ghsl import (
    plot_built_agg_img,
    plot_smod_clusters,
    plot_built_year_img,
    plot_pop_year_img,
    plot_growth
)
from caching_utils import make_cache_dir
from components.text import figureWithDescription
from components.page import pageContent

path_fua = Path('./data/output/cities/')

dash.register_page(
    __name__,
    title='URSA',
    path_template='hist-growth/<country>/<city>'
)

WELCOME_TEXT = [
    (
        "En esta pestaña encontrarás información acerca del crecimiento "
        "histórico de la ciudad. A partir de datos del proyecto "
    ),
    html.A(
        "Global Human Settlement Layer",
        href="https://ghsl.jrc.ec.europa.eu/"
    ),
    (
        " (GHSL) se muestra el cambio en el área urbanizada, la superficie "
        "construida y la población en la zona metropolitana de tu elección."
    ),
]

MAP_INTRO_TEXT = [
    (
        "Los cuatro mapas que se presentan a continuación contienen "
        "información agregada de las características urbanas de la región."
    ),
    html.Ul(
        [
            html.Li(
                "Los límites de la región de análisis se delinean con un "
                "contorno de color azul."
            ),
            html.Li(
                "La región delineada en un color marrón identifica el área "
                "urbana principal."
            ),
            html.Li(
                "El área urbana principal se define porque cada pixel "
                "(100x100 metros) posee una densidad de al menos 300 "
                "habitantes por kilómetro cuadrado al año 2020."
            ),
            html.Li(
                "Las regiones delineadas con un color amarillo corresponden "
                "a la urbanización periférica; se trata de zonas sin "
                "contigüidad al área urbana principal, pero que tienen "
                "una densidad de al menos 300 habitantes por kilómetro "
                "cuadrado al año 2020. "
                "Accede a más información acerca de cada mapa haciendo clic "
                "en el botón correspondiente en la interfaz de usuario."
            ),
        ]
    ),
]

MAP_HIST_BUILTUP_INTRO_TEXT = "Evolución temporal de la construcción. "

MAP_HIST_BUILTUP_EXPANDED_TEXT = html.Div(
    [
        (
            "Las celdas de la cartografía son de 100x100 metros. "
            "Una celda se considera como construida (built-up) cuando "
            "al menos el 20% de su superficie está cubierta por algún "
            "tipo de construcción. "
            "De acuerdo con la definición del "
        ),
        html.Acronym(
            "GHSL",
            title="Global Human Settlement Layer"
        ),
        (
            ", una construcción es cualquier tipo de estructura "
            "techada erigida sobre suelo para cualquier uso. "
            "Este mapa muestra el año en que cada celda se considera "
            "construida por primera vez en las imágenes de satélite."
        ),
    ]
)

MAP_HIST_URBAN_INTRO_TEXT = "Evolución temporal de la urbanización. "

MAP_HIST_URBAN_EXPANDED_TEXT = (
    "En contraste con el suelo construido, una celda de 1000x1000 metros se "
    "considera urbana cuando su densidad de población excede los 300 "
    "habitantes por kilómetro cuadrado. El segundo mapa "
    "representa el año en que cada celda se consideró como urbana por "
    "primera vez a partir del histórico de imágenes de satélite registradas."
)

MAP_BUILT_F_INTRO_TEXT = "Fracción de construcción. "

MAP_BUILT_F_EXPANDED_TEXT = (
    "La escala de colores de azul a amarillo del mapa "
    "representa la fracción de construcción de cada celda de 100x100 metros "
    "para el año 2020. Esta fracción es 0 para una celda sin construcción "
    "(en color azul) y 1 para una celda completamente cubierta por "
    "construcción (en color amarillo)."
)

MAP_POP_INTRO_TEXT = "Número de habitantes. "

MAP_POP_EXPANDED_TEXT = (
    "Este mapa muestra el número de habitantes en cada celda de 100x100 "
    "metros al año 2020."
)

LINE_GRAPH_TEXT_1 = (
    "Este primer gráfico de líneas muestra el cambio en la"
    "superficie urbanizada dentro de la zona de interés del año 1975 al 2020. "
    "El cambio se desglosa en dos categorías: "
    "la superficie urbana dentro del cluster urbano principal y "
    "la superficie urbana en la periferia (desconectada y sin contigüidad "
    "con la mancha urbana). "
    "El recuadro con un contorno azul en los mapas delimita la zona de "
    "análisis en la región metropolitana, a partir del cual se derivan "
    "ambas categorías de la urbanización. "
    "La línea en color marrón en el gráfico corresponde a la superficie "
    "urbana del centro urbano principal, "
    "misma que se identifica en los mapas como el recuadro con un contorno "
    "en color marrón. "
    "La línea amarilla del gráfico representa el cambio por año en la "
    "superficie urbana en la periferia de la ciudad, "
    "cuya representación en el mapa se puede identificar como un recuadro "
    "con un color amarillo."
)

LINE_GRAPH_TEXT_2 = html.Div(
    [
        "A partir de las imágenes de satélite y de la información del ",
        html.Acronym(
            "GHSL",
            title="Global Human Settlement Layer"
        ),
        (
            ", el gráfico de lineas muestra el cambio en la superficie "
            "del área construida dentro de la zona de interés del año "
            "1975 al 2020. "
            "El área en color marrón corresponde a los kilómetros cuadrados "
            "por año de la superficie urbanizada en el cluster urbano "
            "principal de la ciudad. "
            "El área en color amarillo corresponde a la superficie "
            "urbanizada de las zonas periférias sin contigüidad con la "
            "zona urbanizada central. "
            "El lector o lectora puede apreciar el crecimiento de la "
            "superficie urbanizada por año, distinguiendo en que medida "
            "se debe a crecimiento en la periferia versus en la zona central."
        ),
    ]
)

LINE_GRAPH_TEXT_3 = html.Div(
    [
        html.Acronym(
            "GHSL",
            title="Global Human Settlement Layer"
        ),
        """ calcula estimados de población para las zonas metropolitanas de
        todo el mundo. Estos estimados se reportan en una cuadrícula, en este
        caso de 100x100 metros. El gráfico de líneas muestra el cambio en
        número de población de acuerdo con estos estimados, solamente para
        las celdas clasificadas como urbanizadas. Los estimados de población
        fueron elaborados con datos del 2010, extrapolados el 2020. Estaremos
        actualizando la herramienta conforme GHS publica nuevos estimados de
        población basados en las proyecciones de los censos levantados en 2020.
        El lector o lectora puede apreciar el cambio poblacional por
        año y por tipo de urbanización: central o periférica.""",
    ]
)

LINE_GRAPH_TEXT_4 = """El proceso de urbanización y crecimiento urbano va
dejando huecos conforme la ciudad se expande territorialmente. Los mapas
presentados anteriormente mostraron la proporción de suelo construido en
cada celda e identificaban las celdas urbanizadas. Este gráfico de líneas
compara ambos elementos y su cambio en el tiempo. Las
fracciones se presentan para toda la zona metropolitana y también desglosadas
por tipo de urbanización, central y en la periferia."""

LINE_GRAPH_TEXT_5 = (
    "Finalmente, contando con las áreas de superficie construida y urbana "
    "y la población por año, es posible calcular la evolución de la "
    "densidad poblacional a través del tiempo. "
    "En este caso, se presenta la densidad de población, representada "
    "como número de personas por superficie urbanizada en kilométros "
    "cuadrados."
)

LINE_GRAPH_TEXT_6 = (
    "El gráfico de líneas muestra la densidad poblacional, "
    "pero en este caso calculada como el número de personas sobre "
    "la superficie construida en kilómetros cuadrados. "
    "Se puede apreciar la evolución y cambio en la densidad poblacional "
    "del año 1975 al 2020. "
    "La densidad por superficie construida –y no urbanizada- es un "
    "indicador útil para medir el aprovechamiento de la infrainstructura "
    "en la ciudad: a mayor densidad, hay un uso más intensivo de la "
    "misma infraestructura."
)


def layout(country='', city=''):

    if not city or not country:
        return 'No city selected'

    country = unquote(country)
    city = unquote(city)
    path_cache : Path = make_cache_dir(f'./data/cache/{country}-{city}')

    # Load figures
    map1 = plot_built_agg_img(country, city, path_fua, path_cache)
    map2 = plot_smod_clusters(country, city, path_fua, path_cache)
    map3 = plot_built_year_img(country, city, path_fua, path_cache)
    map4 = plot_pop_year_img(country, city, path_fua, path_cache)
    lines1 = plot_growth(
        country,
        city,
        path_fua,
        path_cache,
        y_cols=['urban_cluster_main', 'urban_cluster_other'],
        title="Área urbana",
        ylabel="Área (km²)",
        var_type='extensive'
    )
    lines2 = plot_growth(
        country,
        city,
        path_fua,
        path_cache,
        y_cols=['built_cluster_main', 'built_cluster_other'],
        title="Área construida",
        ylabel="Área (km²)",
        var_type='extensive'
    )
    lines3 = plot_growth(
        country,
        city,
        path_fua,
        path_cache,
        y_cols=['pop_cluster_main', 'pop_cluster_other'],
        title="Población",
        ylabel="Población",
        var_type='extensive'
    )
    lines4 = plot_growth(
        country,
        city,
        path_fua,
        path_cache,
        y_cols=[
            'built_density_cluster_main',
            'built_density_cluster_other',
            'built_density_cluster_all'
        ],
        title="Densidad de construcción",
        ylabel="Fracción de área construida",
        var_type='intensive'
    )
    lines5 = plot_growth(
        country,
        city,
        path_fua,
        path_cache,
        y_cols=[
            'pop_density_cluster_main',
            'pop_density_cluster_other',
            'pop_density_cluster_all'
        ],
        title="Densidad de población",
        ylabel="Personas por km²",
        var_type='intensive'
    )
    lines6 = plot_growth(
        country,
        city,
        path_fua,
        path_cache,
        y_cols=[
            'pop_b_density_cluster_main',
            'pop_b_density_cluster_other',
            'pop_b_density_cluster_all'
        ],
        title="Densidad de población (construcción)",
        ylabel="Personas por km² de construcción",
        var_type='intensive'
    )

    maps = html.Div([
        figureWithDescription(
            dcc.Graph(figure=map1),
            MAP_HIST_BUILTUP_EXPANDED_TEXT
        ),
        figureWithDescription(
            dcc.Graph(figure=map2),
            MAP_HIST_URBAN_EXPANDED_TEXT
        ),
        figureWithDescription(
            dcc.Graph(figure=map3),
            MAP_BUILT_F_EXPANDED_TEXT
        ),
        figureWithDescription(
            dcc.Graph(figure=map4),
            MAP_POP_EXPANDED_TEXT
        ),
    ])

    lines = html.Div([
        figureWithDescription(
            dcc.Graph(figure=lines1),
            LINE_GRAPH_TEXT_1
        ),
        figureWithDescription(
            dcc.Graph(figure=lines2),
            LINE_GRAPH_TEXT_2
        ),
        figureWithDescription(
            dcc.Graph(figure=lines3),
            LINE_GRAPH_TEXT_3
        ),
        figureWithDescription(
            dcc.Graph(figure=lines4),
            LINE_GRAPH_TEXT_4
        ),
        figureWithDescription(
            dcc.Graph(figure=lines5),
            LINE_GRAPH_TEXT_5
        ),
        figureWithDescription(
            dcc.Graph(figure=lines6),
            LINE_GRAPH_TEXT_6
        ),
        ])
    welcomeAlert = dbc.Alert(WELCOME_TEXT, color='secondary')
    mapIntroAlert = dbc.Alert(MAP_INTRO_TEXT, color='light')
    layout = pageContent(
        pageTitle='Crecimiento histórico',
        alerts=[
            welcomeAlert,
            mapIntroAlert
        ],
        content=[
            maps,
            html.Hr(),
            lines,
        ]
    )

    return layout
