import logging
import os
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy import asc
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile

from crud.imageRepo import create_image, update_image
from db.database import get_db
from models.pavilion import Pavilion as PavilionModel
from schemas.pavilion import CreatePavilion, UpdatePavilion

load_dotenv()

AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
S3_REGION_NAME = os.getenv("AWS_REGION")
S3_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
S3_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client(
    "s3",
    region_name=S3_REGION_NAME,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
)

pavilion_not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Pavilion not found"
)


async def create_pavilion(new_pavilion: CreatePavilion, image: UploadFile, db: Session):
    if image is None:
        raise HTTPException(status_code=400, detail="Image file is required")

    new_pavilion_record = PavilionModel(
        name=new_pavilion.name,
        location=new_pavilion.location,
        location_link=new_pavilion.location_link,
        image="",  # Temporariamente vazio
    )
    db.add(new_pavilion_record)
    db.commit()
    db.refresh(new_pavilion_record)  # Agora temos o ID do pavilhao

    img_path = await create_image(image, f"pavilions/{new_pavilion_record.id}")

    new_pavilion_record.image = f"{img_path}"
    db.commit()
    db.refresh(new_pavilion_record)

    return new_pavilion_record


def get_pavilion_by_id(pavilion_id: int, db: Session):
    pavilion = db.query(PavilionModel).filter(PavilionModel.id == pavilion_id).first()

    if not pavilion:
        raise pavilion_not_found_exception

    return pavilion


async def update_pavilion(
    pavilion_id: int,
    pavilion_data: UpdatePavilion,
    image: Optional[UploadFile],
    db: Session,
):
    logging.info(f"Updating pavilion with ID: {pavilion_id}")
    pavilion = db.query(PavilionModel).filter(PavilionModel.id == pavilion_id).first()

    if not pavilion:
        logging.error("Pavilion not found")
        raise pavilion_not_found_exception

    if image:
        logging.info(f"Image provided: {image.filename}")
        img_path = await update_image(image, f"pavilions/{pavilion_id}")
        logging.info(f"Image updated at path: {img_path}")
        pavilion.image = f"/{img_path}"

    for key, value in pavilion_data.dict(exclude_unset=True).items():
        if value is not None:
            logging.info(f"Updating field {key} to {value}")
            setattr(pavilion, key, value)

    db.commit()
    db.refresh(pavilion)
    logging.info(f"Pavilion updated: {pavilion}")
    return pavilion


def delete_pavilion(pavilion_id: int, db: Session):
    pavilion = db.query(PavilionModel).filter(PavilionModel.id == pavilion_id).first()

    if not pavilion:
        raise pavilion_not_found_exception

    if pavilion.image:
        # O campo 'image' armazena a URL completa da imagem no bucket S3
        image_url = pavilion.image
        # Extrai a chave do objeto S3 da URL
        image_key = image_url.split(f"{AWS_S3_BUCKET}/")[-1]

        try:
            s3_client.delete_object(Bucket=AWS_S3_BUCKET, Key=image_key)
        except ClientError as e:
            raise HTTPException(
                status_code=400, detail=f"Error deleting image from S3: {e}"
            )

    db.delete(pavilion)
    db.commit()

    return {"detail": "Pavilion deleted successfully"}
