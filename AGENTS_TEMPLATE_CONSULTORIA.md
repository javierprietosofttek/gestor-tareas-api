# Instrucciones para Devin — [NOMBRE DEL PROYECTO]

> **Template para proyectos de consultoría.**
> Adaptar las secciones marcadas con `[PLACEHOLDER]` antes de usar.

---

## Descripcion del proyecto

[BREVE DESCRIPCION DEL PROYECTO DEL CLIENTE Y SU PROPOSITO]

## Stack tecnologico

| Capa | Tecnologia |
|---|---|
| [CAPA] | [TECNOLOGIA Y VERSION] |

## Estructura del proyecto

```
[ESTRUCTURA DE CARPETAS RELEVANTE]
```

---

## Restricciones de seguridad y compliance

### Archivos que NUNCA se deben modificar sin aprobacion explicita

Devin **no debe** editar, eliminar ni renombrar los siguientes archivos o carpetas sin que el
responsable del proyecto lo autorice por escrito (mensaje en la sesion o comentario en el PR):

| Categoria | Patrones / rutas |
|---|---|
| Configuracion de produccion | `**/production.*`, `**/prod.*`, `.env.production`, `config/production/` |
| CI/CD | `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `bitbucket-pipelines.yml`, `.circleci/` |
| Infraestructura como codigo | `terraform/`, `pulumi/`, `cdk/`, `cloudformation/`, `ansible/`, `helm/`, `k8s/` |
| Secrets y vaults | `.env`, `.env.*`, `**/secrets.*`, `vault/`, `**/credentials.*` |
| Politicas de seguridad | `CODEOWNERS`, `branch-protection*.json`, `.github/settings.yml` |
| Configuracion de paquetes critica | `Dockerfile`, `docker-compose.prod.yml`, lockfiles de produccion |

> Si Devin necesita proponer un cambio en estos archivos, debe:
> 1. Documentar el cambio necesario en el cuerpo del PR.
> 2. Marcar el PR como **Draft**.
> 3. Solicitar revision explicita del responsable antes de sacarlo de Draft.

### Gestion de datos sensibles encontrados en el codigo

Si Devin encuentra datos sensibles (tokens, API keys, contraseñas, PII, datos de clientes reales)
durante su trabajo:

1. **No copiar, loguear ni exponer** el valor sensible en mensajes, PRs o commits.
2. **No eliminar** el dato sin autorizacion — puede ser intencional en entornos legacy.
3. **Notificar inmediatamente** al responsable del proyecto con:
   - Ruta del archivo y linea aproximada.
   - Tipo de dato sensible detectado (credencial, PII, etc.).
   - Sugerencia de remediacion (mover a variable de entorno, vault, etc.).
4. **No continuar** trabajando en ese archivo hasta recibir instrucciones.

### Protocolo ante credenciales expuestas

Si Devin detecta credenciales hardcodeadas o expuestas en el repositorio:

1. **STOP** — Detener cualquier accion que pueda propagar la credencial.
2. **No hacer commit** de ningun archivo que contenga la credencial.
3. **Informar al responsable** del proyecto inmediatamente con nivel de urgencia ALTA:
   - Que credencial se encontro (tipo, no el valor).
   - En que archivo y rama.
   - Si ya esta en el historial de git (fue commiteada previamente).
4. **Sugerir rotacion** de la credencial si hay evidencia de que fue expuesta publicamente.
5. **Proponer** la remediacion tecnica (`.gitignore`, secret manager, variable de entorno)
   solo despues de que el responsable confirme la accion.

---

## Politica de ramas y commits

### Ramas protegidas — restricciones absolutas

Devin **NUNCA** debe:
- Hacer push directo a `main`, `master`, `develop`, `release/*` ni `hotfix/*`.
- Forzar push (`--force` o `--force-with-lease`) a ramas protegidas.
- Eliminar ramas protegidas.
- Modificar reglas de proteccion de ramas.

Todo cambio debe llegar mediante Pull Request con al menos una aprobacion.

### Naming de ramas

Formato obligatorio para trazabilidad:

```
<tipo>/<ticket>-<descripcion-breve>
```

| Tipo | Uso |
|---|---|
| `feat/` | Nueva funcionalidad |
| `fix/` | Correccion de bug |
| `refactor/` | Refactorizacion sin cambio funcional |
| `docs/` | Solo documentacion |
| `test/` | Solo tests |
| `chore/` | Mantenimiento, dependencias, configs no criticas |

**Ejemplos:**
- `feat/PROJ-123-add-user-endpoint`
- `fix/PROJ-456-null-pointer-on-login`
- `docs/PROJ-789-update-api-readme`

> Si no hay sistema de tickets, usar un timestamp: `feat/20260623-add-user-endpoint`

### Naming de commits

Formato: `<tipo>(<scope>): <descripcion imperativa breve>`

```
feat(auth): add JWT token refresh endpoint
fix(tasks): handle null description on update
docs(readme): add deployment instructions
test(users): add edge cases for email validation
```

Reglas:
- Mensaje en **ingles** (o el idioma del equipo — definir aqui: `[IDIOMA]`).
- Primera linea max 72 caracteres.
- Si se necesita mas contexto, añadir cuerpo separado por linea en blanco.
- Un commit por cambio logico — no mezclar feat + fix en el mismo commit.
- Nunca hacer commit de archivos generados, caches, ni bases de datos locales.

---

## Descripcion de Pull Requests — contenido obligatorio

Cada PR creado por Devin **debe incluir** las siguientes secciones:

```markdown
## Resumen

[Que cambia y por que, en 2-3 oraciones max.]

## Cambios realizados

- [Lista concisa de cambios significativos]
- [Usar pseudo-diff o nombres de simbolos cuando aporte claridad]

## Tipo de cambio

- [ ] Nueva funcionalidad (feat)
- [ ] Correccion de bug (fix)
- [ ] Refactorizacion (refactor)
- [ ] Documentacion (docs)
- [ ] Tests (test)
- [ ] Mantenimiento (chore)

## Como probarlo

1. [Pasos para verificar manualmente el cambio]
2. [Comandos de test relevantes]

## Checklist

- [ ] Tests añadidos/actualizados
- [ ] Sin credenciales ni datos sensibles en el codigo
- [ ] Documentacion actualizada si aplica
- [ ] Lint/typecheck pasan sin errores
- [ ] No se modifican archivos protegidos sin aprobacion

## Notas adicionales

[Contexto extra, decisiones de diseño, limitaciones conocidas, etc.]
```

### Reglas adicionales para PRs:
- Si el PR modifica archivos protegidos, debe ser **Draft** hasta aprobacion explicita.
- Incluir capturas de pantalla o logs si el cambio es visual o afecta output.
- Referenciar el ticket/issue asociado si existe.
- No incluir cambios no relacionados con el objetivo del PR (no "drive-by fixes").

---

## Convenciones de codigo

### Idioma

- **Codigo** (variables, funciones, clases, rutas): `[IDIOMA — ej: ingles]`
- **Documentacion y comentarios**: `[IDIOMA — ej: español]`
- **Commits y PRs**: `[IDIOMA — ej: ingles]`

### Estilo

[DEFINIR GUIAS DE ESTILO DEL PROYECTO: linter, formatter, max line length, etc.]

### Tests

- Obligatorios para todo codigo nuevo.
- No conectar a servicios de produccion desde tests.
- Usar mocks/stubs para dependencias externas.

---

## Entorno y despliegue

### Variables de entorno

- Nunca hardcodear valores de configuracion que cambien entre entornos.
- Usar `.env.example` como plantilla documentada (sin valores reales).
- Los valores reales se proporcionan via secret manager o variables de sesion.

### Despliegue

- Devin **no ejecuta** despliegues a produccion.
- Devin puede proponer cambios de configuracion de despliegue, pero solo en PR Draft.
- Cualquier cambio de infraestructura requiere aprobacion explicita.

---

## Contacto y escalacion

| Rol | Contacto | Cuando escalar |
|---|---|---|
| Responsable tecnico | [NOMBRE / USUARIO] | Dudas de arquitectura, cambios protegidos |
| Seguridad | [NOMBRE / USUARIO] | Credenciales expuestas, datos sensibles |
| Product Owner | [NOMBRE / USUARIO] | Dudas de requisitos funcionales |

---

> **Nota:** Este archivo debe revisarse y actualizarse al inicio de cada proyecto de consultoria
> para reflejar las particularidades del cliente y su normativa interna.
