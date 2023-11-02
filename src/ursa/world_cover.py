import ee
from typing import Tuple

BLACK_HEX = "000000"
WHITE_HEX = "FFFFFF"

COVER_IDX = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]

COVER_NAMES = [
    "Árboles",
    "Matorral",
    "Pradera",
    "Cultivos",
    "Construido",
    "Desnudo / Vegetación escasa",
    "Nieve y hielo",
    "Agua",
    "Humedal herbaceo",
    "Manglares",
    "Musgo y liquen",
]
COVER_NAMES_BREAK = [
    "Tree cover",
    "Shrubland",
    "Grassland",
    "Cropland",
    "Built-up",
    "Bare /\nsparse\nvegetation",
    "Snow and ice",
    "Permanent\nwater\nbodies",
    "Herbaceous\nwetland",
    "Mangroves",
    "Moss and\nlichen",
]
COVER_MAP = {key: value for key, value in zip(COVER_IDX, COVER_NAMES)}

COVER_PALETTE = [
    "#006400",
    "#FFBB22",
    "#FFFF4C",
    "#F096FF",
    "#FA0000",
    "#B4B4B4",
    "#F0F0F0",
    "#0064C8",
    "#0096A0",
    "#00CF75",
    "#FAE6A0",
]

COVER_PALETTE_MAP = {key: value for key, value in zip(COVER_IDX, COVER_PALETTE)}

COVER_PALETTE_NAME_MAP = {
    COVER_MAP[key]: value for key, value in COVER_PALETTE_MAP.items()
}


def get_masks(img):
    urban_mask = img.eq(50)

    rural_mask = urban_mask.focalMax(radius=500, units="meters", kernelType="circle")
    rural_mask = rural_mask.bitwiseNot()

    snow_mask = img.neq(70)
    water_mask = img.neq(80)
    unwanted_mask = snow_mask.bitwiseAnd(water_mask)
    rural_mask = rural_mask.bitwiseAnd(unwanted_mask)

    return {"urban": urban_mask, "rural": rural_mask, "unwanted": unwanted_mask}


def get_cover_and_masks(bbox, projection) -> Tuple[ee.Image, dict]:
    lc_cover = ee.ImageCollection("ESA/WorldCover/v200").first().clip(bbox)
    if projection is not None:
        lc_cover = lc_cover.reduceResolution(
            reducer=ee.Reducer.mode(), maxPixels=1024
        ).reproject(projection)
    masks = get_masks(lc_cover)
    lc_cover = lc_cover.updateMask(masks["unwanted"])

    return lc_cover, masks
