FROM jupyter/scipy-notebook
# FROM condaforge/mambaforge

RUN mamba install -y -c conda-forge geemap dash geocube geopandas numpy osmnx pandas plotly rasterio rioxarray scipy Shapely Unidecode xarray pyyaml netcdf4

RUN conda create --name predictor --clone base

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "predictor", "/bin/bash", "-c"]

RUN pip install dash-extensions dash_extensions dash_bootstrap_components dash_gif_component dash_unload_component

# Installing the gcloud cli
# RUN mamba install -y google-cloud-sdk

RUN mkdir app
WORKDIR app
COPY . .

EXPOSE 8050

CMD [ "conda", "run", "--no-capture-output", "-n", "predictor", "python", "-u", "app.py" ]
