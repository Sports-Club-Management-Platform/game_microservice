from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from db.database import get_db
from main import app
from models.club import Club as ClubModel

client = TestClient(app)

@pytest.fixture(scope="module")
def mock_db():
    db = MagicMock(spec=Session)
    app.dependency_overrides[get_db] = lambda: db
    yield db

@pytest.fixture(autouse=True)
def reset_mock_db(mock_db):
    mock_db.reset_mock()

def create_club(mock_db):
    # Simulando um objeto Club do SQLAlchemy com ID
    club_record = ClubModel(
        id=1,  # Certifique-se de que o ID é simulado corretamente
        name="Test Club",
        pavilion_id=1,
        image="../images/test_club.jpg",
    )
    mock_db.add.return_value = None  # Não precisa retornar nada
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)  # Simulando o refresh para atribuir o ID

# Teste para criação de clube
@patch("crud.imageRepo.process_image")
def test_create_club(mock_process_image, mock_db):
    mock_process_image.return_value = "../images/test_club.jpg"

    create_club(mock_db=mock_db)

    response = client.post(
        "/clubs",
        data={
            "name": "Test Club",
            "pavilion_id": 1,
        },
        files={"image": ("test_club.jpg", b"test_image_content", "image/jpg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1  # Verifique se o ID está correto
    assert data["name"] == "Test Club"
    assert data["pavilion_id"] == 1
    assert data["image"] == "../images/test_club.jpg"
    assert mock_db.commit.called is True

# Teste para criação de clube sem imagem
def test_create_club_without_image(mock_db):
    response = client.post(
        "/clubs",
        data={
            "name": "Test Club Without Image",
            "pavilion_id": 1,
        }
    )

    assert response.status_code == 422
    data = response.json()
    assert data["detail"] == [{'input': None, 'loc': ['body', 'image'], 'msg': 'Field required', 'type': 'missing'}]

# Teste para criação de clube com dados inválidos
@patch("crud.imageRepo.process_image")
def test_create_club_invalid_data(mock_process_image, mock_db):
    mock_process_image.return_value = "../images/test_club.jpg"

    response = client.post(
        "/clubs",
        data={
            "name": None,  # Nome inválido
            "pavilion_id": 1,
        },
        files={"image": ("test_club.jpg", b"test_image_content", "image/jpg")},
    )

    assert response.status_code == 400 
    assert response.json()["detail"] == "Name and pavilion_id are required and cannot be empty"

def test_get_club_by_id(mock_db):
    club_data = ClubModel(id=1, name="Test Club", pavilion_id=1, image="path/to/image.jpg")
    mock_db.query.return_value.filter.return_value.first.return_value = club_data

    response = client.get("/clubs/1")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Club"
    assert data["pavilion_id"] == 1
    assert data["image"] == "path/to/image.jpg"
    assert mock_db.query.called is True

def test_get_club_by_id_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/clubs/999")  # ID que não existe
    assert response.status_code == 404
    assert response.json()["detail"] == "Club not found"

def test_get_all_clubs(mock_db):
    club_data = [
        ClubModel(id=1, name="Test Club 1", pavilion_id=1, image="path/to/image1.jpg"),
        ClubModel(id=2, name="Test Club 2", pavilion_id=2, image="path/to/image2.jpg")
    ]
    mock_db.query.return_value.all.return_value = club_data

    response = client.get("/clubs")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Test Club 1"
    assert data[1]["name"] == "Test Club 2"
    assert mock_db.query.called is True

# Teste para atualizar um clube
@patch("crud.imageRepo.update_image")
@patch("crud.imageRepo.process_image")
def test_update_club(mock_process_image, mock_update_image, mock_db):
    mock_process_image.return_value = "path/to/new_club_image.jpg"
    mock_update_image.return_value = "path/to/new_club_image.jpg"

    club_data = ClubModel(id=1, name="Test Club", pavilion_id=1, image="path/to/image.jpg")
    mock_db.query.return_value.filter.return_value.first.return_value = club_data

    response = client.put(
        "/clubs/1",
        data={
            "name": "Updated Club",
            "pavilion_id": 2,
        },
        files={"image": ("new_image.jpg", b"new_image_content", "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Club"
    assert data["pavilion_id"] == 2
    assert data["image"] == "/path/to/new_club_image.jpg"
    assert mock_db.commit.called is True

def test_update_club_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.put(
        "/clubs/999",
        data={
            "name": "Updated Club",
            "pavilion_id": 2,
        },
        files={"image": ("new_image.jpg", b"new_image_content", "image/jpeg")},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Club not found"

# Teste para deletar um clube
@patch("crud.clubRepo.s3_client.delete_object")
def test_delete_club(mock_s3_delete, mock_db):
    club_data = ClubModel(id=1, name="Test Club", pavilion_id=1, image="path/to/image.jpg")
    mock_db.query.return_value.filter.return_value.first.return_value = club_data

    response = client.delete("/clubs/1")

    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Club deleted successfully"
    assert mock_db.delete.called is True
    assert mock_db.commit.called is True
    assert mock_s3_delete.called is True

def test_delete_club_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.delete("/clubs/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Club not found"