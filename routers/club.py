from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from db.database import get_db
from models.club import Club as ClubModel
from repositories.clubRepo import (create_club, delete_club, get_all_clubs,
                                   get_club_by_id, get_pavilion_by_club_id,
                                   update_club)
from schemas.club import ClubCreate, ClubInDB, ClubUpdate

router = APIRouter(tags=["Clubs"])

@router.post("/clubs", response_model=ClubInDB)
async def create_club_endpoint(name: str = Form(...), pavilion_id: int = Form(...), image: UploadFile = File(...), db: Session = Depends(get_db)):
    new_club = ClubCreate(name=name, pavilion_id=pavilion_id)
    return await create_club(new_club, image, db)

@router.get("/clubs/{club_id}", response_model=ClubInDB)
def get_club_by_id_endpoint(club_id: int, db: Session = Depends(get_db)):
    club = get_club_by_id(club_id, db)
    if club is None:
        raise HTTPException(status_code=404, detail="Club not found")
    return club

@router.get("/clubs", response_model=List[ClubInDB])
def get_all_clubs_endpoint(db: Session = Depends(get_db)):
    return get_all_clubs(db)

@router.put("/clubs/{club_id}", response_model=ClubInDB)
async def update_club_endpoint(club_id: int, name: Optional[str] = Form(None), pavilion_id: Optional[int] = Form(None), image: Optional[UploadFile] = File(None), db: Session = Depends(get_db)):
    club_data = ClubUpdate(name=name, pavilion_id=pavilion_id)
    return await update_club(club_id, club_data, image, db)

@router.delete("/clubs/{club_id}")
def delete_club_endpoint(club_id: int, db: Session = Depends(get_db)):
    return delete_club(club_id, db)

@router.get("/clubs/{club_id}/pavilion")
def get_pavilion_by_club_id_endpoint(club_id: int, db: Session = Depends(get_db)):
    return get_pavilion_by_club_id(club_id, db)