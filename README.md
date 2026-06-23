# API de Gestión de Tareas

API REST construida con FastAPI y SQLAlchemy para gestionar tareas.

## Endpoints disponibles

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/tasks/` | Lista todas las tareas |
| GET | `/tasks/{id}` | Obtiene una tarea por id |
| POST | `/tasks/` | Crea una nueva tarea |
| PATCH | `/tasks/{id}` | Actualiza parcialmente una tarea |
| PATCH | `/tasks/{id}/complete` | Marca una tarea como completada (done) |
| DELETE | `/tasks/{id}` | Elimina una tarea |
| DELETE | `/tasks/` | Elimina todas las tareas |

## Arrancar la API

```bash
pip install -r requirements.txt
uvicorn aplicacion.principal:app --reload
```

## Ejecutar tests

```bash
pytest tests/ -v
```
