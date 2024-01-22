import base64
import dash
import json
import os
import pprint
import tempfile

import dash_bootstrap_components as dbc
import layouts.sleuth as sl
import numpy as np
import pandas as pd
import plotly.express as px
import rasterio as rio
import rasterio.warp as warp
import sleuth_sklearn.utils as utils
import ursa.sleuth_prep as sp
import ursa.utils.geometry as ug
import xarray as xr

from dash import html, dcc, callback, Input, Output, State
from io import BytesIO
from pathlib import Path
from rasterio import MemoryFile
from rasterio.crs import CRS
from rasterio.enums import Resampling
from shapely.geometry import shape
from sleuth_sklearn.estimator import SLEUTH

# Traducciones
with open('./data/translations/sleuth/translations_sleuth.json', 'r', encoding='utf-8') as file:
    translations = json.load(file)
    
with open('./data/translations/sleuth/translations2_sleuth.json', 'r', encoding='utf-8') as file:
    translations2 = json.load(file)
    
with open('./data/translations/sleuth/tab_translations_sleuth.json', 'r', encoding='utf-8') as file:
    tab_translations = json.load(file)
    
RASTER_FIELDS = ["slope", "roads", "excluded", "urban"]
RASTER_FIELD_MAP = {
    "slope": "Pendiente",
    "roads": "Caminos",
    "excluded": "Exclusión",
    "urban": "Urbano",
}

PATH_CACHE = Path("./data/cache")

dash.register_page(
    __name__,
    title="SLEUTH",
)

# ==================== Pestaña rasters ====================#

tab_slope = dbc.Tab(
    [
        dbc.Card(
            dbc.CardBody(
                dbc.Container(
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Graph(
                                    id={"type": "graph-raster", "field": "slope"},
                                    responsive=True,
                                    style={"height": "60vh"},
                                ),
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.Button(
                                                html.Span(id="rasters-text1-slope"),
                                                id={"type": "btn-download-orig-raster", "field": "slope"},
                                                className="text-center",
                                            ),
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.Button(
                                                html.Span(id="rasters-text2-slope"),
                                                id={"type": "btn-download-raster", "field": "slope"},
                                                className="text-center",
                                            ),
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.Button(
                                                html.Span(id="rasters-text3-slope"),
                                                id={"type": "btn-restore-raster", "field": "slope"},
                                                className="bg-danger text-center",
                                            ),
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                    dbc.Row(
                                        dbc.Col(
                                            [
                                                html.P(
                                                    html.Span(id="rasters-text4-slope"),
                                                    className="mt-4",
                                                ),
                                                dcc.Upload(
                                                    html.Div(
                                                        [
                                                            html.Span(id="rasters-text5-slope"),
                                                            html.A(html.Span(id="rasters-text6-slope"))
                                                        ]
                                                    ),
                                                    id={"type": "upload-raster", "field": "slope"},
                                                    style={
                                                        "width": "100%",
                                                        "height": "60px",
                                                        "lineHeight": "60px",
                                                        "borderWidth": "1px",
                                                        "borderStyle": "dashed",
                                                        "borderRadius": "5px",
                                                        "textAlign": "center",
                                                    },
                                                ),
                                            ],
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                ],
                                width=4,
                            ),
                        ]
                    )
                )
            )
        )
    ],
    label="Pendiente",
    id = "rasters-slope",
)

tab_roads = dbc.Tab(
    [
        dbc.Card(
            dbc.CardBody(
                dbc.Container(
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Graph(
                                    id={"type": "graph-raster", "field": "roads"},
                                    responsive=True,
                                    style={"height": "60vh"},
                                ),
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.Button(
                                                html.Span(id="rasters-text1-roads"),
                                                id={"type": "btn-download-orig-raster", "field": "roads"},
                                                className="text-center",
                                            ),
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.Button(
                                                html.Span(id="rasters-text2-roads"),
                                                id={"type": "btn-download-raster", "field": "roads"},
                                                className="text-center",
                                            ),
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.Button(
                                                html.Span(id="rasters-text3-roads"),
                                                id={"type": "btn-restore-raster", "field": "roads"},
                                                className="bg-danger text-center",
                                            ),
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                    dbc.Row(
                                        dbc.Col(
                                            [
                                                html.P(
                                                    html.Span(id="rasters-text4-roads"),
                                                    className="mt-4",
                                                ),
                                                dcc.Upload(
                                                    html.Div(
                                                        [
                                                            html.Span(id="rasters-text5-roads"),
                                                            html.A(html.Span(id="rasters-text6-roads"))
                                                        ]
                                                    ),
                                                    id={"type": "upload-raster", "field": "roads"},
                                                    style={
                                                        "width": "100%",
                                                        "height": "60px",
                                                        "lineHeight": "60px",
                                                        "borderWidth": "1px",
                                                        "borderStyle": "dashed",
                                                        "borderRadius": "5px",
                                                        "textAlign": "center",
                                                    },
                                                ),
                                            ],
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                ],
                                width=4,
                            ),
                        ]
                    )
                )
            )
        )
    ],
    label="Caminos",
    id = "rasters-roads",
)


tab_excluded = dbc.Tab(
    [
        dbc.Card(
            dbc.CardBody(
                dbc.Container(
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Graph(
                                    id={"type": "graph-raster", "field": "excluded"},
                                    responsive=True,
                                    style={"height": "60vh"},
                                ),
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.Button(
                                                html.Span(id="rasters-text1-excluded"),
                                                id={"type": "btn-download-orig-raster", "field": "excluded"},
                                                className="text-center",
                                            ),
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.Button(
                                                html.Span(id="rasters-text2-excluded"),
                                                id={"type": "btn-download-raster", "field": "excluded"},
                                                className="text-center",
                                            ),
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.Button(
                                                html.Span(id="rasters-text3-excluded"),
                                                id={"type": "btn-restore-raster", "field": "excluded"},
                                                className="bg-danger text-center",
                                            ),
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                    dbc.Row(
                                        dbc.Col(
                                            [
                                                html.P(
                                                    html.Span(id="rasters-text4-excluded"),
                                                    className="mt-4",
                                                ),
                                                dcc.Upload(
                                                    html.Div(
                                                        [
                                                            html.Span(id="rasters-text5-excluded"),
                                                            html.A(html.Span(id="rasters-text6-excluded"))
                                                        ]
                                                    ),
                                                    id={"type": "upload-raster", "field": "excluded"},
                                                    style={
                                                        "width": "100%",
                                                        "height": "60px",
                                                        "lineHeight": "60px",
                                                        "borderWidth": "1px",
                                                        "borderStyle": "dashed",
                                                        "borderRadius": "5px",
                                                        "textAlign": "center",
                                                    },
                                                ),
                                            ],
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                ],
                                width=4,
                            ),
                        ]
                    )
                )
            )
        )
    ],
    label="Exclusión",
    id = "rasters-excluded",
)


tab_urban = dbc.Tab(
    [
        dbc.Card(
            dbc.CardBody(
                dbc.Container(
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Graph(
                                    id={"type": "graph-raster", "field": "urban"},
                                    responsive=True,
                                    style={"height": "60vh"},
                                ),
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.Button(
                                                html.Span(id="rasters-text1-urban"),
                                                id={"type": "btn-download-orig-raster", "field": "urban"},
                                                className="text-center",
                                            ),
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.Button(
                                                html.Span(id="rasters-text2-urban"),
                                                id={"type": "btn-download-raster", "field": "urban"},
                                                className="text-center",
                                            ),
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.Button(
                                                html.Span(id="rasters-text3-urban"),
                                                id={"type": "btn-restore-raster", "field": "urban"},
                                                className="bg-danger text-center",
                                            ),
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                    dbc.Row(
                                        dbc.Col(
                                            [
                                                html.P(
                                                    html.Span(id="rasters-text4-urban"),
                                                    className="mt-4",
                                                ),
                                                dcc.Upload(
                                                    html.Div(
                                                        [
                                                            html.Span(id="rasters-text5-urban"),
                                                            html.A(html.Span(id="rasters-text6-urban"))
                                                        ]
                                                    ),
                                                    id={"type": "upload-raster", "field": "urban"},
                                                    style={
                                                        "width": "100%",
                                                        "height": "60px",
                                                        "lineHeight": "60px",
                                                        "borderWidth": "1px",
                                                        "borderStyle": "dashed",
                                                        "borderRadius": "5px",
                                                        "textAlign": "center",
                                                    },
                                                ),
                                            ],
                                            class_name="text-center",
                                        ),
                                        class_name="my-2",
                                    ),
                                ],
                                width=4,
                            ),
                        ]
                    )
                )
            )
        )
    ],
    label="Urbano",
    id = "rasters-urban",
)

