# Estándares del Proyecto y Scaffold del Repositorio

**Archivo:** `Project-Standards-and-Repo-Scaffold.md`

> Documento operativo y accionable con todo lo necesario para mantener coherencia en la construcción del proyecto: prioridades de documentación, archivos esenciales, templates listos para pegar, runbooks mínimos, métricas a exponer y checklist de arranque. Estilo práctico y directo, coherente con los otros MD ya generados.

---

## Índice

1. Resumen corto
2. Prioridad P1 — Obligatorio ahora
3. Prioridad P2 — Corto plazo
4. Prioridad P3 — Escala y madurez
5. Estructura del repositorio (mapa rápido)
6. Labels recomendados para GitHub
7. Plantillas y fragmentos listos para pegar (archivos)
   - ISSUE_TEMPLATE/feature.md
   - CONTRIBUTING.md (resumen)
   - .pre-commit-config.yaml
   - Makefile básico
   - devcontainer.json (esqueleto)
8. Procesos y convenciones mínimas (obligatorias)
9. Runbooks operativos mínimos (ops)
10. Dashboard y métricas prioritarias
11. Sugerencia práctica inmediata: qué generar ahora
12. Checklist de onboarding para nuevos colaboradores
13. Notas finales — prioridades tácticas

---

## 1. Resumen corto

Este documento resume lo esencial para que el proyecto crezca ordenado, sea fácil de clonar por otro dev y mantenga prácticas ágiles + XP. Está pensado para ser el "tronco" del repo: copies/pegas los archivos, los versionas y arrancás.

---

## 2. Prioridad P1 — obligatorio ahora

1. `README.md` + Quickstart: comandos para levantar infra dev.
2. `CONTRIBUTING.md` claro y corto.
3. `.github/ISSUE_TEMPLATE/*` (bug, feature, spike, tech-debt).
4. `.pre-commit-config.yaml` con black/isort/flake8/detect-secrets.
5. `devcontainer.json` o `docker-compose.dev.yml` para dev reproducible.
6. `Makefile` con comandos dev comunes.
7. `CI básico` (.github/workflows/ci.yml) que falle si no pasan checks.
8. `SECURITY.md` y política de secretos (usar Docker secrets/Vault).
9. `CHANGELOG.md` (Keep a Changelog).
10. `prompts/README.md` — registro de prompts (versionado y golden outputs).

---

## 3. Prioridad P2 — corto plazo

11. `CODE_OF_CONDUCT.md` y `OWNERS.md` (roles por módulo).
12. Project board (Backlog/Sprint/In Progress/Review/Done) y labels.
13. `pre_push_check.sh` (runner local para TDD & lint antes del push).
14. Pruebas de prompts (mock LLM) y harness de validación de formatos.
15. Observability runbook y alerting básico.
16. Token & cost dashboard (job recurrente para token_usage).
17. Dependabot/Snyk integration en CI.
18. Policy/automation para rota de ownership.

---

## 4. Prioridad P3 — escala y madurez

19. Feature flags y pequeña estrategia de despliegues.
20. Automated retros y ScrumMasterAgent avanzado.
21. RefactorAgent + SonarQube.
22. Marketplace/registry de Agents y versionado semántico.
23. Data governance para RAG/datasets.

---

## 5. Estructura del repositorio (mapa rápido)

```
/ (repo-root)
├─ .github/
│  └─ workflows/
│     └─ ci.yml
├─ infra/
│  ├─ docker-stack.yml
│  └─ docker-compose.dev.yml
├─ services/
├─ prompts/
│  ├─ README.md
│  └─ dev_agent_v1.md
├─ scripts/
├─ docs/
├─ tests/
├─ .env.example
├─ README.md
└─ CONTRIBUTING.md
```

---

## 6. Labels recomendados

`priority/high`, `priority/low`, `type/bug`, `type/feature`, `type/spike`, `type/tech-debt`, `stage/sprint`, `cost/high`, `needs-human`, `pair-session`, `security`.

---

## 7. Plantillas y fragmentos listos para pegar

> Los siguientes archivos están listos para copiar en tu repo. Pégalos tal cual en las rutas indicadas.

### `.github/ISSUE_TEMPLATE/feature.md`

