# asistencia/selfie_handler.py
import os
import base64
import uuid
from typing import Tuple, Optional
import aiofiles

BASE_SELFIES_DIR = "storage/selfies"

def ensure_selfies_dir():
    """Asegura que el directorio de selfies existe."""
    os.makedirs(BASE_SELFIES_DIR, exist_ok=True)


def decode_base64_image(base64_string: str) -> Optional[bytes]:
    """Decodifica una imagen en base64 a bytes."""
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        return base64.b64decode(base64_string)
    except Exception:
        return None


async def guardar_selfie(
    base64_image: str,
    username: str,
    fecha: str
) -> Tuple[bool, Optional[str], str]:
    """Guarda la selfie del técnico y retorna la ruta relativa."""
    ensure_selfies_dir()
    
    image_bytes = decode_base64_image(base64_image)
    if not image_bytes:
        return False, None, "No se pudo procesar la imagen. Formato inválido."
    
    if len(image_bytes) < 5000:
        return False, None, "La imagen es demasiado pequeña. Por favor, toma una selfie válida"
    
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{username}_{fecha}_{unique_id}.jpg"
    filepath = os.path.join(BASE_SELFIES_DIR, filename)
    
    try:
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(image_bytes)
        return True, f"storage/selfies/{filename}", "Selfie guardada correctamente"
    except Exception as e:
        return False, None, f"Error al guardar selfie: {str(e)}"


async def validar_selfie(base64_image: str) -> Tuple[bool, str]:
    """Valida que la selfie sea válida y no esté vacía."""
    if not base64_image:
        return False, "La selfie es obligatoria para registrar asistencia"
    
    image_bytes = decode_base64_image(base64_image)
    if not image_bytes:
        return False, "Formato de imagen inválido"
    
    if len(image_bytes) < 5000:
        return False, "La imagen es demasiado pequeña. Por favor