subsubtabs = [tab_slope, tab_roads, tab_excluded, tab_urban]
downloads = [
    dcc.Download(id={"type": "download-orig-raster", "field": "slope"}),
    dcc.Download(id={"type": "download-raster", "field": "slope"}),
    dcc.Download(id={"type": "download-orig-raster", "field": "roads"}),
    dcc.Download(id={"type": "download-raster", "field": "roads"}),
    dcc.Download(id={"type": "download-orig-raster", "field": "excluded"}),
    dcc.Download(id={"type": "download-raster", "field": "excluded"}),
    dcc.Download(id={"type": "download-orig-raster", "field": "urban"}),
    dcc.Download(id={"type": "download-raster", "field": "urban"}),
    dcc.Download(id="download-predicted-rasters")
]

tab0_content = dbc.Card(dbc.CardBody(dbc.Tabs(subsubtabs)))


# ==================== Pestaña calibración ====================#

# Parámetros
subtab_1 = dbc.Card(
    dbc.CardBody(
        dbc.Container(
            [
                dbc.Row(dbc.Col(html.H4(html.Span(id="calibration-text1")))),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText(
                                        sl.help_text_translation("calibration-text2",
                                                                 translations2["calibration-text3"]["es"],
                                                                 "calibration-text3")
                        
                                    ),
                                    dbc.Select(
                                        required=True,
                                        id={
                                            "type": "val-calibration",
                                            "field": "start-year",
                                        },
                                    ),
                                ]
                            )
                        ),
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText(
                                        sl.help_text_translation("calibration-text4",
                                                                 translations2["calibration-text5"]["es"],
                                                                 "calibration-text5")
                                    ),
                                    dbc.Select(
                                        required=True,
                                        id={
                                            "type": "val-calibration",
                                            "field": "stop-year",
                                        },
                                    ),
                                ]
                            )
                        ),
                    ],
                    className="mb-4",
                ),
                dbc.Row(dbc.Col(html.H4(html.Span(id="calibration-text6")))),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText(
                                        sl.help_text_translation("calibration-text7",
                                                                 translations2["calibration-text8"]["es"],
                                                                 "calibration-text8")
                                    ),
                                    dbc.Input(
                                        type="number",
                                        required=True,
                                        placeholder=10,
                                        value=15,
                                        min=1,
                                        id={
                                            "type": "val-calibration",
                                            "field": "n-iters",
                                        },
                                        debounce=True,
                                    ),
                                ]
                            )
                        ),
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText(
                                        sl.help_text_translation("calibration-text9",
                                                                 translations2["calibration-text10"]["es"],
                                                                 "calibration-text10")
                                    ),
                                    dbc.Input(
                                        type="number",
                                        required=False,
                                        placeholder=0,
                                        value=42,
                                        id={
                                            "type": "val-calibration",
                                            "field": "random-state",
                                        },
                                        debounce=True,
                                    ),
                                ]
                            )
                        ),
                    ],
                    className="mb-4",
                ),
                dbc.Row(dbc.Col(html.H4(html.Span(id="calibration-text11")))),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText(
                                        sl.help_text_translation("calibration-text12",
                                                                 translations2["calibration-text13"]["es"],
                                                                 "calibration-text13")
                                    ),
                                    dbc.Input(
                                        type="number",
                                        required=True,
                                        placeholder=3,
                                        value=3,
                                        min=1,
                                        id={
                                            "type": "val-calibration",
                                            "field": "n-refinement-iters",
                                        },
                                        debounce=True,
                                    ),
                                ]
                            )
                        ),
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText(
                                        sl.help_text_translation("calibration-text14",
                                                                 translations2["calibration-text15"]["es"],
                                                                 "calibration-text15")
                                    ),
                                    dbc.Input(
                                        type="number",
                                        required=True,
                                        placeholder=5,
                                        value=5,
                                        min=1,
                                        id={
                                            "type": "val-calibration",
                                            "field": "n-refinement-splits",
                                        },
                                        debounce=True,
                                    ),
                                ]
                            )
                        ),
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText(
                                        sl.help_text_translation("calibration-text16",
                                                                 translations2["calibration-text17"]["es"],
                                                                 "calibration-text17")
                                    ),
                                    dbc.Input(
                                        type="number",
                                        required=True,
                                        placeholder=3,
                                        value=3,
                                        min=1,
                                        id={
                                            "type": "val-calibration",
                                            "field": "n-refinement-winners",
                                        },
                                        debounce=True,
                                    ),
                                ]
                            )
                        ),
                    ],
                    className="mb-4",
                ),
                dbc.Row(dbc.Col(html.H4(html.Span(id="calibration-text18")))),
                dbc.Row(
                    dbc.Col(
                        dbc.InputGroup(
                            [
                                dbc.InputGroupText(
                                    sl.help_text_translation("calibration-text19",
                                                                 translations2["calibration-text20"]["es"],
                                                                 "calibration-text20")
                                ),
                                dbc.Input(
                                    type="number",
                                    required=True,
                                    placeholder=50,
                                    value=50,
                                    min=0,
                                    max=100,
                                    id={
                                        "type": "val-calibration",
                                        "field": "critical-slope",
                                    },
                                    debounce=True,
                                ),
                            ]
                        )
                    )
                ),
            ]
        )
    )
)


# Coeficientes
# Coeficientes diffusion

subrow_1_diffusion = dbc.Row(dbc.Col(html.H4("Diffusion")))
subrow_2_diffusion = dbc.Row(
    [
        dbc.Col(
            dbc.InputGroup(
                [
                    dbc.InputGroupText(
                    sl.help_text_translation("coeficientes-text1-diffusion",
                                             translations2["coeficientes-text2-diffusion"]["es"],
                                             "coeficientes-text2-diffusion")),
                    dbc.Input(
                        type="number",
                        required=True,
                        placeholder=1,
                        value=1,
                        min=1,
                        max=100,
                        id={"type": "val-calibration-min", "field": "diffusion"},
                    ),
                ]
            )
        ),
        dbc.Col(
            dbc.InputGroup(
                [
                    dbc.InputGroupText(
                    sl.help_text_translation("coeficientes-text3-diffusion",
                                             translations2["coeficientes-text4-diffusion"]["es"],
                                             "coeficientes-text4-diffusion")),
                    dbc.Input(
                        type="number",
                        required=True,
                        placeholder=100,
                        value=100,
                        min=1,
                        max=100,
                        id={"type": "val-calibration-max", "field": "diffusion"},
                    ),
                ]
            )
        ),
    ],
    className="mb-4",
)

