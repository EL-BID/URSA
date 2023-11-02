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
