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
