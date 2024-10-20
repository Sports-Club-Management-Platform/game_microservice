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
from db.database import get_db
from main import app
from models.club import Club
from models.pavilion import Pavilion
from schemas.club import ClubCreate, ClubUpdate

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

@pytest.fixture(name="test_club", scope="function")
def create_test_club(test_db):
    test_pavilion = Pavilion(
        name="Pavilion 1",
        location="Location 1",
        image="/path/to/image"
    )
    test_db.add(test_pavilion)
    test_db.commit()
    test_db.refresh(test_pavilion)
    logger.info(f"Pavilion ID: {test_pavilion.id}")


    test_club = Club(
        name="Club 1",
        image="/path/to/image",
        pavilion_id=test_pavilion.id
    )

    test_db.add(test_club)
    test_db.commit()
    test_db.refresh(test_club)
    logger.info(f"Club 1 ID: {test_club.id}")

    yield test_club

    # Then delete the clubs and pavilion
    logger.info(f"Deleting club 1 ID: {test_club.id}")
    test_db.delete(test_club)
    test_db.commit()

    logger.info(f"Deleting pavilion ID: {test_pavilion.id}")
    test_db.delete(test_pavilion)
    test_db.commit()

@pytest.mark.asyncio
@patch("crud.imageRepo.process_image")
async def test_create_club(mock_process_image, test_db, test_club):
    mock_process_image.return_value = "http://example.com/image.jpg"

    new_club = ClubCreate(
        name="Club 2",
        pavilion_id=test_club.pavilion_id
    )

    test_image = UploadFile(filename="test_image.jpg", file=BytesIO(b"fake image data"))

    created_club = await create_club(new_club, test_image, test_db)

    assert created_club.name == new_club.name
    assert created_club.image == "http://example.com/image.jpg"
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

