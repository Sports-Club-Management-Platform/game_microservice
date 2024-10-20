import logging
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.mysql import MySqlContainer

from crud.gameRepo import (create_game, delete_game, get_all_games,
                           get_all_games_except_next, get_game_by_id,
                           get_next_game, update_game)
from db.database import get_db
from main import app
from models.club import Club
from models.game import Game
from models.pavilion import Pavilion
from schemas.game import GameCreate, GameUpdate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

my_sql_container = MySqlContainer(
    "mysql:8.0",
    root_password="test_root_password",
    dbname="test_db",
    username="test_username",
    password="test_password",
)


@pytest.fixture(name="session", scope="module")
def setup():
    # Start the MySQL container
    my_sql_container.start()
    connection_url = my_sql_container.get_connection_url()
    print(connection_url)
    engine = create_engine(connection_url, connect_args={})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Game.metadata.create_all(engine)
    Club.metadata.create_all(engine)
    Pavilion.metadata.create_all(engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    logger.info("running setup")
    yield SessionLocal
    logger.info("ending setup")
    my_sql_container.stop()


@pytest.fixture(name="test_db", scope="module")
def create_test_db(session):
    db = session()
    logger.info("creating test db")
    yield db
    logger.info("closing test db")
    db.close()

@pytest.fixture(name="test_game", scope="function")
def create_test_game(test_db):
    test_pavilion = Pavilion(
        name="Pavilion 1",
        location="Location 1",
        image="/path/to/image"
    )
    test_db.add(test_pavilion)
    test_db.commit()
    test_db.refresh(test_pavilion)
    logger.info(f"Pavilion ID: {test_pavilion.id}")


    test_club1 = Club(
        name="Club 1",
        image="/path/to/image",
        pavilion_id=test_pavilion.id
    )
    test_club2 = Club(
        name="Club 2",
        image="/path/to/image",
        pavilion_id=test_pavilion.id
    )
    test_db.add(test_club1)
    test_db.add(test_club2)
    test_db.commit()
    test_db.refresh(test_club1)
    test_db.refresh(test_club2)
    logger.info(f"Club 1 ID: {test_club1.id}")
    logger.info(f"Club 2 ID: {test_club2.id}")

    test_game = Game(
        jornada=1,
        score_home=None,
        score_visitor=None,
        date_time="2025-09-25T18:00:00",
        club_home_id=test_club1.id,
        club_visitor_id=test_club2.id,
        pavilion_id=test_pavilion.id,
        finished=False
    )
    test_db.add(test_game)
    test_db.commit()
    yield test_game
    # Delete the game first to avoid foreign key constraint issues
    logger.info(f"Deleting game ID: {test_game.id}")
    test_db.delete(test_game)
    test_db.commit()

    # Then delete the clubs and pavilion
    logger.info(f"Deleting club 1 ID: {test_club1.id}")
    logger.info(f"Deleting club 2 ID: {test_club2.id}")
    test_db.delete(test_club1)
    test_db.delete(test_club2)
    test_db.commit()

    logger.info(f"Deleting pavilion ID: {test_pavilion.id}")
    test_db.delete(test_pavilion)
    test_db.commit()

def test_create_game(test_db, test_game):
    new_game = GameCreate(
        jornada=1,
        score_home=None,
        score_visitor=None,
        date_time="2025-09-25T18:00:00",
        club_home_id=1,
        club_visitor_id=2,
        pavilion_id=1,
        finished=False
    )
    game = create_game(new_game, test_db)
    assert game.jornada == new_game.jornada
    assert game.score_home == new_game.score_home
    assert game.score_visitor == new_game.score_visitor
    assert game.date_time == new_game.date_time
    assert game.club_home_id == new_game.club_home_id
    assert game.club_visitor_id == new_game.club_visitor_id
    assert game.pavilion_id == new_game.pavilion_id
    assert game.finished == new_game.finished

    test_db.delete(game)
    test_db.commit()

def test_get_game_by_id(test_db, test_game):
    game = get_game_by_id(test_game.id, test_db)
    assert game.jornada == test_game.jornada
    assert game.score_home == test_game.score_home
    assert game.score_visitor == test_game.score_visitor
    assert game.date_time == test_game.date_time
    assert game.club_home_id == test_game.club_home_id
    assert game.club_visitor_id == test_game.club_visitor_id
    assert game.pavilion_id == test_game.pavilion_id
    assert game.finished == test_game.finished

def test_get_next_game(test_db, test_game):
    game = get_next_game(test_db)
    assert game.jornada == test_game.jornada
    assert game.score_home == test_game.score_home
    assert game.score_visitor == test_game.score_visitor
    assert game.date_time == test_game.date_time
    assert game.club_home_id == test_game.club_home_id
    assert game.club_visitor_id == test_game.club_visitor_id
    assert game.pavilion_id == test_game.pavilion_id
    assert game.finished == test_game.finished

def test_get_all_games(test_db, test_game):
    games = get_all_games(test_db)
    assert len(games) == 1
    game = games[0]
    assert game.jornada == test_game.jornada
    assert game.score_home == test_game.score_home
    assert game.score_visitor == test_game.score_visitor
    assert game.date_time == test_game.date_time
    assert game.club_home_id == test_game.club_home_id
    assert game.club_visitor_id == test_game.club_visitor_id
    assert game.pavilion_id == test_game.pavilion_id
    assert game.finished == test_game.finished

def test_get_all_games_except_next(test_db, test_game):
    games = get_all_games_except_next(test_db)
    assert len(games) == 0

def test_update_game(test_db, test_game):
    updated_game = GameUpdate(
        jornada= 2,
        club_home_id=test_game.club_visitor_id,
        club_visitor_id=test_game.club_home_id 
    )
    game = update_game(test_game.id, updated_game, test_db)
    assert game.jornada == updated_game.jornada
    assert game.club_home_id == updated_game.club_home_id
    assert game.club_visitor_id == updated_game.club_visitor_id

    test_db.delete(game)
    test_db.commit()

def test_delete_game(test_db, test_game):
    # Verifique se o jogo foi criado corretamente
    game = get_game_by_id(test_game.id, test_db)
    assert game is not None

    # Chame a função delete_game para deletar o jogo
    response = delete_game(test_game.id, test_db)
    assert response == {"detail": "Game deleted successfully"}

    # Verifique se o jogo foi deletado corretamente
    with pytest.raises(HTTPException) as exc_info:
        get_game_by_id(test_game.id, test_db)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Game not found"

