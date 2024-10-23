import logging
import os
from hashlib import md5
from io import BytesIO

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import Depends, HTTPException, UploadFile
from PIL import Image as PILImage
from PIL import ImageOps
from starlette.datastructures import UploadFile as StarletteUploadFile

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def create_image(file: UploadFile, folder: str) -> str:
    return await process_image(file, folder)


async def update_image(file: UploadFile, folder: str) -> str:
    try:
        # List existing images in the folder and delete them from S3
        response = s3.list_objects_v2(Bucket=AWS_S3_BUCKET, Prefix=f"{folder}/")
        if "Contents" in response:
            for obj in response["Contents"]:
                s3.delete_object(Bucket=AWS_S3_BUCKET, Key=obj["Key"])
    except ClientError as e:
        logger.error(f"Error deleting old images from S3: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating image in S3")

    return await process_image(file, folder)


async def process_image(file: UploadFile, folder: str) -> str:
    try:
        # Read file content
        if isinstance(file, StarletteUploadFile):
            logger.info(f"Processing image: {file.filename}")
            file = await file.read()
        img_bytes = BytesIO(file)
        md5sum = md5(img_bytes.getbuffer())
        img = PILImage.open(img_bytes)
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid image")

    # Check image format
    if img.format not in ["JPEG", "PNG", "BMP", "GIF"]:
        logger.error(f"Invalid image format: {img.format}")
        raise HTTPException(status_code=400, detail="Invalid image format")

    # Fix image orientation and convert to RGB
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")

    # Create the image path using the MD5 hash
    img_path = f"{folder}/{md5sum.hexdigest()}.jpg"

    # Save the image to a BytesIO object
    img_buffer = BytesIO()
    img.save(
        img_buffer, format="JPEG", quality="web_high", optimize=True, progressive=True
    )
    img_buffer.seek(0)

    try:
        # Upload the image to S3
        s3.put_object(
            Bucket=AWS_S3_BUCKET,
            Key=img_path,
            Body=img_buffer,
            ContentType="image/jpeg",
            ACL="public-read",  # Permitir leitura pública
        )
        logger.info(f"Image successfully uploaded to S3 at: {img_path}")
    except NoCredentialsError as e:
        logger.error(f"Credentials not available: {str(e)}")
        raise HTTPException(status_code=500, detail="S3 credentials not available")
    except ClientError as e:
        logger.error(f"Failed to upload image to S3: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload image to S3")

    # Return the full S3 URL of the uploaded image
    s3_url = f"https://{AWS_S3_BUCKET}.s3.amazonaws.com/{img_path}"
    return s3_url
