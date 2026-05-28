# Tests para los endpoints de tareas

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

# Fixture que recrea las tablas antes de cada test
import pytest


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)


def test_patch_done_task_returns_400(client):
    """PATCH sobre una tarea con estado done debe devolver 400."""
    # Crear tarea con estado done
    response = client.post(
        "/tasks/", json={"title": "Tarea finalizada", "status": "done"}
    )
    assert response.status_code == 201
    task_id = response.json()["id"]

    # Intentar modificar la tarea completada
    response = client.patch(
        f"/tasks/{task_id}", json={"title": "Nuevo titulo"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede modificar una tarea completada"
