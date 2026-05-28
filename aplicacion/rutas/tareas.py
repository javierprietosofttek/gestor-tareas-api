# Definición de los endpoints REST para la gestión de tareas

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aplicacion.base_de_datos import get_db
from aplicacion.esquemas import TaskCreate, TaskResponse, TaskUpdate
from aplicacion.modelos import Task

# Router con prefijo /tasks; agrupa todos los endpoints de tareas
router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_or_404(task_id: int, db: Session) -> Task:
    """Busca una tarea por su identificador y lanza 404 si no existe.

    Args:
        task_id (int): Identificador único de la tarea a buscar.
        db (Session): Sesión activa de SQLAlchemy para acceder a la base de datos.

    Returns:
        Task: Instancia del modelo ORM correspondiente a la tarea encontrada.

    Raises:
        HTTPException: Si no existe una tarea con el ``task_id`` proporcionado
            (código 404, detalle "Task not found").
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


# Devuelve la lista completa de tareas almacenadas
@router.get("/", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    """Devuelve la lista completa de tareas almacenadas.

    Args:
        db (Session): Sesión activa de SQLAlchemy inyectada por FastAPI.

    Returns:
        List[TaskResponse]: Lista de tareas serializadas según el esquema
            de respuesta. Devuelve una lista vacía si no hay tareas.
    """
    return []


# Devuelve una tarea por su identificador; 404 si no existe
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Devuelve una tarea individual identificada por su ID.

    Args:
        task_id (int): Identificador único de la tarea a obtener.
        db (Session): Sesión activa de SQLAlchemy inyectada por FastAPI.

    Returns:
        TaskResponse: Tarea serializada según el esquema de respuesta.

    Raises:
        HTTPException: Si no existe una tarea con el ``task_id`` proporcionado
            (código 404, detalle "Task not found").
    """
    return get_task_or_404(task_id, db)


# Crea una nueva tarea y devuelve el recurso creado con código 201
@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Crea una nueva tarea y la persiste en la base de datos.

    Args:
        payload (TaskCreate): Esquema con los datos de la tarea a crear.
            Solo el título es obligatorio; la descripción y el estado son
            opcionales.
        db (Session): Sesión activa de SQLAlchemy inyectada por FastAPI.

    Returns:
        TaskResponse: Tarea recién creada serializada según el esquema de
            respuesta, incluyendo los campos generados por la base de datos
            (``id`` y ``created_at``).

    Raises:
        HTTPException: Si el título tiene menos de 3 caracteres
            (código 422, detalle "Title must be at least 3 characters long").
    """
    if len(payload.title) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Title must be at least 3 characters long",
        )
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# Actualiza parcialmente una tarea; solo modifica los campos enviados en el cuerpo
@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    """Actualiza parcialmente una tarea existente.

    Solo se modifican los campos incluidos en el cuerpo de la petición;
    los campos omitidos conservan su valor actual.

    Args:
        task_id (int): Identificador único de la tarea a actualizar.
        payload (TaskUpdate): Esquema con los campos a modificar. Todos
            los campos son opcionales.
        db (Session): Sesión activa de SQLAlchemy inyectada por FastAPI.

    Returns:
        TaskResponse: Tarea actualizada serializada según el esquema de
            respuesta.

    Raises:
        HTTPException: Si no existe una tarea con el ``task_id`` proporcionado
            (código 404, detalle "Task not found").
    """
    task = get_task_or_404(task_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


# Elimina una tarea de la base de datos; devuelve 204 sin cuerpo
@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Elimina una tarea de la base de datos.

    Args:
        task_id (int): Identificador único de la tarea a eliminar.
        db (Session): Sesión activa de SQLAlchemy inyectada por FastAPI.

    Returns:
        None: Respuesta vacía con código de estado HTTP 204.

    Raises:
        HTTPException: Si no existe una tarea con el ``task_id`` proporcionado
            (código 404, detalle "Task not found").
    """
    task = get_task_or_404(task_id, db)
    db.delete(task)
    db.commit()
