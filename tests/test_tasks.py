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


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Recrea las tablas antes de cada test para garantizar aislamiento."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    """Cliente HTTP para interactuar con la API en los tests."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# POST /tasks/ — Creación de tareas
# ---------------------------------------------------------------------------


def test_create_task_success(client):
    """POST con título válido debe crear la tarea y devolver 201."""
    response = client.post("/tasks/", json={"title": "Nueva tarea"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Nueva tarea"
    assert data["status"] == "pending"
    assert data["description"] is None
    assert "id" in data
    assert "created_at" in data


def test_create_task_with_all_fields(client):
    """POST con todos los campos debe respetar los valores proporcionados."""
    payload = {
        "title": "Tarea completa",
        "description": "Descripción de prueba",
        "status": "in_progress",
    }
    response = client.post("/tasks/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Tarea completa"
    assert data["description"] == "Descripción de prueba"
    assert data["status"] == "in_progress"


def test_create_task_short_title_returns_422(client):
    """POST con título de menos de 3 caracteres debe devolver 422."""
    response = client.post("/tasks/", json={"title": "AB"})
    assert response.status_code == 422
    assert response.json()["detail"] == "Title must be at least 3 characters long"


def test_create_task_empty_title_returns_422(client):
    """POST con título vacío debe devolver 422."""
    response = client.post("/tasks/", json={"title": ""})
    assert response.status_code == 422
    assert response.json()["detail"] == "Title must be at least 3 characters long"


# ---------------------------------------------------------------------------
# GET /tasks/ — Listado de tareas
# ---------------------------------------------------------------------------


def test_list_tasks_empty(client):
    """GET /tasks/ sin tareas creadas debe devolver lista vacía."""
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_returns_all(client):
    """GET /tasks/ debe devolver todas las tareas creadas."""
    client.post("/tasks/", json={"title": "Tarea uno"})
    client.post("/tasks/", json={"title": "Tarea dos"})
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# GET /tasks/{task_id} — Obtener tarea por ID
# ---------------------------------------------------------------------------


def test_get_task_success(client):
    """GET /tasks/{id} con ID existente debe devolver la tarea."""
    create_resp = client.post("/tasks/", json={"title": "Tarea de prueba"})
    task_id = create_resp.json()["id"]
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Tarea de prueba"


def test_get_task_not_found_returns_404(client):
    """GET /tasks/{id} con ID inexistente debe devolver 404."""
    response = client.get("/tasks/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# ---------------------------------------------------------------------------
# PATCH /tasks/{task_id} — Actualización parcial
# ---------------------------------------------------------------------------


def test_patch_task_success(client):
    """PATCH con campos válidos debe actualizar solo los campos enviados."""
    create_resp = client.post("/tasks/", json={"title": "Original"})
    task_id = create_resp.json()["id"]
    response = client.patch(
        f"/tasks/{task_id}", json={"title": "Modificada"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Modificada"


def test_patch_task_status_change(client):
    """PATCH puede cambiar el estado de una tarea no completada."""
    create_resp = client.post("/tasks/", json={"title": "Tarea activa"})
    task_id = create_resp.json()["id"]
    response = client.patch(
        f"/tasks/{task_id}", json={"status": "in_progress"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_patch_task_not_found_returns_404(client):
    """PATCH sobre tarea inexistente debe devolver 404."""
    response = client.patch("/tasks/999", json={"title": "Nuevo"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_patch_done_task_returns_400(client):
    """PATCH sobre una tarea con estado done debe devolver 400."""
    response = client.post(
        "/tasks/", json={"title": "Tarea finalizada", "status": "done"}
    )
    assert response.status_code == 201
    task_id = response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}", json={"title": "Nuevo titulo"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede modificar una tarea completada"


def test_patch_task_short_title_returns_422(client):
    """PATCH con título de menos de 3 caracteres debe devolver 422."""
    create_resp = client.post("/tasks/", json={"title": "Tarea válida"})
    task_id = create_resp.json()["id"]
    response = client.patch(f"/tasks/{task_id}", json={"title": "AB"})
    assert response.status_code == 422
    assert response.json()["detail"] == "Title must be at least 3 characters long"


# ---------------------------------------------------------------------------
# DELETE /tasks/{task_id} — Eliminación de tarea
# ---------------------------------------------------------------------------


def test_delete_task_success(client):
    """DELETE con ID existente debe eliminar la tarea y devolver 204."""
    create_resp = client.post("/tasks/", json={"title": "Para eliminar"})
    task_id = create_resp.json()["id"]
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204

    # Verificar que ya no existe
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404


def test_delete_task_not_found_returns_404(client):
    """DELETE con ID inexistente debe devolver 404."""
    response = client.delete("/tasks/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
