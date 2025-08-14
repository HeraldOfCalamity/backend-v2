from datetime import datetime, timezone
import os
from string import Template
from typing import Mapping


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