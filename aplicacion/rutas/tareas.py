# Definición de los endpoints REST para la gestión de tareas

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aplicacion.base_de_datos import get_db
from aplicacion.esquemas import TaskCreate, TaskResponse, TaskUpdate
from aplicacion.modelos import Task, TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_or_404(task_id: int, db: Session) -> Task:
    """Busca una tarea por su identificador y lanza 404 si no existe.

    Args:
        task_id: Identificador único de la tarea.
        db: Sesión activa de SQLAlchemy.

    Returns:
        Instancia del modelo ORM correspondiente a la tarea encontrada.

    Raises:
        HTTPException: Si no existe una tarea con el ``task_id`` proporcionado
            (código 404).
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.get("/", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    """Devuelve la lista completa de tareas almacenadas.

    Args:
        db: Sesión activa de SQLAlchemy inyectada por FastAPI.

    Returns:
        Lista de tareas serializadas. Devuelve una lista vacía si no hay tareas.
    """
    return db.query(Task).all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Devuelve una tarea individual identificada por su ID.

    Args:
        task_id: Identificador único de la tarea a obtener.
        db: Sesión activa de SQLAlchemy inyectada por FastAPI.

    Returns:
        Tarea serializada según el esquema de respuesta.

    Raises:
        HTTPException: Si no existe la tarea (código 404).
    """
    return get_task_or_404(task_id, db)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Crea una nueva tarea y la persiste en la base de datos.

    Args:
        payload: Esquema con los datos de la tarea a crear.
        db: Sesión activa de SQLAlchemy inyectada por FastAPI.

    Returns:
        Tarea recién creada serializada, incluyendo ``id`` y ``created_at``.

    Raises:
        HTTPException: Si el título tiene menos de 3 caracteres (código 422).
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


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    """Actualiza parcialmente una tarea existente.

    Solo se modifican los campos incluidos en el cuerpo de la petición;
    los campos omitidos conservan su valor actual.

    Args:
        task_id: Identificador único de la tarea a actualizar.
        payload: Esquema con los campos a modificar.
        db: Sesión activa de SQLAlchemy inyectada por FastAPI.

    Returns:
        Tarea actualizada serializada según el esquema de respuesta.

    Raises:
        HTTPException: Si no existe la tarea (código 404), si la tarea está
            completada (código 400), o si el título proporcionado tiene menos
            de 3 caracteres (código 422).
    """
    task = get_task_or_404(task_id, db)

    if task.status == TaskStatus.done:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede modificar una tarea completada",
        )

    if payload.title is not None and len(payload.title) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Title must be at least 3 characters long",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Elimina una tarea de la base de datos.

    Args:
        task_id: Identificador único de la tarea a eliminar.
        db: Sesión activa de SQLAlchemy inyectada por FastAPI.

    Raises:
        HTTPException: Si no existe la tarea (código 404).
    """
    task = get_task_or_404(task_id, db)
    db.delete(task)
    db.commit()
