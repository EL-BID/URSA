import dash

import dash_bootstrap_components as dbc
import ursa.ghsl as ghsl
import ursa.utils.geometry as ug

from components.text import figureWithDescription, figureWithDescription_translation, figureWithDescription_translation2
from components.text import mapComponent
from components.page import new_page_layout
from dash import html, dcc, callback, Input, Output
from pathlib import Path
from shapely.geometry import shape
from zipfile import ZipFile

import json

# Traducciones
with open('./data/translations/hist_grow/translations_hist.json', 'r', encoding='utf-8') as file:
    translations = json.load(file)
    
# Traducciones
with open('./data/translations/hist_grow/tab_translations_hist.json', 'r', encoding='utf-8') as file:
    tab_translations = json.load(file)

dash.register_page(__name__, title="URSA")

WELCOME_TEXT = [
    (
        html.Div(id='WELCOME_TEXT_PART1')
    ),
    html.A("Global Human Settlement Layer", href="https://ghsl.jrc.ec.europa.eu/"),
    (
        html.Div(id='WELCOME_TEXT_PART2')
    ),
]

MAP_INTRO_TEXT = [
    (
        html.Div(id='MAP_INTRO_TEXT_PART1')
    ),
    html.Ul(
        [
            html.Li(
                id='MAP_INTRO_TEXT_PART2'
            ),
            html.Li(
                id='MAP_INTRO_TEXT_PART3'
            ),
            html.Li(
                id='MAP_INTRO_TEXT_PART4'
            ),
            html.Li(
                id='MAP_INTRO_TEXT_PART5'
            ),
        ]
    ),
]

MAP_HIST_BUILTUP_INTRO_TEXT = "Evolución temporal de la construcción."

