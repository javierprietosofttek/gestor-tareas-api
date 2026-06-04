# API de Gestión de Tareas

API REST para gestionar tareas construida con FastAPI y SQLAlchemy.

## Requisitos

- Python 3.12+
- pip

## Instalación

```bash
pip install -r requirements.txt
```

## Arrancar el servidor

```bash
uvicorn aplicacion.principal:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`.
Documentación interactiva (Swagger UI) en `http://127.0.0.1:8000/docs`.

## Ejecutar tests

```bash
python -m pytest tests/ -v
```

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/tasks/` | Lista todas las tareas |
| GET | `/tasks/{id}` | Obtiene una tarea por ID |
| POST | `/tasks/` | Crea una nueva tarea |
| PATCH | `/tasks/{id}` | Actualiza parcialmente una tarea |
| DELETE | `/tasks/{id}` | Elimina una tarea |

### Reglas de negocio

- El título de una tarea debe tener al menos 3 caracteres.
- No se puede modificar una tarea con estado `done`.

### Estados válidos

| Estado | Descripción |
|--------|-------------|
| `pending` | Pendiente (valor por defecto) |
| `in_progress` | En progreso |
| `done` | Completada |