# Coeficientes breed
subrow_1_breed = dbc.Row(dbc.Col(html.H4("Breed")))
subrow_2_breed = dbc.Row(
    [
        dbc.Col(
            dbc.InputGroup(
                [
                    dbc.InputGroupText(
                    sl.help_text_translation("coeficientes-text1-breed",
                                             translations2["coeficientes-text2-breed"]["es"],
                                             "coeficientes-text2-breed")),
                    dbc.Input(
                        type="number",
                        required=True,
                        placeholder=1,
                        value=1,
                        min=1,
                        max=100,
                        id={"type": "val-calibration-min", "field": "breed"},
                    ),
                ]
            )
        ),
        dbc.Col(
            dbc.InputGroup(
                [
                    dbc.InputGroupText(
                    sl.help_text_translation("coeficientes-text3-breed",
                                             translations2["coeficientes-text4-breed"]["es"],
                                             "coeficientes-text4-breed")
                    ),
                    dbc.Input(
                        type="number",
                        required=True,
                        placeholder=100,
                        value=100,
                        min=1,
                        max=100,
                        id={"type": "val-calibration-max", "field": "breed"},
                    ),
                ]
            )
        ),
    ],
    className="mb-4",
)

# Coeficientes spread
subrow_1_spread = dbc.Row(dbc.Col(html.H4("Spread")))
subrow_2_spread = dbc.Row(
    [
        dbc.Col(
            dbc.InputGroup(
                [
                    dbc.InputGroupText(
                    sl.help_text_translation("coeficientes-text1-spread",
                                             translations2["coeficientes-text2-spread"]["es"],
                                             "coeficientes-text2-spread")
                    ),
                    dbc.Input(
                        type="number",
                        required=True,
                        placeholder=1,
                        value=1,
                        min=1,
                        max=100,
                        id={"type": "val-calibration-min", "field": "spread"},
                    ),
                ]
            )
        ),
        dbc.Col(
            dbc.InputGroup(
                [
                    dbc.InputGroupText(
                    sl.help_text_translation("coeficientes-text3-spread",
                                             translations2["coeficientes-text4-spread"]["es"],
                                             "coeficientes-text4-spread")
                    ),
                    dbc.Input(
                        type="number",
                        required=True,
                        placeholder=100,
                        value=100,
                        min=1,
                        max=100,
                        id={"type": "val-calibration-max", "field": "spread"},
                    ),
                ]
            )
        ),
    ],
    className="mb-4",
)

# Coeficientes slope
subrow_1_slope = dbc.Row(dbc.Col(html.H4("Slope")))
subrow_2_slope = dbc.Row(
    [
        dbc.Col(
            dbc.InputGroup(
                [
                    dbc.InputGroupText(
                    sl.help_text_translation("coeficientes-text1-slope",
                                             translations2["coeficientes-text2-slope"]["es"],
                                             "coeficientes-text2-slope")
                    ),
                    dbc.Input(
                        type="number",
                        required=True,
                        placeholder=1,
                        value=1,
                        min=1,
                        max=100,
                        id={"type": "val-calibration-min", "field": "slope"},
                    ),
                ]
            )
        ),
        dbc.Col(
            dbc.InputGroup(
                [
                    dbc.InputGroupText(
                    sl.help_text_translation("coeficientes-text3-slope",
                                             translations2["coeficientes-text4-slope"]["es"],
                                             "coeficientes-text4-slope")
                    ),
                    dbc.Input(
                        type="number",
                        required=True,
                        placeholder=100,
                        value=100,
                        min=1,
                        max=100,
                        id={"type": "val-calibration-max", "field": "slope"},
                    ),
                ]
            )
        ),
    ],
    className="mb-4",
)

# Coeficientes road
subrow_1_road = dbc.Row(dbc.Col(html.H4("Road")))
subrow_2_road = dbc.Row(
    [
        dbc.Col(
            dbc.InputGroup(
                [
                    dbc.InputGroupText(
                    sl.help_text_translation("coeficientes-text1-road",
                                             translations2["coeficientes-text2-road"]["es"],
                                             "coeficientes-text2-road")
                    ),
                    dbc.Input(
                        type="number",
                        required=True,
                        placeholder=1,
                        value=1,
                        min=1,
                        max=100,
                        id={"type": "val-calibration-min", "field": "road"},
                    ),
                ]
            )
        ),
        dbc.Col(
            dbc.InputGroup(
                [
                    dbc.InputGroupText(
                    sl.help_text_translation("coeficientes-text3-road",
                                             translations2["coeficientes-text4-road"]["es"],
                                             "coeficientes-text4-road")
                    ),
                    dbc.Input(
                        type="number",
                        required=True,
                        placeholder=100,
                        value=100,
                        min=1,
                        max=100,
                        id={"type": "val-calibration-max", "field": "road"},
                    ),
                ]
            )
        ),
    ],
    className="mb-4",
)

rows_3 = []

rows_3.append(subrow_1_diffusion)
rows_3.append(subrow_2_diffusion)

rows_3.append(subrow_1_breed)
rows_3.append(subrow_2_breed)

rows_3.append(subrow_1_spread)
rows_3.append(subrow_2_spread)

rows_3.append(subrow_1_slope)
rows_3.append(subrow_2_slope)

rows_3.append(subrow_1_road)
rows_3.append(subrow_2_road)


subtab_3 = dbc.Card(dbc.CardBody(rows_3))

# Simulación
submit_button = html.Div(
    [dbc.Button(id="btn-calibrate", n_clicks=0)],
    className="mt-2 text-center",
)

span_list = []
for field in sl.FIELDS:
    elem = html.Li(
        [
            html.Span(html.B(f"{field.title()}: ")),
            html.Span(id={"type": "result-range", "field": field}),
        ]
    )
    span_list.append(elem)

calibration_summary = html.Div(
    [
        html.H4(html.Span(id="simulacion-text1"), className="mt-2"),
        html.Div(
            html.Ul(
                [
                    html.Li(
                        [
                            html.Span(html.B(id = "simulacion-text2")),
                            html.Span(
                                id={"type": "result-calibration", "field": "start-year"}
                            ),
                            html.Span(html.B(" - ")),
                            html.Span(
                                id={"type": "result-calibration", "field": "stop-year"}
                            ),
                        ]
                    ),
                    html.Li(
                        [
                            html.Span(html.B(id = "simulacion-text3")),
                            html.Span(
                                id={"type": "result-calibration", "field": "n-iters"}
                            ),
                        ]
                    ),
                    html.Li(
                        [
                            html.Span(html.B(id = "simulacion-text4")),
                            html.Span(
                                id={
                                    "type": "result-calibration",
                                    "field": "random-state",
                                }
                            ),
                        ]
                    ),
                    html.Li(
                        [
                            html.Span(html.B(id = "simulacion-text5")),
                            html.Span(
                                id={
                                    "type": "result-calibration",
                                    "field": "n-refinement-iters",
                                }
                            ),
                        ]
                    ),
                    html.Li(
                        [
                            html.Span(html.B(id = "simulacion-text6")),
                            html.Span(
                                id={
                                    "type": "result-calibration",
                                    "field": "n-refinement-splits",
                                }
                            ),
                        ]
                    ),
                    html.Li(
                        [
                            html.Span(html.B(id = "simulacion-text7")),
                            html.Span(
                                id={
                                    "type": "result-calibration",
                                    "field": "n-refinement-winners",
                                }
                            ),
                        ]
                    ),
                    html.Li(
                        [
                            html.Span(html.B(id = "simulacion-text8")),
                            html.Span(
                                id={
                                    "type": "result-calibration",
                                    "field": "critical-slope",
                                }
                            ),
                        ]
                    ),
                ]
            ),
        ),
        html.H4(html.Span(id="simulacion-text9"), className="mt-2"),
        html.Div(
            html.Ul(span_list),
        ),
        html.H4(html.Span(id="simulacion-text10"), className="mt-2"),
        html.Ul(
    [
        html.Li(
            [
                html.Span(html.B(id = "Pendiente-faltante")),
                html.Span(
                    id={"type": "result-custom-raster", "field": "slope"}
                ),
            ]
        ),
        html.Li(
            [
                html.Span(html.B(id = "Caminos-faltante")),
                html.Span(
                    id={"type": "result-custom-raster", "field": "roads"}
                ),
            ]
        ),
        html.Li(
            [
                html.Span(html.B(id = "Exclusion-faltante")),
                html.Span(
                    id={"type": "result-custom-raster", "field": "excluded"}
                ),
            ]
        ),
        html.Li(
            [
                html.Span(html.B(id = "Urbano-faltante")),
                html.Span(
                    id={"type": "result-custom-raster", "field": "urban"}
                ),
            ]
        )
    ]
        ),
    ],
)


