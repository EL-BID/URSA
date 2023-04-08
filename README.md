## Instalación

(estos pasos son requeridos sólo una vez)

1. Clonar o descargar el contenido de este repositorio.

2. Instalar
[Docker](https://docs.docker.com/engine/install/)

3. Iniciar la imagen de docker con el código y dependencias. Desde el directorio
donde se ha descargado la aplicación, ejecutar:

        docker build -t bid-urban-growth .

El proceso tomará un buen rato la primera vez, ya que necesitará descargar y
configurar varios componentes de software. Una vez completada la primera
puesta en marcha, las subsiguientes serán casi instantáneas.

## Uso

Para cargar y correr un contenedor con la imagen de docker, se debe ejecutar el siguiente comando:

    python3 launcher.py

Se abrirá una ventana con la dirección http://localhost:8050/ que después de 10 segundos se deberá recargar en caso de que permanezca sin conexión.
