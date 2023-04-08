import base64
from dash import html
import dash_bootstrap_components as dbc

BID_LOGO_PATH = './assets/BID.png'


def b64_image(image_filename):
    # Funcion para leer imagenes
    with open(image_filename, 'rb') as f:
        image = f.read()
    return 'data:image/png;base64,' + base64.b64encode(image).decode('utf-8')


navbar = dbc.NavbarSimple(
    [
        dbc.NavItem(
            dbc.NavLink(
                'Crecimiento histórico',
                id='growth_link',
                href='/hist-growth',
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                'Cobertura de suelo',
                id='lc_link',
                href='/land-cover',
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                'Escenarios de futuro',
                id='sleuth_link',
                href='/sleuth',
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                'Islas de calor',
                id='suhi_link',
                href='/suhi',
            ),
        )
    ],
    brand=[
        html.Img(
            alt="Home",
            src=b64_image(BID_LOGO_PATH),
            style={
                'height': '60px',
                'width': 'auto',
            }
        ),
        html.P('Bahía Blanca, Argentina',
               id='city-info',
               style={
                   'margin-left': '20%',
                   'display': 'inline',
                   'font-weight': 'lighter'
               }
               )
    ],
    style={'height': '100px'},
    dark=True,
    color='primary'
)
