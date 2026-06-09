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


def test_create_task_with_description(client):
    response = client.post(
        "/tasks/", json={"title": "Task with desc", "description": "A short description"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "A short description"


def test_create_task_description_max_length_returns_422(client):
    long_desc = "x" * 201
    response = client.post("/tasks/", json={"title": "Valid title", "description": long_desc})
    assert response.status_code == 422


def test_update_task_description_max_length_returns_422(client):
    create_resp = client.post("/tasks/", json={"title": "Valid title"})
    task_id = create_resp.json()["id"]
    long_desc = "x" * 201
    response = client.patch(f"/tasks/{task_id}", json={"description": long_desc})
    assert response.status_code == 422


def test_create_task_description_at_boundary(client):
    desc_200 = "a" * 200
    response = client.post("/tasks/", json={"title": "Boundary", "description": desc_200})
    assert response.status_code == 201
    assert response.json()["description"] == desc_200
