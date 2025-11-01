# 01 — Arquitectura del MVP (orquestador + agentes)

# 🧩 LECCIÓN 01 — Arquitectura del MVP (orquestador + agentes)

## 🧠 1. Concepto base (en lenguaje claro)

El proyecto está compuesto por **agentes especializados** que trabajan coordinados por un **orquestador**.  
Podés imaginarlo como una _fábrica con distintas estaciones_, donde cada estación cumple una función específica.

| Estación                      | Agente o servicio      | Qué hace                                                             |
| ----------------------------- | ---------------------- | -------------------------------------------------------------------- |
| 🎯 Orquestador                | `FastAPI`              | Recibe las órdenes (issues, tareas) y decide qué agente las ejecuta. |
| 👨‍💻 DevAgent                   | Servicio de desarrollo | Genera o modifica código y tests.                                    |
| 🧪 QAAgent                    | Servicio de pruebas    | Corre los tests, busca fallos y propone fixes.                       |
| 🔍 ReviewAgent                | Servicio de revisión   | Lee el código generado y verifica estándares, seguridad y calidad.   |
| 🧭 POAgent / ScrumMasterAgent | Gestión y control      | Prioriza tareas, revisa métricas, mantiene el flujo ágil.            |
| 🧰 Infraestructura            | Redis, Postgres, MinIO | Proveen colas, base de datos, almacenamiento y logs.                 |

El **orquestador** actúa como “jefe de línea”: recibe una solicitud, la divide en subtareas y se las asigna a los agentes correspondientes.  
Cada agente es un **microservicio independiente**: tiene su propio entorno, tests, logs y puntos de control.  
Si un agente falla, el sistema puede reintentar o reasignar la tarea sin detener toda la cadena.

Cada bloque es un contenedor (Docker) que se comunica mediante **Redis (mensajería)** y **Postgres (registro y memoria)**.  
El flujo es totalmente automatizado, pero siempre deja un punto de revisión humana antes de fusionar código en producción.

## ⚙️ 2. Ejemplo visual (simple y mental)

## Imaginá el flujo completo de desarrollo dentro del sistema:

```bash
[GitHub Issue]
       │
       ▼
[Orquestador FastAPI]
       │
 ┌─────┴─────┐
 │           │
 ▼           ▼
DevAgent    QAAgent
 │           │
 ▼           ▼
Código   Pruebas CI
       │
       ▼
   ReviewAgent
       │
       ▼
  PR en GitHub
```

## 🧩 3. Aplicación real en mi proyecto

En esta arquitectura, los servicios ya definidos son:

- `FastAPI` → el **orquestador central**: asigna tareas a los agentes según el tipo de issue o milestone.
- `Redis` → **cola de mensajería** y **coordinador de eventos** (para que los agentes no se solapen).
- `Postgres` → **base de datos principal**, con `pgvector` para embeddings y memoria contextual.
- `MinIO` → **repositorio de artefactos**, guarda los archivos generados, logs o reportes.
- `GitHub Actions` → **pipeline CI/CD** que ejecuta tests, linters y despliegues automáticos.

Esto permite tener un **flujo de trabajo escalable y auditable**:

- Cada agente deja su traza (qué hizo, cuándo, con qué inputs).
- El orquestador puede asignar múltiples agentes Dev/QA en paralelo.
- Todo está conectado al tablero de GitHub (issues, milestones y PRs).

💡 _En otras palabras: esta arquitectura no solo crea software, sino que también se controla y mejora a sí misma._

---

## 🧭 4. Cómo lo pienso como fábrica

Imaginá que el proyecto entero es una **línea de montaje de software**:

1. El cliente o PO crea un **Issue** (pedido).
2. El **orquestador** lo lee y decide qué agentes deben intervenir.
3. El **DevAgent** escribe el código y los tests iniciales.
4. El **QAAgent** ejecuta los tests y analiza fallos.
5. El **ReviewAgent** revisa estilo, seguridad y buenas prácticas.
6. El **CICDAgent** (o GitHub Actions) corre la validación final.
7. Si todo pasa, se crea un **Pull Request** listo para revisión humana.

Así cada feature o fix sigue el mismo patrón, garantizando calidad y velocidad.

---

## 🧮 5. Claves técnicas a recordar

- Todo está **contenedorizado** (Docker).
- La comunicación es **asíncrona** (Redis → colas, pub/sub).
- La persistencia es **estructurada y semántica** (Postgres + pgvector).
- Las tareas son **trazables** (cada paso deja logs y estados).
- Los agentes están **aislados pero coordinados** (el orquestador los sincroniza).
- La revisión humana es **final y decisiva** (último filtro antes de mergear).

---

## 🧩 6. Resumen rápido

