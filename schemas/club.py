from typing import Optional

from pydantic import BaseModel


class Club(BaseModel):
    name: str
    pavilion_id: int

class ClubCreate(Club):
    # image: UploadFile
    pass

class ClubUpdate(Club):
    name: Optional[str] = None
    # image: Optional[UploadFile] = None
    pavilion_id: Optional[int] = None

class ClubInDB(Club):
    id: int
    image: str