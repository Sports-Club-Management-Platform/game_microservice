from typing import Optional

from pydantic import BaseModel


class Pavilion(BaseModel):
    name: str
    location: str
    location_link: Optional[str] = None

class CreatePavilion(Pavilion):
    # image: UploadFile
    pass

class UpdatePavilion(Pavilion):
    name: Optional[str] = None
    location: Optional[str] = None
    location_link: Optional[str] = None
    # image: Optional[UploadFile] = None

class PavilionInDB(Pavilion):
    id: int
    image: str


    