# Tests para los endpoints de tareas

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# Motor en memoria con StaticPool para aislamiento entre tests
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_create_task_title_too_short_returns_422(client):
    response = client.post("/tasks/", json={"title": "ab"})
    assert response.status_code == 422
    assert response.json()["detail"] == "Title must be at least 3 characters long"


def test_delete_all_tasks_clears_database(client):
    client.post("/tasks/", json={"title": "Tarea uno"})
    client.post("/tasks/", json={"title": "Tarea dos"})
    client.post("/tasks/", json={"title": "Tarea tres"})

    response = client.delete("/tasks/")
    assert response.status_code == 204

    listing = client.get("/tasks/")
    assert listing.status_code == 200
    assert listing.json() == []


def test_delete_all_tasks_on_empty_database_returns_204(client):
    response = client.delete("/tasks/")
    assert response.status_code == 204

    listing = client.get("/tasks/")
    assert listing.status_code == 200
    assert listing.json() == []


def test_create_task_default_priority_is_medium(client):
    response = client.post("/tasks/", json={"title": "Tarea sin prioridad"})
    assert response.status_code == 201
    assert response.json()["priority"] == "medium"


def test_create_task_with_explicit_priority(client):
    response = client.post("/tasks/", json={"title": "Tarea urgente", "priority": "high"})
    assert response.status_code == 201
    assert response.json()["priority"] == "high"


def test_create_task_with_invalid_priority_returns_422(client):
    response = client.post("/tasks/", json={"title": "Tarea rota", "priority": "urgent"})
    assert response.status_code == 422


def test_update_task_priority(client):
    create = client.post("/tasks/", json={"title": "Tarea actualizable"})
    task_id = create.json()["id"]
    assert create.json()["priority"] == "medium"

    response = client.patch(f"/tasks/{task_id}", json={"priority": "low"})
    assert response.status_code == 200
    assert response.json()["priority"] == "low"


def test_update_task_priority_invalid_returns_422(client):
    create = client.post("/tasks/", json={"title": "Tarea para error"})
    task_id = create.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"priority": "critical"})
    assert response.status_code == 422


def test_get_task_includes_priority(client):
    create = client.post("/tasks/", json={"title": "Tarea con prioridad", "priority": "low"})
    task_id = create.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["priority"] == "low"


def test_create_all_priority_levels(client):
    for level in ("low", "medium", "high"):
        response = client.post("/tasks/", json={"title": f"Tarea {level}", "priority": level})
        assert response.status_code == 201
        assert response.json()["priority"] == level
