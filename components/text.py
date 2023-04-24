from dash import html
import dash_bootstrap_components as dbc

FIG_STYLE = {
    'margin-bottom': '30px',
    'box-shadow': 'rgba(0, 0, 0, 0.1) 0px 0px 5px 0px, rgba(0, 0, 0, 0.1) 0px 0px 1px 0px'
}

BLOCK_STYLE = {
    'margin-bottom': '150px',
}


def figureWithDescription(fig, text, title='Default title (change me)'):
    return html.Div(
        [
            html.H3(title, style={'margin-bottom': '15px'}),
            html.Div(
                fig,
                style=FIG_STYLE
            ),
            text,
            html.Hr(),
        ],
        style=BLOCK_STYLE
    )

def figureWithDescriptionOnTheSide(fig, text):
    return dbc.Row(
        [
            dbc.Col(
                fig,
                width=8,
                style=FIG_STYLE
            ),
            dbc.Col(text, width=4)
        ],
        style=BLOCK_STYLE
    )
