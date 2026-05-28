# Tests para los endpoints REST de tareas

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# Motor en memoria con StaticPool para aislar cada ejecución de tests
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def client():
    """Crea las tablas, inyecta la sesión de prueba y limpia al terminar."""
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


# ── GET /tasks/status/{status} ─────────────────────────────────────────


def test_list_tasks_by_status_returns_filtered_results(client):
    """Devuelve solo las tareas cuyo estado coincide con el solicitado."""
    client.post("/tasks/", json={"title": "Tarea pendiente"})
    client.post(
        "/tasks/",
        json={"title": "Tarea en progreso", "status": "in_progress"},
    )
    client.post(
        "/tasks/",
        json={"title": "Tarea terminada", "status": "done"},
    )

    resp = client.get("/tasks/status/pending")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Tarea pendiente"
    assert data[0]["status"] == "pending"


def test_list_tasks_by_status_returns_empty_when_no_matches(client):
    """Devuelve lista vacía si no hay tareas con ese estado."""
    client.post("/tasks/", json={"title": "Tarea pendiente"})

    resp = client.get("/tasks/status/done")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_tasks_by_status_invalid_status(client):
    """Devuelve 422 cuando el estado no pertenece al enum TaskStatus."""
    resp = client.get("/tasks/status/invalid_status")
    assert resp.status_code == 422
    assert "detail" in resp.json()
