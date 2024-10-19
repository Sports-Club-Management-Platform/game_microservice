import os
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy import asc
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile

from crud.imageRepo import create_image, update_image
from db.database import get_db
from models.club import Club as ClubModel
from models.pavilion import Pavilion as PavilionModel
from schemas.club import ClubCreate, ClubUpdate


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
        if key != "image":
            setattr(club, key, value)
    
    db.commit()
    db.refresh(club)
    
    return club

def delete_club(club_id: int, db: Session):
    club = db.query(ClubModel).filter(ClubModel.id == club_id).first()

    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")
    
    if club.image:
        # O campo 'image' armazena o caminho da imagem sem a parte 'static/'
        image_path = os.path.join("static", club.image)
        if os.path.exists(image_path):
            os.remove(image_path)
        else:
            raise HTTPException(status_code=400, detail="Image file not found")
    
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

