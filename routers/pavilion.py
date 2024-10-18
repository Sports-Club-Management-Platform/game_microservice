from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from db.database import get_db
from models.pavilion import Pavilion as PavilionModel
from repositories.pavilionRepo import (create_pavilion, delete_pavilion,
                                       get_pavilion_by_id, update_pavilion)
from schemas.pavilion import CreatePavilion, PavilionInDB, UpdatePavilion

router = APIRouter(tags=["Pavilions"])

@router.post("/pavilions", response_model=PavilionInDB)
async def create_pavilion_endpoint(new_pavilion: CreatePavilion, image: UploadFile, db: Session = Depends(get_db)):
    return await create_pavilion(new_pavilion, image, db)

@router.get("/pavilions/{pavilion_id}", response_model=PavilionInDB)
def get_pavilion_by_id_endpoint(pavilion_id: int, db: Session = Depends(get_db)):
    pavilion = get_pavilion_by_id(pavilion_id, db)
    if pavilion is None:
        raise HTTPException(status_code=404, detail="Pavilion not found")
    return pavilion

@router.put("/pavilions/{pavilion_id}", response_model=PavilionInDB)
async def update_pavilion_endpoint(pavilion_id: int, pavilion_data: UpdatePavilion, image: Optional[UploadFile] = File(None), db: Session = Depends(get_db)):
    return await update_pavilion(pavilion_id, pavilion_data, image, db)

@router.delete("/pavilions/{pavilion_id}")
def delete_pavilion_endpoint(pavilion_id: int, db: Session = Depends(get_db)):
    return delete_pavilion(pavilion_id, db)
