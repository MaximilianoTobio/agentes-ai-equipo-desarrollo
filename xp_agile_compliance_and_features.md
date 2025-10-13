# Análisis: Cumplimiento Agile + XP y Features añadidas

> Documento: análisis crítico de la arquitectura MVP vs principios ágiles y de eXtreme Programming (XP). Incluye: checklist de prácticas XP, gaps detectados, features nuevas propuestas (priorizadas) y especificaciones técnicas mínimas para integrarlas al MVP.

---

## 1. Resumen ejecutivo (directo)

He revisado la arquitectura del MVP (Orquestador + Agents + CI + RAG + Human Gate) y, en términos generales, cumple la mayoría de los requisitos técnicos para soportar un proceso ágil. Sin embargo, **varios principios XP críticos** estaban incompletos o ausentes: principalmente TDD rígido, refactor continuo, propiedad colectiva efectiva, ritmo sostenible, y feedback rápido del cliente.

He listado y priorizado features que vuelven el MVP compatible con XP y la práctica ágil real — cada feature incluye especificación mínima para su implementación y métricas de validación.

---

## 2. Checklist XP / Agile (evaluación rápida)

| Práctica XP/Ágil | ¿Incluida en MVP? | Comentario breve |
|---|---:|---|
| Programación en parejas (pair programming) | Parcial (feature separado) | Documentada y diseñada, falta integración técnica plena. |
| Desarrollo guiado por tests (TDD) | Parcial | CI y tests existen, pero no hay enforcement pre-PR ni tests-first por defecto. |
| Refactorización continua | Parcial | No hay agente/refactor schedule ni métricas de deuda técnica. |
| Propiedad colectiva de código | No | No hay rotación de agentes ni política para ownership compartido. |
| CI frecuente / Integración continua | Sí | CI pipeline básico presente. Reforzar gates. |
| Small releases / Deploy frecuentes | Parcial | Pipeline listo; falta estrategia de releases pequeñas y feature flags. |
| Simplicidad de diseño | Parcial | No hay reglas que limiten tamaño de PR o complexity budgets. |
| Feedback del cliente (on-site customer) | Parcial | Human gate + POAgent; falta loop de feedback continuo y user testing. |
| Metáfora del sistema | No | No definida; podría ayudar a consistencia. |
| Codificación estándar / pair review | Parcial | Linter y style checks están, falta formatter y enforce pre-commit. |

---

## 3. GAPS críticos (resumen rápido)

1. **No-forced TDD**: los DevAgents no están obligados a crear tests antes del código; pueden generar código y tests después.
2. **No plan de refactor**: no existe agente ni job que programe o ejecute refactors regulares.
3. **Propiedad colectiva ausente**: módulos pueden quedar atados a un agente sin rotación ni policy.
4. **No enforcement de DoD previo al push**: aunque hay CI, el PR puede crearse sin pasar gates locales antes del push.
5. **Falta de feature flags / releases pequeñas**: deploys pueden ser monolíticos.
6. **Poca integración del cliente real**: feedback humano existe pero no hay un loop sistemático de validación por usuarios.

---

## 4. Features nuevas propuestas (priorizadas)

A continuación las features, ordenadas por prioridad (P1 = inmediato para XP compliance, P2 = corto plazo, P3 = mejora/optimizaciones). Para cada una: descripción, por qué es necesaria, especificación mínima, cambios en DB/endpoints/prompts, métricas para validar.

### P1 — Enforce TDD / Test-First (obligatorio)
**Por qué:** XP exige tests primero para prevenir regressions y forzar diseño simple.

**Qué hace:** obliga a DevAgent a generar tests (esqueleto o casos) **antes** de generar la implementación; ORCHESTRATOR valida que el PR contiene tests que cubran CA y que al menos se ejecutaron localmente.

**Especificación mínima:**
- Prompt DevAgent actualizado con step-0: "Escribe tests que definan el comportamiento antes de escribir el código".
- Orchestrator añade pre-check local: antes de permitir commit/push, DevAgent debe ejecutar tests en workspace; si tests vacíos/placeholder -> reject or flag `needs-tests`.
- CI gate: PR must include tests files in `tests/` for changed modules.

**DB/Endpoints/Prompts:**
- `agent_logs` registra `tdd: true/false` y `test_generated_at`.
- Endpoint `POST /api/tasks/{id}/validate-tests` para verificación automatizada.

**Métrica:** % de PRs con tests-first; tasa de fallos en CI por falta de tests.

---

### P1 — Pre-push local CI & gates (en workspace)
**Por qué:** reducir ciclos remotos y fallas en CI.

**Qué hace:** antes de crear PR, Agent debe pasar local pipeline (lint + pytest + security quick-scan) en workspace runner.

**Especificación mínima:**
- Runner script `pre_push_check.sh` que agents ejecutan; devuelve non-zero si falla.
- Orchestrator exige resultado `pre_push: pass` antes de crear PR o marca PR con `pre_push_failed=true`.

**Métrica:** % PRs con pre_push pass vs CI pass.

---

### P1 — RefactorAgent / scheduled refactor tasks
**Por qué:** XP demanda refactor constante para mantener diseño simple y code health.

**Qué hace:** agente que periódicamente programa trabajos de refactor (basados en metrics: code-smells, complexity, tech-debt) y abre PRs de refactor pequeñas.

**Especificación mínima:**
- New service `refactor_agent` que consulta SonarQube/linters y lista hotspots.
- Scheduler (CRON) en Orchestrator que crea tasks `refactor:<file|module>` con low-impact scope.

**DB/Endpoints:**
- Tabla `refactor_tasks` con severity, last_reviewed.

**Métrica:** Deuda técnica vs tiempo (reducción tras refactors).

---

