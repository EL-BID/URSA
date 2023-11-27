[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=EL-BID_URSA&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=EL-BID_URSA)
![analytics image (flat)](https://raw.githubusercontent.com/vitr/google-analytics-beacon/master/static/badge-flat.gif)
![analytics](https://www.google-analytics.com/collect?v=1&cid=555&t=pageview&ec=repo&ea=open&dp=/URSA/readme&dt=&tid=UA-4677001-16)


# URSA

**U**rban **R**eporting based on **S**atellite **A**nalysis

## **¿Qué es?**

URSA es un sistema de apoyo para la planificación urbana. Permite acceder de forma sencilla a la enorme cantidad de información capturada por sensores satelitales, encargándose de recopilar, procesar y presentar información clave acerca de la evolución de ciudades en Latinoamérica y el Caribe (LAC).

URSA es una herramienta gratuita, de código abierto.

[TUTORIAL PARA INSTALACIÓN Y USO EN WINDOWS](https://github.com/EL-BID/URSA/blob/main/documentation/URSA-Tutorial-Windows.pdf)


## ¿Por qué fue desarrollada?

El sistema fue desarrollado en colaboración entre la División de Vivienda y Desarrollo Urbano (HUD) del BID y el Centro para el Futuro de las Ciudades del Tecnológico de Monterrey. La misión fue la de diseñar una plataforma que permita a los gobiernos municipales adquirir de forma fácil información cartográfica actualizada, en el formato apropiado y en la resolución geográfica adecuada. 


## ¿Por qué la estamos compartiendo?

URSA está a disposición del público general, y sobre todo de equipos de gobierno, para apoyar los procesos de toma de decisiones, planificación y gestión en ciudades y regiones metropolitanas.

![](https://github.com/bitsandbricks/URSA/raw/main/documentation/URSA_analisis_historico_.gif)


## Instalación

(estos pasos son requeridos sólo una vez)

1. Clonar o descargar el contenido de este repositorio.

2. Instalar
[Docker](https://docs.docker.com/engine/install/)

3. Iniciar la imagen de docker con el código y dependencias. Desde el directorio
donde se ha descargado la aplicación, ejecutar:

```
docker build -t bid-urban-growth .
```

El proceso tomará un buen rato la primera vez, ya que necesitará descargar y
configurar varios componentes de software. Una vez completada la primera
puesta en marcha, las subsiguientes serán casi instantáneas.

## Uso

Para cargar y correr un contenedor con la imagen de docker, se debe ejecutar el siguiente comando:

* **En Windows:** `launcher.bat`
* **En Linux/Mac:** `bash launcher.sh`

Posteriormente, se deberá abrir una ventana del navegador web y apuntar a la dirección http://localhost:8050/. Por razones de compatibilidad, se recomienda utilizar Firefox o Safari.