```md
---
name: Feature
about: Propuesta de nueva funcionalidad
title: "[FEATURE] "
labels: ["type/feature", "priority/low"]
assignees: []
---

## Resumen
(Qué hacemos y por qué)

## Criterios de aceptación
- [ ] CA1
- [ ] CA2

## Alcance
(Qué incluye / qué no incluye)

## Impacto
- Módulos impactados:
- Estimación (puntos o tiempo):

## Notas técnicas / riesgos
```

### `CONTRIBUTING.md` (resumen)

```md
# Contribuir

1. Fork / Branch naming: `feature/<ticket>-short-desc`, `bug/<ticket>-short`.
2. Tests: cada PR debe incluir tests. TDD preferible.
3. Pre-commit: instala `pre-commit` y ejecuta `pre-commit install`.
4. PR template: referencia al issue; incluye checklist DoD.
5. Revisiones: 1 review humano mínimo; no merge automático a `main`.
6. Security: no commits con secretos. Usa Docker secrets / Vault.
```

### `.pre-commit-config.yaml`

```yaml
repos:
- repo: https://github.com/psf/black
  rev: 24.1.0
  hooks:
    - id: black
- repo: https://github.com/PyCQA/isort
  rev: 5.12.0
  hooks:
    - id: isort
- repo: https://github.com/pre-commit/mirrors-flake8
  rev: v6.1.0
  hooks:
    - id: flake8
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.0.4
  hooks:
    - id: detect-secrets
```

### `Makefile` (rápido)

```makefile
.PHONY: up down test lint shell worker

up:
	docker compose -f docker-compose.dev.yml up -d --build

down:
	docker compose -f docker-compose.dev.yml down

test:
	pytest -q

lint:
	black . --check
	flake8

worker:
	python services/agents/dev_agent/worker.py
```

### `devcontainer.json` (esqueleto)

```json
{
  "name": "Labstation Dev",
  "dockerComposeFile": ["docker-compose.dev.yml"],
  "service": "orchestrator",
  "workspaceFolder": "/workspace",
  "extensions": ["ms-python.python", "eamodio.gitlens"]
}
```

---

## 8. Procesos y convenciones mínimas (obligatorias)

- **Commits:** usar Conventional Commits (`feat:`, `fix:`, `chore:`).
- **PR size limit:** ideal < 200 LOC.
- **TDD policy:** tests primero — DevAgent y humanos deben generar tests antes de implementar.
- **Prompt versioning:** cada prompt en `prompts/` con `vX` y `examples/`.
- **Audit trail:** registrar prompt/respuesta y patches en `agent_logs`.

---

## 9. Runbooks operativos mínimos

- `ops/incident.md`: pasos para rollback, cómo desactivar agentes, revocar tokens.
- `ops/token_budget.md`: cómo ver y corregir overruns.
- `ops/deploy.md`: pasos para despliegue manual si CI falla.

---

## 10. Dashboard y métricas prioritarias

- PR cycle time
- Lead time (issue -> merge)
- Tests pass rate
- Token spend per sprint
- Queue length
- Number of pair sessions
- Refactor PRs opened/merged
- CI failure rate

---

## 11. Sugerencia práctica inmediata: qué generar ahora

Generar estos archivos y añadirlos al repo:
- `CONTRIBUTING.md` (completo)
- `.github/ISSUE_TEMPLATE/*` (bug/feature/spike/debt)
- `.pre-commit-config.yaml`
- `Makefile`
- `prompts/README.md`
- `devcontainer.json` o `docker-compose.dev.yml`

Puedo generarlos todos ahora y pegarlos en el canvas/repo si quieres.

---

## 12. Checklist de onboarding para nuevos colaboradores

- [ ] Clonar repo y ejecutar `make up`.
- [ ] Instalar `pre-commit` y ejecutar `pre-commit install`.
- [ ] Revisar `CONTRIBUTING.md` y presentar PR small (<200 LOC).
- [ ] Ejecutar tests: `make test`.
- [ ] Revisar prompts en `prompts/` y ejecutar prompt-tests locales.

---

## 13. Notas finales — prioridades tácticas

1. Empieza por P1 hoy mismo: te dará disciplina y escalabilidad inmediata.
2. No automatices merges: primero TDD + DoD deben estar en su lugar.
3. Versiona prompts desde el día 1: son el núcleo del conocimiento del proyecto.
4. Documenta runbooks simples para emergencias: es lo que te salva cuando algo falla en prod.

---

Documento generado para Max — visión práctica, sin vueltas. (2025-10-01)

