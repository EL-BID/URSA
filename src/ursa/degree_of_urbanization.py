import numpy as np
import pandas as pd
import rioxarray as rxr
import xarray as xr

from scipy.ndimage import label, convolve, center_of_mass
from ursa.ghsl import load_or_download


lvl_1_classes = {
    # 'Urban Center': 3,
    "Urban Cluster": 1,  # 2
    "Rural": 0,  # 1
}


def find_urban_centers(
    pop_array,
    builtup_array,
    u_center_density=1500,
    u_center_pop=50000,
    builtup_trshld=0.5,
    min_hole_size=1500,
    fill=True,
):
    u_center_array = np.zeros_like(pop_array, dtype="uint8")
    # Apply density based classification
    u_center_array[pop_array >= u_center_density] = 1
    # Apply builtup condition
    u_center_array[builtup_array >= builtup_trshld] = 1

    # Label deaults to 4-connectivity
    clusters, nclusters = label(u_center_array)

    # Find their total population and remove them from
    # urban center array if necessary
    labels = []
    for lbl in range(1, nclusters + 1):
        mask = clusters == lbl
        total_pop = pop_array[mask].sum()
        if total_pop < u_center_pop:
            u_center_array[mask] = 0
            clusters[mask] = 0
        else:
            labels.append(lbl)

    # Fill gaps and smooth borders, majority rule
    # Apply per urban center, find all candidates
    # for allocation
    kernel = np.array([[1, 1, 1], [1, -8, 1], [1, 1, 1]])
    for lbl in labels:
        # This needs to be done iteratively until no more additions are performed
        current_center = (clusters == lbl).astype(int)
        while True:
            # Find number of neighbors of each cell
            # Non urban pixels have neighbor values 0-8, while urban
            # pixels have -8-0
            n_nbrs = convolve(current_center, kernel, mode="constant", output=int)
            # New cells are non urban pixels with >=5 neighbors
            mask = n_nbrs >= 5
            if mask.sum() == 0:
                break
            # Update both current center and urban_center_array
            current_center[mask] = 1
            u_center_array[mask] += 1
    # Cells added to more than one urban center have counts > 1.
    # Remove them
    u_center_array[u_center_array > 1] = 0

    if fill:
        # Fill holes smaller than min hole size, defaults to 15km
        # Invert image
        inverted = 1 - u_center_array
        # Find all holes smaller than min size
        holes, nholes = label(inverted)
        for h in range(1, nholes + 1):
            mask = holes == h
            if mask.sum() <= min_hole_size:
                u_center_array[mask] = 1

    return u_center_array


def find_urban_clusters(
    pop_array,
    u_cluster_density=300,
    u_cluster_pop=5000,
    smooth=True,
    fill=True,
    min_hole_size=100,
):
    u_cluster_array = np.zeros_like(pop_array, dtype="uint8")

    # Apply density based classification
    u_cluster_array[pop_array >= u_cluster_density] = 1

    # Label clusters using 8 contiguity
    kernel8 = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
    clusters, nclusters = label(u_cluster_array, structure=kernel8)

    # Find their total population and remove them from
    # if necessary
    labels = []
    for lbl in range(1, nclusters + 1):
        mask = clusters == lbl
        total_pop = pop_array[mask].sum()
        if total_pop < u_cluster_pop:
            u_cluster_array[mask] = 0
            clusters[mask] = 0
        else:
            labels.append(lbl)

    if smooth:
        # Fill gaps and smooth borders, majority rule
        # Apply per urban center, find all candidates
        # for allocation
        kernel = np.array([[1, 1, 1], [1, -8, 1], [1, 1, 1]])
        for lbl in labels:
            # This needs to be done iteratively until no more
            # additions are performed
            current_center = (clusters == lbl).astype(int)
            while True:
                # Find number of neighbors of each cell
                # Non urban pixels have neighbor values 0-8, while urban
                # pixels have -8-0
                n_nbrs = convolve(current_center, kernel, mode="constant", output=int)
                # New cells are non urban pixels with >=5 neighbors
                mask = n_nbrs >= 5
                if mask.sum() == 0:
                    break
                # Update both current center and urban_center_array
                current_center[mask] = 1
                u_cluster_array[mask] += 1
        # Cells added to more than one urban center have counts > 1.
        # Remove them
        u_cluster_array[u_cluster_array > 1] = 0

    if fill:
        # Fill holes smaller min_hole_size, defaults to 1km
        # Invert image
        inverted = 1 - u_cluster_array
        # Find all holes smaller than min size
        holes, nholes = label(inverted)
        for h in range(1, nholes + 1):
            mask = holes == h
            if mask.sum() <= min_hole_size:
                u_cluster_array[mask] = 1

    return u_cluster_array


