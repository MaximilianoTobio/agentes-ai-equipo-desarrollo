# 🏗️ Arquitectura General del Sistema Multi-Agente v2

## 1. Visión General

El sistema está diseñado bajo una arquitectura **modular, distribuida y
resiliente**, compuesta por un **Orchestrator central en alta
disponibilidad** y un conjunto de **agentes especializados** que
colaboran entre sí mediante **Redis Streams** y almacenamiento
persistente en **Postgres + MinIO**.

El flujo general sigue el paradigma **"Issue → Code → Test → Review →
Merge"**, con etapas automatizadas, trazables y auditables.

------------------------------------------------------------------------

## 2. Diagrama General

``` mermaid
flowchart TD
    subgraph User["GitHub / Developer"]
        A[Issue o PR creado]
    end

    subgraph Orchestrator["Orchestrator (FastAPI, HA)"]
        O1[Task Queue (Redis Streams)]
        O2[Outbox Pattern (Postgres)]
        O3[Pair Coordinator]
        O4[Audit Trail / Agent Logs]
    end

    subgraph Agents["Agentes Especializados"]
        D[DevAgent 🧠]
        Q[QAAgent 🧪]
        R[ReviewAgent 👁️]
        F[RefactorAgent 🛠️]
        P[PairCoordinator 🤝]
    end

    subgraph Infra["Infraestructura Base"]
        DB[(Postgres + pgvector)]
        RS[(Redis Streams)]
        S3[(MinIO - Artefactos)]
        PX[(Prometheus / Grafana)]
        JG[(Jaeger Tracing)]
    end

    A -->|Webhook| Orchestrator
    Orchestrator -->|XADD| RS
    RS -->|Consume| D
    D -->|Propuesta + Tests| Q
    Q -->|Resultados + Lint| R
    R -->|Merge / PR| Orchestrator
    Orchestrator -->|Guardar| DB
    D & Q & R -->|Snapshots| S3
    F -->|Refactors Semanales| Orchestrator
    Orchestrator --> PX & JG
```

------------------------------------------------------------------------

## 3. Componentes Principales

### 3.1 Orchestrator (FastAPI)

-   Punto central del sistema (controlador de flujo y estado)
-   Expone endpoints REST y Webhooks para integración con GitHub
-   Procesa tareas mediante Redis Streams y coordina pares de agentes
-   Incluye lógica de:
    -   **Idempotencia de tareas**
    -   **Transactional Outbox**\
    -   **Pair Sessions (Driver/Navigator)**\
    -   **Token Budget Manager**\
    -   **Health Checks y métricas Prometheus**

### 3.2 Agentes Especializados

  ------------------------------------------------------------------------------
  Agente                Rol           Responsabilidades
  --------------------- ------------- ------------------------------------------
  **DevAgent**          Constructor   Generar código + tests cumpliendo TDD y
                                      DoD

  **QAAgent**           Tester        Ejecutar pruebas, validaciones SAST, lint
                                      y cobertura

  **ReviewAgent**       Supervisor    Revisar PR, aprobar o devolver con
                                      feedback

  **RefactorAgent**     Mantenedor    Detectar deuda técnica (SonarQube) y
                                      refactorizar

  **PairCoordinator**   Facilitador   Orquesta sesiones Driver/Navigator para
                                      pair programming
  ------------------------------------------------------------------------------

Cada agente es un microservicio independiente (contenedorizado) con su
propio log, métricas y espacio de trabajo.

------------------------------------------------------------------------

## 4. Flujos Principales

### 4.1 Ciclo Base de Tarea (End-to-End)

``` mermaid
sequenceDiagram
    participant GH as GitHub
    participant OR as Orchestrator
    participant D as DevAgent
    participant Q as QAAgent
    participant R as ReviewAgent
    participant DB as Postgres
    participant RS as Redis

    GH->>OR: Issue creado / webhook
    OR->>RS: XADD task: nueva tarea
    D->>RS: XREADGROUP obtiene tarea
    D->>Q: Propuesta + tests (TDD)
    Q->>R: Resultados, lint, cobertura
    R->>OR: PR aprobado o rechazado
    OR->>DB: Registrar estado + audit trail
    OR->>GH: Crear/mergear PR
```

------------------------------------------------------------------------

### 4.2 Pair Programming Automático

1.  Orchestrator crea `session_id` y bloquea la tarea
    (`pair:lock:<task_id>`).
2.  Driver (DevAgent) propone código inicial (`proposal`).
3.  Navigator (ReviewAgent o QAAgent) valida, comenta o sugiere patch.
4.  Se repite hasta **`accept` o `max_iters`**.
5.  Orchestrator consolida el resultado → crea branch
    `pair/<task_id>/iterN` y PR.
6.  Logs, snapshots y prompts se guardan en Postgres + MinIO.

------------------------------------------------------------------------

### 4.3 Refactorización Programada

