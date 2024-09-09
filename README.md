![analytics image (flat)](https://raw.githubusercontent.com/vitr/google-analytics-beacon/master/static/badge-flat.gif)
![analytics](https://www.google-analytics.com/collect?v=1&cid=555&t=pageview&ec=repo&ea=open&dp=/URSA/readme&dt=&tid=UA-4677001-16)

# URSA

**U**rban **R**eporting based on **S**atellite **A**nalysis

URSA is a support system for urban planning. It allows easy access to the vast amount of information captured by satellite sensors, taking care of collecting, processing, and presenting key information about the evolution of cities in Latin America and the Caribbean (LAC).

URSA is a free, open-source tool.

[Installation guide for Windows](https://github.com/EL-BID/URSA/blob/main/documentation/ENG-URSA_Installation_Guide_Windows.pdf)

[(en español) Guía de instalación en Windows](https://github.com/EL-BID/URSA/blob/main/documentation/ESP-URSA-Guia_Instalacion_Windows.pdf)


## Why was it developed?

The system was developed in collaboration between the Housing and Urban Development Division (HUD) of the IDB and the Center for the Future of Cities at the Tecnológico de Monterrey. The mission was to design a platform that allows municipal governments to easily acquire updated cartographic information in the appropriate format and geographic resolution.


## Why are we sharing it?

URSA is available to the general public, and especially to government teams, to support decision-making, planning, and management processes in cities and metropolitan regions.

![](https://github.com/bitsandbricks/URSA/raw/main/documentation/URSA_analisis_historico_.gif)


## Quick Start

(these steps are required only once)

1. Clone or download the content of this repository.

2. Install Docker.

3. Start the Docker image with the code and dependencies. From the directory where the application was downloaded, run:

```
docker build -t bid-urban-growth .
```

The process will take a while the first time, as it will need to download and configure several software components. Once the initial setup is complete, subsequent launches will be almost instantaneous.


## Usage

To load and run a container with the docker image, the following command must be executed:

* __On Windows:__ launcher.bat
* __On Linux/Mac:__ bash launcher.sh
  
Subsequently, a web browser window should be opened and pointed to the address http://localhost:8050/. For compatibility reasons, it is recommended to use Firefox or Safari.
