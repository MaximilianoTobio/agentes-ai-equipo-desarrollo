# 🧩 Prácticas XP y Ciclo de Desarrollo Automatizado

> **Ubicación sugerida:**
> `/docs/v2/05_practicas_xp_y_ciclo_desarrollo.md`\
> **Propósito:** Documentar cómo el sistema multi-agente aplica de forma
> automatizada las prácticas del método **Extreme Programming (XP)** y
> cómo estas prácticas se integran en su ciclo de vida continuo.

------------------------------------------------------------------------

## 1. Introducción

El proyecto adopta los principios de **Extreme Programming (XP)** no
solo como metodología de desarrollo, sino como **arquitectura
operativa**: los agentes de IA reproducen comportamientos de un equipo
XP real.

Cada práctica XP ---desde TDD hasta Pair Programming--- está
representada como un proceso, agente o regla del sistema.\
El resultado: un flujo de desarrollo **autónomo, trazable y con calidad
garantizada**.

------------------------------------------------------------------------

## 2. Ciclo XP Adaptado al Sistema Multi-Agente

El ciclo de desarrollo automatizado sigue estas fases:

1.  **Planificación (Orchestrator)** → recibe issue o PR.\
2.  **Desarrollo (DevAgent)** → genera código + tests TDD.\
3.  **Pruebas (QAAgent)** → ejecuta y valida tests.\
4.  **Revisión (ReviewAgent)** → analiza calidad y seguridad.\
5.  **Refactorización (RefactorAgent)** → mantiene la salud del código.\
6.  **Pair Programming (PairCoordinator)** → coordina sesiones
    Driver/Navigator.\
7.  **Integración (Orchestrator)** → merge automático si se cumple DoD.

``` mermaid
flowchart LR
    P[Issue GitHub] --> D[DevAgent: Código + Tests]
    D --> Q[QAAgent: Ejecución de Tests]
    Q --> R[ReviewAgent: Aprobación / Feedback]
    R --> F[RefactorAgent: Mantenimiento]
    F --> O[Orchestrator: Merge + Auditoría]
```

------------------------------------------------------------------------

## 3. Test-Driven Development (TDD)

### 3.1 Principio

Cada funcionalidad debe nacer desde una prueba: primero se define **qué
se debe cumplir**, luego se genera el código que lo satisface.

### 3.2 Implementación Técnica

-   El **DevAgent** inicia cada tarea generando un conjunto de tests
    (`pytest`).\
-   No puede avanzar a la etapa de implementación hasta que los tests
    estén definidos.\
-   El Orchestrator valida esta condición mediante la función
    `validate_tdd_compliance()`.
-   Si el PR no contiene tests creados antes del código → **es rechazado
    automáticamente**.

### 3.3 Ejemplo de flujo TDD

1.  DevAgent recibe issue `feat:add_login`.\
2.  Genera `test_login.py` con casos de uso esperados.\
3.  Ejecuta test → falla (fase roja).\
4.  Implementa el código → test pasa (fase verde).\
5.  QAAgent ejecuta suite completa.\
6.  ReviewAgent aprueba merge.

### 3.4 Métricas TDD

-   `tdd_compliance_rate` (% de PRs con tests antes del código).\
-   `avg_test_coverage` (% promedio de cobertura).\
-   `tdd_failures_total` (violaciones detectadas).

------------------------------------------------------------------------

## 4. Pair Programming entre Agentes

### 4.1 Concepto

XP promueve que dos desarrolladores trabajen en conjunto: uno "Driver"
escribe el código, y el otro "Navigator" lo revisa en tiempo real.\
Aquí, esa práctica se implementa entre **DevAgent** y **ReviewAgent** (o
QAAgent), coordinados por el **PairCoordinator**.

### 4.2 Flujo Operativo

1.  El Orchestrator detecta una tarea compleja → inicia `pair_session`.\
2.  Se crean roles: `Driver` (DevAgent) y `Navigator` (ReviewAgent).\
3.  Ambos interactúan vía Redis Streams (`pair:stream:<session_id>`).\
4.  Cada iteración se guarda en Postgres y snapshots en MinIO.\
5.  El proceso termina cuando el Navigator acepta la solución
    (`accept`).

### 4.3 Beneficios

-   Detección temprana de errores.\
-   Mayor calidad semántica del código.\
-   Prompts más coherentes (por retroalimentación cruzada).\
-   Documentación natural del proceso (logs de sesión).

### 4.4 Métricas de Pair Programming

-   `pair_sessions_total`\
-   `avg_pair_iters` (iteraciones promedio por sesión)\
-   `pair_accept_rate` (% sesiones finalizadas exitosamente)

------------------------------------------------------------------------

## 5. Refactorización Continua

### 5.1 Principio

"**Mejora constante, sin alterar funcionalidad.**"\
En XP, el refactor es parte del flujo diario, no una tarea separada.

### 5.2 Implementación

El **RefactorAgent** analiza el repositorio semanalmente con SonarQube:

-   Identifica hotspots y code smells.\
-   Prioriza según severidad.\
-   Crea issues automáticos de refactor.\
-   Envía a DevAgent para corrección.\
-   QAAgent verifica que los tests previos sigan pasando.

### 5.3 Políticas

-   Cambios ≤ 200 LOC por refactor.\
-   Sin alteración de comportamiento observable.\
-   Evaluación automática: deuda técnica antes/después.\
-   Se registran métricas: `refactor_issues_created_total`,
    `tech_debt_ratio`.

