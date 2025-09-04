import base64
from datetime import datetime, timezone
import os
from string import Template
from typing import Mapping
import uuid


def get_utc_now():
    return datetime.now(timezone.utc)

def get_mail_html(template_name: str, valores: Mapping[str, object]) -> str:
    templates_dir = 'templates'
    ruta_archivo = os.path.join(templates_dir, template_name)

    with open(ruta_archivo, 'r', encoding='utf-8') as file:
        contenido = file.read()

    plantilla = Template(contenido)
    resultado = plantilla.safe_substitute(valores)

    return resultado

def save_base_64_image_local(base64_image: str, dir: str= '' ) -> str: 
    folder: str = f'static/images/{dir}'
    os.makedirs(folder, exist_ok=True)

    if "," in base64_image: 
        header, base64_data = base64_image.split(",", 1)
        if 'image/' in header:
            ext = header.split('/')[1].split(';')[0]
        else:
            ext = 'png'

    else:
        base64_data = base64_image
        ext='png'

    filename = f'{uuid.uuid4()}.{ext}'
    file_path = os.path.join(folder, filename)

    with open(file_path, 'wb') as f:
        f.write(base64.b64decode(base64_data))

    return file_path