subtab_5 = dbc.Card(
    dbc.CardBody(
        [
            html.H3(html.Span(id="simulacion-text11")),
            calibration_summary,
            submit_button,
        ]
    )
)


subtab_6 = dbc.Card(dbc.CardBody([html.Div(id="div-calibration-results")]))


tab1_content = dbc.Card(
    dbc.CardBody(
        dbc.Tabs(
            [
                dbc.Tab(subtab_1, label="Parámetros", id = "parametros-calibracion"),
                dbc.Tab(subtab_3, label="Espacio de búsqueda", id = "espacio-calibracion"),
                dbc.Tab(subtab_5, label="Iniciar", id = "iniciar-calibracion"),
                dbc.Tab(
                    subtab_6,
                    label="Resultados",
                    disabled=True,
                    id="result-calibration-subtab",
                ),
            ],
            id="result-calibration-tabs",
        )
    )
)


# ==================== Pestaña predicción ====================#

subtab_2_1 = dbc.Card(
    dbc.CardBody(
        dbc.Container(
            [
                dbc.Row(dbc.Col(html.H4(html.Span(id = "prediccion-text1")))),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText(
                                        sl.help_text_translation("prediccion-text2",
                                             translations2["prediccion-text3"]["es"],
                                             "prediccion-text3")
                                    ),
                                    dbc.Select(
                                        required=True,
                                        id={
                                            "type": "val-prediction",
                                            "field": "start-year",
                                        },
                                    ),
                                ]
                            )
                        ),
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText(
                                        sl.help_text_translation("prediccion-text4",
                                             translations2["prediccion-text5"]["es"],
                                             "prediccion-text5")
                                    ),
                                    dbc.Input(
                                        type="number",
                                        required=True,
                                        placeholder=30,
                                        value=30,
                                        min=1,
                                        id={
                                            "type": "val-prediction",
                                            "field": "num-years",
                                        },
                                        debounce=True,
                                    ),
                                ]
                            )
                        ),
                    ],
                    className="mb-4",
                ),
                dbc.Row(dbc.Col(html.Span(id = "prediccion-text6"))),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText(
                                        sl.help_text_translation("prediccion-text7",
                                             translations2["prediccion-text8"]["es"],
                                             "prediccion-text8")
                                    ),
                                    dbc.Input(
                                        type="number",
                                        required=True,
                                        placeholder=10,
                                        value=15,
                                        min=1,
                                        id={
                                            "type": "val-prediction",
                                            "field": "n-iters",
                                        },
                                        debounce=True,
                                    ),
                                ]
                            )
                        ),
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText(
                                        sl.help_text_translation("prediccion-text9",
                                             translations2["prediccion-text10"]["es"],
                                             "prediccion-text10")
                                    ),
                                    dbc.Input(
                                        type="number",
                                        required=False,
                                        placeholder=0,
                                        value=42,
                                        id={
                                            "type": "val-prediction",
                                            "field": "random-state",
                                        },
                                        debounce=True,
                                    ),
                                ]
                            )
                        ),
                    ],
                    className="mb-4",
                ),
                dbc.Row(dbc.Col(html.H4(html.Span(id = "prediccion-text11")))),
                dbc.Row(
                    dbc.Col(
                        dbc.InputGroup(
                            [
                                dbc.InputGroupText(
                                    sl.help_text_translation("prediccion-text12",
                                             translations2["prediccion-text13"]["es"],
                                             "prediccion-text13")
                                ),
                                dbc.Input(
                                    type="number",
                                    required=True,
                                    placeholder=50,
                                    value=50,
                                    min=0,
                                    max=100,
                                    id={
                                        "type": "val-prediction",
                                        "field": "critical-slope",
                                    },
                                    debounce=True,
                                ),
                            ]
                        )
                    )
                ),
            ],
        )
    )
)

subtab_2_2 = dbc.Card(
    dbc.CardBody(
        dbc.Container(
            [
                dbc.Row(dbc.Col(html.H4(html.Span(id = "prediccion-text14")))),
                dbc.Row(className="mb-2", id="sleuth-row-orig"),
                dbc.Row(dbc.Col(html.H4(html.Span(id = "prediccion-text15")))),
                dbc.Row(className="mb-2", id="sleuth-row-accel"),
                dbc.Row(dbc.Col(html.H4(html.Span(id = "prediccion-text16")))),
                dbc.Row(className="mb-2", id="sleuth-row-deccel"),
                dbc.Row(dbc.Col(html.Hr())),
                dbc.Row(
                    dbc.Col(
                        dbc.Button(
                            "Añadir escenario", id="btn-add-row", class_name="mr-4"
                        )
                    )
                ),
            ],
            id="container-parameters",
        )
    )
)

