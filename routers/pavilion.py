from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from crud.pavilionRepo import (create_pavilion, delete_pavilion,
                               get_pavilion_by_id, update_pavilion)
from db.database import get_db
from models.pavilion import Pavilion as PavilionModel
from schemas.pavilion import CreatePavilion, PavilionInDB, UpdatePavilion

router = APIRouter(tags=["Pavilions"])

@router.post("/pavilions", response_model=PavilionInDB)
async def create_pavilion_endpoint(name: str = Form(...), location: str = Form(...), location_link: Optional[str] = Form(None), image: UploadFile = File(...), db: Session = Depends(get_db)):
    new_pavilion = CreatePavilion(name=name, location=location, location_link=location_link)
    return await create_pavilion(new_pavilion, image, db)

@router.get("/pavilions/{pavilion_id}", response_model=PavilionInDB)
def get_pavilion_by_id_endpoint(pavilion_id: int, db: Session = Depends(get_db)):
    pavilion = get_pavilion_by_id(pavilion_id, db)
    if pavilion is None:
        raise HTTPException(status_code=404, detail="Pavilion not found")
    return pavilion

@router.put("/pavilions/{pavilion_id}", response_model=PavilionInDB)
async def update_pavilion_endpoint(pavilion_id: int, name: Optional[str] = Form(None), location: Optional[str] = Form(None), location_link: Optional[str] = Form(None), image: Optional[UploadFile] = File(None), db: Session = Depends(get_db)):
    pavilion_data = UpdatePavilion(name=name, location=location, location_link=location_link)
    return await update_pavilion(pavilion_id, pavilion_data, image, db)

@router.delete("/pavilions/{pavilion_id}")
def delete_pavilion_endpoint(pavilion_id: int, db: Session = Depends(get_db)):
    return delete_pavilion(pavilion_id, db)
