# ⚙️ Componentes Técnicos del Sistema Multi-Agente v2

> **Ubicación sugerida:** `/docs/v2/03_componentes_tecnicos.md`\
> **Propósito:** Describir los módulos principales del sistema, su
> arquitectura interna, relaciones, y las decisiones de diseño clave que
> sustentan la segunda versión del MVP.

------------------------------------------------------------------------

## 1. Visión General de los Componentes

El sistema está dividido en **seis módulos principales**, cada uno con
responsabilidades específicas y alta cohesión. Todos se comunican a
través de **Redis Streams** y comparten una base común en **Postgres +
MinIO**.

  -------------------------------------------------------------------------------------
  Componente            Tipo           Lenguaje / Stack     Descripción principal
  --------------------- -------------- -------------------- ---------------------------
  **Orchestrator**      Servicio       FastAPI (Python)     Coordina tareas, controla
                        central                             flujo XP, comunica agentes

  **DevAgent**          Agente         Python + OpenAI API  Genera código y tests (TDD)
                        autónomo                            

  **QAAgent**           Agente         Python + pytest +    Ejecuta pruebas y
                        autónomo       linters              validaciones

  **ReviewAgent**       Agente         Python + heurísticas Valida calidad, seguridad y
                        autónomo       XP                   estilo

  **RefactorAgent**     Agente         Python + SonarQube   Planifica y ejecuta
                        autónomo       API                  refactors automáticos

  **PairCoordinator**   Submódulo del  Python + Redis       Facilita sesiones de pair
                        Orchestrator   Streams              programming entre agentes
  -------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 2. Orchestrator

### 2.1 Rol Principal

El **Orchestrator** actúa como núcleo del sistema. Gestiona el ciclo
completo de vida de las tareas y coordina la comunicación entre los
agentes. Garantiza idempotencia, consistencia de datos y observabilidad.

### 2.2 Responsabilidades

-   Recepción de *issues* o *webhooks* de GitHub.\
-   Encolado de tareas en Redis Streams.\
-   Asignación de agentes según complejidad y disponibilidad.\
-   Supervisión de pair sessions.\
-   Registro de logs y métricas.\
-   Persistencia en Postgres con patrón **Transactional Outbox**.\
-   Exposición de endpoints REST `/health`, `/metrics`, `/api/tasks`,
    `/api/prs`.

### 2.3 Decisiones Arquitectónicas

  -----------------------------------------------------------------------
  Decisión                                  Motivo
  ----------------------------------------- -----------------------------
  Uso de FastAPI + Uvicorn                  Permite asincronía nativa,
                                            performance y tipado fuerte

  Redis Streams + ACK                       Fiabilidad de entrega
                                            garantizada

  Postgres + pgvector                       Persistencia + embeddings de
                                            contexto

  MinIO para artefactos                     S3-compatible, integrable con
                                            pipelines CI/CD

  Outbox Pattern                            Evita inconsistencias entre
                                            DB y colas

  Prometheus Exporter                       Observabilidad sin overhead
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 3. DevAgent

### 3.1 Rol

Es el **constructor del sistema**, encargado de traducir los criterios
de aceptación en código funcional y pruebas. Opera bajo un flujo
**estrictamente TDD**.

### 3.2 Responsabilidades

-   Analizar tareas y generar código mínimo funcional.\
-   Crear tests unitarios antes de la implementación.\
-   Cumplir Definition of Done (DoD): lint, coverage, logs.\
-   Enviar resultados al Orchestrator y QAAgent.

### 3.3 Interacción

1.  Consume tareas de `tasks:stream` (Redis).\
2.  Crea branch temporal `dev/<task_id>`.\
3.  Genera código y tests → los guarda en MinIO.\
4.  Publica evento `code_generated` en Redis (vía outbox).

### 3.4 Justificación Técnica

-   Prompts diseñados para **modularidad + reproducibilidad**.\
-   Utiliza plantillas few-shot entrenadas con históricos.\
-   Control de tokens por sesión para reducir costos.

------------------------------------------------------------------------

## 4. QAAgent

### 4.1 Rol

El **QAAgent** valida la calidad del código generado por DevAgent.
Evalúa funcionalidad, estilo, cobertura y seguridad.

### 4.2 Responsabilidades

-   Ejecutar `pytest`, linters (`flake8`, `bandit`).\
-   Analizar logs y detectar fallos.\
-   Generar reportes JSON con resultados.\
-   Emitir `qa_passed` o `qa_failed` al Orchestrator.

### 4.3 Interacción

1.  Escucha en `tasks:stream` mensajes tipo `code_generated`.\
2.  Descarga artefacto desde MinIO.\
3.  Corre pruebas dentro de sandbox aislado (gVisor).\
4.  Publica resultados en Redis + logs en Postgres.

### 4.4 Justificación Técnica

-   Uso de sandbox garantiza seguridad ante código generado.\
-   Integración con cobertura → métrica de calidad XP.\
-   Métricas Prometheus expuestas: `qa_tests_passed_total`,
    `qa_tests_failed_total`.

------------------------------------------------------------------------

## 5. ReviewAgent

