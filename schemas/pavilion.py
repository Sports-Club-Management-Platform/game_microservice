from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Pavilion(BaseModel):
    name: str
    location: str
    location_link: Optional[str] = None
    image: str

class CreatePavilion(Pavilion):
    pass

class UpdatePavilion(Pavilion):
    name: Optional[str] = None
    location: Optional[str] = None
    location_link: Optional[str] = None
    image: Optional[str] = None

class PavilionInDB(Pavilion):
    id: int


    