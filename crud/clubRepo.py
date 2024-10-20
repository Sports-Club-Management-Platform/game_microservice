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
from models.club import Club as ClubModel
from models.pavilion import Pavilion as PavilionModel
from schemas.club import ClubCreate, ClubUpdate

load_dotenv()

S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET")
S3_REGION_NAME = os.getenv("AWS_REGION")
S3_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
S3_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client(
    's3',
    region_name=S3_REGION_NAME,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

async def create_club(new_club: ClubCreate, image: UploadFile, db: Session):
    if image is None:
        raise HTTPException(status_code=400, detail="Image file is required")

    new_club_record = ClubModel(
        name=new_club.name,
        pavilion_id=new_club.pavilion_id,
        image=""  # Temporariamente vazio
    )
    db.add(new_club_record)
    db.commit()
    db.refresh(new_club_record)  # Agora temos o ID do clube

    img_path = await create_image(image, f"clubs/{new_club_record.id}")

    new_club_record.image = f"{img_path}"
    db.commit()
    db.refresh(new_club_record)

    return new_club_record

def get_club_by_id(club_id: int, db: Session):
    club = db.query(ClubModel).filter(ClubModel.id == club_id).first()
    
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")
    
    return club

def get_all_clubs(db: Session):
    clubs = db.query(ClubModel).all()
    
    return clubs

async def update_club(club_id: int, club_data: ClubUpdate, image: Optional[UploadFile], db: Session):
    club = db.query(ClubModel).filter(ClubModel.id == club_id).first()
    
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")

    if image:
        img_path = await update_image(image, f"clubs/{club_id}")
        club.image = f"/{img_path}"
    
    for key, value in club_data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(club, key, value)
    
    db.commit()
    db.refresh(club)
    
    return club

def delete_club(club_id: int, db: Session):
    club = db.query(ClubModel).filter(ClubModel.id == club_id).first()

    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")
    
    if club.image:
        # O campo 'image' armazena a URL completa da imagem no bucket S3
        image_url = club.image
        # Extrai a chave do objeto S3 da URL
        image_key = image_url.split(f"{S3_BUCKET_NAME}/")[-1]

        try:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=image_key)
        except ClientError as e:
            raise HTTPException(status_code=400, detail=f"Error deleting image from S3: {e}")

    db.delete(club)
    db.commit()
    
    return {"detail": "Club deleted successfully"}

def get_pavilion_by_club_id(club_id: int, db: Session):
    club = db.query(ClubModel).filter(ClubModel.id == club_id).first()

    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")
    
    pavilion = db.query(PavilionModel).filter(PavilionModel.id == club.pavilion_id).first()

    if not pavilion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pavilion not found")

    return pavilion

