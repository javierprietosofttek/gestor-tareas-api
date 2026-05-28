# Tests para los endpoints REST de tareas

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.modelos import TaskStatus
from aplicacion.principal import app

# Motor en memoria con StaticPool para aislar cada ejecución de tests
engine_test = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Fixture funcional: recrea las tablas antes de cada bloque de tests
Base.metadata.create_all(bind=engine_test)

client = TestClient(app)


# ─── Helpers ──────────────────────────────────────────────────────────

def _reset_db():
    """Elimina y recrea todas las tablas para aislar los tests."""
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)


def _create_task(title="Tarea de prueba", description=None, status="pending"):
    """Atajo para crear una tarea vía POST y devolver la respuesta JSON."""
    payload = {"title": title}
    if description is not None:
        payload["description"] = description
    if status != "pending":
        payload["status"] = status
    return client.post("/tasks/", json=payload)


# ═══════════════════════════════════════════════════════════════════════
#  GET /tasks/ — Listar tareas
# ═══════════════════════════════════════════════════════════════════════

class TestListTasks:
    def setup_method(self):
        _reset_db()

    def test_list_tasks_empty(self):
        """Devuelve lista vacía cuando no hay tareas."""
        response = client.get("/tasks/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_tasks_multiple(self):
        """Devuelve todas las tareas existentes."""
        _create_task(title="Primera")
        _create_task(title="Segunda")
        response = client.get("/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        titles = {t["title"] for t in data}
        assert titles == {"Primera", "Segunda"}


# ═══════════════════════════════════════════════════════════════════════
#  GET /tasks/{task_id} — Obtener tarea por id
# ═══════════════════════════════════════════════════════════════════════

class TestGetTask:
    def setup_method(self):
        _reset_db()

    def test_get_task_not_found(self):
        """404 cuando el id no existe."""
        response = client.get("/tasks/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_get_task_success(self):
        """Devuelve la tarea correcta cuando existe."""
        created = _create_task(title="Detalle").json()
        response = client.get(f"/tasks/{created['id']}")
        assert response.status_code == 200
        assert response.json()["title"] == "Detalle"
        assert response.json()["id"] == created["id"]

    def test_get_task_invalid_id_type(self):
        """422 cuando el id no es un entero válido."""
        response = client.get("/tasks/abc")
        assert response.status_code == 422

    def test_get_task_negative_id(self):
        """404 cuando se usa un id negativo (válido como int pero inexistente)."""
        response = client.get("/tasks/-1")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_get_task_zero_id(self):
        """404 cuando se usa id=0 (válido como int pero inexistente)."""
        response = client.get("/tasks/0")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"


# ═══════════════════════════════════════════════════════════════════════
#  POST /tasks/ — Crear tarea
# ═══════════════════════════════════════════════════════════════════════

class TestCreateTask:
    def setup_method(self):
        _reset_db()

    def test_create_task_missing_title(self):
        """422 cuando no se envía el título obligatorio."""
        response = client.post("/tasks/", json={})
        assert response.status_code == 422
        body = response.json()
        assert "detail" in body

    def test_create_task_null_title(self):
        """422 cuando el título es null."""
        response = client.post("/tasks/", json={"title": None})
        assert response.status_code == 422

    def test_create_task_invalid_status(self):
        """422 cuando se envía un estado no válido."""
        response = client.post("/tasks/", json={"title": "X", "status": "invalid"})
        assert response.status_code == 422
        body = response.json()
        assert "detail" in body

    def test_create_task_invalid_body(self):
        """422 cuando el cuerpo no es JSON válido."""
        response = client.post("/tasks/", content="no es json", headers={"Content-Type": "application/json"})
        assert response.status_code == 422

    def test_create_task_title_only(self):
        """Crea tarea con solo el título; estado por defecto es pending."""
        response = _create_task(title="Solo título")
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Solo título"
        assert data["description"] is None
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data

    def test_create_task_all_fields(self):
        """Crea tarea con todos los campos proporcionados."""
        response = client.post("/tasks/", json={
            "title": "Completa",
            "description": "Con descripción",
            "status": "in_progress",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Completa"
        assert data["description"] == "Con descripción"
        assert data["status"] == "in_progress"

    def test_create_task_each_status(self):
        """Permite crear tareas con cada uno de los estados válidos."""
        for st in TaskStatus:
            response = _create_task(title=f"Tarea {st.value}", status=st.value)
            assert response.status_code == 201
            assert response.json()["status"] == st.value

    def test_create_task_empty_string_title(self):
        """Acepta un título de cadena vacía (no hay validación de longitud mínima)."""
        response = _create_task(title="")
        assert response.status_code == 201
        assert response.json()["title"] == ""

    def test_create_task_extra_fields_ignored(self):
        """Campos extra en el cuerpo no causan error; se ignoran."""
        response = client.post("/tasks/", json={
            "title": "Extra",
            "unknown_field": "valor",
        })
        assert response.status_code == 201
        data = response.json()
        assert "unknown_field" not in data

    def test_create_task_returns_generated_id(self):
        """Cada tarea creada obtiene un id incremental único."""
        r1 = _create_task(title="A").json()
        r2 = _create_task(title="B").json()
        assert r1["id"] != r2["id"]

    def test_create_task_created_at_present(self):
        """La respuesta incluye created_at como cadena ISO no vacía."""
        data = _create_task(title="Fecha").json()
        assert data["created_at"] is not None
        assert len(data["created_at"]) > 0


# ═══════════════════════════════════════════════════════════════════════
#  PATCH /tasks/{task_id} — Actualizar tarea
# ═══════════════════════════════════════════════════════════════════════

class TestUpdateTask:
    def setup_method(self):
        _reset_db()

    def test_update_task_not_found(self):
        """404 cuando la tarea a actualizar no existe."""
        response = client.patch("/tasks/9999", json={"title": "No existe"})
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_update_task_invalid_status(self):
        """422 cuando se envía un estado no válido."""
        created = _create_task(title="Actualizar").json()
        response = client.patch(
            f"/tasks/{created['id']}",
            json={"status": "invalid_status"},
        )
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_update_task_invalid_id_type(self):
        """422 cuando el id no es un entero."""
        response = client.patch("/tasks/abc", json={"title": "X"})
        assert response.status_code == 422

    def test_update_task_title(self):
        """Actualiza solo el título sin afectar los demás campos."""
        created = _create_task(title="Original", description="Desc").json()
        response = client.patch(
            f"/tasks/{created['id']}",
            json={"title": "Modificado"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Modificado"
        assert data["description"] == "Desc"
        assert data["status"] == "pending"

    def test_update_task_status(self):
        """Actualiza solo el estado."""
        created = _create_task(title="Estado").json()
        response = client.patch(
            f"/tasks/{created['id']}",
            json={"status": "done"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "done"

    def test_update_task_description(self):
        """Actualiza solo la descripción."""
        created = _create_task(title="Desc").json()
        response = client.patch(
            f"/tasks/{created['id']}",
            json={"description": "Nueva descripción"},
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Nueva descripción"

    def test_update_task_multiple_fields(self):
        """Actualiza múltiples campos a la vez."""
        created = _create_task(title="Multi").json()
        response = client.patch(
            f"/tasks/{created['id']}",
            json={"title": "Nuevo", "status": "in_progress", "description": "D"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Nuevo"
        assert data["status"] == "in_progress"
        assert data["description"] == "D"

    def test_update_task_empty_payload(self):
        """PATCH sin campos no modifica nada; devuelve la tarea sin cambios."""
        created = _create_task(title="Intacta").json()
        response = client.patch(f"/tasks/{created['id']}", json={})
        assert response.status_code == 200
        assert response.json()["title"] == "Intacta"

    def test_update_task_set_description_to_null(self):
        """Permite establecer la descripción a null explícitamente."""
        created = _create_task(title="Nullable", description="Algo").json()
        response = client.patch(
            f"/tasks/{created['id']}",
            json={"description": None},
        )
        assert response.status_code == 200
        assert response.json()["description"] is None

    def test_update_task_preserves_created_at(self):
        """La fecha de creación no cambia tras actualizar."""
        created = _create_task(title="Fecha").json()
        response = client.patch(
            f"/tasks/{created['id']}",
            json={"title": "Actualizada"},
        )
        assert response.json()["created_at"] == created["created_at"]


# ═══════════════════════════════════════════════════════════════════════
#  DELETE /tasks/{task_id} — Eliminar tarea
# ═══════════════════════════════════════════════════════════════════════

class TestDeleteTask:
    def setup_method(self):
        _reset_db()

    def test_delete_task_not_found(self):
        """404 cuando la tarea a eliminar no existe."""
        response = client.delete("/tasks/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_delete_task_success(self):
        """Elimina la tarea y devuelve 204 sin cuerpo."""
        created = _create_task(title="Eliminar").json()
        response = client.delete(f"/tasks/{created['id']}")
        assert response.status_code == 204
        assert response.content == b""

    def test_delete_task_twice(self):
        """Eliminar la misma tarea dos veces devuelve 404 la segunda vez."""
        created = _create_task(title="Doble").json()
        first = client.delete(f"/tasks/{created['id']}")
        assert first.status_code == 204
        second = client.delete(f"/tasks/{created['id']}")
        assert second.status_code == 404
        assert second.json()["detail"] == "Task not found"

    def test_delete_task_invalid_id_type(self):
        """422 cuando el id no es un entero."""
        response = client.delete("/tasks/abc")
        assert response.status_code == 422

    def test_delete_task_removes_from_list(self):
        """Tras eliminar, la tarea ya no aparece en la lista."""
        created = _create_task(title="Desaparece").json()
        client.delete(f"/tasks/{created['id']}")
        tasks = client.get("/tasks/").json()
        ids = [t["id"] for t in tasks]
        assert created["id"] not in ids

    def test_delete_task_does_not_affect_others(self):
        """Eliminar una tarea no afecta a las demás."""
        t1 = _create_task(title="Sobrevive").json()
        t2 = _create_task(title="Eliminada").json()
        client.delete(f"/tasks/{t2['id']}")
        remaining = client.get("/tasks/").json()
        assert len(remaining) == 1
        assert remaining[0]["id"] == t1["id"]
