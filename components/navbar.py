import base64
from dash import html
import dash_bootstrap_components as dbc

BID_LOGO_PATH = './assets/BID.png'

LAND_COVER_ICON_PATH = './assets/Icon_Cobertura.png'
HEAT_ISLANDS_ICON_PATH = './assets/Icon_Islas.png'
HIST_GROWTH_ICON_PATH = './assets/Icon_Crecimiento.png'
FUTURE_WORLD_ICON_PATH = './assets/Icon_Escenarios.png'

def b64_image(image_filename):
    # Function to read images
    with open(image_filename, 'rb') as f:
        image = f.read()
    return 'data:image/png;base64,' + base64.b64encode(image).decode('utf-8')

def navIcon(icon_path):
    return html.Img(
            alt=icon_path,
            src=b64_image(icon_path),
            style={
                'height': '60px',
                'width': 'auto',
            }
        )

navbar = dbc.Nav(
    [
        dbc.NavItem(
            dbc.NavLink(
                navIcon(HIST_GROWTH_ICON_PATH),
                id='growth_link',
                href='/hist-growth',
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                navIcon(LAND_COVER_ICON_PATH),
                id='lc_link',
                href='/land-cover',
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                navIcon(FUTURE_WORLD_ICON_PATH),
                id='sleuth_link',
                href='/sleuth',
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                navIcon(HEAT_ISLANDS_ICON_PATH),
                id='suhi_link',
                href='/suhi',
            ),
        )
    ],
    vertical=True,  # Set vertical attribute to True
    pills=True,  # Optionally use pills style
)

navbar_with_logo = dbc.Container(
    [
        html.Img(
            alt="Home",
            src=b64_image(BID_LOGO_PATH),
            style={
                'height': '60px',
                'width': 'auto',
                'margin-bottom': '20px',  # Add some bottom margin for spacing
            }
        ),
        html.P('Bahía Blanca, Argentina',
               id='city-info',
               style={
                   'font-weight': 'lighter'
               }
               )
    ],
    className="mt-4",  # Optionally add some top margin for spacing
)

# vertical_navbar = dbc.Container(
    # [
        # dbc.Row(
            # [
                # # dbc.Col(navbar_with_logo, width=2),  # Adjust the width as needed
                # # dbc.Col(navbar, width=10),  # Adjust the width as needed
                # navbar
            # ],
            # className="mt-4",
        # )
    # ]
# )

# Rest of your code...
