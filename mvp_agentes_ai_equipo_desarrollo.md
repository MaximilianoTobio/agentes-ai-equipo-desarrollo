# MVP — Equipo de desarrollo formado por agentes AI

**Nombre archivo:** `MVP-Agentes-AI-Equipo-Desarrollo.md`

> Documento técnico y operativo para el MVP: orquestador de agentes AI que producen software siguiendo metodologías ágiles + XP. Enfocado a despliegue práctico en infraestructura existente (Docker Swarm + Traefik en `labstation.dev`).

---

## 1. Resumen ejecutivo (1 párrafo)

Construiremos un MVP que permita orquestar un *equipo de agentes AI* (Product Owner, Scrum Master, Dev, QA, CI) para generar, testear y preparar despliegues de software. El flujo mantiene un **humano en el loop** para garantizar calidad y seguridad: nada se mergea a `main` sin aprobación humana. El objetivo es validar que los agentes puedan automatizar la mayor parte del ciclo de desarrollo rutinario (scaffold → tests → PR → pipeline → reports) reduciendo tiempo de ejecución y manteniendo trazabilidad.

---

## 2. Objetivos del MVP

- Probar la viabilidad técnica de agentes AI que:
  - Generen código y tests a partir de historias de usuario.
  - Empaqueten cambios como PRs con DoD.
  - Disparen pipelines CI y analicen resultados.
- Mantener seguridad y control humano en merges y despliegues.
- Medir métricas clave (lead time, PR cycle, tokens API by sprint).

---

## 3. Componentes y roles

### 3.1 Orquestador (Core)
- **Tipo:** Servicio FastAPI.
- **Funciones:** gestionar backlog, asignar tareas, coordinar agentes, exponer API para la UI y webhooks de GitHub.
- **Persistencia:** PostgreSQL (metadatos) + pgvector para embeddings RAG.

### 3.2 Agentes (microservicios / workers)
- **ProductOwnerAgent**: transforma epics/inputs en historias de usuario con criterios de aceptación.
- **ScrumMasterAgent**: crea sprints, asigna tareas, genera resúmenes y métricas.
- **DevAgent**: genera código, tests (pytest), commits atómicos, Dockerfile, y PRs.
- **QAAgent**: crea y ejecuta tests de integración/contrato, revisa cobertura.
- **CICDAgent**: dispara pipelines y analiza resultados, reporta fallos.
- **ReviewAgent (LLMReviewer)**: revisa calidad de código, chequeos básicos de seguridad, estilo y complejidad.
- **Human Gate**: punto obligatorio de aprobación antes del merge a `main`.

### 3.3 Infra mínima
- Docker Swarm + Traefik (ya disponibles en `labstation.dev`).
- Servicios: Postgres (+ pgvector), Redis, MinIO, Orquestador, Agent Workers, GitHub Actions Runner (opcional), Prometheus/Grafana, Sentry.

---

## 4. Flujo end-to-end (Sprint → Deploy)

1. Input: **Epic/Idea** (texto, voz o archivo). ProductOwnerAgent genera backlog con US y criterios de aceptación.
2. ScrumMasterAgent define sprint y asigna US a DevAgents.
3. DevAgent toma US, recupera contexto (RAG), crea rama `feature/ISSUE-###`, implementa código + `pytest` unit tests, ejecuta tests locales.
4. DevAgent push → crea PR con template y checklist de DoD.
5. CICDAgent dispara pipeline (GitHub Actions): lint → pytest → build image.
6. QAAgent ejecuta pruebas adicionales y ReviewAgent revisa PR.
7. Notificación al humano (slack/telegram/ui) para revisión rápida.
8. Humano aprueba → merge → deploy a staging.
9. Smoke tests automáticos, then manual decision for production.
10. ScrumMasterAgent compila métricas y genera retro.

---

## 5. Contratos y prompts clave

> **Nota:** estos son *contratos de comportamiento* para los agentes; deben ser implementados como prompts + validaciones lógicas.

### 5.1 Prompt maestro — DevAgent (esqueleto)