subtab_2_3 = dbc.Card(
    dbc.CardBody(
        [
            html.H3(html.Span(id = "prediccion-text17")),
            html.Div(
                [
                    html.H4(html.Span(id = "prediccion-text18")),
                    html.Ul(
                        [
                            html.Li(
                                [
                                    html.Span(html.B(html.Span(id = "prediccion-text19"))),
                                    html.Span(
                                        id={
                                            "type": "result-prediction",
                                            "field": "start-year",
                                        }
                                    ),
                                ]
                            ),
                            html.Li(
                                [
                                    html.Span(html.B(html.Span(id = "prediccion-text20"))),
                                    html.Span(
                                        id={
                                            "type": "result-prediction",
                                            "field": "num-years",
                                        }
                                    ),
                                ]
                            ),
                            html.Li(
                                [
                                    html.Span(html.B(html.Span(id = "prediccion-text21"))),
                                    html.Span(
                                        id={
                                            "type": "result-prediction",
                                            "field": "n-iters",
                                        }
                                    ),
                                ]
                            ),
                            html.Li(
                                [
                                    html.Span(html.B(html.Span(id = "prediccion-text22"))),
                                    html.Span(
                                        id={
                                            "type": "result-prediction",
                                            "field": "random-state",
                                        }
                                    ),
                                ]
                            ),
                            html.Li(
                                [
                                    html.Span(html.B(html.Span(id = "prediccion-text23"))),
                                    html.Span(
                                        id={
                                            "type": "result-prediction",
                                            "field": "critical-slope",
                                        }
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
            html.Div(
                [
                    html.H4(html.Span(id = "prediccion-text24")),
                    html.Span(id = "prediccion-text25"),
                    html.Div(id="div-result-prediction-coefficients"),
                ]
            ),
            html.Div(
                [
                    html.H4(html.Span(id = "prediccion-text26")),
                    html.Ul(
    [
        html.Li(
            [
                html.Span(html.B(id = "Pendiente-faltante2")),
                html.Span(
                    id={"type": "result-custom-raster", "field": "slope"}
                ),
            ]
        ),
        html.Li(
            [
                html.Span(html.B(id = "Caminos-faltante2")),
                html.Span(
                    id={"type": "result-custom-raster", "field": "roads"}
                ),
            ]
        ),
        html.Li(
            [
                html.Span(html.B(id = "Exclusion-faltante2")),
                html.Span(
                    id={"type": "result-custom-raster", "field": "excluded"}
                ),
            ]
        ),
        html.Li(
            [
                html.Span(html.B(id = "Urbano-faltante2")),
                html.Span(
                    id={"type": "result-custom-raster", "field": "urban"}
                ),
            ]
        )
    ]
        ),
                ]
            ),
            html.Div(
                [dbc.Button("Ejecutar predicción", id="btn-predict", n_clicks=0)],
                className="mt-2 text-center",
            ),
        ]
    )
)

subtab_2_4 = dbc.Card(dbc.CardBody(id="card-prediction-results"))

tab2_content = dbc.Card(
    dbc.CardBody(
        dbc.Tabs(
            [
                dbc.Tab(subtab_2_1, label="Parámetros", id = "parametros-prediccion"),
                dbc.Tab(subtab_2_2, label="Escenarios", id = "escenarios-prediccion"),
                dbc.Tab(subtab_2_3, label="Iniciar", id = "iniciar-prediccion"),
                dbc.Tab(
                    subtab_2_4,
                    label="Resultados",
                    disabled=True,
                    id="result-prediction-subtab",
                ),
            ],
            active_tab="tab-0",
            id="result-prediction-tabs",
        )
    )
)

# ==================== Layout principal ====================#

tabs = dbc.Tabs(
    [
        dbc.Tab(label="Resumen", id="sleuth-tab-3"),
        dbc.Tab(tab0_content, label="Rasters", id = "Rasters-principal"),
        dbc.Tab(tab1_content, label="Calibración", id = "Calibracion-principal"),
        dbc.Tab(tab2_content, label="Predicción", id = "Prediccion-principal"),
    ]
)

alerts = [
    dbc.Alert(
        id={"type": "raster-alert", "field": field},
        is_open=False,
        dismissable=True,
        color="danger",
    )
    for field in RASTER_FIELDS
]

stores_coefficients = []
for field in sl.FIELDS:
    store = dcc.Store(id={"type": "memory-orig-coefficient", "field": field})
    stores_coefficients.append(store)

stores_attrs = []
stores_rasters = []
for field in RASTER_FIELDS:
    stores_attrs.append(dcc.Store(id={"type": "memory-attrs", "field": field}))
    stores_rasters.append(dcc.Store(id={"type": "memory-raster", "field": field}))
    

all_stores = (
    stores_coefficients
    + stores_attrs
    + stores_rasters
    + [
        dcc.Store(id="memory-years"),
        dcc.Store(id="memory-predicted-rasters"),
    ]
)

# Traducciones
language_buttons = dbc.ButtonGroup(
    [
        dbc.Button("Español", id="btn-lang-es", n_clicks=0),
        dbc.Button("English", id="btn-lang-en", n_clicks=0),
        dbc.Button("Portuguese", id="btn-lang-pt", n_clicks=0),
    ],
    style={"position": "absolute", "top": "10px", "right": "10px", "z-index": "1"},
)

layout = html.Div(
    alerts
    + all_stores
    + downloads
    + [
        html.Div(tabs, className="mb-2"),
        dcc.Download(id="download-sleuth"),
        dcc.Download(id="download-config"),
    ]
)

"""
layout = html.Div(
    [language_buttons, layout],
    style={"position": "relative"}
)
"""

@callback(
    [Output(key, 'children') for key in translations.keys()],
    [Input('current-language-store', 'data')]
)
def update_translated_content(language_data):
    language = language_data['language'] if language_data else 'es'
    updated_content = [translations[key][language] for key in translations.keys()]
    return updated_content

@callback(
    [Output(key, "title") for key in translations2.keys()],
    [Input('btn-lang-es', 'n_clicks'),
     Input('btn-lang-en', 'n_clicks'),
     Input('btn-lang-pt', 'n_clicks')]
)
def update_translated_content2(btn_lang_es, btn_lang_en, btn_lang_pt):
    ctx = dash.callback_context

    if not ctx.triggered:
        language = 'es'  # Predeterminado
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        language = 'es' if button_id == 'btn-lang-es' else 'en' if button_id == 'btn-lang-en' else 'pt'

    return [translations2[key][language] for key in translations2.keys()]

# ---

@callback(
    [Output(key, 'label') for key in tab_translations.keys()], 
    [Input('btn-lang-es', 'n_clicks'),
     Input('btn-lang-en', 'n_clicks'),
     Input('btn-lang-pt', 'n_clicks')]
)

def update_tab_labels(btn_lang_es, btn_lang_en, btn_lang_pt):
    ctx = dash.callback_context

    if not ctx.triggered:
        language = 'es'  # Idioma predeterminado
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        language = 'es' if button_id == 'btn-lang-es' else 'en' if button_id == 'btn-lang-en' else 'pt'

    tab_labels = [tab_translations[key][language] for key in tab_translations.keys()]

    return tab_labels  

# ---

# ==================== Callbacks ====================#


# Actualizar selector de años
@callback(
    Output({"type": "val-calibration", "field": "stop-year"}, "options"),
    Input({"type": "val-calibration", "field": "start-year"}, "value"),
    State("memory-years", "data"),
    prevent_initial_call=True
)
def update_year_range(start_year, years):
    start_year = int(start_year)
    idx = years.index(start_year)
    return years[idx + 2 :]


# Actualizar gráficas
@callback(
    Output({"type": "graph-raster", "field": dash.MATCH}, "figure"),
    Input({"type": "memory-raster", "field": dash.MATCH}, "data"),
    State("memory-years", "data"),
)
def update_graphs(arr, years):
    arr = np.array(arr)
    if arr.ndim == 2:
        return sl.make_simple_raster(arr)
    else:
        return sl.make_simple_multiband_raster(arr, years)


# Descargar arreglos
def raster_to_bytes(data, crs, transform, dtype=rio.int32):
    if data.ndim == 2:
        n_bands = 1
        height, width = data.shape
    else:
        n_bands, height, width = data.shape

    with MemoryFile() as memfile:
        with memfile.open(
            driver="GTiff",
            height=height,
            width=width,
            crs=crs,
            transform=transform,
            dtype=dtype,
            count=n_bands,
        ) as dataset:
            if data.ndim == 2:
                dataset.write(data, 1)
            else:
                for i in range(n_bands):
                    dataset.write(data[i], i + 1)
        return memfile.read()


# Originales
@callback(
    Output({"type": "download-orig-raster", "field": dash.MATCH}, "data"),
    Input({"type": "btn-download-orig-raster", "field": dash.MATCH}, "n_clicks"),
    State("global-store-hash", "data"),
    prevent_initial_call=True,
)
def download_orig_raster(n_clicks, id_hash):
    id_hash = str(id_hash)

    triggered_field = dash.callback_context.triggered_id["field"]
    fpath = PATH_CACHE / id_hash / f"{triggered_field}.npy"
    data = np.load(fpath)
    data = data.astype(rio.int32)

    fpath_attrs = PATH_CACHE / id_hash / "attributes.json"
    with open(fpath_attrs, "r") as f:
        attrs = json.load(f)

    crs = CRS.from_string(attrs["crs"])
    transform = rio.Affine(*attrs["transform"])
    bytes = raster_to_bytes(data, crs, transform)
    return dcc.send_bytes(bytes, f"{field}.tif")


# Actuales
@callback(
    Output({"type": "download-raster", "field": dash.MATCH}, "data"),
    Input({"type": "btn-download-raster", "field": dash.MATCH}, "n_clicks"),
    State({"type": "memory-raster", "field": dash.MATCH}, "data"),
    State({"type": "memory-attrs", "field": dash.MATCH}, "data"),
    prevent_initial_call=True,
)
def download_current_raster(n_clicks, data, attrs):
    data = np.array(data, dtype=rio.int32)
    crs = CRS.from_string(attrs["crs"])
    transform = rio.Affine(*attrs["transform"])
    field = dash.callback_context.triggered_id["field"]
    bytes = raster_to_bytes(data, crs, transform)
    return dcc.send_bytes(bytes, f"{field}.tif")


# Subir arreglos personalizados
@callback(
    Output(
        {"type": "memory-raster", "field": dash.MATCH}, "data", allow_duplicate=True
    ),
    Output({"type": "memory-attrs", "field": dash.MATCH}, "data", allow_duplicate=True),
    Output({"type": "raster-alert", "field": dash.MATCH}, "is_open"),
    Output({"type": "raster-alert", "field": dash.MATCH}, "children"),
    Input({"type": "upload-raster", "field": dash.MATCH}, "contents"),
    State("global-store-hash", "data"),
    prevent_initial_call=True,
)
def update_arrays(uploaded, id_hash):
    id_hash = str(id_hash)
    fpath = PATH_CACHE / id_hash / "attributes.json"
    with open(fpath, "r") as f:
        attrs = json.load(f)

    target_height = attrs["height"]
    target_width = attrs["width"]

    enc = uploaded.split(",")[1]
    dec = base64.b64decode(enc)
    bytes_img = BytesIO(dec)

    source_crs = None
    source_transform = None

    with MemoryFile(bytes_img) as memfile:
        with memfile.open() as dataset:
            try:
                source_crs = dataset.crs
                source_transform = dataset.transform
            except Exception:
                pass
            if source_crs is None or source_transform is None:
                return (
                    dash.no_update,
                    dash.no_update,
                    True,
                    "El raster proporcionado no tiene un CRS asignado, no se hizo la actualización.",
                )

            target_crs = CRS.from_string(attrs["crs"])

            source = dataset.read(1)

            target_height_native = source.shape[1] / target_width * dataset.res[1]
            target_width_native = source.shape[0] / target_height * dataset.res[0]

            reprojected, reprojected_transform = warp.reproject(
                source=source,
                src_crs=source_crs,
                src_transform=source_transform,
                dst_crs=target_crs,
                resampling=Resampling.bilinear,
                dst_resolution=(target_height_native, target_width_native),
            )
            reprojected = reprojected[0]

    out_dict = dict(crs=target_crs.to_string(), transform=list(reprojected_transform))

    return reprojected.tolist(), out_dict, False, None


# Restaurar arreglos
@callback(
    Output(
        {"type": "memory-raster", "field": dash.MATCH}, "data", allow_duplicate=True
    ),
    Output({"type": "memory-attrs", "field": dash.MATCH}, "data", allow_duplicate=True),
    Input({"type": "btn-restore-raster", "field": dash.MATCH}, "n_clicks"),
    State("global-store-hash", "data"),
    prevent_initial_call=True,
)
def restore_raster(n_clicks, id_hash):
    id_hash = str(id_hash)
    triggered_field = dash.callback_context.triggered_id["field"]
    arr = np.load(PATH_CACHE / id_hash / f"{triggered_field}.npy")
    
    with open(PATH_CACHE / id_hash / "attributes.json", "r") as f:
        attrs = json.load(f)

    return arr, attrs


def process_grids(grid_slope, grid_excluded, grid_roads):
    grid_slope = np.array(grid_slope, dtype=np.int32)
    grid_excluded = np.array(grid_excluded, dtype=np.int32)
    grid_roads = np.array(grid_roads, dtype=np.int32)
    (
        grid_roads,
        grid_roads_i,
        grid_roads_j,
        grid_roads_dist,
    ) = sp.derive_auxiliary_roads_numpy(grid_roads)
    return {
        "grid_slope": grid_slope,
        "grid_excluded": grid_excluded,
        "grid_roads": grid_roads,
        "grid_roads_i": grid_roads_i,
        "grid_roads_j": grid_roads_j,
        "grid_roads_dist": grid_roads_dist,
    }


# Ejecutar calibración
state_vals = []
for field in sl.FIELDS:
    state_1 = State({"type": "val-calibration-min", "field": field}, "value")
    state_2 = State({"type": "val-calibration-max", "field": field}, "value")
    state_vals.append(state_1)
    state_vals.append(state_2)


@callback(
    Output("div-calibration-results", "children"),
    Output("result-calibration-tabs", "active_tab"),
    Output("result-calibration-subtab", "disabled"),
    Input("btn-calibrate", "n_clicks"),
    State({"type": "val-calibration", "field": "n-iters"}, "value"),
    State({"type": "val-calibration", "field": "n-refinement-iters"}, "value"),
    State({"type": "val-calibration", "field": "n-refinement-splits"}, "value"),
    State({"type": "val-calibration", "field": "n-refinement-winners"}, "value"),
    *state_vals,
    *[
        State({"type": "memory-raster", "field": field}, "data")
        for field in RASTER_FIELDS
    ],
    State({"type": "val-calibration", "field": "critical-slope"}, "value"),
    State({"type": "val-calibration", "field": "random-state"}, "value"),
    State("memory-years", "data"),
    State({"type": "val-calibration", "field": "start-year"}, "value"),
    State({"type": "val-calibration", "field": "stop-year"}, "value"),
    prevent_initial_call=True,
)
def start_calibration(
    n_clicks,
    n_iters,
    n_refinement_iters,
    n_refinement_splits,
    n_refinement_winners,
    diffusion_min,
    diffusion_max,
    breed_min,
    breed_max,
    spread_min,
    spread_max,
    slope_min,
    slope_max,
    road_min,
    road_max,
    grid_slope,
    grid_roads,
    grid_excluded,
    grid_urban,
    crit_slope,
    random_state,
    years,
    start_year,
    end_year,
):
    start_year = int(start_year)
    end_year = int(end_year)

    assert len(years) == len(grid_urban)

    processed_grids = process_grids(grid_slope, grid_excluded, grid_roads)

    model = SLEUTH(
        n_iters=n_iters,
        n_refinement_iters=n_refinement_iters,
        n_refinement_splits=n_refinement_splits,
        n_refinement_winners=n_refinement_winners,
        coef_range_diffusion=(diffusion_min, diffusion_max),
        coef_range_breed=(breed_min, breed_max),
        coef_range_spread=(spread_min, spread_max),
        coef_range_slope=(slope_min, slope_max),
        coef_range_road=(road_min, road_max),
        crit_slope=crit_slope,
        random_state=random_state,
        **processed_grids,
    )

    out_dir = Path(os.path.join(tempfile.gettempdir(), os.urandom(12).hex()))
    out_dir.mkdir(parents=False, exist_ok=False)

    wanted_years = []
    wanted_urban = []
    for year, grid in zip(years, grid_urban):
        year = int(year)
        if start_year <= year <= end_year:
            wanted_years.append(year)
            wanted_urban.append(grid)
    wanted_years = np.array(wanted_years, dtype=np.int32)
    wanted_urban = np.array(wanted_urban, dtype=np.int32)

    model.fit(wanted_urban, wanted_years, out_dir)

    table = dbc.Table(
        [
            html.Thead(html.Tr([html.Th("Coeficiente"), html.Th("Valor")])),
            html.Tbody(
                [
                    html.Tr([html.Td("Diffusion"), html.Td(model.coef_diffusion_)]),
                    html.Tr([html.Td("Breed"), html.Td(model.coef_breed_)]),
                    html.Tr([html.Td("Spread"), html.Td(model.coef_spread_)]),
                    html.Tr([html.Td("Slope"), html.Td(model.coef_slope_)]),
                    html.Tr([html.Td("Road"), html.Td(model.coef_road_)]),
                ]
            ),
        ],
        bordered=True,
    )

    return table, "tab-3", False


# Actualizar resumen de parámetros
@callback(
    Output({"type": "result-calibration", "field": dash.MATCH}, "children"),
    Input({"type": "val-calibration", "field": dash.MATCH}, "value"),
)
def update_summary(value):
    return str(value)


# Actualizar resumen de rangos de búsqueda
@callback(
    Output({"type": "result-range", "field": dash.MATCH}, "children"),
    Input({"type": "val-calibration-min", "field": dash.MATCH}, "value"),
    Input({"type": "val-calibration-max", "field": dash.MATCH}, "value"),
    Input({"type": "val-calibration", "field": "n-refinement-splits"}, "value"),
)
def update_ranges(c_min, c_max, c_num):
    grid = utils.generate_grid(c_min, c_max, c_num)
    grid = list(grid)
    return pprint.pformat(grid)


# ==================== Predicción ====================#


# Actualizar resumen de rasters personalizados
@callback(
    Output({"type": "result-custom-raster", "field": dash.MATCH}, "children"),
    Output(
        {"type": "result-prediction-custom-raster", "field": dash.MATCH}, "children"
    ),
    Input({"type": "memory-raster", "field": dash.MATCH}, "data"),
    State("global-store-hash", "data"),
)
def update_custom_raster_results(current, id_hash):
    id_hash = str(id_hash)
    triggered_field = dash.callback_context.triggered_id["field"]
    original = np.load(PATH_CACHE / id_hash / f"{triggered_field}.npy")

    return ("No", "No") if np.array_equal(current, original, equal_nan=True) else ("Sí", "Sí")


# Actualizar resumen de coeficientes
@callback(
    Output("div-result-prediction-coefficients", "children"),
    Input(
        {"type": "val-prediction-coefficient", "field": dash.ALL, "index": dash.ALL},
        "value",
    ),
    State({"type": "memory-orig-coefficient", "field": dash.ALL}, "data"),
)
def update_prediction_coefficient_display(rows, original):
    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th("Escenario"),
                    html.Th("Diffusion"),
                    html.Th("Breed"),
                    html.Th("Spread"),
                    html.Th("Slope"),
                    html.Th("Road"),
                ]
            )
        )
    ]

    body = []
    for i in range(len(rows) // 5):
        cells = [html.Td(i + 1)]
        for j in range(5):
            value = rows[5 * i + j]
            if original[j] == value:
                cell = html.Td(str(value))
            else:
                cell = html.Td(html.Span([str(value), html.Sup("*")]))
            cells.append(cell)

        row = html.Tr(cells)
        body.append(row)
    table_body = [html.Tbody(body)]

    table = dbc.Table(table_header + table_body, bordered=True)
    return table


# Actualizar resumen de parámetros
@callback(
    Output({"type": "result-prediction", "field": dash.MATCH}, "children"),
    Input({"type": "val-prediction", "field": dash.MATCH}, "value"),
)
def update_prediction_param_display(value):
    return str(value)


def run_single_prediction(
    n_iters,
    processed_grids,
    grid_urban,
    critical_slope,
    random_state,
    coef_diffusion,
    coef_breed,
    coef_spread,
    coef_slope,
    coef_road,
    start_year,
    num_years,
    all_years,
):
    model = SLEUTH(
        n_iters=n_iters,
        grid_excluded=processed_grids["grid_excluded"],
        grid_roads=processed_grids["grid_roads"],
        grid_roads_dist=processed_grids["grid_roads_dist"],
        grid_roads_i=processed_grids["grid_roads_i"],
        grid_roads_j=processed_grids["grid_roads_j"],
        grid_slope=processed_grids["grid_slope"],
        crit_slope=critical_slope,
        random_state=random_state,
    )

    model.coef_diffusion_ = coef_diffusion
    model.coef_breed_ = coef_breed
    model.coef_spread_ = coef_spread
    model.coef_slope_ = coef_slope
    model.coef_road_ = coef_road

    sim_years = list(range(start_year + 1, start_year + num_years + 1))

    start_idx = all_years.index(start_year)
    seed_grid = np.array(grid_urban[start_idx], dtype=bool)

    grid, _, _ = model.predict(seed_grid, num_years)

    grid_plot = xr.DataArray(
        data=grid * 100,
        dims=["Año", "y", "x"],
        coords={
            "Año": sim_years,
            "y": list(range(grid.shape[1])),
            "x": list(range(grid.shape[2])),
        },
    )

    fig = px.imshow(
        grid_plot,
        animation_frame="Año",
        labels=dict(color="Probabilidad de urbanización"),
        zmin=0,
        zmax=100,
        aspect="equal",
    )
    fig.update_xaxes(showticklabels=False, visible=False)
    fig.update_yaxes(showticklabels=False, visible=False)

    return grid, fig


# Iniciar predicción
@callback(
    Output("card-prediction-results", "children"),
    Output("result-prediction-tabs", "active_tab"),
    Output("result-prediction-subtab", "disabled"),
    Output("memory-predicted-rasters", "data"),
    Input("btn-predict", "n_clicks"),
    *[
        State(
            {"type": "val-prediction-coefficient", "field": field, "index": dash.ALL},
            "value",
        )
        for field in sl.FIELDS
    ],
    *[
        State({"type": "memory-raster", "field": field}, "data")
        for field in RASTER_FIELDS
    ],
    State({"type": "val-prediction", "field": "n-iters"}, "value"),
    State({"type": "val-prediction", "field": "random-state"}, "value"),
    State({"type": "val-prediction", "field": "critical-slope"}, "value"),
    State({"type": "val-prediction", "field": "start-year"}, "value"),
    State("memory-years", "data"),
    State({"type": "val-prediction", "field": "num-years"}, "value"),
    prevent_initial_call=True,
)
def start_prediction(
    n_clicks,
    coefs_diffusion,
    coefs_breed,
    coefs_spread,
    coefs_slope,
    coefs_road,
    grid_slope,
    grid_roads,
    grid_excluded,
    grid_urban,
    n_iters,
    random_state,
    critical_slope,
    start_year,
    all_years,
    num_years,
):
    all_years = [int(year) for year in all_years]
    start_year = int(start_year)
    num_years = int(num_years)

    processed_grids = process_grids(grid_slope, grid_excluded, grid_roads)
    grid_urban = np.array(grid_urban)

    tabs = []
    grids = []
    for i, (diffusion, breed, spread, slope, road) in enumerate(
        zip(coefs_diffusion, coefs_breed, coefs_spread, coefs_slope, coefs_road)
    ):
        grid, fig = run_single_prediction(
            n_iters=n_iters,
            processed_grids=processed_grids,
            grid_urban=grid_urban,
            critical_slope=critical_slope,
            random_state=random_state,
            coef_diffusion=diffusion,
            coef_breed=breed,
            coef_road=road,
            coef_slope=slope,
            coef_spread=spread,
            start_year=start_year,
            num_years=num_years,
            all_years=all_years,
        )

        tab = dbc.Tab(
            dbc.Card(
                dbc.CardBody(
                    dbc.Container(
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Graph(
                                        figure=fig,
                                        responsive=True,
                                        style={"height": "60vh"},
                                    ),
                                    width=8,
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Descargar rasters",
                                        id={
                                            "type": "btn-download-predicted-rasters",
                                            "index": i,
                                        },
                                        className="my-2",
                                    ),
                                    width=4,
                                    className="text-center",
                                ),
                            ]
                        )
                    )
                )
            ),
            label=f"Escenario {i+1}",
        )
        tabs.append(tab)
        grids.append(grid)

    x = all_years
    y = [grid.sum() / grid.size for grid in grid_urban]
    z = ["Observaciones"] * len(x)

    final_y = y[-1]

    for i in range(len(grids)):
        x_pred = list(range(start_year + 1, start_year + num_years + 1))
        y_pred = [grid.sum() / grid.size for grid in grids[i]]
        z_pred = [f"Escenario {i + 1}"] * (len(x_pred) + 1)

        x_pred = [start_year] + x_pred
        y_pred = [final_y] + y_pred

        x.extend(x_pred)
        y.extend(y_pred)
        z.extend(z_pred)

    df = pd.DataFrame(
        zip(x, y, z), columns=["Año", "Porcentaje de urbanización", "Categoría"]
    )

    fig = px.line(df, x="Año", y="Porcentaje de urbanización", color="Categoría")
    fig.update_yaxes(tickformat=",.0%")

    plot_tab = dbc.Tab(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig))), label="Resumen")
    tabs = [plot_tab] + tabs

    out = dbc.Tabs(tabs, active_tab="tab-0")

    grids = np.stack(grids)

    return out, "tab-3", False, grids.tolist()


