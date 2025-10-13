# Feature: Pair Programming entre Agentes — Diseño y Especificación

> Documento técnico para añadir la feature "Pair Programming entre agentes" al MVP cuando se considere. Contiene: lógica, protocolos, data model, pseudocódigo, prompts, criterios de aceptación, métricas y plan de rollout.

---

## 1. Resumen ejecutivo

La feature habilita sesiones de *pair programming* entre agentes (Driver + Navigator) y variantes *mob* para que trabajen colaborativamente sobre la misma tarea antes de crear un PR. Busca reducir fallos en CI, elevar la calidad y simular la dinámica humana de pair programming dentro del pipeline automatizado.

---

## 2. Objetivos

- Forzar revisión temprana en el ciclo de cambios (shift-left).  
- Disminuir la cantidad de ciclos de corrección en CI.  
- Generar un registro auditable de la discusión/decisiones entre agentes.  
- Mantener trazabilidad y reproducibilidad (prompts y patches versionados).

---

## 3. Requisitos funcionales (mínimos)

1. Orquestador puede crear/gestionar `pair-session` por `task_id`.
2. Reserva/locking de tareas para evitar race conditions.
3. Canal de comunicación bidireccional entre Driver y Navigator (Redis Streams o similar).
4. Workspace temporal compartido (runner local o espacio en MinIO + git repo local) con control de versiones por iteración.
5. Protocolos de mensajes definidos (proposal, patch, comment, test-result, accept, reject).
6. Registro en `agent_logs` de cada iteración: prompt usado, respuesta, patch-hash, tests resultado.
7. Límite de iteraciones y fallback automático.
8. Reglas DoD aplicadas antes de que Driver cree PR.

---

## 4. Requisitos no funcionales

- TTL en locks (e.g., 10 min) y mecanismo de renovación por heartbeat.  
- Latencia de la sesión < 5s por iteración ideal (depende de LLM).  
- Auditoría inmutable (hashes de patch + referencia a artefacto en MinIO).  
- Control de costos: contador de tokens por sesión y límite configurable.

---

## 5. Arquitectura técnica (componentes)

- **Pair Coordinator (parte del Orchestrador)**: crea sessions, reserva task, asigna agents.
- **Redis Streams**: `pair:stream:<session_id>` como bus de mensajes.
- **Locks Redis**: `pair:lock:<task_id>` (SETNX + TTL).
- **Workspace Runner / Executor**: carpeta temporal `/workspaces/<session_id>` en runner (CI runner o nodo agent) donde se hace `git init`, checkout, apply patches y run tests.
- **Agent Workers**: Driver y Navigator con capacidades para read/write al workspace y publicar mensajes en stream.
- **Persistent Store**: `agent_logs` (Postgres) + artefactos a MinIO.

---

## 6. Protocolo y mensajes (especificación)

**Streams key:** `pair:stream:<session_id>`

**Message schema (JSON):**

```json
{
  "session_id":"pair-<task>-<ts>",
  "task_id": 123,
  "iter": 1,
  "type": "proposal|comment|patch|test-result|accept|reject|heartbeat",
  "agent_id": "dev_agent_A",
  "payload": { ... },
  "timestamp": "2025-10-01T19:00:00Z"
}
```

**Payload fields (sugeridos):**
- `files`: [{"path":"services/api/foo.py","content":"..."}]  
- `patch`: unified-diff string  
- `tests`: {"pytest": {"passed":12,"failed":0}}  
- `comment`: "..."  
- `coverage`: 0.85  
- `token_usage`: {"model":"o4-mini","tokens":1200}

---

## 7. Ciclo de vida de la sesión

1. **Start**: Orchestrador crea `session_id`, setea lock `pair:lock:<task_id>`, crea stream y asigna driver/navigator.
2. **Iteración**: Driver envía `proposal` con patch/files -> Navigator ejecuta tests/lint en workspace -> Navigator responde `comment`/`patch`/`accept`.
3. **Aplicación**: Driver aplica patch sugerido o argumenta rechazo; escribe `test-result`.
4. **Convergencia**: repetir hasta `accept` o hasta `max_iters` alcanzado.
5. **Finalize**: Driver crea branch `pair/<task_id>/iter<last>` y PR incluyendo `session_id` y log resumido. Orchestrador archiva la session en `agent_logs` y limpia lock.
6. **Fallback**: si timeout o max_iters alcanzado sin `accept`, PR se crea con tag `needs-late-review` y se notifica a humano.

---

## 8. Workspace y operaciones git (recomendado)

