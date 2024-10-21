from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from db.database import get_db
from main import app
from models.pavilion import Pavilion as PavilionModel
from schemas.pavilion import CreatePavilion

client = TestClient(app)

@pytest.fixture(scope="module")
def mock_db():
    db = MagicMock(spec=Session)
    app.dependency_overrides[get_db] = lambda: db
    yield db

@pytest.fixture(autouse=True)
def reset_mock_db(mock_db):
    mock_db.reset_mock()


# Teste para criar um pavilhão
def create_pavilion(mock_db):
    # Simulando um objeto Pavilion do SQLAlchemy com ID
    pavilion_record = PavilionModel(
        id=1,  # Certifique-se de que o ID é simulado corretamente
        name="Test Pavilion",
        location="Test Location",
        image="../images/batata_pavilhao.jpg",
    )
    mock_db.add.return_value = None  # Não precisa retornar nada
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)  # Simulando o refresh para atribuir o ID

# Teste para criação de pavilhão
@patch("crud.pavilionRepo.create_image")
def test_create_pavilion(mock_create_image, mock_db):
    mock_create_image.return_value = "../images/batata_pavilhao.jpg"

    create_pavilion(mock_db=mock_db)

    response = client.post(
        "/pavilions",
        data={
            "name": "Test Pavilion",
            "location": "Test Location",
            "location_link": "https://google.com",
        },
        files={"image": ("batata_pavilhao.jpg", b"test_image_content", "image/jpg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1  # Verifique se o ID está correto
    assert data["name"] == "Test Pavilion"
    assert data["location"] == "Test Location"
    assert data["image"] == "../images/batata_pavilhao.jpg"
    assert mock_db.commit.called is True

# Teste para criação de pavilhão sem imagem
def test_create_pavilion_without_image(mock_db):
    response = client.post(
        "/pavilions",
        data={
            "name": "Test Pavilion Without Image",
            "location": "Test Location",
            "location_link": "https://google.com"
        }
    )

    assert response.status_code == 422
    data = response.json()
    assert data["detail"] == [{'input': None, 'loc': ['body', 'image'], 'msg': 'Field required', 'type': 'missing'}]

# Teste para criação de pavilhão com dados inválidos
@patch("crud.pavilionRepo.create_image")
def test_create_pavilion_invalid_data(mock_create_image, mock_db):
    mock_create_image.return_value = "../images/batata_pavilhao.jpg"

    response = client.post(
        "/pavilions",
        data={
            "name": None,  # Nome inválido
            "location": "Test Location",
            "location_link": "https://google.com"
        },
        files={"image": ("batata_pavilhao.jpg", b"test_image_content", "image/jpg")},
    )

    assert response.status_code == 400 
    assert response.json()["detail"] == "Name, location, and location link are required and cannot be empty"

def test_get_pavilion_by_id(mock_db):
    pavilion_data = PavilionModel(id=1, name="Test Pavilion", location="Test Location", image="path/to/image.jpg")
    mock_db.query.return_value.filter.return_value.first.return_value = pavilion_data

    response = client.get("/pavilions/1")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Pavilion"
    assert data["location"] == "Test Location"
    assert data["image"] == "path/to/image.jpg"
    assert mock_db.query.called is True

def test_get_pavilion_by_id_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/pavilions/999")  # ID que não existe
    assert response.status_code == 404
    assert response.json()["detail"] == "Pavilion not found"

# Teste para atualizar um pavilhão
@patch("crud.imageRepo.update_image")
@patch("crud.imageRepo.process_image")
def test_update_pavilion(mock_process_image, mock_update_image, mock_db):
    mock_process_image.return_value = "path/to/new_pavilion_image.jpg"
    mock_update_image.return_value = "path/to/new_pavilion_image.jpg"

    pavilion_data = PavilionModel(id=1, name="Test Pavilion", location="Test Location", image="path/to/image.jpg")
    mock_db.query.return_value.filter.return_value.first.return_value = pavilion_data

    response = client.put(
        "/pavilions/1",
        data={
            "name": "Updated Pavilion",
            "location": "Updated Location",
        },
        files={"image": ("new_image.jpg", b"new_image_content", "image/jpeg")},
    )

    print(response.json())  # Debugging statement to print the response JSON

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Pavilion"
    assert data["location"] == "Updated Location"
    assert data["image"] == "/path/to/new_pavilion_image.jpg"
    assert mock_db.commit.called is True


# Teste para eliminar um pavilhão
@patch("crud.pavilionRepo.s3_client.delete_object")
def test_delete_pavilion(mock_s3_delete, mock_db):
    pavilion_data = PavilionModel(id=1, name="Test Pavilion", location="Test Location", image="https://clubs-and-pavilions-photos-bucket.s3.amazonaws.com/pavilions/1/test_image.jpg")
    mock_db.query.return_value.filter.return_value.first.return_value = pavilion_data

    response = client.delete("/pavilions/1")

    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Pavilion deleted successfully"
    assert mock_db.delete.called is True
    assert mock_db.commit.called is True
    assert mock_s3_delete.called is True

def test_delete_pavilion_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.delete("/pavilions/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Pavilion not found"