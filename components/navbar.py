import dash
from dash import html, callback, Output, Input
import dash_bootstrap_components as dbc

from utils.image_utils import b64_image

LAND_COVER_ICON_PATH = "./assets/Icon_Cobertura.png"
HEAT_ISLANDS_ICON_PATH = "./assets/Icon_Islas.png"
HIST_GROWTH_ICON_PATH = "./assets/Icon_Crecimiento.png"
FUTURE_WORLD_ICON_PATH = "./assets/Icon_Escenarios.png"


def navIcon(icon_path):
    return html.Img(
        alt=icon_path,
        src=b64_image(icon_path),
        style={
            "height": "60px",
            "width": "auto",
        },
    )


NAV_LINK_STYLE = {
    "padding": "0",
}


navbar = dbc.Nav(
    [
        dbc.NavItem(
            [
                dbc.NavLink(
                    navIcon(HIST_GROWTH_ICON_PATH),
                    id="growth_link",
                    href="/hist-growth",
                    style=NAV_LINK_STYLE,
                ),
                dbc.Tooltip("Crecimiento histórico", target="growth_link"),
            ]
        ),
        dbc.NavItem(
            [
                dbc.NavLink(
                    navIcon(LAND_COVER_ICON_PATH),
                    id="lc_link",
                    href="/land-cover",
                    style=NAV_LINK_STYLE,
                ),
                dbc.Tooltip("Cobertura de suelo", target="lc_link"),
            ]
        ),
        dbc.NavItem(
            [
                dbc.NavLink(
                    navIcon(FUTURE_WORLD_ICON_PATH),
                    id="sleuth_link",
                    href="/sleuth",
                    style=NAV_LINK_STYLE,
                ),
                dbc.Tooltip("Escenarios de futuro", target="sleuth_link"),
            ]
        ),
        dbc.NavItem(
            [
                dbc.NavLink(
                    navIcon(HEAT_ISLANDS_ICON_PATH),
                    id="suhi_link",
                    href="/suhi",
                    style=NAV_LINK_STYLE,
                ),
                dbc.Tooltip("Islas de calor", target="suhi_link"),
            ]
        ),
    ],
    vertical=True,
    pills=True,
)

# Define the callback
@callback(
    Output("page-title", "children"),
    Output("page-title", "title"),
    Input("growth_link", "n_clicks"),
    Input("lc_link", "n_clicks"),
    Input("sleuth_link", "n_clicks"),
    Input("suhi_link", "n_clicks"),
)
def update_title(growth_clicks, lc_clicks, sleuth_clicks, suhi_clicks):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "growth_link":
        return "Crecimiento histórico", "Crecimiento histórico"
    elif triggered_id == "lc_link":
        return "Cobertura de suelo", "Cobertura de suelo"
    elif triggered_id == "sleuth_link":
        return "Escenarios de futuro", "Escenarios del futuro"
    elif triggered_id == "suhi_link":
        return "Islas de calor", "Islas de calor"
    else:
        return "Inicio", ""
