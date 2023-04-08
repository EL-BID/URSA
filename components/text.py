from dash import html
import dash_bootstrap_components as dbc

FIG_STYLE = {
    'margin-bottom': '30px',
    'box-shadow': 'rgba(0, 0, 0, 0.1) 0px 0px 5px 0px, rgba(0, 0, 0, 0.1) 0px 0px 1px 0px'
}

BLOCK_STYLE = {
    'margin-bottom': '150px',
}


def figureWithDescription(fig, text):
    return html.Div(
        [
            html.Div(
                fig,
                style=FIG_STYLE
            ),
            html.Div(
                [
                    html.Hr(),
                    text,
                ],
                style={
                    'margin': '0 50px',
                }
            ),
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
