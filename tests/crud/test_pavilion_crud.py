import logging
from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.mysql import MySqlContainer

from crud.pavilionRepo import (create_pavilion, delete_pavilion,
                               get_pavilion_by_id, update_pavilion)
from db.database import get_db
from main import app
from models.pavilion import Pavilion
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

@pytest.fixture(name="test_pavilion", scope="function")
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

    yield test_pavilion

    logger.info(f"Deleting pavilion ID: {test_pavilion.id}")
    test_db.delete(test_pavilion)
    test_db.commit()

@pytest.mark.asyncio
@patch("crud.imageRepo.process_image")
async def test_create_pavilion(mock_process_image, test_db):
    mock_process_image.return_value = "http://example.com/image.jpg"

    new_pavilion = CreatePavilion(
        name="Pavilion 2",
        location="Location 2",
    )

    test_image = UploadFile(filename="test_image.jpg", file=BytesIO(b"fake image data"))

    created_pavilion = await create_pavilion(new_pavilion, test_image, test_db)

    assert created_pavilion.name == new_pavilion.name
    assert created_pavilion.location == new_pavilion.location
    assert created_pavilion.image == "http://example.com/image.jpg"

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