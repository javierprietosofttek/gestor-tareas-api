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


def test_complete_task_sets_status_to_done(client):
    create_resp = client.post("/tasks/", json={"title": "Tarea pendiente"})
    task_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "pending"

    response = client.patch(f"/tasks/{task_id}/complete")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "done"
    assert data["id"] == task_id


def test_complete_task_not_found_returns_404(client):
    response = client.patch("/tasks/9999/complete")
    assert response.status_code == 404
    assert response.json()["detail"] == "Resource not found"
