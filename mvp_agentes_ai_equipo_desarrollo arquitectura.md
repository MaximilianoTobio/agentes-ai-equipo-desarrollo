# MVP — Equipo de Agentes AI para Desarrollo (Documentación operativa)

**Archivo:** `MVP-Agentes-AI-Equipo-Desarrollo.md`

> Objetivo: documentación exhaustiva y accionable para análisis y ejecución del MVP que orquesta agentes IA para formar un equipo de desarrollo (metodologías ágiles + XP). Contiene: arquitectura, árbol de archivos, contratos/prompts, snippets listos (docker-stack, CI, worker), DB schema, endpoints, checklist Sprint 0, seguridad, métricas y pasos de despliegue.

---

## Índice

1. Resumen ejecutivo
2. Alcance del MVP
3. Componentes y responsabilidades
4. Diagrama de flujo (texto)
5. Árbol de archivos (mono-repo) — detalle
6. Endpoints y esquemas de comunicación
7. Contractos, prompts y plantillas (PR template, prompts maestros)
8. Base de datos: tablas clave y esquema
9. Infra y snippets ejecutables
   - docker-stack.yml completo (listo para pegar)
   - GitHub Actions (ci.yml)
   - Ejemplo `worker.py` (DevAgent)
10. Scripts y utilidades
11. Sprint 0 — backlog, DoD y checklist de validación
12. Seguridad, gobernanza y auditoría
13. Métricas y observabilidad
14. Riesgos y mitigaciones
15. Roadmap post-MVP
16. Pasos de despliegue paso a paso (comandos)
17. Control de versiones de prompts y pruebas de prompts
18. Notas operativas y recomendaciones rápidas

---

## 1. Resumen ejecutivo

Este MVP orquesta agentes IA con roles definidos (PO, ScrumMaster, Dev, QA, CI, Reviewer) para automatizar tareas repetitivas del ciclo de desarrollo: transformar epics en historias, generar código y tests, crear PRs, ejecutar CI y reportar resultados. **Principio no negociable:** humano en el loop para merges a `main`.

El diseño apuesta por un mono-repo y despliegue sobre Docker Swarm + Traefik (tú ya lo tienes en `labstation.dev`). El stack usa Python (FastAPI para el Orquestador), Redis para cola, Postgres (+ pgvector) para persistencia y RAG, y MinIO para artefactos.

---

## 2. Alcance del MVP

**Incluye:**
- Orquestador (FastAPI) con APIs básicas y UI mínima.
- Pool de Agent Workers (DevAgent, QAAgent, ReviewAgent, CICDAgent, PO, ScrumMaster functional).
- Integración con GitHub (crear branch, push, PR) y GitHub Actions para CI.
- Infra mínima en Contabo: Postgres, Redis, MinIO.
- Auditoría: registros de prompts/respuestas en DB.

**No incluye (post-MVP):** despliegues canary automáticos, agentes avanzados de seguridad/perf, marketplace de agentes.

---

## 3. Componentes y responsabilidades

- **Orchestrator (Core)**: administra backlog, sprints, encola tareas en Redis, recibe webhooks GitHub, administra estado, expone API y UI.
- **Agents (workers)**: consumen tareas, ejecutan prompts, actúan sobre repos (crear rama, commits, tests), suben resultados y logs.
- **Queue (Redis)**: `tasks:pending`, `tasks:in_progress`, `tasks:done`.
- **Postgres (+pgvector)**: metadata, audit trail, almacenamiento de embeddings.
- **MinIO**: artefactos binarios y logs pesados.
- **CI (GitHub Actions)**: pruebas, lint, build y security-scan.
- **Traefik + Docker Swarm**: routing y certificados TLS.
- **Observability**: Prometheus, Grafana, Sentry.

---

## 4. Diagrama de flujo (texto)

1. Entrada: epic/idea → POST `/api/epics` en Orchestrator.
2. POAgent genera historias → Orchestrator crea `stories` y encola `tasks` en Redis.
3. DevAgent consume tarea, recupera contexto (RAG) y repo, crea rama `feature/X`, implementa código + `pytest` tests.
4. DevAgent push → crea PR via GitHub API.
5. GitHub webhook → Orchestrator y CICDAgent trigger CI.
6. QAAgent y ReviewAgent analizan resultados y añaden comentarios/etiquetas al PR.
7. Notificación a humano (UI/Slack/Telegram). Humano revisa y aprueba/deniega.
8. Merge → deploy a `staging` (pipeline). Smoke tests automáticos.
9. ScrumMasterAgent genera métricas y retro; updates backlog.

---

## 5. Árbol de archivos (mono-repo) — detalle

