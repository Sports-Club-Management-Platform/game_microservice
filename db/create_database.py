import asyncio
import os

from fastapi import UploadFile
from sqlalchemy.orm import Session

from crud.imageRepo import create_image
from db.database import engine
from models.club import Club
from models.game import Game
from models.pavilion import Pavilion


def create_tables():
    Pavilion.metadata.create_all(bind=engine)
    Club.metadata.create_all(bind=engine)
    Game.metadata.create_all(bind=engine)
