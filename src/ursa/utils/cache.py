import json

import geopandas as gpd

from ursa.utils.geometry import geometry_to_json, hash_geometry
from ursa.utils.raster import get_bboxes

def generate_hash_files(path_cache):
    df = gpd.read_file(path_cache / "cities_fua.gpkg")

    hashes = {}
    hashes_inv = {}
    for _, row in df.iterrows():
        country, city = row["country"], row["city"]
        
        bbox, *_ = get_bboxes(city, country, path_cache)
        bbox_json = geometry_to_json(bbox)
        id_hash = hash_geometry(bbox_json)

        if country not in hashes:
            hashes[country] = {}
        hashes[country][city] = id_hash

        hashes_inv[id_hash] = {"country": country, "city": city}

    with open(path_cache / "city_hashes.json", "w", encoding="utf8") as f:
        json.dump(hashes, f, ensure_ascii=False)

    with open(path_cache / "city_hashes_inverse.json", "w", encoding="utf8") as f:
        json.dump(hashes_inv, f, ensure_ascii=False)