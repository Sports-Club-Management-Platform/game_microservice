from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from models.game import Game as GameModel
from repositories.gameRepo import (create_game, delete_game, get_all_games,
                                   get_all_games_except_next, get_game_by_id,
                                   get_next_game, update_game)
from schemas.game import GameCreate, GameInDB, GameUpdate

router = APIRouter(tags=["Games"])

@router.post("/games", response_model=GameInDB)
def create_game_endpoint(new_game: GameCreate, db: Session = Depends(get_db)):
    return create_game(new_game, db)

@router.get("/games/{game_id}", response_model=GameInDB)
def get_game_by_id_endpoint(game_id: int, db: Session = Depends(get_db)):
    game = get_game_by_id(game_id, db)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@router.get("/games/next", response_model=GameInDB)
def get_next_game_endpoint(db: Session = Depends(get_db)):
    game = get_next_game(db)
    if game is None:
        raise HTTPException(status_code=404, detail="No upcoming game found")
    return game

@router.get("/games", response_model=List[GameInDB])
def get_all_games_endpoint(db: Session = Depends(get_db)):
    return get_all_games(db)

@router.get("/games/exclude-next", response_model=List[GameInDB])
def get_all_games_except_next_endpoint(db: Session = Depends(get_db)):
    return get_all_games_except_next(db)

@router.put("/games/{game_id}", response_model=GameInDB)
def update_game_endpoint(game_id: int, game_data: GameUpdate, db: Session = Depends(get_db)):
    return update_game(game_id, game_data, db)

@router.delete("/games/{game_id}")
def delete_game_endpoint(game_id: int, db: Session = Depends(get_db)):
    return delete_game(game_id, db)
