from geemap import colormaps

colors = colormaps.get_palette('YlGnBu', 10, hashtag=True)

codes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
         21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37]

year_list = [1972, 1978, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993,
             1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004,
             2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015,
             2016, 2017, 2018, 2019]

cmap = ({1: colors[0], 2: colors[1], 3: colors[2]}
        | {c: colors[3] for c in range(4, 9)}
        | {c: colors[4] for c in range(9, 14)}
        | {c: colors[5] for c in range(14, 19)}
        | {c: colors[6] for c in range(19, 24)}
        | {c: colors[7] for c in range(24, 29)}
        | {c: colors[8] for c in range(29, 34)}
        | {c: colors[9] for c in range(34, 38)})

dummy_class = ['1972', '1978', '1985', '1990', '1995', '2000', '2005', '2010',
               '2015', '2019']

gisa_dummy_cmap = {y: c for y, c in zip(dummy_class, colors)}


def gisa_yearly_s3(bbox, data_path=None,
                   s3_path='GISA_v02_COG.tif',
                   bucket='tec-expansion-urbana-p'):
    """Downloads GISA v2 windowed rasters for each available year.

    Takes a bounding box (bbox) and downloads the corresponding raster from a
    the global GISA COG stored on Amazon S3. Then process the original raster
    data to extract yearly urbanization and creates a geotiff with
    a band for each year.

    Parameters
    ----------
    bbox : Polygon
        Shapely Polygon defining the bounding box.
    data_path : Path
        Path to directory to store yearly GISA rasters.
        If none, don't write to disk.
    s3_dir : str
        Relative path to GISA COG on S3.
    bucket : str

    Returns
    -------
    raster : rioxarray.DataArray
        In memory raster.

    """

    # Get gisa in original encoding
    subset, profile = np_from_bbox_s3(s3_path, bbox, bucket)

    # Create yearly numpy arrays
    gisa_dict = (
        {1972: 1, 1978: 2}
        | {year: val + 3 for val, year in enumerate(range(1985, 2020))}
    )

    array_list = [subset]
    for year, pix_val in gisa_dict.items():
        gisa_binary = np.logical_and(0 < subset, subset <= pix_val).astype('uint8')
        array_list.append(gisa_binary)
    gisa_full = np.concatenate(array_list)

    # Create rioxarray
    profile['count'] = gisa_full.shape[0]
    with tempfile.NamedTemporaryFile() as tmpfile:
        with rio.open(tmpfile.name, 'w', **profile) as dst:
            dst.write(gisa_full)
        raster = rxr.open_rasterio(tmpfile.name)

   # Rename band dimension to reflect years, 0 is original data encoding
    raster.coords['band'] = [0] + list(gisa_dict.keys())

    # Save
    if data_path is not None:
        raster.rio.to_raster(data_path / 'GISAv2.tif')

    return raster
