from typing import List, Optional

from sqlalchemy import (ARRAY, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)

from db.database import Base


class Pavilion(Base):
    __tablename__ = "pavilions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True, nullable=False)
    location = Column(String(264), nullable=False)
    location_link = Column(String(2048), nullable=True)
    image = Column(String(2048), nullable=False)
