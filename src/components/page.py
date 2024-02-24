from dash import html, callback, Input, Output
import dash_bootstrap_components as dbc


def pageContentLayout(pageTitle, alerts, content):
    title = html.H2(pageTitle, style={"margin": "50px 0"})
    ruler = html.Hr(style={"margin": "50px 0"})

    result = [title]
    result.extend(alerts)
    result.append(ruler)
    result.extend(content)

    return html.Div(result)


def new_page_layout(maps, tabs, stores=None, alerts=None):
    if stores is None:
        stores = []

    if alerts is None:
        alerts = []

    return dbc.Container(
        alerts
        + [
            dbc.Row(
                [
                    dbc.Col(maps, id="map-col", style={"height": "88vh"}),
                    dbc.Col(
                        dbc.Button(
                            html.I(
                                className="bi bi-arrow-right-short",
                                id="toggle-icon",
                            ),
                            id="toggle-button",
                            color="secondary",
                            outline=True,
                            className="d-flex align-items-center justify-content-center btn-sm",
                            style={
                                "height": "35%",
                                "width": "10px",
                                "border-bottom-right-radius": "0px",
                                "border-top-right-radius": "0px",
                            },
                        ),
                        className="col-auto d-flex align-items-center m-0 p-0 border-end border-secondary",
                    ),
                    dbc.Col(
                        [
                            dbc.Tabs(
                                tabs,
                                id="tabs",
                                active_tab=tabs[0].tab_id,
                            ),
                            html.Div(id="tab-content"),
                        ],
                        id="plots-col",
                    ),
                ],
            ),
        ]
        + stores,
        className="p-0 m-0",
        fluid=True,
    )


@callback(
    Output("plots-col", "style"),
    Output("toggle-icon", "className"),
    Output("map-col", "width"),
    Output("plots-col", "width"),
    Input("toggle-button", "n_clicks"),
)
def toggle_plots(n_clicks):
    if n_clicks and n_clicks % 2 != 0:
        return {"display": "none"}, "bi bi-arrow-left-short", 11, 0
    return {"display": "block"}, "bi bi-arrow-right-short", 6, 5
