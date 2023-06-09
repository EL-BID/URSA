from dash import Dash, html, Input, Output, State, callback, dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import dash
from components.country_selector import country_selector
from components.navbar import navbar
from pathlib import Path
import ee
import subprocess
import sys

sys.path.append("./src")
sys.path.append("./utils")

data_path = Path("./data")

CONTENT_STYLE = {
    "color": "gray",
}

HEADER_STYLE = {"text-align": "center", "margin": "50px"}

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP]
)

content = dcc.Loading(
    children=[
        html.Div(
            [dash.page_container],
            id="content",
            style=CONTENT_STYLE,
        ),
    ],
    id="loading-spinner",
    className="loading-callback-spinner",
    type="circle",
)

app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col(country_selector, width={"size":5, "offset":1})),
        dbc.Row(
            [dbc.Col(navbar, className="col-auto"), dbc.Col(content)],
        ),
    ],
    style={"backgroundColor": "#FBFBFB"},
    fluid=True,
)


@callback(
    Output("growth_link", "href"),
    Output("lc_link", "href"),
    Output("sleuth_link", "href"),
    Output("suhi_link", "href"),
    Input("submit-button", "n_clicks"),
    State("cou-dro", "value"),
    State("cit-dro", "value"),
    prevent_initial_call=True,
)
def set_city(n_clicks, country, city):
    """Sets updates nav links and header.

    State:
    (A state would save the colected data but it won't trigger anything)
        - value (cou-dro): contry value.
        - value (cit-dro): city value.

    Input:
        - n_clicks: a click triggers the callback.

    Output:
        - children (header): a list containing the city and country in html
          format.
        - g_link: Link for historic growth page.
        - lc_link: Link for land cover.
        - sleuth_link: Link for slueth page.
    """

    if n_clicks > 0:
        g_link = f"/hist-growth/{country}/{city}"
        lc_link = f"/land-cover/{country}/{city}"
        sleuth_link = f"/sleuth/{country}/{city}"
        suhi_link = f"/suhi/{country}/{city}"
        return g_link, lc_link, sleuth_link, suhi_link

    else:
        return PreventUpdate


if __name__ == "__main__":
    try:
        ee.Initialize()
        print("¡La autenticación de Google Earth Engine ha sido exitosa!")
    except ee.EEException as e:
        print('Iniciando proceso de autenticación de Google Earth Engine ...')
        subprocess.run(
            "earthengine authenticate --auth_mode=notebook", shell=True)
        ee.Initialize()
        print("¡La autenticación de Google Earth Engine ha sido exitosa!")
    except:
        print("Unexpected error:", sys.exc_info()[0])
        print("¡Error desconocido en la autenticación!")
        raise
    app.run_server(host='0.0.0.0', debug=False)