- Runner hace `git clone` del repo sandbox o checkout base branch en `/workspaces/<session_id>`.
- Cada iteración puede aplicar parches vía `git apply` o escribir archivos y `git add && git commit -m "pair session <iter>"`.
- Antes del PR final, ejecutar `pre-commit` hooks y `pytest`.
- Artefactos: guardar snapshot `.tar.gz` del workspace en MinIO con nombre `pair_session/<session_id>/iter_<n>.tar.gz`.

---

## 9. Prompts (Driver / Navigator) — plantilla

**Driver** (dev_agent_driver_v1.md):
> Eres DevAgent-Driver. Tarea: <summary>. Debes generar un primer `proposal` con los cambios mínimos que implementen los CA. Espera la respuesta del Navigator. Documenta cada iteración con `iter`, `summary`, `files_changed`, `tests_passed`, `token_usage`.

**Navigator** (review_agent_navigator_v1.md):
> Eres ReviewAgent-Navigator. Al recibir un `proposal`, ejecuta tests y linters. Si encuentras problemas, genera un `patch` con cambios concretos o un `comment`. Si código cumple CA y pruebas pasan, responde `accept`. Prioriza seguridad y edge-cases. Explica en 1-2 frases la razón de cada cambio.

---

## 10. DoD (aplicable a pair sessions)

- Tests unitarios relevantes pasan localmente.  
- Lint & style OK.  
- No secrets en cambios.  
- Coverage mínima (configurable).  
- Prompt/responses registrados en `agent_logs`.

---

## 11. Manejo de errores y timeouts

- Heartbeat: driver/navigator envían `heartbeat` cada 30s. Si no hay heartbeat por TTL (ej. 120s), sesión marked as `stalled`.
- Retry: si falla aplicación de patch -> rollback a último snapshot y post `comment` con error.  
- Max iteraciones: configurable (ej. 6). Al superar -> finalize with `needs-late-review`.

---

## 12. Auditoría y trazabilidad

- Cada mensaje stream se persiste (resumen) en `agent_logs` con campos: session_id, iter, agent_id, prompt_id, patch_hash, tests_result, token_usage.
- Snapshots/artefactos guardados en MinIO para reconstrucción forense.
- Hashes y referencias almacenadas para firmar/cambiar autenticidad.

---

## 13. Métricas específicas de la feature

- `pair_sessions_started` (count)
- `pair_sessions_successful` (accept before max_iter)
- `avg_iters_per_session`
- `tokens_per_session`
- `ci_fail_rate_after_pairing` (compare to baseline)
- `fix_commits_after_merge`(compare paired vs unpaired)

---

## 14. Pruebas (testing plan)

- Unit tests para Pair Coordinator (locking, stream management).  
- Integration test: dummy driver+navigator local simulating a full session (use local runner).  
- End-to-end: real repo sandbox where a pair session debe crear un PR válido que pase CI.  
- Mutation testing en el driver-generated code para validar robustness.

---

## 15. Plan de rollout (phased)

1. **Phase 0 (loose-pair):** Navigator comenta PRs (sin locking ni streams). Bajo riesgo, baja inversión.  
2. **Phase 1 (tight-pair MVP):** Implement Pair Coordinator + Redis Streams + workspace runner; limit to 10% de tareas (core features).  
3. **Phase 2 (scale):** añadir mob sessions, token cost optimizations, selección automática de pairs por complejidad.  
4. **Phase 3:** métricas automáticas + autotune max_iters/token budgets.

Criterio para promover fase: reducción estadística significativa en `ci_fail_rate` y `fix_commits_after_merge` sin aumento desproporcionado en tokens/time-to-pr.`

---

## 16. Checklist para integrar al MVP

- [ ] Implementar Pair Coordinator en Orchestrator.
- [ ] Añadir Redis Streams + lock logic.
- [ ] Crear runner workspace en CI/node y scripts git apply/commit.
- [ ] Versionar prompts Driver/Navigator en `prompts/` y registrar uso.
- [ ] Implementar persistencia en `agent_logs` y snapshots en MinIO.
- [ ] Tests automáticos (unit, integration, e2e) para el flow.
- [ ] Métricas expuestas en Prometheus.
- [ ] Documentación para operación y rollback.

---

## 17. Notas operativas y recomendaciones de coste

- Monitorea tokens por session; configura límites por tipo de tarea.  
- Si los tokens son caros, considera: 1) usar modelos locales para Navigator (revisión), 2) compactar prompts (usar system prompts + few-shot), 3) cache de respuestas RAG.

---

## 18. Anexos: pseudocódigo coordinar

(Se agrega pseudocódigo de reserva, stream read/write y finalize — en el doc original para implementación)

---

*Documento creado para integración futura en el MVP. Version: 2025-10-01.*

