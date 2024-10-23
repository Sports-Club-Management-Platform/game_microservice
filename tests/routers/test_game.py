from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from db.database import get_db
from main import app
from models.game import Game as GameModel

client = TestClient(app)

@pytest.fixture(scope="module")
def mock_db():
    db = MagicMock(spec=Session)
    app.dependency_overrides[get_db] = lambda: db
    yield db

@pytest.fixture(autouse=True)
def reset_mock_db(mock_db):
    mock_db.reset_mock()

def create_game(mock_db):
    # Simulando um objeto Game do SQLAlchemy com ID
    game_record = GameModel(
        id=1,  # Certifique-se de que o ID é simulado corretamente
        jornada=1,
        score_home=None,
        score_visitor=None,
        date_time="2023-10-10T10:00:00",
        club_home_id=1,
        club_visitor_id=2,
        pavilion_id=1,
        finished=False
    )
    mock_db.add.return_value = None  # Não precisa retornar nada
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)  # Simulando o refresh para atribuir o ID

# Teste para criação de jogo
def test_create_game(mock_db):
    create_game(mock_db=mock_db)

    response = client.post(
        "/games",
        json={
            "jornada": 1,
            "score_home": None,
            "score_visitor": None,
            "date_time": "2023-10-10T10:00:00",
            "club_home_id": 1,
            "club_visitor_id": 2,
            "pavilion_id": 1,
            "finished": False
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1  # Verifique se o ID está correto
    assert data["jornada"] == 1
    assert data["score_home"] == None
    assert data["score_visitor"] == None
    assert data["date_time"] == "2023-10-10T10:00:00"
    assert data["club_home_id"] == 1
    assert data["club_visitor_id"] == 2
    assert data["pavilion_id"] == 1
    assert data["finished"] is False
    assert mock_db.commit.called is True

def test_get_game_by_id(mock_db):
    game_data = GameModel(id=1, jornada=1, score_home=None, score_visitor=None, date_time="2023-10-10T10:00:00", club_home_id=1, club_visitor_id=2, pavilion_id=1, finished=False)
    mock_db.query.return_value.filter.return_value.first.return_value = game_data

    response = client.get("/games/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["jornada"] == 1
    assert data["score_home"] == None
    assert data["score_visitor"] == None
    assert data["date_time"] == "2023-10-10T10:00:00"
    assert data["club_home_id"] == 1
    assert data["club_visitor_id"] == 2
    assert data["pavilion_id"] == 1
    assert data["finished"] is False
    assert mock_db.query.called is True

def test_get_game_by_id_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/games/999")  # ID que não existe
    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"

def test_get_next_game(mock_db):
    game_data = GameModel(id=1, jornada=1, score_home=None, score_visitor=None, date_time="2023-10-10T10:00:00", club_home_id=1, club_visitor_id=2, pavilion_id=1, finished=False)
    mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = game_data

    response = client.get("/games/next")

    print(response.json())  # Debugging statement to print the response JSON

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["jornada"] == 1
    assert data["score_home"] is None
    assert data["score_visitor"] is None
    assert data["date_time"] == "2023-10-10T10:00:00"
    assert data["club_home_id"] == 1
    assert data["club_visitor_id"] == 2
    assert data["pavilion_id"] == 1
    assert data["finished"] is False
    assert mock_db.query.called is True

def test_get_next_game_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    response = client.get("/games/next")
    assert response.status_code == 404
    assert response.json()["detail"] == "No upcoming game found"

def test_get_all_games(mock_db):
    game_data = [
        GameModel(id=1, jornada=1, score_home=2, score_visitor=1, date_time="2023-10-10T10:00:00", club_home_id=1, club_visitor_id=2, pavilion_id=1, finished=False),
        GameModel(id=2, jornada=2, score_home=3, score_visitor=2, date_time="2023-10-11T10:00:00", club_home_id=3, club_visitor_id=4, pavilion_id=2, finished=True)
    ]
    mock_db.query.return_value.all.return_value = game_data

    response = client.get("/games")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[1]["id"] == 2
    assert mock_db.query.called is True

def test_get_all_games_except_next(mock_db):
    next_game = GameModel(id=1, jornada=1, score_home=None, score_visitor=None, date_time="2025-10-10T10:00:00", club_home_id=1, club_visitor_id=2, pavilion_id=1, finished=False)
    game_data = [
        GameModel(id=2, jornada=2, score_home=None, score_visitor=None, date_time="2025-10-11T10:00:00", club_home_id=3, club_visitor_id=4, pavilion_id=2, finished=False)
    ]
    mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = next_game
    mock_db.query.return_value.filter.return_value.all.return_value = game_data

    response = client.get("/games/exclude-next")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 2
    assert mock_db.query.called is True

def test_update_game(mock_db):
    game_data = GameModel(id=1, jornada=1, score_home=2, score_visitor=1, date_time="2023-10-10T10:00:00", club_home_id=1, club_visitor_id=2, pavilion_id=1, finished=False)
    mock_db.query.return_value.filter.return_value.first.return_value = game_data

    response = client.put(
        "/games/1",
        json={
            "jornada": 2,
            "score_home": 3,
            "score_visitor": 2,
            "date_time": "2023-10-11T10:00:00",
            "club_home_id": 3,
            "club_visitor_id": 4,
            "pavilion_id": 2,
            "finished": True
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["jornada"] == 2
    assert data["score_home"] == 3
    assert data["score_visitor"] == 2
    assert data["date_time"] == "2023-10-11T10:00:00"
    assert data["club_home_id"] == 3
    assert data["club_visitor_id"] == 4
    assert data["pavilion_id"] == 2
    assert data["finished"] is True
    assert mock_db.commit.called is True

def test_update_game_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.put(
        "/games/999",
        json={
            "jornada": 2,
            "score_home": None,
            "score_visitor": None,
            "date_time": "2025-10-11T10:00:00",
            "club_home_id": 3,
            "club_visitor_id": 4,
            "pavilion_id": 2,
            "finished": True
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"

# Teste para eliminar um jogo
def test_delete_game(mock_db):
    game_data = GameModel(id=1, jornada=1, score_home=2, score_visitor=1, date_time="2023-10-10T10:00:00", club_home_id=1, club_visitor_id=2, pavilion_id=1, finished=False)
    mock_db.query.return_value.filter.return_value.first.return_value = game_data

    response = client.delete("/games/1")

    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Game deleted successfully"
    assert mock_db.delete.called is True
    assert mock_db.commit.called is True

def test_delete_game_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.delete("/games/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"