@callback(
    Output("download-predicted-rasters", "data"),
    Input({"type": "btn-download-predicted-rasters", "index": dash.ALL}, "n_clicks"),
    State("memory-predicted-rasters", "data"),
    State("global-store-hash", "data"),
    prevent_initial_call=True,
)
def download_predicted_rasters(n_clicks, data, id_hash):
    id_hash = str(id_hash)
    triggered_field = dash.callback_context.triggered_id["field"]
    triggered_idx = dash.callback_context.triggered_id["index"]

    with open(PATH_CACHE / id_hash / "attributes.json", "r") as f:
        attrs = json.load(f)
    
    if n_clicks[triggered_idx] is None:
        return dash.no_update

    data = np.array(data, dtype=rio.float64)
    data = data[triggered_idx]

    crs = CRS.from_string(attrs["crs"])
    transform = rio.Affine(*attrs["transform"])
    bytes = raster_to_bytes(data, crs, transform, dtype=rio.float64)
    return dcc.send_bytes(bytes, "predicted.tif")


@callback(
    Output("container-parameters", "children", allow_duplicate=True),
    Input("btn-add-row", "n_clicks"),
    Input("btn-lang-es", "n_clicks"),
    Input("btn-lang-en", "n_clicks"),
    Input("btn-lang-pt", "n_clicks"),
    State("container-parameters", "children"),
    State({"type": "memory-orig-coefficient", "field": dash.ALL}, "data"),
    prevent_initial_call=True,
)
def add_parameter_row(n_clicks, children, orig_coefficients, btn_lang_es, btn_lang_en, btn_lang_pt):
    if n_clicks is None:
        return dash.no_update
    
    ctx = dash.callback_context
    if not ctx.triggered:
        language = 'es'  # Idioma predeterminado
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        language = 'es' if button_id == 'btn-lang-es' else 'en' if button_id == 'btn-lang-en' else 'pt'

    coefficients = {}
    for state, value in zip(dash.callback_context.states_list[1], orig_coefficients):
        coefficients[state["id"]["field"]] = value

    idx = (len(children) - 1) // 3
    new_row = sl.create_parameter_row(idx, coefficients, language=language)

    new_children = children[:-1]
    new_children.append(dbc.Row(dbc.Col(html.H4(f"Escenario {idx + 1}"))))
    new_children.append(new_row)
    new_children.append(dbc.Row(dbc.Col([html.Hr()])))
    new_children.append(children[-1])
    return new_children


