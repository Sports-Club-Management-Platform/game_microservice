import logging
from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.mysql import MySqlContainer

from crud.clubRepo import (create_club, delete_club, get_all_clubs,
                           get_club_by_id, get_pavilion_by_club_id,
                           update_club)
from crud.gameRepo import (create_game, delete_game, get_all_games,
                           get_all_games_except_next, get_game_by_id,
                           get_next_game, update_game)
from crud.pavilionRepo import (create_pavilion, delete_pavilion,
                               get_pavilion_by_id, update_pavilion)
from db.database import get_db
from main import app
from models.club import Club
from models.game import Game
from models.pavilion import Pavilion
from schemas.club import ClubCreate, ClubUpdate
from schemas.game import GameCreate, GameUpdate
from schemas.pavilion import CreatePavilion, UpdatePavilion

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
    Pavilion.metadata.create_all(engine)
    Club.metadata.create_all(engine)
    Game.metadata.create_all(engine)

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

def create_test_pavilion(test_db):
    test_pavilion = Pavilion(
        name="Pavilion 1",
        location="Location 1",
        image="/path/to/image"
    )
    test_db.add(test_pavilion)
    test_db.commit()
    test_db.refresh(test_pavilion)
    logger.info(f"Pavilion ID: {test_pavilion.id}")
    return test_pavilion

def create_test_club(test_db, pavilion_id):
    test_club = Club(
        name="Club 1",
        image="/path/to/image",
        pavilion_id=pavilion_id
    )
    test_db.add(test_club)
    test_db.commit()
    test_db.refresh(test_club)
    logger.info(f"Club ID: {test_club.id}")
    return test_club

def create_test_game(test_db, club_home_id, club_visitor_id, pavilion_id):
    test_game = Game(
        jornada=1,
        score_home=None,
        score_visitor=None,
        date_time="2025-09-25T18:00:00",
        club_home_id=club_home_id,
        club_visitor_id=club_visitor_id,
        pavilion_id=pavilion_id,
        finished=False
    )
    test_db.add(test_game)
    test_db.commit()
    test_db.refresh(test_game)
    logger.info(f"Game ID: {test_game.id}")
    return test_game

@pytest.fixture(name="test_pavilion", scope="function")
def test_pavilion_fixture(test_db):
    test_pavilion = create_test_pavilion(test_db)
    yield test_pavilion
    logger.info(f"Deleting pavilion ID: {test_pavilion.id}")
    test_db.delete(test_pavilion)
    test_db.commit()

@pytest.fixture(name="test_club", scope="function")
def test_club_fixture(test_db, test_pavilion):
    test_club = create_test_club(test_db, test_pavilion.id)
    yield test_club
    logger.info(f"Deleting club ID: {test_club.id}")
    test_db.delete(test_club)
    test_db.commit()

@pytest.fixture(name="test_game", scope="function")
def test_game_fixture(test_db, test_club, test_pavilion):
    test_game = create_test_game(test_db, test_club.id, test_club.id, test_pavilion.id)
    yield test_game
    logger.info(f"Deleting game ID: {test_game.id}")
    test_db.delete(test_game)
    test_db.commit()

@pytest.mark.asyncio
@patch("crud.imageRepo.process_image")
async def test_create_pavilion(mock_process_image, test_db):
    mock_process_image.return_value = "https://example.com/image.jpg"

    new_pavilion = CreatePavilion(
        name="Pavilion 2",
        location="Location 2",
    )

    test_image = UploadFile(filename="test_image.jpg", file=BytesIO(b"fake image data"))

    created_pavilion = await create_pavilion(new_pavilion, test_image, test_db)

    assert created_pavilion.name == new_pavilion.name
    assert created_pavilion.location == new_pavilion.location
    assert created_pavilion.image == "https://example.com/image.jpg"

    test_db.delete(created_pavilion)
    test_db.commit()

def test_get_pavilion_by_id(test_db, test_pavilion):
    pavilion = get_pavilion_by_id(test_pavilion.id, test_db)

    assert pavilion.name == test_pavilion.name
    assert pavilion.location == test_pavilion.location
    assert pavilion.image == test_pavilion.image

@pytest.mark.asyncio
async def test_update_pavilion(test_db, test_pavilion):
    new_pavilion_data = UpdatePavilion(
        name="Pavilion 3",
        location="Location 3",
    )

    updated_pavilion = await update_pavilion(test_pavilion.id, new_pavilion_data, None, test_db)

    assert updated_pavilion.name == new_pavilion_data.name
    assert updated_pavilion.location == new_pavilion_data.location

def test_delete_pavilion(test_db, test_pavilion):
    pavilion = get_pavilion_by_id(test_pavilion.id, test_db)
    assert pavilion is not None

    response = delete_pavilion(test_pavilion.id, test_db)
    assert response == {"detail": "Pavilion deleted successfully"}

    with pytest.raises(HTTPException) as exc_info:
        get_pavilion_by_id(test_pavilion.id, test_db)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Pavilion not found"

@pytest.mark.asyncio
@patch("crud.imageRepo.process_image")
async def test_create_club(mock_process_image, test_db, test_pavilion):
    mock_process_image.return_value = "https://example.com/image.jpg"

    new_club = ClubCreate(
        name="Club 2",
        pavilion_id=test_pavilion.id
    )

    test_image = UploadFile(filename="test_image.jpg", file=BytesIO(b"fake image data"))

    created_club = await create_club(new_club, test_image, test_db)

    assert created_club.name == new_club.name
    assert created_club.image == "https://example.com/image.jpg"
    assert created_club.pavilion_id == new_club.pavilion_id

    test_db.delete(created_club)
    test_db.commit()

def test_get_club_by_id(test_db, test_club):
    club = get_club_by_id(test_club.id, test_db)

    assert club.name == test_club.name
    assert club.image == test_club.image
    assert club.pavilion_id == test_club.pavilion_id

def test_get_pavilion_by_club_id(test_db, test_club):
    pavilion = get_pavilion_by_club_id(test_club.id, test_db)

    assert pavilion.name == "Pavilion 1"
    assert pavilion.location == "Location 1"
    assert pavilion.image == "/path/to/image"

@pytest.mark.asyncio
async def test_update_club(test_db, test_club):
    new_club_data = ClubUpdate(
        name="Club 3"
    )

    updated_club = await update_club(test_club.id, new_club_data, None, test_db)

    assert updated_club.name == new_club_data.name

def test_delete_club(test_db, test_club):
    club = get_club_by_id(test_club.id, test_db)
    assert club is not None

    response = delete_club(test_club.id, test_db)
    assert response == {"detail": "Club deleted successfully"}

    with pytest.raises(HTTPException) as exc_info:
        get_club_by_id(test_club.id, test_db)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Club not found"

def test_create_game(test_db, test_club, test_pavilion):
    new_game = GameCreate(
        jornada=1,
        score_home=None,
        score_visitor=None,
        date_time="2025-09-25T18:00:00",
        club_home_id=test_club.id,
        club_visitor_id=test_club.id,
        pavilion_id=test_pavilion.id,
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
    game = get_game_by_id(test_game.id, test_db)
    assert game is not None

    response = delete_game(test_game.id, test_db)
    assert response == {"detail": "Game deleted successfully"}

    with pytest.raises(HTTPException) as exc_info:
        get_game_by_id(test_game.id, test_db)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Game not found"