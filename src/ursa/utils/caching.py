from pathlib import Path


def make_cache_dir(path_dir: str) -> Path:
    path_cache = Path(path_dir)
    path_cache.mkdir(parents=True, exist_ok=True)

    return path_cache
