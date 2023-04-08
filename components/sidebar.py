from dash import Output, Input, html, callback
import dash_bootstrap_components as dbc
from pathlib import Path
import geopandas as gpd

data_path = Path('./data')
cities_fua = gpd.read_file(data_path / 'output/cities/cities_fua.gpkg')
cities_uc = gpd.read_file(data_path / 'output/cities/cities_uc.gpkg')

DROPDOWN_STYLE = {
    'color': 'gray',
    'width': '67%',
    'margin': '10px auto',
    'font-size': '1.125rem',
}

BUTTON_STYLE = {
    'margin': '10px auto',
    'width': 'fit-content'
}

# Dropdown for city and country
country_dropdown = dbc.Select(
    options=[
        {
            'label': country,
            'value': country
        }
        for country in cities_fua.country.unique()
    ],
    value='Argentina',
    id='cou-dro',
    style=DROPDOWN_STYLE
)

city_dropdown = dbc.Select(
    options=[
        {
            'label': city,
            'value': city
        }
        for city in cities_fua[cities_fua.country == 'Argentina'].city.unique()
    ],
    value='Bahía Blanca',
    id='cit-dro',
    style=DROPDOWN_STYLE
)

sidebar = dbc.Col(
    [
        dbc.Row(
            [
                dbc.Label("Filtrar por país"),
                country_dropdown
            ]
        ),
        dbc.Row(
            [
                dbc.Label("Filtrar por ciudad"),
                city_dropdown
            ]
        ),
        html.Div(
            [
                dbc.Button(
                    'Consultar',
                    id='submit-button',
                    n_clicks=0,
                    color='primary',
                )
            ],
            style=BUTTON_STYLE
        ),
    ],
    width=2
)


@callback(
    Output('cit-dro', 'options'),
    Output('cit-dro', 'value'),
    Input('cou-dro', 'value'),
)
def filter_city(cou):
    '''Callback to display only the cities that belog to the country that
    was previously selected.

    Input:
      - cou: contry value.

    Output:
      - option (list): cities list.
      - value (string): a city to display in the box.
    '''
    if not cou:
        return [{'label': '--', 'value': ''}], ''

    df_cou = cities_fua[cities_fua.country == cou]
    df_cou = df_cou.city.unique()
    df_cou = list(df_cou)
    df_cou.sort()
    options = [{'label': city, 'value': city} for city in df_cou]

    return options, options[0]['value']
