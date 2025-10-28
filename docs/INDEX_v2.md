# 🧠 Proyecto Agentes AI -- Documentación Técnica v2

> **Ubicación sugerida:** `/docs/v2/INDEX_v2.md`\
> **Propósito:** Servir como punto de entrada y guía maestra para toda
> la documentación del sistema multi‑agente.\
> **Versión:** v2.0 --- Octubre 2025

------------------------------------------------------------------------

## 📘 Introducción

El sistema **Agentes AI -- Equipo de Desarrollo** implementa un
ecosistema de agentes autónomos especializados (Dev, QA, Review,
Refactor) coordinados bajo una arquitectura XP y CI/CD.\
Cada componente refleja una práctica ágil moderna: TDD, pair
programming, refactor continuo y feedback automatizado.

La versión **v2.0** incorpora mejoras derivadas de la auditoría de
arquitectura 2025, enfocándose en:\
- Robustez operativa.\
- Seguridad y aislamiento.\
- Escalabilidad horizontal.\
- Métricas XP medibles.\
- Cost‑efficiency en modelos LLM.

------------------------------------------------------------------------

## 🧩 Estructura de Documentación `/docs/v2/`

  -----------------------------------------------------------------------------------------------------------------------------------------
  Archivo                                                                               Descripción                 Propósito
  ------------------------------------------------------------------------------------- --------------------------- -----------------------
  **[01_resumen_y\_objetivos.md](01_resumen_y_objetivos.md)**                           Resumen general y metas del Contexto y alcance
                                                                                        sistema                     

  **[02_arquitectura_general.md](02_arquitectura_general.md)**                          Diagrama y flujos de alto   Estructura global
                                                                                        nivel                       

  **[03_componentes_tecnicos.md](03_componentes_tecnicos.md)**                          Detalle arquitectónico por  Diseño modular
                                                                                        módulo                      

  **[04_infraestructura_y\_despliegue.md](04_infraestructura_y_despliegue.md)**         Redes, HA, Swarm,           Infraestructura base
                                                                                        persistencia                

  **[05_practicas_xp_y\_ciclo_desarrollo.md](05_practicas_xp_y_ciclo_desarrollo.md)**   Cómo el sistema aplica XP   Metodología viva

  **[06_seguridad_y\_aislamiento.md](06_seguridad_y_aislamiento.md)**                   Sandboxing, control de      Seguridad operacional
                                                                                        acceso, auditoría           

  **[07_escalabilidad_y\_optimizacion.md](07_escalabilidad_y_optimizacion.md)**         Caching, routing, batch,    Eficiencia y costos
                                                                                        auto‑scaling                

  **[08_metricas_y\_monitoreo.md](08_metricas_y_monitoreo.md)**                         KPIs técnicos, dashboards,  Observabilidad
                                                                                        alertas                     

  **[09_roadmap_y\_plan_implementacion.md](09_roadmap_y_plan_implementacion.md)**       Sprints 0--3 y roadmap      Ejecución XP
                                                                                        evolutivo                   

  **[10_anexos_operativos.md](10_anexos_operativos.md)**                                Runbooks, incidentes,       Operaciones y soporte
                                                                                        checklists                  
  -----------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 🧱 Estructura Técnica Global

``` mermaid
flowchart TD
    GH[GitHub Repositorio] --> OR[Orchestrator FastAPI]
    OR --> RS[Redis Streams]
    OR --> DB[(Postgres + pgvector)]
    OR --> S3[MinIO Artefactos]
    OR --> PX[Prometheus / Grafana]
    RS --> D[DevAgent]
    RS --> Q[QAAgent]
    RS --> R[ReviewAgent]
    RS --> F[RefactorAgent]
    D & Q & R & F --> OR
```

------------------------------------------------------------------------

## ⚙️ Prácticas XP Implementadas

  -----------------------------------------------------------------------
  Práctica              Estado            Implementación
  --------------------- ----------------- -------------------------------
  **TDD**               ✅ Activa         DevAgent genera tests antes del
                                          código

  **Pair Programming**  ✅ Activa         Coordinación Driver/Navigator
                                          vía Redis

  **Refactor Continuo** ✅ Activa         SonarQube + RefactorAgent
                                          semanal

  **Propiedad           🔄 Parcial        OwnershipManager en desarrollo
  Colectiva**                             

  **Ritmo Sostenible**  ✅ Activa         TokenBudgetManager +
                                          distribución tareas

  **DoD Automático**    ✅ Activa         Endpoint `/api/pr/verify-dod`
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 📈 Indicadores de Madurez

  Nivel                     Descripción                          Estado
  ------------------------- ------------------------------------ --------
  L1 -- Estable             Infraestructura y resiliencia base   ✅
  L2 -- XP Completo         TDD, QA, Refactor, Pair activos      ✅
  L3 -- Escalable           Cache + Routing + Batch activos      ✅
  L4 -- Auto‑optimización   Escalado + Alertas dinámicas         🔄
  L5 -- Autónomo            Marketplace y feedback continuo      ⏳

------------------------------------------------------------------------

## 🚦 Reglas de Operación

1.  **Todo cambio requiere Issue + PR.**\
2.  **El DoD es ley:** ningún merge sin checklist verde.\
3.  **Nada sin trazabilidad:** toda acción deja registro en audit
    trail.\
4.  **Los agentes no poseen estado propio.**\
5.  **Los incidentes se documentan siempre.**

------------------------------------------------------------------------

## 🧩 Integraciones Clave

  Componente               Rol
  ------------------------ --------------------------------------
  GitHub                   Fuente de issues y PRs
  Docker Swarm             Orquestación de servicios
  Traefik                  Proxy y TLS
  Postgres + pgvector      Persistencia e indexación contextual
  Redis Streams            Mensajería entre agentes
  MinIO                    Almacenamiento de artefactos
  Prometheus + Grafana     Monitoreo y alertas
  Jaeger + OpenTelemetry   Trazabilidad completa

------------------------------------------------------------------------

## 🧪 Checklist de Validación Global

  Área                  Verificación                            Estado
  --------------------- --------------------------------------- --------
  **Infraestructura**   Orchestrator + Redis + Postgres en HA   ✅
  **XP Practices**      TDD + Refactor + Pairing activos        ✅
  **Seguridad**         Sandboxing y gestión de secretos        ✅
  **Métricas**          Prometheus + Grafana operativos         ✅
  **Escalabilidad**     Auto‑scaling agentes \> 3               🔄
  **Documentación**     v2 completa y publicada                 ✅

------------------------------------------------------------------------

## 🧾 Versionado y Control

  -----------------------------------------------------------------------
  Versión            Fecha          Cambios Relevantes
  ------------------ -------------- -------------------------------------
  **v1.0**           Jun 2025       MVP funcional inicial

  **v1.5**           Ago 2025       Auditoría técnica parcial

  **v2.0**           Oct 2025       Reestructuración total (XP +
                                    seguridad + monitoreo)
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 👥 Autores y Responsables

  Rol                   Nombre / Agente
  --------------------- -----------------------------
  Coordinador técnico   **Max (Product Owner)**
  Arquitectura XP       **GPT‑5 (IA Asistente)**
  Infraestructura       **DevOps Agent**
  QA y Refactor         **QAAgent / RefactorAgent**
  Revisión documental   **ReviewAgent**

------------------------------------------------------------------------

**Fin de la Documentación v2**\
\> "Un sistema bien documentado es un sistema que puede aprender de sí
mismo."

------------------------------------------------------------------------
