from datetime import datetime

from fastapi import Depends, HTTPException, status
from sqlalchemy import asc
from sqlalchemy.orm import Session

from db.database import get_db
from models.game import Game as GameModel
from schemas.game import GameCreate, GameUpdate

game_not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Game not found"
)


def create_game(new_game: GameCreate, db: Session):
    db_game = GameModel(
        jornada=new_game.jornada,
        score_home=new_game.score_home,
        score_visitor=new_game.score_visitor,
        date_time=new_game.date_time,
        club_home_id=new_game.club_home_id,
        club_visitor_id=new_game.club_visitor_id,
        pavilion_id=new_game.pavilion_id,
        finished=new_game.finished,
    )

    db.add(db_game)
    db.commit()
    db.refresh(db_game)

    return db_game


def get_game_by_id(game_id: int, db: Session):
    game = db.query(GameModel).filter(GameModel.id == game_id).first()

    if not game:
        raise game_not_found_exception

    return game


def get_next_game(db: Session):
    current_time = datetime.now()

    next_game = (
        db.query(GameModel)
        .filter(GameModel.date_time > current_time)
        .order_by(asc(GameModel.date_time))
        .first()
    )

    return next_game


def get_all_games(db: Session):
    games = db.query(GameModel).all()

    return games


def get_all_games_except_next(db: Session):
    next_game = get_next_game(db)

    games = db.query(GameModel).filter(GameModel.id != next_game.id).all()

    return games


def update_game(game_id: int, game_data: GameUpdate, db: Session):
    game = db.query(GameModel).filter(GameModel.id == game_id).first()

    if not game:
        raise game_not_found_exception

    for key, value in game_data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(game, key, value)

    db.commit()
    db.refresh(game)

    return game


def delete_game(game_id: int, db: Session):
    game = db.query(GameModel).filter(GameModel.id == game_id).first()

    if not game:
        raise game_not_found_exception

    db.delete(game)
    db.commit()

    return {"detail": "Game deleted successfully"}