def dou_lvl1(
    density,
    builtup,
    u_center_density=1500,
    u_center_pop=50000,
    builtup_trshld=0.5,
    u_cluster_density=300,
    u_cluster_pop=5000,
):
    u_cluster_array = find_urban_clusters(
        density.values, u_cluster_density, u_cluster_pop
    )

    # u_center_array = find_urban_centers(
    #     density.values,
    #     builtup.values,
    #     u_center_density,
    #     u_center_pop,
    #     builtup_trshld)

    dou_array = np.full_like(density.values, lvl_1_classes["Rural"], dtype="uint8")
    dou_array[u_cluster_array > 0] = lvl_1_classes["Urban Cluster"]
    # dou_array[u_center_array > 0] = lvl_1_classes['Urban Center']
    dou_rxr = density.copy(data=dou_array)

    return dou_rxr


def get_stats_dict(
    class_array, pop_array, builtup_array, classes, year, cell_area=0.01, connectivity=4
):
    stat_list = []
    if not isinstance(classes, dict):
        if connectivity == 8:
            class_array, ncenters = label(class_array, structure=np.ones((3, 3)))
        else:
            class_array, ncenters = label(class_array)
        classes = {f"{classes} {lbl}": lbl for lbl in range(1, ncenters + 1)}

    for c, l in classes.items():
        mask = class_array == l
        stat_dict = {"Grupo": c}
        stat_dict["year"] = year
        stat_dict["Area"] = mask.sum() * cell_area
        stat_dict["Area_fraction"] = stat_dict["Area"] / (class_array.size * cell_area)
        stat_dict["Pob"] = pop_array[mask].sum() * cell_area
        stat_dict["Pop_density"] = stat_dict["Pob"] / stat_dict["Area"]
        stat_dict["Pop_fraction"] = stat_dict["Pob"] / pop_array.sum()
        stat_dict["Builtup_area"] = builtup_array[mask].sum() * cell_area
        stat_dict["Builtup_fraction"] = stat_dict["Builtup_area"] / (
            builtup_array.sum() * cell_area
        )
        stat_dict["centroid"] = center_of_mass(mask)
        stat_list.append(stat_dict)
    return stat_list


def get_stats_df(dou_array, pop_array, builtup_array, year):
    df = pd.DataFrame(
        get_stats_dict(dou_array, pop_array, builtup_array, lvl_1_classes, year)
        # + get_stats_dict(
        #     (dou_array == lvl_1_classes['Urban Center']).astype(int),
        #     pop_array,
        #     builtup_array,
        #     'Center',
        #     year
        # )
        + get_stats_dict(
            (dou_array > 1).astype(int),
            pop_array,
            builtup_array,
            "Cluster",
            year,
            connectivity=8,
        )
    )

    return df


def find_closest(df, centroid):
    d = np.inf
    for i, cent in enumerate(df.centroid):
        dd = np.sum((cent - centroid) ** 2)
        if dd < d:
            d = dd
            idx = i
    return df.iloc[idx]


