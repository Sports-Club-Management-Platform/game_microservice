from typing import List, Optional

from sqlalchemy import (ARRAY, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)

from db.database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    jornada = Column(Integer, nullable=False)
    score_home = Column(Integer, nullable=True)
    score_visitor = Column(Integer, nullable=True)
    date_time = Column(DateTime, nullable=False)
    club_home_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    club_visitor_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    pavilion_id = Column(Integer, ForeignKey("pavilions.id"), nullable=False)
    finished = Column(Boolean, nullable=False, default=False)