### 5.1 Rol

Simula al **revisor humano** del ciclo XP. Verifica calidad estructural,
seguridad, y cumplimiento del DoD antes del merge.

### 5.2 Responsabilidades

-   Revisar PRs generados automáticamente.\
-   Analizar seguridad (SAST) y dependencias.\
-   Detectar smells de código o debt.\
-   Aceptar o rechazar PRs → comunicar al Orchestrator.

### 5.3 Interacción

1.  Recibe notificación desde Orchestrator o GitHub Webhook.\
2.  Descarga código, ejecuta revisión.\
3.  Si aprueba → solicita merge.\
4.  Si rechaza → devuelve feedback estructurado a DevAgent.

### 5.4 Justificación Técnica

-   Prompts ajustados con heurísticas de revisión (seguridad + estilo).\
-   Funciona como "gatekeeper" del pipeline CI/CD.\
-   Rechaza cambios que no cumplan TDD, coverage o DoD.

------------------------------------------------------------------------

## 6. RefactorAgent

### 6.1 Rol

Responsable de la **deuda técnica y mantenimiento evolutivo**. Opera
como cronjob semanal autónomo.

### 6.2 Responsabilidades

-   Escanear repos con SonarQube API.\
-   Detectar hotspots y crear issues de refactor.\
-   Priorizar por complejidad y severidad.\
-   Enviar cambios a DevAgent y ReviewAgent.

### 6.3 Decisiones Clave

  Aspecto      Implementación
  ------------ ------------------------------------------------------
  Frecuencia   Lunes 9:00 AM (scheduler APScheduler)
  Límite       10 refactors automáticos por semana
  Alcance      ≤ 200 LOC modificadas / sin cambio de comportamiento
  Evaluación   Comparar métricas Sonar antes/después

------------------------------------------------------------------------

## 7. PairCoordinator

### 7.1 Rol

Facilita el **pair programming entre agentes**. Asigna roles
(Driver/Navigator), controla iteraciones y persistencia.

### 7.2 Responsabilidades

-   Crear `session_id` y bloquear `task_id`.\
-   Coordinar mensajes vía `pair:stream:<session_id>`.\
-   Gestionar iteraciones (`proposal`, `patch`, `comment`, `accept`).\
-   Guardar logs y snapshots en MinIO.

### 7.3 Estructura de Mensaje

``` json
{
  "session_id": "pair-task-001",
  "iter": 2,
  "type": "patch",
  "agent": "navigator",
  "payload": { "files": ["main.py"], "coverage": 0.92 },
  "timestamp": "2025-10-25T19:00:00Z"
}
```

### 7.4 Beneficios Arquitectónicos

-   Reduce tasa de fallos en CI (\>30%).\
-   Registra razonamiento de agentes → auditable.\
-   Facilita aprendizaje cruzado y refinamiento de prompts.

------------------------------------------------------------------------

## 8. Dependencias Críticas

  -------------------------------------------------------------------------------
  Dependencia          Rol            Riesgo si falla         Mitigación
  -------------------- -------------- ----------------------- -------------------
  Redis Streams        Comunicación   Pérdida de tareas       ACK + retry +
                       principal                              reclaim pending

  Postgres             Persistencia   Inconsistencias         Outbox + backups
                                                              automáticos

  MinIO                Artefactos     Faltan snapshots        Retención
                                                              redundante

  Traefik              Routing / SSL  Caída de endpoints      Replicas + health
                                                              checks

  GitHub               CI/CD y PRs    Fallo en webhooks       Retry + cache local
  -------------------------------------------------------------------------------

------------------------------------------------------------------------

## 9. Diagramas de Interacción Simplificados

``` mermaid
flowchart LR
    subgraph Orchestrator
        O1[Assign Task]
        O2[Outbox Publish]
    end

    subgraph Agents
        D[DevAgent]
        Q[QAAgent]
        R[ReviewAgent]
        F[RefactorAgent]
    end

    O1 --> D
    D --> Q
    Q --> R
    R --> O2
    F --> O1
```

------------------------------------------------------------------------

## 10. Resumen de Responsabilidades

  ------------------------------------------------------------------------------------
  Componente        Tipo        Responsabilidad central  Persistencia   Comunicación
  ----------------- ----------- ------------------------ -------------- --------------
  Orchestrator      API         Flujo XP, pairing,       Postgres +     REST + Streams
                    principal   coordinación             Redis          

  DevAgent          Agente      Generación TDD           MinIO + Redis  Streams

  QAAgent           Agente      Validación               Postgres +     Streams
                                                         Redis          

  ReviewAgent       Agente      Revisión final           Postgres       REST +
                                                                        Webhooks

  RefactorAgent     Agente      Mantenimiento            SonarQube +    REST + Streams
                                                         GitHub         

  PairCoordinator   Submódulo   Pair sessions            Postgres +     Redis Streams
                                                         MinIO          
  ------------------------------------------------------------------------------------

------------------------------------------------------------------------

**Versión:** v2.0 --- Octubre 2025\
**Autor:** Equipo de Ingeniería -- Proyecto Agentes AI