### P1 — Definition of Done (DoD) enforced and automatable
**Por qué:** garantizar calidad mínima y consistencia.

**Qué hace:** DoD se vuelve una policy comprobable: tests, coverage, lint, docs, security-scan. Agents deben marcar `dod:passed` y Orchestrator bloquea PR sin DoD.

**Especificación mínima:**
- DoD checklist codificada en Orchestrator; endpoint `POST /api/pr/verify-dod` que ejecuta checks.

**Métrica:** % PRs merged con DoD completo.

---

### P1 — Sustainable Pace & Agent Rate Limiting
**Por qué:** evitar overwork y sobrecostos; asegurar ritmo de entrega estable.

**Qué hace:** controlar número de tasks concurrentes por agent, limitar tokens por agent per sprint, y exponer alertas si load alto.

**Especificación mínima:**
- Agent config `concurrency_limit`, `tokens_budget_per_sprint`.
- Orchestrator encola tareas según sprint capacity; endpoint `GET /api/agent/{id}/capacity`.

**Métrica:** cumplimiento de budget, queue length, agent CPU usage.

---

### P2 — Collective Code Ownership (rotations)
**Por qué:** XP promueve propiedad colectiva para evitar silos.

**Qué hace:** política y automation para rotar agentes entre módulos y forzar revisiones cruzadas.

**Especificación mínima:**
- Orchestrator assigner que evita asignar el mismo agent a un módulo más de N sprints seguidos.
- `ownership` tag in `modules` table; rotation policy endpoint.

**Métrica:** % módulos con multiple agents contributions.

---

### P2 — Continuous Refactoring Metrics & SonarQube integration
**Por qué:** medir calidad objetiva.

**Qué hace:** integrar SonarQube (o similar) y exponer reportes en dashboard; generar tasks automáticos de baja prioridad para smells.

**Spec mínima:** Sonar scanner job en CI; RefactorAgent reads API.

**Métrica:** code smell count, complexity per file.

---

### P2 — Automated Retrospectives (ScrumMasterAgent enhancement)
**Por qué:** retro rápidas y accionables mantienen mejora continua.

**Qué hace:** generar retro notes, detect action items automáticamente y crear tasks en backlog (small follow-ups).

**Spec mínima:** endpoint `GET /api/sprint/{id}/retro` que devuelve resumen y tasks creados.

**Métrica:** % action items closed next sprint.

---

### P2 — Planning Game (POAgent + estimation support)
**Por qué:** XP uses planning game for prioritization and estimation.

**Qué hace:** POAgent runs planning sessions: proposes story estimates, supports planning poker simulation among agents/humans.

**Spec mínima:** UI flow in Orchestrator to run a planning session and record estimates.

**Métrica:** estimate accuracy (estimated vs actual hours)

---

### P3 — Feature flags & small releases
**Por qué:** enable small safe releases and rollback.

**Qué hace:** integrate basic feature-flag system (Unleash/LaunchDarkly) and promote canary deployments.

**Spec mínima:** add `feature_flag` metadata to PR and pipeline to toggle flag at deploy.

**Métrica:** deployments per week; rollback rate.

---

### P3 — On-site customer feedback loop (CustomerFeedbackAgent)
**Por qué:** close feedback loop with real users.

**Qué hace:** create flows to gather user feedback from UI, annotate stories and create follow-up tasks.

**Spec mínima:** endpoint to submit feedback, POAgent ingests and links to stories.

**Métrica:** % stories with user feedback attached.

---

## 5. Cambios mínimos en DB / API (resumen)

- Nueva tablas: `refactor_tasks`, `pair_sessions` (si no existe), `module_ownership`.
- Campos nuevos en `agent_logs`: `tdd_enforced`, `pre_push_status`, `token_usage_session`.
- Endpoints nuevos: `/api/tasks/{id}/validate-tests`, `/api/agent/{id}/capacity`, `/api/sprint/{id}/retro`, `/api/refactor_tasks`.

---

## 6. Prompts y políticas (resumen)

- DevAgent prompt: añadir clause TDD-first y limit PR size (ej. "max 200 LOC por PR").
- ReviewAgent/Navigator: añadir checks para design simplicity y edge-cases.
- RefactorAgent: policy para scope de refactor (no más de X files / Y LOC por PR).

---

## 7. Métricas globales para validar cumplimiento XP

- % PRs con tests-first (objetivo > 80% en 3 sprints).
- PR CI failure rate (debe bajar con pairing/refactor).
- Deuda técnica (sonar) por sprint.
- Story lead time y cycle time (reducir gradualmente).
- Tokens per sprint (control costo).

---

## 8. Plan de integración (qué hacer ahora)

1. Implementar P1 features: TDD enforcement, Pre-push gate, RefactorAgent, DoD enforcement, rate-limiting. (Sprint 0 extension — 2 sprints)
2. Medir y ajustar: correr 2 sprints con estas politicas y revisar métricas.
3. Implementar P2: collective ownership, SonarQube, automated retros.
4. Implementar P3: flags, customer feedback automation.

---

## 9. Notas finales (cruda y práctica)

- Lo esencial: **no** automatices merges hasta que TDD y DoD sean enforceables. Si quieres velocidad sin calidad, el proyecto se fragmenta y se vuelve injugable.
- Empieza por P1; te dará seguridad y base para escalar. No te obsesiones con P3 antes de estabilizar P1/P2.

---

Documento generado por ChatGPT — versión: 2025-10-01

Si querés, genero ahora mismo:
- Implementación mínima del `pre_push_check.sh` + ejemplo de hook en `worker.py` para TDD enforcement, o
- `refactor_agent` minimal (worker + scheduler) listo para pegar.

Elijo uno y lo genero ya: indico los archivos exactos que creo para que puedas copiarlos.

