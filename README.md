# 🤖 Agentes AI -- Equipo de Desarrollo

> **Versión:** v2.0 --- Octubre 2025\
> **Auditoría completada:** ✔️ Arquitectura, Seguridad, Escalabilidad y
> XP\
> **Documentación completa:** [/docs/v2](docs/v2/INDEX_v2.md)

------------------------------------------------------------------------

![GitHub last
commit](https://img.shields.io/github/last-commit/MaximilianoTobio/agentes-ai-equipo-desarrollo?style=flat-square)
![Status](https://img.shields.io/badge/status-active-success?style=flat-square)
![XP
Practices](https://img.shields.io/badge/XP-Practices%20Implemented-blue?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)

------------------------------------------------------------------------

## 🧭 Visión General

**Agentes AI -- Equipo de Desarrollo** es un ecosistema de agentes
inteligentes que trabajan colaborativamente para **escribir, probar y
revisar software** bajo los principios de **Extreme Programming (XP)** y
**Scrum**.\
El sistema actúa como una **fábrica de software autónoma**, donde cada
agente cumple un rol especializado dentro de un flujo trazable y seguro.

-   🧠 **DevAgent:** genera código y tests (TDD).\
-   🧪 **QAAgent:** ejecuta validaciones y métricas de calidad.\
-   👁️ **ReviewAgent:** revisa PRs y aprueba merges.\
-   🛠️ **RefactorAgent:** corrige deuda técnica y mantiene el sistema.\
-   🤝 **PairCoordinator:** coordina sesiones de pair programming.\
-   ⚙️ **Orchestrator:** cerebro central que coordina todo el flujo.

> "El objetivo no es solo generar código, sino construir **software que
> se mejora a sí mismo**."

------------------------------------------------------------------------

## 🏗️ Arquitectura General

``` mermaid
flowchart TD
  GH[GitHub] --> OR[Orchestrator FastAPI]
  OR --> RS[Redis Streams]
  OR --> DB[(Postgres + pgvector)]
  OR --> S3[MinIO Artefactos]
  RS --> D[DevAgent]
  RS --> Q[QAAgent]
  RS --> R[ReviewAgent]
  RS --> F[RefactorAgent]
  D & Q & R & F --> OR
  OR --> PX[Prometheus / Grafana]
  OR --> JG[Jaeger / OpenTelemetry]
```

**Stack principal:**\
FastAPI • Redis Streams • Postgres • MinIO • Prometheus • Grafana •
Docker Swarm • Traefik

------------------------------------------------------------------------

## 📚 Documentación Técnica (v2)

  --------------------------------------------------------------------------------------------------------
  Sección                                                        Descripción
  -------------------------------------------------------------- -----------------------------------------
  [01 -- Resumen y Objetivos](docs/v2/01_resumen_y_objetivos.md) Propósito y visión general del sistema

  [02 -- Arquitectura                                            Diseño estructural y flujos de datos
  General](docs/v2/02_arquitectura_general.md)                   

  [03 -- Componentes                                             Detalle de cada módulo y su relación
  Técnicos](docs/v2/03_componentes_tecnicos.md)                  

  [04 -- Infraestructura y                                       Entorno, redes, HA, Swarm
  Despliegue](docs/v2/04_infraestructura_y_despliegue.md)        

  [05 -- Prácticas XP y Ciclo de                                 Implementación XP completa
  Desarrollo](docs/v2/05_practicas_xp_y_ciclo_desarrollo.md)     

  [06 -- Seguridad y                                             Sandboxing, secretos, auditoría
  Aislamiento](docs/v2/06_seguridad_y_aislamiento.md)            

  [07 -- Escalabilidad y                                         Caching, routing, auto‑scaling
  Optimización](docs/v2/07_escalabilidad_y_optimizacion.md)      

  [08 -- Métricas y                                              KPIs, dashboards, alertas
  Monitoreo](docs/v2/08_metricas_y_monitoreo.md)                 

  [09 -- Roadmap y Plan de                                       Sprints 0--3 y roadmap extendido
  Implementación](docs/v2/09_roadmap_y_plan_implementacion.md)   

  [10 -- Anexos Operativos](docs/v2/10_anexos_operativos.md)     Runbooks, incidentes y mantenimiento
  --------------------------------------------------------------------------------------------------------

📘 **Índice completo:** [INDEX_v2.md](docs/v2/INDEX_v2.md)

------------------------------------------------------------------------

## 🧱 Ciclo XP Automatizado

``` mermaid
sequenceDiagram
    participant GH as GitHub
    participant OR as Orchestrator
    participant D as DevAgent
    participant Q as QAAgent
    participant R as ReviewAgent
    participant F as RefactorAgent

    GH->>OR: Issue / PR
    OR->>D: Asignación de tarea (Redis Stream)
    D->>Q: Código + Tests
    Q->>R: Validación QA
    R->>OR: Aprobación / Feedback
    F->>OR: Refactor Semanal
    OR->>GH: Merge + Auditoría
```

**Prácticas XP activas:**\
TDD ✅ • Pair Programming ✅ • Refactorización Continua ✅ • DoD
Automático ✅ • Propiedad Colectiva 🔄

------------------------------------------------------------------------

## 🔐 Seguridad y Trazabilidad

-   Código generado ejecutado solo en sandboxes aislados.\
-   Ningún agente accede a secretos de producción.\
-   Auditoría inmutable en Postgres (particionada por mes).\
-   Traefik gestiona TLS y exposición segura.\
-   Límite de presupuesto de tokens por sprint (TokenBudgetManager).

> "Nada se ejecuta sin control, nada se pierde sin registro."

------------------------------------------------------------------------

## 📈 Estado Actual

  ---------------------------------------------------------------------------
  Área              Estado               Observaciones
  ----------------- -------------------- ------------------------------------
  Infraestructura   ✅ Operativa         Orchestrator HA + Redis Streams
  base                                   

  XP completo       ✅ Activo            TDD, Refactor, Pair, QA

  Observabilidad    ✅ Integrada         Prometheus + Grafana + Jaeger

  Seguridad         ✅ Validada          Sandbox + secretos + DoD

  Escalabilidad     🔄 En curso          Cache + routing + autoscaling

  Documentación     ✅ Completa          v2 finalizada tras auditoría
  ---------------------------------------------------------------------------

------------------------------------------------------------------------

## 🗺️ Roadmap 2025

  Sprint   Enfoque              Objetivo
  -------- -------------------- ---------------------------------
  **S0**   Core & Resiliencia   Infraestructura base + HA
  **S1**   XP Compliance        XP completo + observabilidad
  **S2**   Optimización         Pair programming + caching
  **S3**   Madurez              Escalado y eficiencia de costos

------------------------------------------------------------------------

## 💡 Por qué este proyecto importa

Este sistema representa un nuevo paradigma: **equipos de IA colaborando
bajo reglas humanas**, no reemplazando humanos.\
Es una arquitectura viva, capaz de aprender, auditarse y mejorar con
cada iteración.

> "No es IA generando código; es una metodología entera automatizada."

------------------------------------------------------------------------

## 👥 Equipo y Roles

  Rol                        Responsable
  -------------------------- -----------------------------
  Product Owner              **Max**
  Arquitectura XP            **GPT‑5 (Asistente IA)**
  DevOps & Infraestructura   **DevAgent**
  QA / Refactor              **QAAgent / RefactorAgent**
  Revisión                   **ReviewAgent**

------------------------------------------------------------------------

## 🧾 Licencia

Este proyecto se distribuye bajo la licencia **MIT**.\
Puedes usarlo, modificarlo y adaptarlo libremente, manteniendo la
atribución.

------------------------------------------------------------------------

**© 2025 -- Proyecto Agentes AI -- Equipo de Desarrollo**\
\> "El código se escribe en Python, pero la arquitectura se escribe en
disciplina."
