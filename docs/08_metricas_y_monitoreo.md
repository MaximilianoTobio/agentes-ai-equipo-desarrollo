# 📊 Métricas, Monitoreo y Observabilidad

> **Ubicación sugerida:** `/docs/v2/08_metricas_y_monitoreo.md`\
> **Propósito:** Documentar cómo se miden, visualizan y monitorean las
> métricas técnicas, XP y de costos del sistema multi-agente.\
> **Enfoque:** observabilidad integral, KPIs accionables y alertas
> preventivas.

------------------------------------------------------------------------

## 1. Filosofía de Observabilidad

> "No se puede mejorar lo que no se mide."

La observabilidad del sistema busca más que recolectar datos:\
permite **entender el comportamiento de los agentes, anticipar errores y
optimizar recursos.**

El sistema combina métricas (Prometheus), trazas (Jaeger) y dashboards
(Grafana) para obtener una visión completa de la salud técnica y del
rendimiento XP.

------------------------------------------------------------------------

## 2. Arquitectura de Monitoreo

``` mermaid
flowchart LR
    A[Orchestrator] -->|Exposición /metrics| P[Prometheus]
    B[Agents] -->|Métricas internas| P
    P --> G[Grafana Dashboards]
    A --> J[Jaeger Traces]
    B --> J
    G --> U[Usuario / DevOps]
```

### Componentes

  ---------------------------------------------------------------------------
  Servicio                       Rol              Ejemplo
  ------------------------------ ---------------- ---------------------------
  **Prometheus**                 Recolecta        `/metrics` endpoint
                                 métricas         
                                 expuestas por    
                                 agentes y        
                                 orquestador      

  **Grafana**                    Visualiza        Lead time, TDD, latencia
                                 dashboards       
                                 técnicos y XP    

  **Jaeger**                     Rastrea trazas   Issue → Merge completo
                                 distribuidas     

  **Alertmanager**               Envía alertas a  Tokens, fallos CI, colas
                                 Slack/Telegram   largas
  ---------------------------------------------------------------------------

------------------------------------------------------------------------

## 3. Tipos de Métricas

### 3.1 Técnicas (DevOps)

  ---------------------------------------------------------------------------------
  Métrica                          Descripción                   Fuente
  -------------------------------- ----------------------------- ------------------
  `orchestrator_up`                Estado del servicio           Orchestrator

  `api_request_duration_seconds`   Latencia de endpoints         FastAPI Middleware

  `queue_length`                   Longitud de Redis Streams     Redis Exporter

  `messages_lost_total`            Mensajes fallidos o           Orchestrator
                                   duplicados                    

  `ci_failures_total`              Fallos en pipelines           GitHub Actions

  `uptime_ratio`                   \% disponibilidad servicio    Prometheus
  ---------------------------------------------------------------------------------

### 3.2 XP / Desarrollo

  -------------------------------------------------------------------------
  Métrica                  Descripción                   Origen
  ------------------------ ----------------------------- ------------------
  `tdd_compliance_rate`    \% de PRs con tests previos   Orchestrator

  `coverage_avg`           Cobertura promedio            QAAgent

  `pair_success_rate`      Éxito de sesiones             PairCoordinator
                           Driver/Navigator              

  `refactors_per_sprint`   Refactors ejecutados          RefactorAgent

  `tech_debt_ratio`        Deuda técnica medida          SonarQube

  `lead_time_avg_hours`    Tiempo issue → merge          DB Query
  -------------------------------------------------------------------------

### 3.3 Costos / Eficiencia

  -----------------------------------------------------------------------------
  Métrica                    Descripción                   Fuente
  -------------------------- ----------------------------- --------------------
  `token_usage_total`        Tokens consumidos por sprint  Orchestrator

  `token_budget_remaining`   Presupuesto restante          TokenBudgetManager

  `llm_cache_hit_rate`       Eficiencia del caché          Redis Exporter

  `cost_per_pr_usd`          Costo promedio por PR         Dashboard

  `cache_savings_percent`    Tokens ahorrados por caching  Prometheus Rule
  -----------------------------------------------------------------------------

------------------------------------------------------------------------

## 4. Dashboards Clave en Grafana

### 4.1 **📈 Dashboard "System Health"**

-   Uptime del orquestador (gauge)
-   Latencia API (P50/P95/P99)
-   Queue Length (gráfico en tiempo real)
-   CPU/RAM de agentes

### 4.2 **🧪 Dashboard "XP Metrics"**