```
/ (repo-root)
├─ .github/
│  └─ workflows/
│     ├─ ci.yml
│     └─ deploy.yml
├─ infra/
│  ├─ docker-stack.yml
│  ├─ traefik/
│  │  ├─ dynamic.yml
│  │  └─ static.yml
│  └─ terraform/ (opcional)
├─ services/
│  ├─ orchestrator/
│  │  ├─ app/
│  │  │  ├─ main.py
│  │  │  ├─ api/
│  │  │  │  ├─ endpoints_epics.py
│  │  │  │  ├─ endpoints_tasks.py
│  │  │  │  └─ webhooks.py
│  │  │  ├─ models/
│  │  │  │  └─ db_models.py
│  │  │  └─ ui/ (React/Vite simple)
│  │  ├─ Dockerfile
│  │  └─ requirements.txt
│  ├─ agents/
│  │  ├─ dev_agent/
│  │  │  ├─ worker.py
│  │  │  ├─ prompts/
│  │  │  │  └─ dev_agent_v1.md
│  │  │  ├─ Dockerfile
│  │  │  └─ requirements.txt
│  │  ├─ qa_agent/
│  │  ├─ review_agent/
│  │  └─ cicd_agent/
│  └─ workers-common/
├─ infra-scripts/
│  ├─ bootstrap.sh
│  └─ migrate_db.sh
├─ docs/
│  ├─ architecture.md
│  └─ prompts.md
├─ prompts/
│  ├─ dev_agent_v1.md
│  ├─ dev_agent_v2.md
│  └─ po_agent_v1.md
├─ migrations/
├─ scripts/
│  ├─ gh_create_pr.py
│  └─ run_local_worker.sh
├─ tests/
├─ .env.example
└─ README.md
```

### Explicación rápida por carpeta
- `services/orchestrator/app/api` — endpoints REST y webhook handler.
- `services/agents/*/prompts` — prompt templates versionadas.
- `workers-common` — utilidades compartidas (GitHub client, OpenAI client wrapper, logger, retry logic).
- `infra-scripts/bootstrap.sh` — scripts para inicializar servicios en Swarm.

---

## 6. Endpoints y esquemas de comunicación

**Orchestrator API (REST)**

- `POST /api/epics` — crear epic (body: title, description, owner_id)
- `GET  /api/backlog` — listar historias y tareas
- `POST /api/sprints` — crear sprint (body: start, end, stories[])
- `POST /api/tasks/{task_id}/assign` — asignar tarea a un agente
- `GET  /api/metrics` — obtener métricas del sprint
- `POST /webhooks/github` — recibir eventos PR/status

**Colas Redis**
- Key `tasks:pending` (list)
- Key `tasks:in_progress`
- Key `tasks:done`

**GitHub**
- Agents usan tokens para crear branches, push y abrir PRs (REST API v3). Webhooks notifican PR opened, PR status.

---

## 7. Contratos, prompts y plantillas

### 7.1 Prompt maestro — DevAgent (versión ejemplo)

```
Eres DevAgent (Python).
Entradas:
- repo_url
- issue_id
- criterios_de_aceptacion (lista)
- contexto_RAG (resumen)

Objetivos (ordenados):
1. Crear rama: feature/ISSUE-<id>
2. Scaffold y/o modificar archivos necesarios.
3. Implementar funcionalidad en Python con tests (pytest) que cubran CA.
4. Incluir Dockerfile si aplica.
5. Ejecutar tests locales. Si fallan, corregir antes de push.
6. Hacer push y crear PR con PR template.

Si hay ambigüedades, escribe un bloque `CLARIFY:` con preguntas concretas (máx 5).
```

Guarda este prompt en `prompts/dev_agent_v1.md` y **siempre** registra (persistir) el prompt completo usado en `agent_logs` para auditoría.

### 7.2 PR template (archivo .github/PULL_REQUEST_TEMPLATE.md)

```md
# PR: [ISSUE-###] Título

## Descripción
- Resumen corto

## Criterios de aceptación
- [ ] CA1
- [ ] CA2

## Checklist (DoD)
- [ ] Tests unitarios pasan (pytest)
- [ ] Linter OK
- [ ] Coverage mínima (si aplica)
- [ ] Documentación actualizada
- [ ] Security scan

## Notas adicionales
```

---

## 8. Base de datos: tablas clave y esquema (Postgres)

### Tablas principales (simplificadas)