def stats_for_largest_cluster(df_stats):
    # We want only urban clusters
    df_clusts = df_stats[df_stats.Grupo.str.startswith("Cluster")]

    # Get year lists
    years = sorted(df_stats.year.unique())

    # For first year find largest cluster in population
    df_year = df_clusts[df_clusts.year == years[0]]
    centroid = df_year.iloc[df_year.Pob.argmax()].centroid

    # Loop over years choosing always the same cluster
    largest_clustrs = []
    for year in years:
        df_year = df_clusts[df_clusts.year == year]
        closest = find_closest(df_year, centroid)
        largest_clustrs.append(closest)
    df_largest = pd.concat(largest_clustrs, axis=1)
    return df_largest.T


def load_input_data_ghs(bbox_mollweide, path_cache, resolution=100):
    print("Loading GHS datasets for Degree of Urbanization ...")

    rasters = {}
    for key in ["BUILT_S", "POP", "LAND"]:
        res = load_or_download(
            bbox_mollweide, key, data_path=path_cache, resolution=resolution
        )
        res = res.rio.set_nodata(0)
        rasters[key] = res

    # Get population density grid in km^2
    cell_area = rasters["POP"].rio.resolution()[0] ** 2
    pop_density = rasters["POP"] / cell_area * 1e6

    # Get built-up grid
    # Convert to builtup fraction
    built_fraction = rasters["BUILT_S"] / cell_area

    # Get land fraction grid
    land_fraction = rasters["LAND"] / cell_area

    print("Done.")

    return pop_density, built_fraction, land_fraction


def dou_for_ghs(bbox_mollweide, path_cache, resolution=100):
    (pop_density, built_fraction, land_fraction) = load_input_data_ghs(
        bbox_mollweide, path_cache, resolution
    )

    # Extract constand land fraction array (band 0)
    land_fraction = land_fraction.values[0]

    print(pop_density.shape)
    print(built_fraction.shape)

    assert pop_density.shape == built_fraction.shape
    assert pop_density.shape[1:] == land_fraction.shape

    # The year list is enconded in the xarray for pop and built
    year_list = pop_density.coords["band"].values

    # Setup thresholds
    u_center_density = 1500
    u_center_pop = 50000
    builtup_trshld = 0.5
    u_cluster_density = 300
    u_cluster_pop = 5000

    df_list = []
    xr_list = []
    for year in year_list:
        print(f"Calculating DoU for year {year}...")
        density = pop_density.sel(band=year)
        builtup = built_fraction.sel(band=year)

        print("    Building array...")
        dou_xr = dou_lvl1(
            density,
            builtup,
            u_center_density,
            u_center_pop,
            builtup_trshld,
            u_cluster_density,
            u_cluster_pop,
        )

        print("    Getting stats...")
        df_stats = get_stats_df(dou_xr.values, density.values, builtup.values, year)

        # dou_xr.rio.to_raster(path_cache / f'dou_{year}.tif')
        # harmonize from previous year
        if year > year_list[0]:
            prev = xr_list[-1].values
            dou_xr.values = np.logical_or(prev, dou_xr.values).astype("uint8")
        xr_list.append(dou_xr)
        df_list.append(df_stats)
        print("Done.")
    dou_full = xr.concat(xr_list, pd.Index(year_list, name="year"))
    dou_full.rio.to_raster(path_cache / "dou.tif")
    df_stats = pd.concat(df_list)
    df_stats["centroid"] = df_stats.centroid.apply(lambda x: np.array(x))
    # df_largest = stats_for_largest_cluster(df_stats)

    df_stats.to_csv(path_cache / "dou_stats.csv")
    # df_largest.to_csv(path_cache / 'dou_largest.csv')


def load_or_process_dou(bbox_mollweide, path_cache, force=False):
    fpath = path_cache / "dou.tif"
    if fpath.exists() and not force:
        pass
    else:
        dou_for_ghs(bbox_mollweide, path_cache)
    raster = rxr.open_rasterio(fpath, cache=False)
    raster.coords["band"] = list(range(1975, 2021, 5))

    return raster