-   TDD compliance rate
-   Test coverage
-   Pair sessions completadas
-   Refactors por sprint
-   DoD pass/fail ratio

### 4.3 **💰 Dashboard "Token & Cost Control"**

-   Tokens usados por agente/sprint
-   Cache hit rate
-   Cost per PR (USD)
-   Alertas de budget
-   Savings acumulado (%)

### 4.4 **🧭 Dashboard "Lead Time & Flow Efficiency"**

-   Lead time promedio por tipo de issue
-   Cycle time (creación → merge)
-   Throughput por sprint
-   Flow efficiency (% de trabajo activo vs espera)

------------------------------------------------------------------------

## 5. Alertas Automáticas

### 5.1 Ejemplos de Reglas Prometheus

``` yaml
groups:
  - name: orchestrator.rules
    rules:
      - alert: OrchestratorDown
        expr: up{job="orchestrator"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Orchestrator caído"
          description: "El servicio principal no responde."

      - alert: QueueTooLong
        expr: queue_length > 100
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Redis Streams congestionado"
          description: "Hay más de 100 tareas pendientes."

      - alert: TokenBudgetCritical
        expr: token_budget_remaining < 0.1
        labels:
          severity: critical
        annotations:
          summary: "Presupuesto de tokens casi agotado"
          description: "El sistema debe reducir uso de modelos LLM."
```

### 5.2 Canales de Alerta

-   **Slack / Telegram** → notificaciones instantáneas.\
-   **Email / Ops dashboard** → informes diarios.\
-   **Webhook** → integración con n8n o monitor interno.

------------------------------------------------------------------------

## 6. Trazabilidad con Jaeger

Cada tarea (issue → PR) genera una **trace distribuida** con spans: 1.
Webhook recibido (GitHub)\
2. Creación de tarea (Orchestrator)\
3. DevAgent → QAAgent → ReviewAgent\
4. Merge final / audit trail

Permite: - Medir latencia por etapa.\
- Detectar cuellos de botella.\
- Trazar incidentes end-to-end.

Ejemplo de nombre de trace:\
`TRACE[feat:add_login:T-104]`

------------------------------------------------------------------------

## 7. Métricas de Negocio y ROI

A nivel estratégico, las métricas técnicas se combinan con indicadores
de productividad:

  ------------------------------------------------------------------------
  KPI               Descripción                          Meta
  ----------------- ------------------------------------ -----------------
  **Costo / PR**    USD promedio por PR generado         \< \$8

  **ROI vs          Ahorro total en tokens + horas       \> 400%
  desarrollo                                             
  manual**                                               

  **Lead time**     Tiempo issue → merge                 \< 4h

  **MTTR**          Tiempo medio de resolución de fallos \< 10 min

  **Deuda técnica** \% detectado por SonarQube           \< 5%
  ------------------------------------------------------------------------

------------------------------------------------------------------------

## 8. Política de Métricas y Reporting

### 8.1 Recolección continua

Todas las métricas se exponen en `/metrics` y se actualizan cada 30s.

### 8.2 Retención

-   Prometheus: 30 días (rotación).\
-   Postgres (XP/negocio): histórico completo (con particiones
    mensuales).

### 8.3 Reporting periódico

-   **Semanal:** métricas XP (DoD, refactors, TDD).\
-   **Mensual:** métricas financieras (tokens, costos, ROI).\
-   **Incidentes:** reportes post-mortem automáticos (ver Anexo B2).

------------------------------------------------------------------------

## 9. Interpretación de KPIs

### 9.1 "Semáforo XP"

  Color   Estado      Significado
  ------- ----------- ----------------------------
  🟢      Saludable   Dentro de umbrales
  🟡      En riesgo   Requiere ajuste operativo
  🔴      Crítico     Acción inmediata requerida

### 9.2 Ejemplo de análisis

-   **QueueLength alto + TDD rate bajo:** falta capacidad de DevAgent.\
-   **Token usage alto + Cache hit bajo:** prompts redundantes o mala
    clasificación.\
-   **Lead time alto pero tests ok:** cuello en ReviewAgent.

------------------------------------------------------------------------

## 10. Conclusión

El sistema no solo ejecuta tareas: **se mide a sí mismo**.\
Cada agente, pipeline y decisión queda reflejada en métricas
cuantificables, lo que permite una evolución basada en evidencia.

> "Lo que no se mide, se repite. Lo que se mide, se mejora."

------------------------------------------------------------------------

**Versión:** v2.0 --- Octubre 2025\
**Autor:** Equipo de Ingeniería -- Proyecto Agentes AI