```sql
CREATE TABLE users (
  id serial PRIMARY KEY,
  name text,
  role text,
  github_id text
);

CREATE TABLE epics (
  id serial PRIMARY KEY,
  title text,
  description text,
  created_by int references users(id),
  status text,
  created_at timestamptz default now()
);

CREATE TABLE stories (
  id serial PRIMARY KEY,
  epic_id int references epics(id),
  title text,
  acceptance_criteria jsonb,
  estimate int,
  status text
);

CREATE TABLE tasks (
  id serial PRIMARY KEY,
  story_id int references stories(id),
  assigned_to text, -- agent id or human id
  status text,
  attempt_count int default 0,
  payload jsonb
);

CREATE TABLE pr_records (
  id serial PRIMARY KEY,
  pr_number int,
  repo text,
  branch text,
  status text,
  result jsonb,
  created_at timestamptz default now()
);

CREATE TABLE agent_logs (
  id serial PRIMARY KEY,
  agent text,
  task_id int references tasks(id),
  prompt text,
  response text,
  decision text,
  metadata jsonb,
  created_at timestamptz default now()
);

-- pgvector table for embeddings
CREATE TABLE embeddings (
  id serial PRIMARY KEY,
  source text,
  embedding vector(1536),
  metadata jsonb
);
```

> Nota: ajusta la dimensión vectorial según modelo que uses.

---

## 9. Infra y snippets ejecutables

A continuación hay artefactos listos para usar. **Asegúrate de reemplazar secretos** en `.env` o Docker secrets.

### 9.1 `infra/docker-stack.yml` (completo — ejemplo)

```yaml
version: "3.8"
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: "${POSTGRES_PASSWORD}"
    volumes:
      - pgdata:/var/lib/postgresql/data
    deploy:
      restart_policy:
        condition: on-failure

  redis:
    image: redis:7
    deploy:
      restart_policy:
        condition: on-failure

  minio:
    image: minio/minio:latest
    command: server /data
    environment:
      MINIO_ROOT_USER: "${MINIO_ROOT_USER}"
      MINIO_ROOT_PASSWORD: "${MINIO_ROOT_PASSWORD}"
    volumes:
      - minio_data:/data
    deploy:
      restart_policy:
        condition: on-failure

  orchestrator:
    build: ../services/orchestrator
    env_file: ../.env
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 1
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.orchestrator.rule=Host(`orchestrator.labstation.dev`)"

  dev_agent:
    build: ../services/agents/dev_agent
    env_file: ../.env
    depends_on:
      - orchestrator
      - redis
    deploy:
      replicas: 2
      labels:
        - "traefik.enable=false"

volumes:
  pgdata:
  minio_data:
```

> Ajusta rutas `build` si usas contexto de despliegue distinto. En Swarm, normalmente subes el repo al host y corres `docker stack deploy -c infra/docker-stack.yml stackname`.

### 9.2 GitHub Actions — `.github/workflows/ci.yml`

```yaml
name: CI
on:
  pull_request:
    types: [opened, synchronize, reopened]

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
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run unit tests
        run: pytest -q
      - name: Lint
        run: |
          pip install flake8
          flake8 . --max-line-length=120 || true
      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: pytest-report
          path: tests/reports || ''
```

### 9.3 Ejemplo `worker.py` (DevAgent — minimal)

```python
# services/agents/dev_agent/worker.py
import os
import time
import json
import redis
import requests
from github import Github
# from openai import OpenAI  # usa tu wrapper

REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')
redis_client = redis.from_url(REDIS_URL)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GH = Github(GITHUB_TOKEN)

QUEUE = 'tasks:pending'


def process_task(task_json):
    data = json.loads(task_json)
    repo_full = data['repo']
    issue_id = data['issue_id']
    # 1. obtener contexto (simplificado)
    # 2. generar patch con LLM (omitido)
    # 3. crear branch y commit localmente o via API
    repo = GH.get_repo(repo_full)
    base_branch = repo.get_branch('main')
    new_branch_name = f"feature/issue-{issue_id}"
    try:
        repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=base_branch.commit.sha)
    except Exception as e:
        print('branch exists or error', e)
    # TODO: apply changes via git operations or create file via API
    # crear PR
    pr = repo.create_pull(title=f"[ISSUE-{issue_id}] Implement feature",
                          body="Auto-generated PR by DevAgent",
                          head=new_branch_name,
                          base='main')
    print('PR created', pr.number)


if __name__ == '__main__':
    while True:
        task = redis_client.lpop(QUEUE)
        if not task:
            time.sleep(2)
            continue
        try:
            process_task(task.decode())
        except Exception as e:
            print('Error processing task', e)
```

> **Advertencia:** en producción evita crear commits/pr mediante la API sin controles. Mejor usar un runner que haga `git` en un workspace para aplicar parches y ejecutar tests.

---

## 10. Scripts y utilidades

- `scripts/bootstrap.sh` — prepara volúmenes, crea DB, corre migraciones.
- `scripts/migrate_db.sh` — ejecutar Alembic migrations.
- `scripts/run_local_worker.sh` — arranca un worker local conectándose a Redis.
- `scripts/gh_create_pr.py` — helper para crear PRs en tests locales.

Incluye pruebas locales en `tests/agents` para validar que `worker.py` crea PRs en repos sandbox.

---

## 11. Sprint 0 — backlog, DoD y checklist

