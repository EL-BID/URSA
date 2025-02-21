from argparse import ArgumentParser
from os.path import basename
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen, urlretrieve

import shutil
import zipfile

from rasterio.io import MemoryFile

import rasterio.mask # pylint: disable=unused-import
import rasterio.merge # pylint: disable=unused-import
import rasterio as rio

import geopandas as gpd


def clamp(x: float, offset: float, scale: float) -> int:
    return int((x - offset) // scale * scale + offset)


def clamp_latlon(min_lon: float, min_lat: float, max_lon: float, max_lat: float, *, scale: float, lon_offset: float=0, lat_offset: float=0) -> tuple[list[float], list[float]]:
    left_lon = clamp(min_lon, lon_offset, scale)
    right_lon = clamp(max_lon, lon_offset, scale)

    bot_lat = clamp(min_lat, lat_offset, scale)
    top_lat = clamp(max_lat, lat_offset, scale)

    lons = [left_lon]
    if left_lon != right_lon:
        lons.append(right_lon)

    lats = [bot_lat]
    if bot_lat != top_lat:
        lats.append(top_lat)

    return lons, lats


def generate_coord_str(pattern: str, lon: int, lat: int) -> str:
    if lon < 0:
        lon_prefix = "W"
    else:
        lon_prefix = "E"
    lon_str = f"{lon_prefix}{str(abs(lon)).rjust(3, "0")}"

    if lat < 0:
        lat_prefix = "S"
    else:
        lat_prefix = "N"
    lat_str = f"{lat_prefix}{abs(lat)}"

    return pattern.format(lon=lon_str, lat=lat_str)


def download_zip(download_path: Path, lon: int, lat: int) -> Path:
    url = generate_coord_str("https://worldcover2021.esa.int/data/archive/ESA_WorldCover_10m_2021_v200_60deg_macrotile_{lat}{lon}.zip", lon, lat)
    response = urlopen(url)
    fname = download_path / basename(response.url)
    if fname.exists():
        print(f"{fname} already exists. Skipping.")
    else:
        urlretrieve(url, fname)
    return fname


def extract_tifs(zip_path: Path, out_dir: Path, lons: list[int], lats: list[int]) -> None:
    fname_pattern = "ESA_WorldCover_10m_2021_V200_{lat}{lon}_Map.tif"

    with zipfile.ZipFile(zip_path) as f_parent:
        out_dir = Path(out_dir)

        for lon in lons:
            for lat in lats:
                fname = generate_coord_str(fname_pattern, lon, lat)
                if fname in f_parent.namelist():
                    with f_parent.open(fname) as f_source, open(out_dir / fname, "wb") as f_target:
                        shutil.copyfileobj(f_source, f_target)


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "GEOMETRY",
        help="Path to the geometry file defining the region of interest. Accepted formats: .shp, .geojson, .gpkg",
        type=str
    )
    parser.add_argument(
        "--out-path",
        help="Path where to save the resultant raster.",
        type=str,
        default="./raster.tif"
    )
    parser.add_argument(
        "--download-path",
        help="Directory where to download WorldCover files.",
        type=str,
        default="./download"
    )
    args = parser.parse_args()

    download_path = Path(args.download_path)
    download_path.mkdir(exist_ok=True, parents=True)

    final_path = Path(args.out_path)

    geom = gpd.read_file(args.GEOMETRY)
    bounds = geom.to_crs("EPSG:4326")["geometry"].item().bounds
    
    coarse_lons, coarse_lats = clamp_latlon(*bounds, scale=60, lat_offset=30)
    fine_lons, fine_lats = clamp_latlon(*bounds, scale=3)

    with TemporaryDirectory() as out_dir:
        out_dir = Path(out_dir)

        for lon in coarse_lons:
            for lat in coarse_lats:
                zip_path = download_zip(download_path, lon, lat)
                extract_tifs(zip_path, out_dir, fine_lons, fine_lats)
        
        sources = []
        for fname in out_dir.glob("*.tif"):
            sources.append(rio.open(fname))
        
        with MemoryFile() as f_merged:
            try:
                rio.merge.merge(sources, dst_path=f_merged.name)
            except Exception: # pylint: disable=broad-exception-caught
                return
            finally:
                for source in sources:
                    source.close()

            with f_merged.open() as ds:
                crs = ds.crs
                masked, transform = rio.mask.mask(ds, [geom.to_crs(ds.crs)["geometry"].item()], crop=True, nodata=0)

        with rio.open(
            final_path, 
            "w",
            driver="GTiff",
            count=masked.shape[0],
            height=masked.shape[1],
            width=masked.shape[2],
            crs=crs,
            transform=transform,
            dtype=masked.dtype,
            nodata=0,
            compress="lzw"
        ) as ds:
            ds.write(masked[0], 1)


if __name__ == "__main__":
    main()
