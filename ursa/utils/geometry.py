import json
import pyproj
import shapely

import numpy as np


def reproject_geometry(geo, target_crs, start_crs="EPSG:4326"):
    project = pyproj.Transformer.from_proj(
        pyproj.Proj(start_crs), pyproj.Proj(target_crs), always_xy=True
    )
    out = shapely.ops.transform(project.transform, geo)
    return out


def geometry_to_json(geo):
    return json.loads(shapely.to_geojson(geo))


def hash_geometry(bbox_latlon_json):
    id_hash = 0
    coords = np.array(bbox_latlon_json["coordinates"])
    for elem in np.nditer(coords):
        id_hash += hash(int(elem * 1e6))
    id_hash = hash(id_hash)
    return id_hash
