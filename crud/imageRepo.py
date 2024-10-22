import logging
import os
from hashlib import md5
from io import BytesIO

from fastapi import Depends, HTTPException, UploadFile
from PIL import Image as PILImage
from PIL import ImageOps
from starlette.datastructures import UploadFile as StarletteUploadFile

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def create_image(file: UploadFile, folder: str) -> str:
    return await process_image(file, folder)


async def update_image(file: UploadFile, folder: str) -> str:
    previous_images = [f for f in os.listdir(f"static/{folder}") if f.endswith(".jpg")]
    for old_image in previous_images:
        os.remove(os.path.join(f"static/{folder}", old_image))

    return await process_image(file, folder)


async def process_image(file: UploadFile, folder: str) -> str:
    try:
        # Lê o conteúdo do arquivo
        if isinstance(file, StarletteUploadFile):
            logger.info(f"Processing image: {file.filename}")
            file = await file.read()
        img_bytes = BytesIO(file)
        md5sum = md5(img_bytes.getbuffer())
        img = PILImage.open(img_bytes)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image")

    # Verifica o formato da imagem
    if img.format not in ["JPEG", "PNG", "BMP", "GIF"]:
        logger.error(f"Invalid image format: {img.format}")
        raise HTTPException(status_code=400, detail="Invalid image format")

    # Corrige a orientação da imagem (EXIF) e converte para RGB
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")

    # Cria o diretório, se ainda não existir
    os.makedirs(f"static/{folder}", exist_ok=True)

    # Define o caminho da imagem usando o hash MD5
    img_path = f"/{folder}/{md5sum.hexdigest()}.jpg"

    # Salva a nova imagem no caminho especificado
    img.save(
        f"static{img_path}",
        format="JPEG",
        quality="web_high",
        optimize=True,
        progressive=True,
    )

    return img_path  # Retorna o caminho da nova imagem
