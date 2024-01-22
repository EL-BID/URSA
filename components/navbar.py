import dash_bootstrap_components as dbc

from dash import html
from pathlib import Path
from ursa.utils.image import b64_image

HOME_ICON_PATH = "./assets/Icon_map.png"
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
                    navIcon(HOME_ICON_PATH),
                    id="home_link",
                    href="/",
                    style=NAV_LINK_STYLE,
                ),
                dbc.Tooltip("Inicio", target="home_link"),
            ]
        ),
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

def create_navbar(language):
    navbar_translations = {
        'Inicio': {
            'es': 'Inicio',
            'en': 'Home',
            'pt': 'Início'
        },
        'Crecimiento histórico': {
            'es': 'Crecimiento histórico',
            'en': 'Historical Growth',
            'pt': 'Crescimento Histórico'
        },
        'Cobertura de suelo': {
            'es': 'Cobertura de suelo',
            'en': 'Land Cover',
            'pt': 'Cobertura do Solo'
        },
        'Escenarios de futuro': {
            'es': 'Escenarios de futuro',
            'en': 'Future Scenarios',
            'pt': 'Cenários Futuros'
        },
        'Islas de calor': {
            'es': 'Islas de calor',
            'en': 'Heat Islands',
            'pt': 'Ilhas de Calor'
        }
    }

    navbar = dbc.Nav(
        [
            dbc.NavItem(
                [
                    dbc.NavLink(
                        navIcon(HOME_ICON_PATH),
                        id="home_link",
                        href="/",
                        style=NAV_LINK_STYLE,
                    ),
                    dbc.Tooltip(navbar_translations['Inicio'][language], target="home_link"),
                ]
            ),
            dbc.NavItem(
                [
                    dbc.NavLink(
                        navIcon(HIST_GROWTH_ICON_PATH),
                        id="growth_link",
                        href="/hist-growth",
                        style=NAV_LINK_STYLE,
                    ),
                    dbc.Tooltip(navbar_translations['Crecimiento histórico'][language], target="growth_link"),
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
                    dbc.Tooltip(navbar_translations['Cobertura de suelo'][language], target="lc_link"),
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
                    dbc.Tooltip(navbar_translations['Escenarios de futuro'][language], target="sleuth_link"),
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
                    dbc.Tooltip(navbar_translations['Islas de calor'][language], target="suhi_link"),
                ]
            ),
        ],
        vertical=True,
        pills=True,
    )

    return navbar
