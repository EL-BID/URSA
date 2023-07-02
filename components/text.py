from dash import html, dcc
import dash_bootstrap_components as dbc

FIG_STYLE = {
    'margin-bottom': '30px',
    'box-shadow': 'rgba(0, 0, 0, 0.1) 0px 0px 5px 0px, rgba(0, 0, 0, 0.1) 0px 0px 1px 0px',
    'margin-top': '25px',
}

BLOCK_STYLE = {
    'height': '100%',
}


def figureWithDescription(fig, text, title='Default title (change me)'):
    info_id = f"{title.lower().replace(' ', '-')}-info"

    tooltip = dbc.Tooltip(
        text,
        target=info_id,
        placement="top",
    )

    info_button = html.I(
        id=info_id,
        className="bi bi-info-circle d-inline",
    )

    return html.Div(
        [
            html.Div(
                [
                    html.Div(html.H4(title), className="d-inline p-0 m-0", style={"font-size": "1.2rem"}),
                    " ",
                    info_button,
                    tooltip,
                    html.Hr(),
                    fig,

                ], style=FIG_STYLE)
        ],
        style=BLOCK_STYLE,
    )


def mapComponent(title, mapFig):
    return html.Div([
        html.H4(title),
        dcc.Graph(figure=mapFig, style={"height": "85%"}),
    ], style={"height": "100%", "margin-bottom" : "50px"})
