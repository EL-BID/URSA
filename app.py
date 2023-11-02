import dash
import ee
import subprocess
import sys

import dash_bootstrap_components as dbc

from components.navbar import navbar
from dash import Dash, html, dcc
from pathlib import Path
from ursa.utils.image import b64_image


BID_LOGO_PATH = "./assets/BID_blue.png"
PATH_FUA = Path("./data/output/cities/")

sys.path.append("./src")
sys.path.append("./utils")

data_path = Path("./data")

HEADER_STYLE = {"text-align": "center", "margin": "50px"}

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
)

content = dcc.Loading(
    children=[
        html.Div(
            [dash.page_container],
            id="content",
        ),
    ],
    id="loading-spinner",
    className="loading-callback-spinner",
    type="circle",
)

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.A(
                        html.Img(
                            alt="Home",
                            src=b64_image(BID_LOGO_PATH),
                            style={
                                "height": "30px",
                                "width": "auto",
                                "margin": "15px 0px",
                                "cursor": "pointer",
                            },
                        ),
                        href="/",
                    ),
                    width=2,
                ),
                dbc.Col(
                    id="page-title",
                    className="d-flex justify-content-center align-items-center",
                    style={"fontSize": "2rem"},
                ),
            ]
        ),
        dbc.Row(
            [dbc.Col(navbar, className="col-auto"), dbc.Col(content)],
        ),
        dcc.Store(id="global-store-bbox-latlon"),
        dcc.Store(id="global-store-bbox-latlon-orig"),
        dcc.Store(id="global-store-hash-orig"),
        dcc.Store(id="global-store-uc-latlon"),
        dcc.Store(id="global-store-fua-latlon"),
        dcc.Store(id="global-store-hash"),
    ],
    style={"backgroundColor": "#FBFBFB", "color": "gray"},
    fluid=True,
)


if __name__ == "__main__":
    try:
        ee.Initialize()
        print("¡La autenticación de Google Earth Engine ha sido exitosa!")
    except ee.EEException as e:
        print("Iniciando proceso de autenticación de Google Earth Engine ...")
        subprocess.run("earthengine authenticate --auth_mode=notebook", shell=True)
        ee.Initialize()
        print("¡La autenticación de Google Earth Engine ha sido exitosa!")
    except:
        print("Unexpected error:", sys.exc_info()[0])
        print("¡Error desconocido en la autenticación!")
        raise
    app.run_server(host="0.0.0.0", debug=False)
