from dash import html, dcc
import dash_bootstrap_components as dbc

BLOCK_STYLE = {
    "backgroundColor": "white",
    "boxShadow": "rgba(0, 0, 0, 0.1) 0px 0px 5px 0px, rgba(0, 0, 0, 0.1) 0px 0px 1px 0px",
    "margin": "30px 30px",
}


def figureWithDescription(fig, text, title="Default title (change me)"):
    info_id = f"{title.lower().replace(' ', '-')}-info"

    tooltip = dbc.Tooltip(
        text,
        target=info_id,
        placement="top",
    )

    info_button = html.I(
        id=info_id,
        className="bi bi-info-circle text-info",
    )

    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col([info_button, tooltip], width=2),
                    dbc.Col(html.H4(title), width=10),
                ],
                className="p-2 d-flex justify-content-center align-items-center",
            ),
            html.Hr(className="mt-2 mb-2"),
            fig,
        ],
        style=BLOCK_STYLE,
    )

def figureWithDescription_translation(fig, text_id, title_id):
    info_id = f"{title_id}-info"
    tooltip = dbc.Tooltip(id=text_id, target=info_id, placement="top")
    info_button = html.I(id=info_id, className="bi bi-info-circle text-info")
    title_element = html.H4(id=title_id)

    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col([info_button, tooltip], width=2),
                    dbc.Col(title_element, width=10),
                ],
                className="p-2 d-flex justify-content-center align-items-center",
            ),
            html.Hr(className="mt-2 mb-2"),
            fig,
        ],
        style=BLOCK_STYLE,
    )

def figureWithDescription_translation2(fig, text_ids, title_id):
    info_id = f"{title_id}-info"
    
    text_elements = [html.Span(id=text_id) if text_id != "GHSL" else html.Acronym("GHSL", title="Global Human Settlement Layer") for text_id in text_ids]

    tooltip = dbc.Tooltip(text_elements, target=info_id, placement="top")
    
    info_button = html.I(id=info_id, className="bi bi-info-circle text-info")
    title_element = html.H4(id=title_id)

    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col([info_button, tooltip], width=2),
                    dbc.Col(title_element, width=10),
                ],
                className="p-2 d-flex justify-content-center align-items-center",
            ),
            html.Hr(className="mt-2 mb-2"),
            fig,
        ],
        style=BLOCK_STYLE,
    )


def mapComponent(title, id):
    return html.Div(
        [
            html.H4(title),
            dcc.Graph(style={"height": "85%"}, id=id),
        ],
        style={"height": "100%", "margin-bottom": "50px"},
    )
