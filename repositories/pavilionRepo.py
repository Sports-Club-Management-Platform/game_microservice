import os
from datetime import datetime

from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy import asc
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile

from db.database import get_db
from models.pavilion import Pavilion as PavilionModel
from repositories.imageRepo import create_image, update_image
from schemas.pavilion import CreatePavilion, UpdatePavilion


async def create_pavilion(new_pavilion: CreatePavilion, image: UploadFile, db: Session):
    if image is None:
        raise HTTPException(status_code=400, detail="Image file is required")

    new_pavilion_record = PavilionModel(
        name=new_pavilion.name,
        location=new_pavilion.location,
        location_link=new_pavilion.location_link,
        image=""  # Temporariamente vazio
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pavilion not found")
    
    return pavilion

async def update_pavilion(pavilion_id: int, pavilion_data: UpdatePavilion, image: UploadFile, db: Session):
    pavilion = db.query(PavilionModel).filter(PavilionModel.id == pavilion_id).first()
    
    if not pavilion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pavilion not found")
    
    if image is None:
        raise HTTPException(status_code=400, detail="Image file is required")

    img_path = await update_image(image, f"pavilions/{pavilion_id}")
    pavilion.image = f"/{img_path}"
    
    for key, value in pavilion_data.dict(exclude_unset=True).items():
        if key != "image":
            setattr(pavilion, key, value)
    
    db.commit()
    db.refresh(pavilion)
    
    return pavilion

def delete_pavilion(pavilion_id: int, db: Session):
    pavilion = db.query(PavilionModel).filter(PavilionModel.id == pavilion_id).first()

    if not pavilion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pavilion not found")
    
    if pavilion.image:
        # O campo 'image' armazena o caminho da imagem sem a parte 'static/'
        image_path = os.path.join("static", pavilion.image)
        if os.path.exists(image_path):
            os.remove(image_path)
        else:
            raise HTTPException(status_code=400, detail="Image file not found")
    
    db.delete(pavilion)
    db.commit()
    
    return {"detail": "Pavilion deleted successfully"}