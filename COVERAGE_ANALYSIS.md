# Analisis de cobertura de tests

**Fecha:** 2026-06-29
**Comando:** `pytest tests/ -v --cov=aplicacion --cov-report=term-missing`
**Cobertura global:** 81 % (96 statements, 18 sin cubrir)

## Resumen del reporte

| Modulo | Stmts | Miss | Cobertura | Lineas sin cubrir |
|---|---|---|---|---|
| `aplicacion/__init__.py` | 0 | 0 | 100 % | — |
| `aplicacion/base_de_datos.py` | 12 | 4 | 67 % | 24-28 |
| `aplicacion/esquemas.py` | 19 | 0 | 100 % | — |
| `aplicacion/modelos.py` | 15 | 0 | 100 % | — |
| `aplicacion/principal.py` | 6 | 0 | 100 % | — |
| `aplicacion/rutas/__init__.py` | 0 | 0 | 100 % | — |
| `aplicacion/rutas/tareas.py` | 44 | 14 | 68 % | 30-33, 67, 124-129, 163-165 |

---

## Los 3 modulos con menor cobertura

### 1. `aplicacion/base_de_datos.py` — 67 % (4 statements sin cubrir)

**Lineas sin cubrir:** 24-28 (funcion `get_db`)

**Casos no cubiertos:**

La funcion generadora `get_db()` (lineas 24-28) nunca se ejecuta en los tests porque el fixture `client` la reemplaza con `override_get_db` via `app.dependency_overrides`. Esto significa que:

- La creacion de sesion con `SessionLocal()` de produccion no se prueba.
- El bloque `try/yield/finally` (yield de la sesion y cierre con `db.close()`) no se ejecuta.
- No se verifica que la sesion se cierre correctamente tras una peticion (rama `finally`).

**Estimacion de esfuerzo: Bajo**

Se necesita un unico test que instancie el generador directamente y verifique que produce una sesion valida y la cierra. Ejemplo conceptual:

```python
def test_get_db_yields_session_and_closes():
    gen = get_db()
    session = next(gen)
    assert session is not None
    gen.close()  # dispara el bloque finally
```

Tiempo estimado: ~15 minutos.

---

### 2. `aplicacion/rutas/tareas.py` — 68 % (14 statements sin cubrir)

**Lineas sin cubrir:** 30-33, 67, 124-129, 163-165

**Casos no cubiertos:**

| Lineas | Funcion / Endpoint | Descripcion |
|---|---|---|
| 30-33 | `get_task_or_404()` | Funcion auxiliar que busca una tarea por ID y lanza `HTTPException(404)`. No se invoca porque ninguno de los endpoints que la usan esta testeado. |
| 67 | `GET /tasks/{task_id}` | Endpoint `get_task`. No existe ningun test para obtener una tarea individual (ni happy path ni caso 404). |
| 124-129 | `PATCH /tasks/{task_id}` | Endpoint `update_task`. No existe ningun test para actualizacion parcial (ni happy path, ni 404, ni validacion de campos). |
| 163-165 | `DELETE /tasks/{task_id}` | Endpoint `delete_task`. No existe ningun test para eliminar una tarea individual (ni happy path ni caso 404). |

En resumen, **tres de los cinco endpoints CRUD carecen de tests por completo** (`GET /{id}`, `PATCH /{id}`, `DELETE /{id}`). Esto deja sin cubrir:

- Happy path de cada endpoint (crear tarea, luego consultarla/actualizarla/eliminarla).
- Caso de error 404 para IDs inexistentes en cada endpoint.
- Validaciones en `PATCH` (por ejemplo, actualizar con titulo de menos de 3 caracteres, cambiar estado a un valor invalido).

**Estimacion de esfuerzo: Bajo**

Son tests CRUD estandar que siguen el mismo patron que los existentes (`client.post`, `client.get`, etc.). Se necesitan al menos 6 tests nuevos (happy path + error para cada endpoint). El fixture `client` ya esta preparado.

Tiempo estimado: ~30-45 minutos.

---

### 3. `aplicacion/esquemas.py` — 100 % (0 statements sin cubrir)

> **Nota:** Este modulo tiene 100 % de cobertura de sentencias, pero ocupa el tercer lugar porque los demas modulos (`__init__.py`, `principal.py`, `modelos.py`, `rutas/__init__.py`) tambien estan al 100 % con menos logica de validacion relevante. `esquemas.py` es el mas significativo para analizar porque define la validacion de entrada de la API.

**Casos no cubiertos explicitamente (a pesar del 100 % de sentencias):**

Aunque todas las sentencias se ejecutan (los esquemas se importan y se usan indirectamente), no existen tests unitarios dedicados a verificar los esquemas Pydantic. Falta cobertura funcional de:

- **`TaskCreate`**: validacion de campos obligatorios (`title` requerido), valor por defecto de `status` (`pending`), comportamiento con `description=None`.
- **`TaskUpdate`**: verificar que todos los campos son opcionales (`exclude_unset=True`), que enviar un body vacio `{}` es valido.
- **`TaskResponse`**: verificar que `model_config = {"from_attributes": True}` permite construir el esquema desde un objeto ORM, y que todos los campos esperados estan presentes.
- **Validacion de enum**: enviar un `status` invalido (por ejemplo `"cancelled"`) y verificar que Pydantic lo rechaza antes de llegar al endpoint.

**Estimacion de esfuerzo: Bajo**

Son tests de validacion Pydantic directos, sin dependencia de base de datos ni servidor. Se instancian los esquemas con datos validos e invalidos y se verifican los resultados.

Tiempo estimado: ~20-30 minutos.

---

## Resumen de esfuerzo

| Modulo | Cobertura actual | Tests necesarios | Esfuerzo |
|---|---|---|---|
| `aplicacion/base_de_datos.py` | 67 % | 1 test | Bajo (~15 min) |
| `aplicacion/rutas/tareas.py` | 68 % | 6+ tests | Bajo (~45 min) |
| `aplicacion/esquemas.py` | 100 % (sentencias) | 4-6 tests | Bajo (~25 min) |

**Esfuerzo total estimado:** ~1.5 horas para cubrir todos los casos identificados.

**Impacto esperado:** Subir la cobertura global del 81 % al ~95 %+ al cubrir los endpoints `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` y la funcion `get_db`.
