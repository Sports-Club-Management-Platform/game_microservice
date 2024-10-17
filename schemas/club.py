from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Club(BaseModel):
    name: str
    image: str
    pavilion_id: int

class ClubCreate(Club):
    pass

class ClubUpdate(Club):
    name = Optional[str] = None
    image = Optional[str] = None
    pavilion_id: Optional[int] = None

class ClubInDB(Club):
    id: int