@callback(
    Output("container-parameters", "children"),
    Input({"type": "btn-delete-row", "index": dash.ALL}, "n_clicks"),
    State(
        {"type": "val-prediction-coefficient", "field": dash.ALL, "index": dash.ALL},
        "value",
    ),
    prevent_initial_call=True,
)
def delete_parameter_row(n_clicks, current_coefficients):
    triggered_idx = dash.callback_context.triggered_id["index"]
    if n_clicks[triggered_idx] is None:
        return dash.no_update

    children = []
    row_count = 0
    for i in range(len(current_coefficients) // 5):
        if triggered_idx != i:
            coefficients = {
                "diffusion": current_coefficients[5 * i + 0],
                "breed": current_coefficients[5 * i + 1],
                "spread": current_coefficients[5 * i + 2],
                "slope": current_coefficients[5 * i + 3],
                "road": current_coefficients[5 * i + 4],
            }
            new_row = sl.create_parameter_row(row_count, coefficients)
            children.append(dbc.Row(dbc.Col(html.H4(f"Escenario {row_count + 1}"))))
            children.append(new_row)
            children.append(dbc.Row(dbc.Col(html.Hr())))
            row_count += 1

    children.append(
        dbc.Row(
            dbc.Col(dbc.Button("Añadir escenario", id="btn-add-row", class_name="mr-4"))
        )
    )

    return children


@callback(
    Output({"type": "val-calibration", "field": "start-year"}, "value"),
    Output({"type": "val-calibration", "field": "start-year"}, "options"),
    Output({"type": "val-calibration", "field": "stop-year"}, "value"),
    Output({"type": "val-prediction", "field": "start-year"}, "value"),
    Output({"type": "val-prediction", "field": "start-year"}, "options"),
    Input("memory-years", "data"),
)
def update_selects(years):
    max_years = max(years)
    return min(years), years[:-2], max_years, max_years, years


@callback(
    *[
        Output({"type": "memory-orig-coefficient", "field": field}, "data")
        for field in sl.FIELDS
    ],
    Output("sleuth-row-orig", "children"),
    Output("sleuth-row-accel", "children"),
    Output("sleuth-row-deccel", "children"),
    Input("global-store-hash", "data"),
)
def update_coefficient_stores(id_hash):
    id_hash = str(id_hash)

    with open("./data/output/cities/coefficients_by_hash.json", "r", encoding="utf8") as f:
        coefficients = json.load(f)

    found_coefficients = {}
    if id_hash in coefficients:
        found_coefficients = coefficients[id_hash]
    else:
        found_coefficients = {f: 1 for f in sl.FIELDS}

    row_orig = sl.create_parameter_row(0, parameters=found_coefficients)
    row_accel = sl.create_parameter_row(
        0, parameters=sl.get_parameters_asc(found_coefficients)
    )
    row_deccel = sl.create_parameter_row(
        0, parameters=sl.get_parameters_des(found_coefficients)
    )

    return [found_coefficients[field] for field in sl.FIELDS] + [
        row_orig,
        row_accel,
        row_deccel,
    ]


@callback(
    Output("memory-years", "data"),
    Output("sleuth-tab-3", "children"),
    *[
        Output({"type": "memory-attrs", "field": field}, "data")
        for field in RASTER_FIELDS
    ],
    *[
        Output({"type": "memory-raster", "field": field}, "data")
        for field in RASTER_FIELDS
    ],
    Input("global-store-hash", "data"),
    Input("global-store-bbox-latlon", "data"),
    Input('btn-lang-es', 'n_clicks'),
    Input('btn-lang-en', 'n_clicks'),
    Input('btn-lang-pt', 'n_clicks')
)

def download_data(id_hash, bbox_latlon, btn_lang_es, btn_lang_en, btn_lang_pt):
    
    ctx = dash.callback_context
    
    if not ctx.triggered:
        language = 'es'  # Idioma predeterminado
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        language = 'es' if button_id == 'btn-lang-es' else 'en' if button_id == 'btn-lang-en' else 'pt'
        
    id_hash = str(id_hash)
    path_cache = PATH_CACHE / id_hash

    bbox_latlon = shape(bbox_latlon)
    bbox_mollweide = ug.reproject_geometry(bbox_latlon, "ESRI:54009").envelope

    sp.load_or_prep_rasters(bbox_mollweide, path_cache)

    with open(path_cache / "attributes.json", "r") as f:
        attributes = json.load(f)

    out_attributes = [
        dict(transform=attributes["transform"], crs=attributes["crs"])
        for _ in RASTER_FIELDS
    ]
    years = attributes["years"]

    out_rasters = []
    urban_rasters = None
    for field in RASTER_FIELDS:
        raster = np.load(path_cache / f"{field}.npy")
        out_rasters.append(raster)
        if field == "urban":
            urban_rasters = raster

    summary = sl.summary(id_hash, urban_rasters, years, language=language)

    return [years, summary] + out_attributes + out_rasters