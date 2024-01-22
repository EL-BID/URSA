import dash
import json

import dash_bootstrap_components as dbc
import dash_leaflet as dl
import geopandas as gpd
import ursa.utils.raster as ru

from dash import callback, html, Input, Output, State
from pathlib import Path
from shapely.geometry import shape
from ursa.utils.geometry import geometry_to_json, hash_geometry


dash.register_page(__name__, path="/")

PATH_FUA = Path("./data/output/cities/")

cities_fua = gpd.read_file("./data/output/cities/cities_fua.gpkg")
cities_uc = gpd.read_file("./data/output/cities/cities_uc.gpkg")

with open("./data/output/cities/cities_by_country.json", "r", encoding="utf8") as f:
    cities_by_country = json.load(f)

# Traducciones
with open('./data/translations/home/translations_home.json', 'r', encoding='utf-8') as file:
    translations = json.load(file)
    
DROPDOWN_STYLE = {
    "color": "gray",
    "width": "67%",
    "margin": "10px auto",
    "font-size": "1.125rem",
}

BUTTON_STYLE = {"margin": "10px auto", "width": "fit-content"}


country_dropdown = dbc.Select(
    options=[
        {"label": country, "value": country} for country in cities_fua.country.unique()
    ],
    value="Argentina",
    id="dropdown-country",
    style=DROPDOWN_STYLE,
    persistence=True,
    persistence_type="session",
)

city_dropdown = dbc.Select(
    id="dropdown-city",
    style=DROPDOWN_STYLE,
    persistence=True,
    persistence_type="session",
)

# Translation

language_buttons = dbc.ButtonGroup(
    [
        dbc.Button("Español", id="btn-lang-es", n_clicks=0),
        dbc.Button("English", id="btn-lang-en", n_clicks=0),
        dbc.Button("Portuguese", id="btn-lang-pt", n_clicks=0),
    ],
    style={"position": "absolute", "top": "10px", "right": "10px", "z-index": "1"},
)

layout = html.Div(
    [
        dbc.Alert(
            id="global-custom-region-alert",
            is_open=False,
            color="danger",
            dismissable=True,
        ),
        #language_buttons,
        html.H1(id="text1"),
        html.Div(
            [
                html.P(
                    id="text2"
                ),
                html.P(id="text3"),
                html.P(
                    id="text4"
                ),
            ]
        ),
        html.Div(
            [
                dbc.Container(
                    [
                        dbc.Row(
                            [
                                dbc.Col(country_dropdown, width=4),
                                dbc.Col(city_dropdown, width=4),
                            ],
                            justify="center",
                        ),
                        dbc.Row(
                            dbc.Col(
                                dbc.Button(id="btn-country-select"),
                                class_name="text-center",
                            )
                        ),
                    ]
                ),
                dbc.Container(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dl.Map(
                                        [
                                            dl.TileLayer(),
                                            dl.FeatureGroup(
                                                children=dl.EditControl(
                                                    id="global-edit-control",
                                                    position="topright",
                                                    draw=dict(
                                                        circle=False,
                                                        line=False,
                                                        polyline=False,
                                                        rectangle=True,
                                                        polygon=False,
                                                        marker=False,
                                                        circlemarker=False,
                                                    ),
                                                    edit=dict(remove=True),
                                                ),
                                                id="global-feature-group",
                                            ),
                                            dl.Rectangle(
                                                bounds=[[0, 0], [1, 0]],
                                                id="global-polygon",
                                            ),
                                        ],
                                        style={"height": "70vh"},
                                        center=[-5, -80],
                                        zoom=4,
                                        id="global-map",
                                        className="my-2",
                                    ),
                                    width=10,
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            dbc.Card(
                                                dbc.CardBody(
                                                    html.P(
                                                            id="text5",
                                                        style={"text-align": "start"},
                                                    )
                                                ),
                                                class_name="supp-info",
                                            ),
                                            dbc.Card(
                                                dbc.CardBody(
                                                    html.P(
                                                            id="text6",
                                                        style={"text-align": "start"},
                                                    )
                                                ),
                                                class_name="supp-info",
                                            ),
                                            dbc.Button(
                                                id="global-btn-apply-region"
                                            ),
                                        ],
                                        style={"text-align": "center"},
                                    ),
                                    width=2,
                                ),
                            ],
                            justify="center",
                        ),
                    ]
                ),
            ]
        ),
    ]
)