```
Eres DevAgent (Python). Entradas:
- repo_url
- issue_id
- criterios_de_aceptacion
- contexto_RAG (resume)

Objetivo:
1. Crear rama: feature/ISSUE-<id>
2. Implementar funcionalidad en Python (máximo 500 LOC por PR preferible).
3. Escribir tests con pytest que cubran comportamiento.
4. Añadir Dockerfile y/o cambios infra necesarios mínimos.
5. Hacer commits atómicos con mensajes claros.
6. Ejecutar tests locales; si fallan, corregir antes de push.
7. Crear PR con descripción, checklist DoD y artifacts.

Si algo no está claro, devuelve un bloque `CLARIFY:` con preguntas concretas (máximo 5 preguntas).
```

### 5.2 PR template (Markdown)

```md
# PR: [ISSUE-123] Título corto

## Descripción
- Resumen: ...
- Issue relacionado: #123

## Criterios de aceptación
- [ ] CA1
- [ ] CA2

## Checklist (DoD)
- [ ] Tests unitarios pasan (pytest)
- [ ] Linter OK
- [ ] Coverage >= X% (si aplica)
- [ ] Docs actualizados
- [ ] Scan básico de deps

## Artefactos
- Imagen: repo/feature-123:sha
```

---

## 6. Sprint 0 — backlog mínimo para arrancar

1. Deploy infra mínima en Contabo (postgres+pgvector, redis, minio, orquestador, worker). DoD: servicios accesibles por Traefik.
2. Integración GitHub: webhook y token. DoD: push->orquestador recibe evento.
3. DevAgent MVP: capaz de crear rama, scaffold endpoint y tests; crear PR. DoD: PR creado automáticamente.
4. CI básico: pytest + lint job. DoD: job verde en PR.
5. Web UI mínimo (lista backlog, PRs, approve button). DoD: login (basic), ver items.
6. Human Gate: proteger `main` y crear proceso de revisión manual.

---

## 7. Ejemplos técnicos mínimos

### 7.1 `docker-stack.yml` minimal (snippet)

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: "changeme"
  redis:
    image: redis:7
  orchestrator:
    image: labstation/orchestrator:latest
    environment:
      - DATABASE_URL=postgres://postgres:changeme@postgres:5432/orc
      - REDIS_URL=redis://redis:6379
    deploy:
      replicas: 1

volumes:
  pgdata:
```

> Ajusta secrets y servicios según tus políticas.

### 7.2 GitHub Actions (job pytest) — snippet

```yaml
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest -q
```

---

## 8. Seguridad y gobernanza

- **No merge automático** a `main` — aprobación humana obligatoria.
- Tokens con *scope mínimo*; rotación cada X días.
- Escaneo de dependencias en CI (snyk/owasp deps).
- Auditable: registrar decisión de cada agente (razón y prompt usado) en DB.

---

## 9. Métricas a medir desde el día 1

- Lead time (issue -> merge)
- PR cycle time
- % tests passing
- Cost de API por sprint (tokens, $)
- Flaky-test rate
- Número de aclaraciones `CLARIFY:` por sprint (indica specs incompletas)

---

## 10. Riesgos y mitigaciones rápidas

- **Drift de código**: cobertura obligatoria y revisión humana.
- **Costos**: usar modelos locales (Ollama) para pruebas intensivas; cachear resultados del RAG.
- **Seguridad**: restringir permisos de agentes y usar Vault.

---

## 11. Roadmap (post-MVP)

1. RAG con pgvector/Qdrant para contexto profundo.
2. Agentes especializados (security, infra, perf).
3. Runner self-hosted para pruebas costosas.
4. Autodeploy con canary + rollback automático.
5. Marketplace interno de agentes (plugins: formatter, i18n, accessibility).

---

## 12. Artefactos entregados en este .MD

- Prompt maestro DevAgent (sección 5.1)
- PR template (sección 5.2)
- Snippets: `docker-stack.yml` y GitHub Actions (sección 7)
- Sprint 0 checklist (sección 6)

---

## 13. Próximos pasos recomendados (acción inmediata)

1. Ejecutar Sprint 0: montar infra mínima y validar que un DevAgent pueda crear un PR simple.
2. Medir consumo de tokens y velocidad del cycle en ese primer PR.
3. Ajustar prompts y DoD según resultados.
4. Implementar Human Gate y reglas de seguridad.

---

## 14. Notas finales — Tenlo presente

Esto es un MVP deliberadamente conservador: maximizar automatización repetitiva, minimizar riesgo. Lo importante es **control**, **trazabilidad** y **medición**: si los agentes generan valor repetible en sprint 0, entonces acelerarás con confianza.


---

*Documento generado para Max — visión práctica, sin rodeos, listo para implementación.*

