from dash import Dash, html, Input, Output, State, callback, dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import dash
from components.sidebar import sidebar
from components.navbar import navbar
from pathlib import Path
import ee
import subprocess
import sys
# from ast import literal_eval
# import json
# mport base64

data_path = Path('./data')

CONTENT_STYLE = {
    "color": "gray",
    "width": '80%',
    "height": 'fit-content',
    "padding": "10px 10px",
    "margin": 'auto',
}

HEADER_STYLE = {
    'text-align': 'center',
    'margin': '50px'
}

app = Dash(
    __name__,
    use_pages=True,
)

content = dcc.Loading(
    children=[
        dbc.Row(
            [
                sidebar,
                dbc.Col(
                    [
                        dash.page_container
                    ], id="content",
                    width=9
                ),
            ],
            style=CONTENT_STYLE,
        )
    ],
    id="loading-spinner",
    className="loading-callback-spinner",
    type="circle",
)

app.layout = html.Div([
    navbar,
    content
], style={'backgroundColor': '#FBFBFB'})


@callback(
    Output('city-info', 'children'),
    Output('growth_link', 'href'),
    Output('lc_link', 'href'),
    Output('sleuth_link', 'href'),
    Output('suhi_link', 'href'),
    Input('submit-button', 'n_clicks'),
    State('cou-dro', 'value'),
    State('cit-dro', 'value'),
    prevent_initial_call=True
)
def set_city(n_clicks, country, city):
    '''Sets updates nav links and header.

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
    '''

    if n_clicks > 0:

        header_txt = '{0}, {1}'.format(city, country)

        g_link = f'/hist-growth/{country}/{city}'
        lc_link = f'/land-cover/{country}/{city}'
        sleuth_link = f'/sleuth/{country}/{city}'
        suhi_link = f'/suhi/{country}/{city}'

        return header_txt, g_link, lc_link, sleuth_link, suhi_link
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