@callback(
    [Output(key, 'children') for key in translations.keys()],
    [Input('current-language-store', 'data')]
)
def update_translated_content(language_data):
    language = language_data['language'] if language_data else 'es'
    updated_content = [translations[key][language] for key in translations.keys()]
    return updated_content

@callback(
    Output("dropdown-city", "options"),
    Output("dropdown-city", "value"),
    Input("dropdown-country", "value"),
)
def filter_city(country):
    """Callback to display only the cities that belong to the country that
    was previously selected.

    Input:
      - cou: contry value.

    Output:
      - option (list): cities list.
      - value (string): a city to display in the box.
    """

    options = [{"label": city, "value": city} for city in cities_by_country[country]]
    return options, options[0]["value"]


@callback(
    Output("global-store-bbox-latlon", "data", allow_duplicate=True),
    Output("global-store-bbox-latlon-orig", "data"),
    Output("global-store-uc-latlon", "data"),
    Output("global-store-fua-latlon", "data"),
    Output("global-store-hash", "data", allow_duplicate=True),
    Output("global-map", "viewport"),
    Output("global-polygon", "bounds"),
    Input("btn-country-select", "n_clicks"),
    State("dropdown-country", "value"),
    State("dropdown-city", "value"),
    prevent_initial_call=True,
)
def set_city(n_clicks, country, city):
    """Sets updates nav links and header.

    State:
    (A state would save the colected data but it won't trigger anything)
        - value (dropdown-country): contry value.
        - value (dropdown-city): city value.

    Input:
        - n_clicks: a click triggers the callback.

    Output:
        - children (header): a list containing the city and country in html
          format.
        - g_link: Link for historic growth page.
        - lc_link: Link for land cover.
        - sleuth_link: Link for slueth page.
    """

    if n_clicks is None or n_clicks == 0:
        return (dash.no_update,) * 7

    bbox_latlon, uc_latlon, fua_latlon = ru.get_bboxes(city, country, PATH_FUA)

    bbox_latlon_json = geometry_to_json(bbox_latlon)
    uc_latlon_json = geometry_to_json(uc_latlon)
    fua_latlon_json = geometry_to_json(fua_latlon)

    id_hash = hash_geometry(bbox_latlon_json)

    path_cache = Path(f"./data/cache/{str(id_hash)}")
    path_cache.mkdir(exist_ok=True, parents=True)

    centroid = bbox_latlon.centroid

    coords = bbox_latlon.exterior.coords
    bounds = [coords[0], coords[2]]
    bounds = [[y, x] for x, y in bounds]

    return (
        bbox_latlon_json,
        bbox_latlon_json,
        uc_latlon_json,
        fua_latlon_json,
        id_hash,
        dict(center=[centroid.y, centroid.x], transition="flyTo", zoom=9),
        bounds,
    )


@callback(
    Output("global-store-bbox-latlon", "data"),
    Output("global-store-hash", "data"),
    Output("global-custom-region-alert", "children"),
    Output("global-custom-region-alert", "is_open"),
    Output("global-custom-region-alert", "color"),
    Input("global-btn-apply-region", "n_clicks"),
    State("global-edit-control", "geojson"),
    State("global-store-bbox-latlon-orig", "data"),
    prevent_initial_call=True,
)
def set_custom_bbox(n_clicks, geojson, bbox_orig):
    if n_clicks is None or n_clicks == 0:
        return [dash.no_update] * 5

    features = geojson["features"]
    if len(features) == 0:
        id_hash = hash_geometry(bbox_orig)
        path_cache = Path(f"./data/cache/{str(id_hash)}")
        path_cache.mkdir(exist_ok=True, parents=True)
        return (
            bbox_orig,
            id_hash,
            "No se proveyó ninguna región personalizada. Se utilizará la original.",
            True,
            "warning",
        )

    bbox_json = features[0]["geometry"]
    bbox = shape(bbox_json)
    bbox_orig = shape(bbox_orig)

    if not bbox_orig.contains(bbox):
        return (
            dash.no_update,
            dash.no_update,
            "La región personalizada provista no está contenida en la original.",
            True,
            "danger",
        )

    id_hash = hash_geometry(bbox_json)
    path_cache = Path(f"./data/cache/{str(id_hash)}")
    path_cache.mkdir(exist_ok=True, parents=True)

    if len(features) == 1:
        return bbox_json, id_hash, dash.no_update, dash.no_update, dash.no_update
    else:
        return (
            bbox_json,
            id_hash,
            "Más de una región personalizada provista. Se tomará una al azar.",
            True,
            "warning",
        )