| Elemento                 | Rol        | Ejemplo                            |
| ------------------------ | ---------- | ---------------------------------- |
| Orquestador              | Coordina   | “Asigno esta tarea al DevAgent”    |
| DevAgent                 | Desarrolla | “Genero el código y tests”         |
| QAAgent                  | Valida     | “Ejecuto tests y reporto errores”  |
| ReviewAgent              | Revisa     | “Verifico seguridad y estilo”      |
| Postgres + Redis + MinIO | Infra      | “Guardo memoria, colas y archivos” |
| GitHub Actions           | CI/CD      | “Corro tests en cada PR”           |

---

## ✏️ 7. Ejercicio de comprensión

Dibuja (en papel o digital) cómo fluye una tarea desde que se crea un Issue en GitHub  
hasta que se hace el merge del PR.

Incluye:

- Qué servicios intervienen.
- Qué datos pasan (mensajes, tests, logs).
- Dónde interviene el humano (revisión final).

> ✅ Consejo: cuando termines tu dibujo, intenta explicarlo en voz alta.  
> Si podés explicarlo sin leer, ya entendiste la arquitectura de tu fábrica.

---

## Cómo lo aplicamos en mi proyecto

En mi proyecto, la arquitectura de agentes se traduce en varios **servicios concretos**, cada uno con una responsabilidad clara y endpoints definidos.  
Estos servicios están orquestados por `FastAPI` y se comunican a través de `Redis`, compartiendo datos persistentes en `Postgres` y artefactos en `MinIO`.

### 🧩 Servicios principales

| Servicio                                       | Descripción                                                                                      | Endpoint / Ejemplo                                                                           |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| **Orquestador (FastAPI)**                      | Coordina todo el flujo: recibe los issues, crea tareas y asigna agentes.                         | `POST /tasks` → crea una nueva tarea<br>`GET /status/{id}` → devuelve el estado de una tarea |
| **DevAgent**                                   | Genera o modifica código según la tarea recibida. Trabaja con TDD (primero tests, luego código). | `POST /generate` → recibe instrucciones y devuelve archivos `.py` o `.md`                    |
| **QAAgent**                                    | Ejecuta pruebas (`pytest`) y analiza errores o incumplimientos del DoD.                          | `POST /run-tests` → corre los tests y devuelve reporte JSON                                  |
| **ReviewAgent**                                | Analiza la calidad del código: estilo, seguridad, cobertura, secretos, convenciones.             | `POST /review` → evalúa código y devuelve observaciones                                      |
| **ScrumMasterAgent / POAgent**                 | Supervisa tareas, organiza el backlog y prioriza issues.                                         | `GET /metrics/sprint` → devuelve estadísticas del sprint                                     |
| **Infraestructura (Redis / Postgres / MinIO)** | Soporte base para la comunicación, persistencia y almacenamiento de resultados.                  | `redis://localhost:6379`<br>`postgresql://user:pass@db:5432/devdb`<br>`minio://artifacts/`   |

---

### ⚙️ Flujo simplificado entre servicios

1. **Orquestador** recibe un issue nuevo desde GitHub (webhook o API).
2. Crea una **tarea** y la envía al **DevAgent** vía Redis.
3. DevAgent genera código y tests, y los guarda en MinIO.
4. El **QAAgent** ejecuta los tests usando el código recién generado.
5. Si pasa, el **ReviewAgent** revisa calidad y convenciones.
6. Si todo está OK, se crea un **Pull Request** automático en GitHub.
7. El humano (vos o un revisor) aprueba o solicita cambios.

---

### 🧠 Ejemplo concreto (flujo real)

```bash
# 1. El orquestador recibe un issue desde GitHub
POST /tasks
{
  "issue_id": 42,
  "type": "feature",
  "description": "Crear endpoint /health para el servicio QAAgent"
}

# 2. Orquestador asigna al DevAgent
POST /assign
{
  "agent": "DevAgent",
  "task_id": "42",
  "instructions": "Generar endpoint /health en FastAPI y test asociado"
}

# 3. DevAgent responde con código
200 OK
{
  "file_created": "qa_agent/api/health.py",
  "test_created": "tests/test_health.py"
}

# 4. QAAgent corre los tests
POST /run-tests
{
  "repo": "qa_agent",
  "branch": "feature/health-endpoint"
}
```

🧩 Este flujo muestra cómo una tarea (issue) se transforma en código, se valida, se revisa y termina como un PR automáticamente.
✅ Conclusión

Esta capa de aplicación práctica demuestra que cada agente es una pieza intercambiable y auditable.
La arquitectura te permite agregar nuevos agentes (por ejemplo, DocsAgent o SecurityAgent) sin alterar el sistema base.
Cada uno expone endpoints REST estándar, usa Redis para mensajería y se valida con los mismos principios XP (TDD, DoD, refactor y revisión).
