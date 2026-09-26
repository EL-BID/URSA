TEMP_COLORS = {
    "Muy frío": "#2166AC",
    "Frío": "#67A9CF",
    "Ligeramente frío": "#D1E5F0",
    "Templado": "#F7F7F7",
    "Ligeramente cálido": "#FDDBC7",
    "Caliente": "#EF8A62",
    "Muy caliente": "#B2182B",
}

TEMP_CAT_MAP = {i + 1: n for i, n in enumerate(TEMP_COLORS.keys())}

TEMP_NAMES = list(TEMP_CAT_MAP.values())

RdBu7 = ["#2166AC", "#67A9CF", "#D1E5F0", "#F7F7F7", "#FDDBC7", "#EF8A62", "#B2182B"]

RdBu7k = ["#2166AC", "#67A9CF", "#D1E5F0", "#808080", "#FDDBC7", "#EF8A62", "#B2182B"]

TEMP_PALETTE_MAP = {x: y for x, y in zip(TEMP_NAMES, RdBu7)}

TEMP_PALETTE_MAP_INV = {value: key for key, value in TEMP_PALETTE_MAP.items()}

TEMP_PALETTE_MAP_K = {x: y for x, y in zip(TEMP_NAMES, RdBu7k)}

TEMP_PALETTE_MAP_INV_K = {value: key for key, value in TEMP_PALETTE_MAP_K.items()}

# Basemap served by OpenFreeMap. It needs no API key and has no usage quota,
# unlike the CARTO styles that plotly.js used to inline ("carto-positron"),
# which now return watermarked tiles when requested without a key.
BASEMAP_STYLE = "https://tiles.openfreemap.org/styles/positron"

# OpenFreeMap, OpenMapTiles and OpenStreetMap only allow this basemap to be
# used as long as the credit stays visible on the map.
BASEMAP_ATTRIBUTION = (
    '<a href="https://openfreemap.org/" target="_blank">OpenFreeMap</a> © '
    '<a href="https://www.openmaptiles.org/" target="_blank">OpenMapTiles</a> © '
    '<a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>'
    " contributors"
)
