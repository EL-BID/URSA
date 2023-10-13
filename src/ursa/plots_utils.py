import numpy as np
import plotly.express as px
import pandas as pd


def get_line_traces(geo_df, class_col, name_dict, color_dict):
    """ Builds traces for linerings in geo_df GeoDataFrame.
    This traces can be added to a map.

    Parameters
    ----------
    geo_df : GeoDataFrame
        GeoDataFrame with Polygons to plot.
    class_col : sts
        Column in geo_df with different classes.
    name_dict : Dict
        Dictionary mapping classes to legend names.
    color_dict : List
        Dictionary mapping names to legend colors.
    """

    # Project to web mercator
    geo_df = geo_df.to_crs(epsg=4326)

    lats = []
    lons = []
    names = []

    for feature, cls in zip(geo_df.geometry, geo_df[class_col]):
        name = name_dict[cls]
        linestring = feature.exterior
        x, y = linestring.xy
        lats = np.append(lats, y)
        lons = np.append(lons, x)
        names = np.append(names, [name]*len(y))
        lats = np.append(lats, None)
        lons = np.append(lons, None)
        names = np.append(names, None)

    df = pd.DataFrame({'lats': lats, 'lons': lons, 'names': names})

    fig = px.line_mapbox(df, lat='lats', lon='lons', color='names',
                         color_discrete_map=color_dict)

    # Remove hover info
    fig.update_traces(hovertemplate=None, hoverinfo="skip")

    return fig.data
