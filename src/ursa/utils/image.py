import base64


def b64_image(image_filename):
    # Funcion para leer imagenes
    with open(image_filename, "rb") as f:
        image = f.read()
    return "data:image/png;base64," + base64.b64encode(image).decode("utf-8")