MAP_HIST_BUILTUP_EXPANDED_TEXT = html.Div(
    [
        html.Span(id="MAP_HIST_BUILTUP_EXPANDED_TEXT_PART1"),
        html.Acronym("GHSL", title="Global Human Settlement Layer"),
        html.Span(id="MAP_HIST_BUILTUP_EXPANDED_TEXT_PART2"),
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

LINE_GRAPH_TEXT_1 = """Este primer gráfico de líneas muestra el cambio en la
    superficie urbanizada dentro de la zona de interés del año 1975 al 2020.
    El cambio se desglosa en dos categorías:
    la superficie urbana dentro del cluster urbano principal y
    la superficie urbana en la periferia (desconectada y sin contigüidad
    con la mancha urbana).
    El recuadro con un contorno azul en los mapas delimita la zona de
    análisis en la región metropolitana, a partir del cual se derivan
    ambas categorías de la urbanización.
    La línea en color marrón en el gráfico corresponde a la superficie
    urbana del centro urbano principal,
    misma que se identifica en los mapas como el recuadro con un contorno
    en color marrón.
    La línea amarilla del gráfico representa el cambio por año en la
    superficie urbana en la periferia de la ciudad,
    cuya representación en el mapa se puede identificar como un recuadro
    con un color amarillo."""

LINE_GRAPH_TEXT_2 = html.Div(
    [
        html.Span(id="LINE_GRAPH_TEXT_2_PART1"),
        html.Acronym("GHSL", title="Global Human Settlement Layer"),
        html.Span(id="LINE_GRAPH_TEXT_2_PART2"),
    ],
)

LINE_GRAPH_TEXT_3 = html.Div(
    [
        html.Acronym("GHSL", title="Global Human Settlement Layer"),
        
        html.Span(id="LINE_GRAPH_TEXT_3"),
    ]
)

LINE_GRAPH_TEXT_4 = """El proceso de urbanización y crecimiento urbano va
dejando huecos conforme la ciudad se expande territorialmente. Los mapas
presentados anteriormente mostraron la proporción de suelo construido en
cada celda e identificaban las celdas urbanizadas. Este gráfico de líneas
compara ambos elementos y su cambio en el tiempo. Las fracciones se presentan para toda la zona metropolitana y también desglosadas por tipo de urbanización, central y en la periferia."""

LINE_GRAPH_TEXT_5 = """Finalmente, contando con las áreas de superficie construida y urbana y la población por año, es posible calcular la evolución de la densidad poblacional a través del tiempo. En este caso, se presenta la densidad de población, representada como número de personas por superficie urbanizada en kilométros cuadrados."""

LINE_GRAPH_TEXT_6 = """El gráfico de líneas muestra la densidad poblacional,
pero en este caso calculada como el número de personas sobre la superficie
construida en kilómetros cuadrados. Se puede apreciar la evolución y cambio
en la densidad poblacional del año 1975 al 2020. La densidad por superficie
construida—y no urbanizada—es un indicador útil para medir el aprovechamiento
de la infrainstructura en la ciudad: a mayor densidad, hay un uso más intensivo
de la misma infraestructura. """


maps = html.Div(
    [
        html.Div(
            [
                html.H4(id="map-title-1"),  
                mapComponent(title="", id="growth-map-1")  
            ],
            style={"margin-bottom": "20px"}  
        ),
        html.Div(
            [
                html.H4(id="map-title-2"),  
                mapComponent(title="", id="growth-map-2")  
            ],
            style={"margin-bottom": "20px"} 
        ),
        html.Div(
            [
                html.H4(id="map-title-3"),  
                mapComponent(title="", id="growth-map-3") 
            ],
            style={"margin-bottom": "20px"}  
        ),
        html.Div(
            [
                html.H4(id="map-title-4"),  
                mapComponent(title="", id="growth-map-4")  
            ],
            style={"margin-bottom": "20px"}  
        )

    ],
    style={"height": "90vh", "overflow": "scroll"},
)

lines = html.Div(
    [
        figureWithDescription_translation(
        dcc.Graph(id="growth-lines-1"),
        "LINE_GRAPH_TEXT_1",  # ID descripción
        "sub1"  # ID título
        ),
        
        figureWithDescription_translation2(
           dcc.Graph(id="growth-lines-2"), 
            ["LINE_GRAPH_TEXT_2_PART1", "GHSL", "LINE_GRAPH_TEXT_2_PART2"], 
            "sub2"  
        ),
        
        figureWithDescription_translation2(
            dcc.Graph(id="growth-lines-3"), 
            ["GHSL", "LINE_GRAPH_TEXT_3"], 
            "sub3"
        ),
        
        figureWithDescription_translation(
        dcc.Graph(id="growth-lines-4"),
        "LINE_GRAPH_TEXT_4",  # ID descripción
        "sub4"  # ID título
        ),
        
        figureWithDescription_translation(
        dcc.Graph(id="growth-lines-5"),
        "LINE_GRAPH_TEXT_5",  # ID descripción
        "sub5"  # ID título
        ),
        figureWithDescription_translation(
        dcc.Graph(id="growth-lines-6"),
        "LINE_GRAPH_TEXT_6",  # ID descripción
        "sub6"  # ID título
        ),
    ],
    style={"height": "82vh", "overflow": "scroll"},
)


welcomeAlert = dbc.Card(dbc.CardBody(WELCOME_TEXT), class_name="main-info")
mapIntroAlert = dbc.Card(dbc.CardBody(MAP_INTRO_TEXT), class_name="supp-info")
constructionYearMapInfoAlert = dbc.Card(
    dbc.CardBody(
        [
            html.H4(id="sub7"),
            MAP_HIST_BUILTUP_EXPANDED_TEXT,
        ]
    ),
    class_name="supp-info",
)
urbanCellYearMapInfoAlert = dbc.Card(
    dbc.CardBody(
        [
            html.H4(id="sub8"),
            html.Span(id = "MAP_HIST_URBAN_EXPANDED_TEXT"),
        ]
    ),
    class_name="supp-info",
)
contstructionFractionMapInfoAlert = dbc.Card(
    dbc.CardBody([html.H4(id="sub9"), 
                  
                  html.Span(id = "MAP_BUILT_F_EXPANDED_TEXT")]),
    class_name="supp-info",
)
inhabitantsFractionMapInfoAlert = dbc.Card(
    dbc.CardBody([html.H4(id = "sub10"), 
                  html.Span(id = "MAP_POP_EXPANDED_TEXT")]),
    class_name="supp-info",
)


download_button = html.Div(
    [
        dbc.Button(id="btn-download-rasters", color="light"),
        dcc.Download(id="download-rasters-zip"),
        html.Span(
            "?",
            id="tooltip-target01",
            style={
                "textAlign": "center",
                "color": "white",
                "height": 25,
                "width": 25,
                "background-color": "#bbb",
                "border-radius": "50%",
                "display": "inline-block",
            },
        ),
        dbc.Tooltip(
            html.Span(id = "download-raster-instructions"),
            target="tooltip-target01",
        ),
    ]
)


tabs = [
    dbc.Tab(
        lines,
        label = "Gráficas",
        id="tab-plots-hist",
        tab_id="tabPlots",
    ),
    dbc.Tab(
        html.Div(
            [
                welcomeAlert,
                mapIntroAlert,
                constructionYearMapInfoAlert,
                urbanCellYearMapInfoAlert,
                contstructionFractionMapInfoAlert,
                inhabitantsFractionMapInfoAlert,
            ]
        ),
        label= "Info",
        id="tab-info-hist",
        tab_id="tabInfo",
    ),
    dbc.Tab(
        html.Div([download_button]),

        label= "Descargables",
        id="tab-download-hist",
        tab_id="tabDownload",
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
    maps,
    tabs,
    stores=[dcc.Location(id="growth-location")],
    alerts=[
        dbc.Alert(
           html.Span(id="charts-generation-error"),
            id="growth-alert",
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

# --

@callback(
    [Output(key, 'label') for key in tab_translations.keys()], 
    [Input('btn-lang-es', 'n_clicks'),
     Input('btn-lang-en', 'n_clicks'),
     Input('btn-lang-pt', 'n_clicks')]
)
def update_tab_labels(btn_lang_es, btn_lang_en, btn_lang_pt):
    ctx = dash.callback_context

    if not ctx.triggered:
        language = 'es'  # Idioma predeterminado
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        language = 'es' if button_id == 'btn-lang-es' else 'en' if button_id == 'btn-lang-en' else 'pt'

    tab_labels = [tab_translations[key][language] for key in tab_translations.keys()]

    return tab_labels  

# ---


@callback(
    Output("download-rasters-zip", "data"),
    Input("btn-download-rasters", "n_clicks"),
    prevent_initial_call=True,
)
def download_file(n_clicks):
    rasters: list[str] = [
        "GHS_BUILT_S_100.tif",
        #'GHS_LAND_100.tif',
        "GHS_POP_100.tif",
        "GHS_SMOD_1000.tif",
        #'dou.tif',
        #'protected.tif',
        #'slope.tif'
    ]

    zip_file_name: str = f"hist-growth-rasters.zip"

    def write_archive(bytes_io):
        with ZipFile(bytes_io, mode="w") as zip_object:
            for raster_file_name in rasters:
                zip_object.write(raster_file_name, raster_file_name)

    return dcc.send_bytes(write_archive, zip_file_name)


@callback(
    Output("growth-lines-1", "figure"),
    Output("growth-lines-2", "figure"),
    Output("growth-lines-3", "figure"),
    Output("growth-lines-4", "figure"),
    Output("growth-lines-5", "figure"),
    Output("growth-lines-6", "figure"),
    Output("growth-map-1", "figure"),
    Output("growth-map-2", "figure"),
    Output("growth-map-3", "figure"),
    Output("growth-map-4", "figure"),
    Output("growth-alert", "is_open"),
    Output("growth-location", "pathname"),
    Input("global-store-hash", "data"),
    Input("global-store-bbox-latlon", "data"),
    [Input("global-store-uc-latlon", "data"),
    Input('btn-lang-es', 'n_clicks'),
    Input('btn-lang-en', 'n_clicks'),
    Input('btn-lang-pt', 'n_clicks')]
)
def generate_lines(id_hash, bbox_latlon, uc_latlon, btn_lang_es, btn_lang_en, btn_lang_pt):
    error_triggered = False

    if id_hash is None:
        return [dash.no_update] * 11 + ["/"]
    
    ctx = dash.callback_context
    if not ctx.triggered:
        language = 'es'  # Idioma predeterminado
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        language = 'es' if button_id == 'btn-lang-es' else 'en' if button_id == 'btn-lang-en' else 'pt'

    path_cache = Path(f"./data/cache/{str(id_hash)}")

    bbox_latlon = shape(bbox_latlon)
    bbox_mollweide = ug.reproject_geometry(bbox_latlon, "ESRI:54009").envelope

    uc_latlon = shape(uc_latlon)
    uc_mollweide = ug.reproject_geometry(uc_latlon, "ESRI:54009")

    centroid_mollweide = uc_mollweide.centroid

    smod, built, pop = ghsl.load_plot_datasets(bbox_mollweide, path_cache, clip=True)

    growth_df = ghsl.get_urb_growth_df(
        smod=smod,
        built=built,
        pop=pop,
        centroid_mollweide=centroid_mollweide,
        path_cache=path_cache,
    )

    translations = {
        "es": {
            "Urban Area": "Área urbana",
            "Built Area": "Área construida",
            "Population": "Población",
            "Construction Density": "Densidad de construcción",
            "Population Density": "Densidad de población",
            "Population Density (Construction)": "Densidad de población (construcción)",
            "Area (km²)": "Área (km²)",
            "People per km²": "Personas por km²",
            "People per km² of Construction": "Personas por km² de construcción",
            "Fraction of Built Area": "Fracción de área construida"
            
        },
        "en": {
            "Urban Area": "Urban Area",
            "Built Area": "Built Area",
            "Population": "Population",
            "Construction Density": "Construction Density",
            "Population Density": "Population Density",
            "Population Density (Construction)": "Population Density (Construction)",
            "Area (km²)": "Area (km²)",
            "People per km²": "People per km²",
            "People per km² of Construction": "People per km² of Construction",
            "Fraction of Built Area": "Fraction of Built Area"
            
        },
        "pt": {
            "Urban Area": "Área urbana",
            "Built Area": "Área construída",
            "Population": "População",
            "Construction Density": "Densidade de construção",
            "Population Density": "Densidade populacional",
            "Population Density (Construction)": "Densidade populacional (construção)",
            "Area (km²)": "Área (km²)",
            "People per km²": "Pessoas por km²",
            "People per km² of Construction": "Pessoas por km² de construção",
            "Fraction of Built Area": "Fração da Área Construída"
       
        }
    }


    
    line_plot_params = [
        dict(
            y_cols=["urban_cluster_main", "urban_cluster_other"],
            title=translations[language]["Urban Area"],
            ylabel=translations[language]["Urban Area"],
            var_type="extensive",
        ),
        dict(
            y_cols=["built_cluster_main", "built_cluster_other"],
            title=translations[language]["Built Area"],
            ylabel=translations[language]["Built Area"],
            var_type="extensive",
        ),
        # 
        
        dict(
        y_cols=["pop_cluster_main", "pop_cluster_other"],
        title=translations[language]["Population"],
        ylabel=translations[language]["Population"],
        var_type="extensive",
        ),
        dict(
            y_cols=[
                "built_density_cluster_main",
                "built_density_cluster_other",
                "built_density_cluster_all",
            ],
            title=translations[language]["Construction Density"],
            ylabel=translations[language]["Fraction of Built Area"],
            var_type="intensive",
        ),
        dict(
            y_cols=[
                "pop_density_cluster_main",
                "pop_density_cluster_other",
                "pop_density_cluster_all",
            ],
            title=translations[language]["Population Density"],
            ylabel=translations[language]["People per km²"],
            var_type="intensive",
        ),
        dict(
            y_cols=[
                "pop_b_density_cluster_main",
                "pop_b_density_cluster_other",
                "pop_b_density_cluster_all",
            ],
            title=translations[language]["Population Density (Construction)"],
            ylabel=translations[language]["People per km² of Construction"],
            var_type="intensive",
        ),
    ]

    plots = []
    for params in line_plot_params:
        try:
            lines = ghsl.plot_growth(growth_df, **params, language = language)
            plots.append(lines)
        except Exception:
            plots.append(dash.no_update)
            error_triggered = True

    map1 = ghsl.plot_built_agg_img(smod, built, bbox_mollweide, centroid_mollweide, language = language)
    map2 = ghsl.plot_smod_clusters(smod, bbox_latlon, language=language)
    map3 = ghsl.plot_built_year_img(
        smod, built, bbox_latlon, bbox_mollweide, centroid_mollweide, language = language
    )
    map4 = ghsl.plot_pop_year_img(smod, pop, bbox_mollweide, centroid_mollweide, language = language)

    plots.append(map1)
    plots.append(map2)
    plots.append(map3)
    plots.append(map4)

    return plots + [error_triggered, dash.no_update]