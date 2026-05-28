# ADR-001: Elección de SQLite como base de datos

## Estado

**Aceptado**

## Fecha

2025-05-28

## Contexto

La API de gestión de tareas necesita una base de datos relacional para almacenar tareas con sus atributos (título, descripción, estado y fecha de creación). El proyecto se concibe como una aplicación ligera de propósito interno, orientada a un volumen moderado de datos y un número reducido de usuarios concurrentes.

Requisitos clave que condicionan la decisión:

- **Simplicidad de despliegue**: evitar dependencias externas como servidores de base de datos independientes.
- **Facilidad de desarrollo**: que cualquier desarrollador pueda clonar el repositorio y arrancar la API sin configuración adicional.
- **Compatibilidad con SQLAlchemy 2.0**: el ORM elegido para el proyecto debe soportar el motor de base de datos sin adaptadores adicionales.
- **Soporte para tests aislados**: poder ejecutar la suite de tests con una base de datos en memoria, sin afectar datos reales.
- **Bajo coste operativo**: no requerir administración de servidores de base de datos ni licencias.

## Decisión

Se elige **SQLite** como motor de base de datos, utilizando un archivo local (`tareas.db`) para persistencia y conexiones en memoria con `StaticPool` para los tests.

### Razones principales

1. **Cero configuración**: SQLite no requiere instalar ni administrar un servidor de base de datos. El archivo `tareas.db` se crea automáticamente en la raíz del proyecto al iniciar la aplicación.
2. **Incluido en la biblioteca estándar de Python**: el módulo `sqlite3` viene integrado en Python 3.12+, lo que elimina dependencias externas a nivel de sistema.
3. **Compatibilidad nativa con SQLAlchemy**: el dialecto `sqlite:///` funciona sin instalar drivers adicionales, a diferencia de PostgreSQL (`psycopg2`) o MySQL (`mysqlclient`/`pymysql`).
4. **Tests con base de datos en memoria**: SQLite permite crear bases de datos en memoria (`sqlite://`) con `StaticPool`, lo que garantiza tests rápidos y completamente aislados.
5. **Portabilidad**: el archivo de base de datos es un único fichero que se puede copiar, respaldar o mover fácilmente entre entornos.
6. **Rendimiento adecuado**: para el volumen de datos y concurrencia esperados, SQLite ofrece un rendimiento más que suficiente sin la sobrecarga de un sistema cliente-servidor.

## Alternativas consideradas

### PostgreSQL

| Aspecto | Valoración |
|---|---|
| **Ventajas** | Sistema robusto y maduro con soporte completo de ACID. Excelente manejo de concurrencia mediante MVCC. Tipos de datos avanzados (JSON, arrays, hstore). Amplio ecosistema de extensiones (PostGIS, pg_trgm). Escalabilidad horizontal con réplicas de lectura. Soporte nativo de transacciones complejas y procedimientos almacenados. |
| **Inconvenientes** | Requiere instalar y administrar un servidor de base de datos independiente. Añade complejidad al despliegue y a la configuración del entorno de desarrollo. Necesita un driver adicional (`psycopg2` o `asyncpg`) que puede requerir dependencias del sistema (`libpq-dev`). Mayor consumo de recursos (memoria y CPU) incluso en reposo. Configuración de conexiones, usuarios y permisos necesaria antes del primer uso. |

### MySQL

| Aspecto | Valoración |
|---|---|
| **Ventajas** | Amplia adopción en la industria y gran comunidad. Buen rendimiento en operaciones de lectura intensiva. Herramientas maduras de administración (MySQL Workbench, phpMyAdmin). Soporte de replicación maestro-esclavo. Compatible con la mayoría de proveedores de hosting. |
| **Inconvenientes** | Requiere un servidor independiente, con la misma complejidad operativa que PostgreSQL. Necesita un driver adicional (`mysqlclient` o `pymysql`), lo que añade dependencias. Manejo de transacciones y bloqueos menos sofisticado que PostgreSQL. Algunas limitaciones en tipos de datos y en el cumplimiento estricto de SQL estándar. Licencia dual (GPL/comercial) que puede complicar ciertos escenarios de distribución. |

## Consecuencias

### Positivas

- **Arranque inmediato**: los desarrolladores pueden clonar el repositorio y ejecutar `uvicorn aplicacion.principal:app --reload` sin instalar ni configurar ningún servicio externo.
- **Pipeline de CI sencillo**: no se necesitan servicios adicionales (contenedores de base de datos, Docker Compose) para ejecutar los tests.
- **Mantenimiento mínimo**: no hay servidores de base de datos que monitorizar, actualizar o escalar.
- **Respaldo trivial**: basta con copiar el archivo `tareas.db` para obtener una copia completa de los datos.

### Negativas y riesgos a largo plazo

- **Concurrencia limitada**: SQLite utiliza bloqueos a nivel de archivo para escrituras. Si el proyecto evoluciona hacia múltiples usuarios concurrentes con escrituras frecuentes, el rendimiento se degradará.
- **Sin soporte de red nativo**: SQLite no soporta conexiones remotas. Si se necesita separar la aplicación del almacenamiento de datos (por ejemplo, en arquitecturas con múltiples instancias), será necesario migrar a otro motor.
- **Funcionalidades SQL reducidas**: SQLite no soporta de forma nativa `ALTER TABLE` completo, tipos de datos estrictos ni algunas funciones avanzadas disponibles en PostgreSQL o MySQL. Esto puede limitar futuras migraciones de esquema.
- **No apto para alta disponibilidad**: no existe un mecanismo integrado de replicación ni failover. En escenarios donde se requiera alta disponibilidad, habrá que migrar a PostgreSQL u otro sistema con soporte de réplicas.
- **Migración futura**: si las necesidades del proyecto crecen, será necesario cambiar de motor. Gracias al uso de SQLAlchemy como capa de abstracción, esta migración se limita principalmente a cambiar la URL de conexión y el driver, pero requerirá pruebas exhaustivas para garantizar compatibilidad de tipos y comportamiento.

### Plan de mitigación

- Mantener SQLAlchemy como capa de abstracción para facilitar una eventual migración.
- No utilizar funcionalidades específicas de SQLite en las consultas (dialectos, funciones propias).
- Documentar el umbral de concurrencia y volumen a partir del cual se recomienda evaluar la migración a PostgreSQL.
- Revisar esta decisión si el número de usuarios concurrentes supera las decenas o el volumen de datos supera los cientos de miles de registros.
