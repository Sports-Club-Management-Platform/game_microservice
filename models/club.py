from typing import List, Optional

from sqlalchemy import (ARRAY, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)

from db.database import Base


class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True, nullable=False)
    image = Column(String(2048), nullable=False)
    pavilion_id = Column(Integer, ForeignKey("pavilions.id"), nullable=False)