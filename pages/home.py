import dash
from dash import html

dash.register_page(
    __name__,
    title='URSA',
    path='/'
)

layout = html.Div(
    children=[
        html.H1(children='Bienvenida'),
        html.Div(
            children=[
                html.P(
                    'Esta aplicación web le permitirá explorar el crecimiento '
                    'histórico y futuro de su ciudad.'
                ),
                html.P(
                    'Por favor seleccione una ciudad en el menú de la '
                    'izquierda y pulse el botón antes de continuar.'
                ),
                html.P(
                    'Una vez elegida la ciudad puede explorar las '
                    'visualizaciónes en la barrade navegación superior.'
                )
            ]
        ),
    ]
)