-   RefactorAgent ejecuta cada lunes (cron)
-   Obtiene hotspots desde SonarQube
-   Genera issues de refactor automáticos
-   Cada refactor sigue el ciclo completo (Dev + QA + Review)
-   Métricas: deuda técnica, complejidad, LOC modificadas

------------------------------------------------------------------------

## 5. Infraestructura Base

### 5.1 Contenedores Principales

  ------------------------------------------------------------------------
  Servicio             Tecnología               Descripción
  -------------------- ------------------------ --------------------------
  `orchestrator`       FastAPI + Uvicorn        Núcleo del sistema (API
                                                REST, lógica XP)

  `postgres`           PostgreSQL 15 + pgvector Persistencia
                                                estructurada + embeddings

  `redis`              Redis 7                  Mensajería asíncrona
                                                (Streams + Locks)

  `minio`              S3-compatible            Artefactos y snapshots

  `prometheus`         Go                       Métricas de sistema

  `grafana`            Web                      Dashboards

  `jaeger`             Go                       Distributed tracing

  `agents/*`           Python                   Módulos de IA
                                                especializados
  ------------------------------------------------------------------------

------------------------------------------------------------------------

### 5.2 Redes y Conectividad

-   `labstack_net` → comunicación entre servicios principales\
-   `labstack_monitoring` → Prometheus, Grafana, Jaeger\
-   DNS interno gestionado por Docker Swarm\
-   Traefik gestiona certificados TLS y balanceo HTTP

------------------------------------------------------------------------

### 5.3 Alta Disponibilidad (HA)

``` yaml
orchestrator:
  deploy:
    replicas: 3
    placement:
      max_replicas_per_node: 1
    update_config:
      parallelism: 1
      delay: 10s
    restart_policy:
      condition: on-failure
      delay: 5s
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

-   **3 réplicas activas** con fail-over automático\
-   Redis persistente y montado con `appendonly=yes`\
-   Postgres con backups automáticos en `/backups/postgres`\
-   MinIO replicado (1 primary, 1 mirror opcional)

------------------------------------------------------------------------

## 6. Comunicación y Sincronización

  ------------------------------------------------------------------------
  Medio                  Uso              Garantía
  ---------------------- ---------------- --------------------------------
  **Redis Streams**      Intercambio de   ACK explícito, no se pierden
                         tareas y         mensajes
                         mensajes entre   
                         agentes          

  **Transactional Outbox Garantía de      ACID + reintento automático
  (Postgres)**           entrega entre DB 
                         y Redis          

  **Webhooks GitHub**    Integración con  HTTP 200 + retries
                         repos y PRs      

  **MinIO**              Almacenamiento   Persistente + versionado
                         de artefactos    

  **Prometheus / Grafana Observabilidad   Alertas + trazas distribuidas
  / Jaeger**                              
  ------------------------------------------------------------------------

------------------------------------------------------------------------

## 7. Auditoría y Logs

-   Cada agente registra:

    -   `session_id`, `task_id`, `iter`, `patch_hash`
    -   `tests_result`, `token_usage`, `coverage`

-   Orchestrator registra:

    -   Entradas del outbox\
    -   Eventos XP (pairing, tests, merges)

-   Todos los logs se centralizan en `agent_logs` (Postgres)

-   Snapshots de código en MinIO (`pair_session/<id>/iter_X.tar.gz`)

-   Audit trail particionado mensual:

    ``` sql
    CREATE TABLE audit_trail_2025_10 PARTITION OF audit_trail
        FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
    ```

------------------------------------------------------------------------

## 8. Diagramas de Datos Simplificados

``` mermaid
erDiagram
    TASKS ||--o{ AGENT_LOGS : "produce"
    AGENT_LOGS ||--o{ OUTBOX_EVENTS : "publica"
    OUTBOX_EVENTS ||--o{ REDIS_STREAMS : "emite"
    AGENT_LOGS ||--o{ MINIO_ARTIFACTS : "guarda"
    AUDIT_TRAIL ||--o{ TASKS : "registra"
```

------------------------------------------------------------------------

## 9. Escalabilidad y Extensión

-   **Escalabilidad horizontal:** cualquier agente puede añadirse en
    paralelo.
-   **Compatibilidad con microservicios externos:** API REST y colas
    estándar.
-   **Extensión:** nuevos agentes (e.g., DocAgent, POAgent) pueden
    integrarse declarando un rol en el Orchestrator.
-   **Failover:** si un agente falla, Redis reasigna la tarea.

------------------------------------------------------------------------

## 10. Estado Actual y Roadmap

**Estado actual:** MVP funcional (v2) con mejoras de resiliencia y
trazabilidad.\
**Siguiente fase:** Sprint 1 (XP Compliance + Observabilidad).

------------------------------------------------------------------------

**Versión:** v2.0 --- Octubre 2025\
**Autor:** Equipo de Ingeniería -- Proyecto Agentes AI