------------------------------------------------------------------------

## 6. Propiedad Colectiva del Código

### 6.1 Concepto XP

Todo el equipo comparte la propiedad del código; nadie "posee" un
módulo.

### 6.2 Aplicación en el Sistema

El **OwnershipManager** (módulo interno del Orchestrator):

-   Rota automáticamente la asignación de agentes a módulos.\
-   Garantiza que ningún agente trabaje más de 3 sprints seguidos en el
    mismo módulo.\
-   Mantiene equilibrio de carga y conocimiento compartido.

**Ejemplo:**\
`DevAgent-A` trabaja en `module/auth` durante Sprint 1--3 → en Sprint 4
el Orchestrator reasigna esa área a `DevAgent-B`.

### 6.3 Beneficios

-   Previene dependencia de un solo agente ("bus factor").\
-   Aumenta la diversidad de estilos y prompts.\
-   Fomenta adaptabilidad y calidad evolutiva.

------------------------------------------------------------------------

## 7. Ritmo Sostenible (Sustainable Pace)

### 7.1 Filosofía

XP establece que el equipo debe mantener un ritmo de trabajo constante y
humano.\
En este sistema, el **ritmo sostenible** se traduce en balance de carga
entre agentes y control de costos de tokens.

### 7.2 Implementación

-   Cada agente tiene límite de tareas por sprint
    (`max_tasks_per_agent = 40`).\
-   TokenBudgetManager impide sobreuso de modelos.\
-   Si un agente alcanza el 80% del presupuesto, el Orchestrator
    redistribuye las tareas a otros agentes.

### 7.3 Métricas de Ritmo

-   `avg_tasks_per_agent`\
-   `token_budget_utilization`\
-   `agent_overload_events` (cuando un agente excede límites)

------------------------------------------------------------------------

## 8. Definition of Done (DoD) Automático

### 8.1 Concepto

Un trabajo se considera terminado cuando cumple **todos los criterios
técnicos** establecidos: tests, lint, cobertura, documentación, y
seguridad.

### 8.2 Implementación

El Orchestrator expone `/api/pr/verify-dod` que valida automáticamente
antes de merge:

  Criterio       Descripción                        Verificación
  -------------- ---------------------------------- --------------
  ✅ Tests       Todos los tests pasan              QAAgent
  ✅ Lint        `flake8` sin errores               QAAgent
  ✅ Coverage    ≥ 80%                              QAAgent
  ✅ Docs        Docstrings + README actualizados   DevAgent
  ✅ Security    `bandit` sin findings críticos     ReviewAgent
  ✅ Audit Log   Registro en Postgres completado    Orchestrator

Si cualquier condición falla, el PR queda bloqueado y se devuelve
feedback estructurado al agente responsable.

### 8.3 Ejemplo de respuesta API

``` json
{
  "task_id": "T-134",
  "dod_checklist": {
    "tests": "PASS",
    "lint": "PASS",
    "coverage": "PASS",
    "security": "PASS",
    "docs": "PASS",
    "audit_log": "PASS"
  },
  "status": "ACCEPTED"
}
```

------------------------------------------------------------------------

## 9. Integración Continua y Feedback Inmediato

El sistema XP automatizado requiere que la integración sea continua y
visible.

### 9.1 CI/CD Automatizado

-   Los PR generados pasan por validación en GitHub Actions.\
-   Cada pipeline ejecuta tests, lint y validaciones de DoD.\
-   Resultados se envían al Orchestrator para registro de métricas.

### 9.2 Feedback Inmediato

-   Fallos de test o lint generan alertas Prometheus
    (`ci_failures_total`).\
-   Los agentes ajustan su comportamiento en próximos sprints mediante
    prompts autoafinados.

------------------------------------------------------------------------

## 10. Métricas Globales XP

  --------------------------------------------------------------------------
  Métrica            Origen            Objetivo             Umbral
  ------------------ ----------------- -------------------- ----------------
  **TDD Compliance   Orchestrator      Cumplimiento tests   ≥ 95%
  Rate**                               primero              

  **Average Lead     Postgres          Issue → Merge        \< 4h
  Time**                                                    

  **Refactors per    RefactorAgent     Salud del código     ≥ 5
  Sprint**                                                  

  **Tech Debt        SonarQube         Deuda técnica        \< 5%
  Ratio**                                                   

  **Pair Success     PairCoordinator   Sesiones exitosas    ≥ 80%
  Rate**                                                    

  **CI Failure       GitHub Actions    Calidad pipeline     \< 10%
  Rate**                                                    
  --------------------------------------------------------------------------

------------------------------------------------------------------------

## 11. Cultura XP dentro del Sistema

> "El código no solo debe compilar: debe enseñar."

La arquitectura busca **trasladar la cultura XP a los agentes**, no solo
las reglas.\
Cada iteración del sistema es una oportunidad de aprendizaje colectivo y
mejora continua.

-   Cada fallo alimenta la siguiente iteración (retroalimentación).\
-   Cada refactor se documenta y mide.\
-   Cada PR se convierte en evidencia de mejora evolutiva.

------------------------------------------------------------------------

**Versión:** v2.0 --- Octubre 2025\
**Autor:** Equipo de Ingeniería -- Proyecto Agentes AI