### Sprint 0 (1 semana, objetivo: poner en marcha el ciclo completo con un PR automático)

Tareas mínimas:
1. Desplegar infra mínima (Postgres+pgvector, Redis, MinIO, Orchestrator, DevAgent). **DoD:** servicios accesibles y `orchestrator` responde `/health`.
2. Configurar token GitHub y webhook. **DoD:** push de prueba dispara webhook.
3. Implementar `worker.py` MVP que crea PR en repo sandbox. **DoD:** PR visible en GitHub.
4. Pipeline CI básico (pytest) funcionando. **DoD:** PR ejecuta job `test` y pasa si tests verdes.
5. UI mínima: mostrar backlog y lista de PRs. **DoD:** login básico y ver items.

Checklist de validación final Sprint 0:
- [ ] PR creado por DevAgent
- [ ] CI pasa en PR
- [ ] Logs de agent en `agent_logs` con prompt y respuesta
- [ ] Human gate configurado (branch protection)
- [ ] Métricas básicas recogidas (lead time ejemplo)

---

## 12. Seguridad, gobernanza y auditoría

- **Tokens mínimos:** GitHub token con scope limitado (repo, workflow if needed). OpenAI key con secret management.
- **Secrets:** usar Docker secrets o Vault; jamás commit a repo.
- **Audit trail:** guardar prompt completo y respuesta en `agent_logs` para cada acción automática.
- **Branch protection:** `main` protegido; required reviewers (human).
- **Scans:** dependabot/Snyk/Owasp Dependency Check en CI.

---

## 13. Métricas y observabilidad

Métricas a recolectar desde el principio:
- Lead time: issue → merged
- PR cycle time: open → merged
- Tests pass rate
- API tokens usage por agente (tokens/sprint)
- Flaky tests rate
- Número de `CLARIFY:` emitidos por sprint

Observability:
- Logs centralizados (MinIO/artifacts + DB minimal)
- Prometheus metrics endpoint en Orchestrator y agents
- Grafana dashboard mínimo: sprint metrics, queue length, agents up, token spend
- Sentry para excepciones

---

## 14. Riesgos y mitigaciones

- **Overtrust LLM**: humano obligado para merges. Tests + coverage obligatorios.
- **API costs**: cache RAG responses, usar modelos locales para pruebas (Ollama), limitar llamadas de dev-agent en pruebas.
- **Secrets leakage**: Vault + rotate tokens.
- **Bad PRs**: ReviewAgent + QAAgent + pipeline que no permita merge sin checks.

---

## 15. Roadmap post-MVP (priorizado)

1. RAG avanzado: pgvector/Qdrant + retriever-seat tuning.
2. Agents especializados: SecurityAgent, PerfAgent, InfraAgent.
3. Self-hosted runners para heavy CI jobs.
4. Canary deploys automáticos y rollback.
5. Marketplace interno de prompts/agentes.

---

## 16. Pasos de despliegue (rápido)

1. Clona repo en host: `git clone <repo>`
2. Copia `.env.example` a `.env` y completa secretos.
3. En host Swarm: `docker stack deploy -c infra/docker-stack.yml labstack`.
4. Espera que servicios suban: `docker service ls`.
5. Ver logs: `docker service logs labstack_orchestrator -f --tail 200`.
6. Inicializa BD: `docker exec -it <postgres_container> psql -U postgres -c "CREATE DATABASE orchestrator;"` o usa `bootstrap.sh`.
7. Arranca worker locally para pruebas: `./scripts/run_local_worker.sh`.
8. Prueba flow: POST `/api/epics` con payload de prueba; espera PR generado.

---

## 17. Control de versiones de prompts y pruebas de prompts

- Cada prompt se versiona en `prompts/` con `*_vN.md`.
- Para cada versión, hay tests unitarios que simulan inputs esperados y validan el formato del output (por ejemplo, JSON con keys `branch`, `files`, `tests`).
- Registro en DB `agent_logs` del prompt exacto (texto) y la respuesta para auditoría y retraining.

---

## 18. Notas operativas y recomendaciones rápidas

- Empieza con un repositorio sandbox público/privado para pruebas; no uses `main` de proyectos reales.
- Mantén el humano en el loop por al menos 3 sprints antes de automatizar merges.
- Mide tokens y costos desde la primera semana.
- Prioriza tests y DoD sobre la velocidad de entrega en sprint 0.

---

### Archivo generado por: ChatGPT — documento técnico operativo (versión: 2025-10-01)

*Si querés, ahora:*
- Genero archivos individuales `docker-stack.yml`, `.github/workflows/ci.yml` y `services/agents/dev_agent/worker.py` listos para descargar; o
- Transformo la estructura en un `cookiecutter` / scaffold repo que puedas `git clone` y desplegar.

Dime cuál prefieres y lo preparo inmediatamente.

