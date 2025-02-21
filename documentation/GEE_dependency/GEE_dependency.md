# Google Earth Engine Dependency

The current version of URSA requires users to provide a Google Earth Engine authentication token when starting the program. This is necessary for the on-the-fly downloading of large files with updated imagery.

Below is a list of features that rely on data obtained through Google Earth Engine:

- **Land Cover:** Uses **WorldCover** rasters.
- **Future Scenarios:** Downloads data from **Geomorpho90m** (topography) and the **World Database on Protected Areas** (WDPA).
- **Urban Heat Islands:** Downloads and processes temperature data from **Landsat 9**.

## Alternative Sources

Most datasets obtained from Earth Engine can be downloaded from other sources. In that case, some spatial and temporal processing tasks previously handled by Earth Engine (such as date and region filtering, image mosaic creation, etc.) will need to be performed by the user.


| **Dataset**  | **Alternative Source** | **Notes** |
|-------------|----------------------|-----------|
| WorldCover  | [European Space Agency](https://esa-worldcover.org/en) | The raster is divided into large grid cells (covering multiple countries), so in most cases, users will need to download only one file. |
| Geomorpho90m | [OpenTopography](https://portal.opentopography.org/dataspace/dataset?opentopoID=OTDS.012020.4326.1) | The raster is divided into multiple cells. |
| WDPA | [Protected Planet](https://www.protectedplanet.net/en/thematic-areas/wdpa) | No additional notes. |
| Landsat 9 | [USGS](https://earthexplorer.usgs.gov/) | The raster is divided into spatial cells and temporal intervals. The website provides an API for automated requests. |

The only exception is Dynamic World data, which, despite being available under an open license (CC BY 4.0), is hosted exclusively on the Google Earth Engine platform.

# Example of Using Alternative Sources

File `example.py` includes a script to download, merge, and clip WorldCover rasters from the ESA website. 
