import dash_bootstrap_components as dbc

from dash import html


def generate_drive_text(how, where):
    return html.Div(
        [
            dbc.Card(
                dbc.CardBody(html.H4("Descarga de Datos")), class_name="main-info"
            ),
            dbc.Card(
                dbc.CardBody([html.H5("¿Cómo se realiza la descarga?"), html.P(how)]),
                class_name="supp-info",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("¿Dónde se descarga el archivo?"),
                        where,
                    ]
                ),
                class_name="supp-info",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("¿Cuales son los estados de la descarga?"),
                        "Los estados de la tarea de descarga son los siguientes:",
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.B("UNSUBMITTED"),
                                        " - Pendiente en el cliente.",
                                    ]
                                ),
                                html.Li(
                                    [html.B("READY"), " - En cola en el servidor."]
                                ),
                                html.Li([html.B("RUNNING"), " - En ejecución."]),
                                html.Li(
                                    [html.B("COMPLETED"), " - Completada exitosamente."]
                                ),
                                html.Li(
                                    [
                                        html.B("FAILED"),
                                        " - No completada debido a un error.",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.B("CANCEL_REQUESTED"),
                                        " - En ejecución pero se ha solicitado su cancelación.",
                                    ]
                                ),
                                html.Li([html.B("CANCELED"), " - Cancelada."]),
                            ]
                        ),
                    ]
                ),
                class_name="supp-info",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("¿Es posible hacer descargas simultáneas?"),
                        "URSA únicamente permite la ejecución de una tarea de descarga a la vez. Espere a que se complete la tarea antes de crear una nueva. Esto puede tomar varios minutos.",
                    ]
                ),
                class_name="supp-info",
            ),
        ]
    )

def generate_drive_text_translation(how, where):
    return html.Div(
        [
            dbc.Card(
                dbc.CardBody(html.H4(id="generate-drive-text1")), class_name="main-info"
            ),
            dbc.Card(
                dbc.CardBody([html.H5(id="generate-drive-text2"), html.P(id="HOW")]),
                class_name="supp-info",
            ),
            dbc.Card(
                dbc.CardBody(
                    [html.H5(id="generate-drive-text3"), html.P(id="WHERE")]
                ),
                class_name="supp-info",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5(id="generate-drive-text4"),
                        html.Span(id="generate-drive-text5"),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.B("UNSUBMITTED"),
                                        html.Span(" - Pendiente en el cliente.", id="generate-drive-text6"),
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.B("READY"),
                                        html.Span(" - En cola en el servidor.", id="generate-drive-text7"),
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.B("RUNNING"),
                                        html.Span(" - En ejecución.", id="generate-drive-text8"),
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.B("COMPLETED"),
                                        html.Span(" - Completada exitosamente.", id="generate-drive-text9"),
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.B("FAILED"),
                                        html.Span(" - No completada debido a un error.", id="generate-drive-text10"),
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.B("CANCEL_REQUESTED"),
                                        html.Span(" - En ejecución pero se ha solicitado su cancelación.", id="generate-drive-text11"),
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.B("CANCELED"),
                                        html.Span(" - Cancelada.", id="generate-drive-text12"),
                                    ]
                                ),
                            ]
                        ),  
                    ]
                ), 
                class_name="supp-info",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5(id="generate-drive-text13"),
                        html.Span(id="generate-drive-text14"),
                    ]
                ),
                class_name="supp-info",
            ),
        ]
    )
