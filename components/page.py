from dash import html, callback, Input, Output
import dash_bootstrap_components as dbc

def pageContentLayout(pageTitle, alerts, content):
    title = html.H2(
        pageTitle,
        style={'margin': '50px 0'}
    )
    ruler = html.Hr(style={'margin': '50px 0'})

    result = [title]
    result.extend(alerts)
    result.append(ruler)
    result.extend(content)

    return html.Div(result)

def newPageLayout(map, controls, plots, alerts, buttons):
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(map, id="map-col", style={"height": "88vh"}),
                    dbc.Col(
                        dbc.Button(
                            html.I(
                                className="bi bi-arrow-right-short", id="toggle-icon"
                            ),
                            id="toggle-button",
                            color="secondary",
                            className="d-flex align-items-center justify-content-center",
                            style={"width": "15px", "height": "500px"},
                        ),
                        className="col-auto d-flex align-items-center",
                    ),
                    dbc.Col(
                        [
                            dbc.Tabs(
                                [
                                    dbc.Tab(
                                        controls,
                                        label="Controles",
                                        id="tab-controls",
                                        tab_id="tabControls",
                                    ),
                                    dbc.Tab(
                                        plots,
                                        label="Gráficas",
                                        id="tab-plots",
                                        tab_id="tabPlots",
                                    ),
                                    dbc.Tab(
                                        html.Div(alerts),
                                        label="Info",
                                        id="tab-info",
                                        tab_id="tabInfo",
                                    ),
                                    dbc.Tab(
                                        html.Div(buttons),
                                        label="Descargables",
                                        id="tab-download",
                                        tab_id="tabDownload",
                                    ),
                                ],
                                id="tabs",
                                active_tab="tabControls",
                                className="mt-3",
                            ),
                            html.Div(id="tab-content"),
                        ],
                        id="plots-col",
                        width=6,
                    ),
                ],
            ),
        ],
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
