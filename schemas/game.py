from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Game(BaseModel):
    jornada: int
    score_home: Optional[int] = None     # ignoring for now
    score_visitor: Optional[int] = None #ignoring for now
    date_time: datetime
    club_home_id: int      #int?
    club_visitor_id: int    #int?
    pavilion_id: int        #int?
    finished: Optional[bool] = None          #needed??

class GameCreate(Game):
    pass

class GameUpdate(Game):
    jornada: Optional[int] = None
    score_home: Optional[int] = None
    score_visitor: Optional[int] = None
    date_time: Optional[datetime] = None
    club_home_id: Optional[int] = None
    club_visitor_id: Optional[int] = None
    pavilion_id: Optional[int] = None
    finished: Optional[bool] = None

class GameInDB(Game):
    id: int


