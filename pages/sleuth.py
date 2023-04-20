import dash
from dash import html, dcc, callback, Input, Output, State
from urllib.parse import unquote
from pathlib import Path

from caching_utils import make_cache_dir
import sleuth_prep as prep

path_fua = Path('./data/output/cities/')

dash.register_page(
    __name__,
    title='URSA',
    path_template='sleuth/<country>/<city>'
)


def layout(country='', city=''):

    if not city or not country:
        return 'No city selected'

    country = unquote(country)
    city = unquote(city)
    path_cache : Path = make_cache_dir(f'./data/cache/{country}-{city}')

    fpath = prep.load_or_prep_rasters(country, city, path_fua, path_cache)
    scen_path = prep.create_scenario_file(
        path_cache,
        stop_year=2050,
        scenario='calibration')

    layout = html.Div(
        [
            html.P(
                'Esta pestaña continua en desarrollo.'
                'Para generar los datos necesarios para el simulador '
                'de expansión presiona el botón correspondiente.'
                'Al presionar el botón descargaras los datos '
                'para ejecutar el simulador de forma manual.'
            ),
            html.Div(id='fpath-div', style={'display': 'none'},
                     children=str(fpath)),
            html.Button("Descarga datos", id="btn-download-sleuth"),
            dcc.Download(id="download-sleuth"),

            html.Div(id='scen-path-div', style={'display': 'none'},
                     children=str(scen_path)),
            html.Button("Descarga archivo config", id="btn-download-config"),
            dcc.Download(id="download-config")

        ]
    )

    return layout


@callback(
    Output("download-sleuth", "data"),
    Input("btn-download-sleuth", "n_clicks"),
    State("fpath-div", 'children'),
    prevent_initial_call=True,
)
def get_data(n_clicks, fpath):
    return dcc.send_file(fpath)


@callback(
    Output("download-config", "data"),
    Input("btn-download-config", "n_clicks"),
    State("scen-path-div", 'children'),
    prevent_initial_call=True,
)
def get_scen(n_clicks, fpath):
    return dcc.send_file(fpath)
