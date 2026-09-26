from ursa.constants import BASEMAP_ATTRIBUTION


def add_basemap_credit(fig):
    """Adds the basemap credit to a standalone Plotly map.

    Plotly has no layout level attribution for its mapbox maps, so the credit
    for BASEMAP_STYLE has to be drawn as an annotation. It is placed on the
    bottom left corner to keep clear of the data source credits, which the
    callers add on the bottom right one.
    """
    fig.add_annotation(
        text=BASEMAP_ATTRIBUTION,
        showarrow=False,
        xref="paper",
        yref="paper",
        x=0,
        y=0,
        xanchor="left",
        yanchor="bottom",
        font={"size": 10},
    )

    return fig
