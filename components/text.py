from dash import html, dcc
import dash_bootstrap_components as dbc

FIG_STYLE = {
    'margin-bottom': '30px',
    'box-shadow': 'rgba(0, 0, 0, 0.1) 0px 0px 5px 0px, rgba(0, 0, 0, 0.1) 0px 0px 1px 0px'
}

BLOCK_STYLE = {
    'margin-bottom': '150px',
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
        className="bi bi-info-circle",
    )

    return html.Div(
        [
            html.H3(title, style={'margin': '50px 0'}),
            html.Div(
                [
                    html.Div([
                        fig,
                        html.Div(
                        [
                            info_button,
                            tooltip,
                        ],
                        className="position-absolute top-0 start-0",
                    )],
                    className="position-relative",
                    )
                ],
                style=FIG_STYLE,
            ),
            html.Hr(),
        ],
        style=BLOCK_STYLE,
    )


def mapComponent(title, mapFig):
    return html.Div([
        html.H4(title),
        dcc.Graph(figure=mapFig, style={"height": "85%"}),
    ], style={"height": "100%", "margin-bottom" : "50px"})
