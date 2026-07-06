# Analisis de cobertura de tests

**Fecha:** 2026-07-06
**Cobertura global:** 81 % (96 statements, 18 sin cubrir)

Resultado completo de `pytest --cov=aplicacion --cov-report=term-missing`:

| Modulo | Stmts | Miss | Cover | Lineas sin cubrir |
|---|---|---|---|---|
| `aplicacion/__init__.py` | 0 | 0 | 100 % | -- |
| `aplicacion/base_de_datos.py` | 12 | 4 | **67 %** | 24-28 |
| `aplicacion/esquemas.py` | 19 | 0 | 100 % | -- |
| `aplicacion/modelos.py` | 15 | 0 | 100 % | -- |
| `aplicacion/principal.py` | 6 | 0 | 100 % | -- |
| `aplicacion/rutas/__init__.py` | 0 | 0 | 100 % | -- |
| `aplicacion/rutas/tareas.py` | 44 | 14 | **68 %** | 30-33, 67, 124-129, 163-165 |

---

## Los 3 modulos con menor cobertura

### 1. `aplicacion/base_de_datos.py` -- 67 % (4 lineas sin cubrir)

**Lineas no cubiertas:** 24-28 (funcion `get_db` completa)

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Que casos no estan cubiertos:**

- La funcion `get_db` nunca se ejecuta en los tests porque el fixture `client`
  la reemplaza con `override_get_db` (inyecta una sesion en memoria). Esto
  significa que el ciclo de vida de la sesion de produccion (apertura, yield,
  cierre) no se prueba directamente.

**Esfuerzo estimado: Bajo**

- Se puede escribir un test unitario que invoque el generador `get_db()`
  directamente, verificando que produce una sesion y que la cierra en el bloque
  `finally`. Para evitar tocar `tareas.db` (produccion), se puede hacer mock de
  `SessionLocal` o reasignar temporalmente el engine. Son ~10-15 lineas de test.

---

### 2. `aplicacion/rutas/tareas.py` -- 68 % (14 lineas sin cubrir)

**Lineas no cubiertas:**

| Lineas | Funcion / Endpoint | Descripcion |
|---|---|---|
| 30-33 | `get_task_or_404()` | Helper que busca una tarea por ID y lanza 404 si no existe |
| 67 | `GET /tasks/{task_id}` | Endpoint para obtener una tarea individual |
| 124-129 | `PATCH /tasks/{task_id}` | Endpoint para actualizar parcialmente una tarea |
| 163-165 | `DELETE /tasks/{task_id}` | Endpoint para eliminar una tarea individual |

**Que casos no estan cubiertos:**

- **`GET /tasks/{id}`**: No hay ningun test -- ni happy path (obtener tarea
  existente) ni error path (tarea inexistente -> 404).
- **`PATCH /tasks/{id}`**: No hay ningun test -- ni happy path (actualizar
  campos de una tarea) ni error path (tarea inexistente -> 404).
- **`DELETE /tasks/{id}`**: No hay ningun test -- ni happy path (eliminar tarea
  existente) ni error path (tarea inexistente -> 404).
- **`get_task_or_404`**: Al no probarse ninguno de los 3 endpoints anteriores,
  este helper compartido tampoco se ejecuta nunca.

En resumen: los unicos endpoints con tests son `POST /tasks/` (caso de error con
titulo corto), `DELETE /tasks/` (borrado masivo) y `GET /tasks/` (solo como
verificacion dentro de otros tests). Faltan tests para los 3 endpoints que
operan sobre una tarea individual.

**Esfuerzo estimado: Medio**

- Se necesitan ~6 tests nuevos (happy path + error path para cada endpoint),
  siguiendo la convencion de `AGENTS.md` que exige verificar codigo de estado
  HTTP **y** campo `detail`. Ejemplo de tests necesarios:
  1. `test_get_task_returns_existing_task` -- crea una tarea, la obtiene por ID,
     verifica campos.
  2. `test_get_task_not_found_returns_404` -- pide un ID inexistente, verifica
     404 y `detail`.
  3. `test_update_task_modifies_fields` -- crea tarea, la actualiza con PATCH,
     verifica cambios.
  4. `test_update_task_not_found_returns_404` -- PATCH a ID inexistente, verifica
     404 y `detail`.
  5. `test_delete_task_removes_single_task` -- crea tarea, la elimina, verifica
     204 y que ya no existe.
  6. `test_delete_task_not_found_returns_404` -- DELETE a ID inexistente, verifica
     404 y `detail`.
- Estimacion: ~60-80 lineas de codigo de test, ~30-45 minutos de trabajo.

---

### 3. `aplicacion/esquemas.py` -- 100 % (0 lineas sin cubrir)

> **Nota:** Solo 2 modulos tienen cobertura inferior al 100 %. El resto de
> modulos (`esquemas.py`, `modelos.py`, `principal.py`) estan al 100 %. Se
> incluye `esquemas.py` como tercer modulo por ser el de mayor complejidad
> logica entre los que ya estan cubiertos.

**Estado actual:** Totalmente cubierto por los tests existentes de forma
indirecta (los endpoints serializan/deserializan usando estos esquemas).

**Posibles mejoras (no reflejadas en cobertura):**

- Aunque la cobertura de lineas es 100 %, no hay tests unitarios dedicados a los
  esquemas Pydantic que verifiquen:
  - Validacion de campos opcionales vs. obligatorios en `TaskCreate`.
  - Que `TaskUpdate` acepte payloads parciales (`exclude_unset`).
  - Que `TaskResponse` serialice correctamente un objeto ORM (`from_attributes`).
  - Valores invalidos para el enum `TaskStatus`.

**Esfuerzo estimado: Bajo**

- Son tests de validacion pura de Pydantic, sin necesidad de servidor ni BD.
  ~4-5 tests, ~30 lineas, ~15 minutos.

---

## Resumen de prioridades

| Prioridad | Modulo | Cobertura actual | Esfuerzo | Impacto esperado |
|---|---|---|---|---|
| Alta | `aplicacion/rutas/tareas.py` | 68 % | Medio | +14 lineas cubiertas -> sube a ~100 % |
| Media | `aplicacion/base_de_datos.py` | 67 % | Bajo | +4 lineas cubiertas -> sube a 100 % |
| Baja | `aplicacion/esquemas.py` | 100 % | Bajo | Mejora robustez sin impacto en % |

**Recomendacion:** Priorizar los tests de `rutas/tareas.py` porque cubre los 3
endpoints sin probar y aporta el mayor incremento de cobertura (+14 lineas).
Despues, cubrir `base_de_datos.py` para llegar al 100 % en todos los modulos.
