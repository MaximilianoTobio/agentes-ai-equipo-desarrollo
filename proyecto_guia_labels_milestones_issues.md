# Guía: Crear el Proyecto en la sección "Proyectos" — Labels, Milestones, Releases y Plantillas de Issues

**Archivo:** `Proyecto-Guia-Labels-Milestones-Issues.md`

> Documento práctico y directo para crear y gestionar el Proyecto dentro de la sección *Proyectos* del chat. Incluye pasos para subir los MD como tronco del proyecto, cómo configurar etiquetas (labels), milestones/releases, plantillas de issues, tablero Kanban, y un mini-glosario con explicaciones sencillas para que no te pierda nada en el flujo de desarrollo.

---

## 1. Objetivo de este documento

Que configures el proyecto correctamente en la sección *Proyectos* y entiendas claramente qué son y para qué sirven:
- **Labels** (etiquetas): categorizar y priorizar issues rápidamente.
- **Milestones / Releases**: agrupar trabajo por objetivos y fechas.
- **Plantillas de Issues**: estandarizar lo que debe contener un issue para que cualquiera (agente o humano) pueda trabajar con claridad.

Además incluyo plantillas, convenciones y un checklist que pegás en el Proyecto para arrancar hoy.

---

## 2. Pasos rápidos para crear el Proyecto y subir los MD

1. En la sección *Proyectos* crea un nuevo proyecto con nombre: `Agentes-AI-Equipo-Desarrollo`.
2. Descripción corta: "Orquestador + agentes IA para formar un equipo de desarrollo ágil (XP). Fuente: documentos técnicos (MVP, Pair, XP compliance, scaffold)."
3. Crea columnas Kanban: `Backlog`, `Sprint 0 / To Do`, `In Progress`, `In Review`, `Blocked`, `Done`.
4. Sube los documentos que ya generamos (archivos MD):
   - `MVP-Agentes-AI-Equipo-Desarrollo.md`
   - `Feature-Pair-Programming-Agentes.md`
   - `XP-Agile-Compliance-and-Features.md`
   - `Project-Standards-and-Repo-Scaffold.md`
   - `Project-Standards-and-Repo-Scaffold` (otros si existen)
   Subirlos como archivos del proyecto o pegarlos en la sección de archivos del proyecto.
5. Crea los labels recomendados (siguientes sección).
6. Crea milestones (siguientes sección) y asignalos a issues cuando los crees.
7. Copia/pega las plantillas de issues (más abajo) en la configuración de issues del proyecto.
8. Crea el backlog inicial (usa los 10 issues que te pasé) y organízalos en `Backlog` o `Sprint 0 / To Do` según prioridad.

---

## 3. Labels — qué son y cómo usarlos

**Qué son:** etiquetas cortas que se aplican a issues y PRs para clasificarlos por tipo, prioridad, estado o coste. Son filtros rápidos para ver lo que importa.

**Por qué importan:** con muchos issues y agentes, los labels te permiten filtrar, priorizar y asignar trabajo sin leer cada issue.

**Convención recomendada (nombre / color sugerido):**
- `priority/high` — trabajo crítico. (rojo)
- `priority/medium` — importante pero no crítico. (naranja)
- `priority/low` — baja prioridad. (gris)
- `type/feature` — nuevas funcionalidades. (azul)
- `type/bug` — errores. (rojo oscuro)
- `type/spike` — investigación / prueba de concepto. (purple)
- `type/tech-debt` — deuda técnica. (brown)
- `stage/sprint` — para agrupar por sprint activo. (teal)
- `cost/high` — tareas con alto costo / tokens. (dark red)
- `needs-human` — requiere intervención humana. (yellow)
- `pair-session` — tarea que usará pair programming entre agentes. (light blue)
- `security` — asuntos de seguridad. (black)
- `blocked` — bloqueado por dependencia externa. (dark grey)
- `ready-for-review` — listo para revisión humana. (green)

**Cómo aplicarlos (reglas simples):**
- Cada issue debe tener al menos 2 labels: un `type/*` y un `priority/*`.
- Usa `needs-human` para tareas que los agentes no deben tocar hasta intervención humana.
- Usa `pair-session` para identificar tasks en las que quieres activar pairing.
- Cuando mueves a `In Review` añade `ready-for-review`.

---

## 4. Milestones y Releases — qué son y cómo usarlos

**Qué son (en pocas palabras):**
- **Milestone:** objetivo o hito que agrupa varios issues hacia una meta (por ejemplo: `Sprint 0 — Infra & PR MVP`).
- **Release:** normalmente una versión entregable (ej.: `v0.1-MVP`) que se despliega o se considera entregada al cliente.

**Por qué usar milestones/release:**
- Mantienen foco: todos saben qué issues deben cerrarse para alcanzar el objetivo.
- Permiten reporting: ver % completado del milestone y qué falta.
- Ordenan entregas: agrupas PRs/Issues que entran en una release.

**Convenciones prácticas:**
- Crea milestones por sprint y uno por release: `Sprint 0 — Infra & PR MVP`, `Sprint 1 — Pair MVP`, `MVP Release v0.1`.
- Asigna issues al milestone correspondiente al crearlo. Si el issue cruza sprints, crea subtasks y asigna las subtareas a milestones distintos.
- Usa fechas objetivo para los milestones (esto ayuda a priorizar).

**Ejemplo:**
- Milestone: `Sprint 0 — Infra & PR MVP` (start: 2025-10-02 — end: 2025-10-09) → incluye issues de infra, devagent MVP, CI básica.
- Release: `v0.1-MVP` → taggable cuando la mayoría (ej. 90%) de issues del milestone están cerrados y QA manual ok.

---

## 5. Plantillas de Issues — por qué y ejemplos

**Por qué usarlas:** uniformidad. Cuando todos los issues siguen el mismo formato, los agentes (y las personas) pueden procesarlos automáticamente: generar subtasks, estimar, correr tests, etc.

**Qué debe incluir toda plantilla (mínimo):**
- Título claro y conciso.  
- Resumen/Descripción corta (qué y por qué).  
- Criterios de aceptación (CA) — verificables.  
- Alcance (qué incluye y qué no).  
- Pasos de validación / DoD.  
- Estimación (puntos o tiempo).  
- Labels sugeridos.

**Plantillas sugeridas (pegar en .github/ISSUE_TEMPLATE):**

1) `feature.md` (ya lo generamos).  
2) `bug.md` — formato rápido: descripción, pasos para reproducir, logs, impacto, labels.  
3) `spike.md` — investigación: objetivo, exit criteria, tiempo estimado.  
4) `tech-debt.md` — impacto, riesgo, esfuerzo estimado.

**Ejemplo de `bug.md`:**
```md
---
name: Bug
about: Reporta un fallo
title: "[BUG] "
labels: ["type/bug", "priority/high"]
---

## Resumen
(Que pasó en 1-2 líneas)

## Pasos para reproducir
1. Paso 1
2. Paso 2

## Resultado actual
(Qué pasa ahora)

## Resultado esperado
(Qué debería pasar)

## Logs / Capturas
(Adjuntar)

## Estimación
Puntos: X
```

---

## 6. Buenas prácticas de uso (consejos prácticos)

- **WIP limit (límite de trabajo en progreso):** en `In Progress` pon un límite (ej. 3). No más de 3 tareas activas por agente/humano para reducir contexto switching.
- **PR pequeños:** <200 LOC ideal. Si un issue necesita más, divide en subtasks.
- **TDD y DoD:** cada issue debe definir criterios de aceptación y tests. Usa `pre_push_check.sh` para validar localmente antes de PR.
- **Etiquetado obligatorio:** al crear un issue, añade `type/*` y `priority/*`.
- **Asignaciones:** si es tarea de infra/ops, marca `needs-human` y asigna a la persona; si es feature para agentes, asigna a `DevAgent` o deja sin asignar y que Orchestrator lo tome.
- **Revisiones:** PR necesita al menos 1 revisor humano (Human Gate) para merge en `main`.

---

## 7. Checklist rápido para cada issue (DoD que pegás en el template)

- [ ] Tests unitarios incluidos
- [ ] Linter y style OK
- [ ] Documentación actualizada (si aplica)
- [ ] Audit trail: prompt/responses (si fue generado por agente)
- [ ] PR pequeño (<200 LOC) o dividido en subtasks
- [ ] Asignado a milestone correcto

---

## 8. Ejemplo de flujo operativo (desde idea a release)

1. Crear issue (usar plantilla `feature` o `bug`). Añadir labels y asignar milestone.
2. Priorizar en backlog y mover a `Sprint 0 / To Do` si entra en sprint.
3. Orchestrator/DevAgent toma la tarea → crea branch `feature/<id>-short` y trabaja localmente (TDD: tests primero).
4. DevAgent crea PR (pre-push checks pasados). PR marcado `ready-for-review`.
5. Reviewer humano revisa, acepta o solicita cambios.
6. CI ejecuta tests, build y security-scan; pasar todos los checks.
7. Merge a `staging` y deploy a entorno de pruebas; QA humana verifica.
8. Merge a `main` y marcar release (si aplica). Cerrar milestone cuando objetivo alcanzado.

---

## 9. Checklist para subir los MD y arrancar el proyecto (lista de copia/pega)

- [ ] Crear Proyecto `Agentes-AI-Equipo-Desarrollo` en Proyectos.  
- [ ] Crear columnas Kanban: Backlog, Sprint 0 / To Do, In Progress, In Review, Blocked, Done.  
- [ ] Subir documentos MD (todos los generados).  
- [ ] Crear labels según lista recomendada.  
- [ ] Crear milestones: `Sprint 0 — Infra & PR MVP`, `Sprint 1 — Pair MVP`, `MVP Release v0.1`.  
- [ ] Copiar plantillas de issues en configuración de issues.  
- [ ] Crear backlog inicial (pega los 10 issues listos).  
- [ ] Asignar primer sprint y mover issues a `Sprint 0 / To Do`.

---

## 10. Preguntas frecuentes rápidas (FAQ)

- **¿Milestone vs Release?** Milestone agrupa issues de un objetivo (ej. sprint). Release es versión entregada. A menudo 1 release = 1 o varios milestones.
- **¿Cuántas etiquetas usar?** Las mínimas: `type/*` + `priority/*`. Evita crear labels redundantes.
- **¿Quién debe crear issues?** Cualquiera: tú, agentes o colaboradores. Usa plantillas para consistencia.
- **¿Qué es WIP limit?** Límite de tareas activas para evitar multitasking ineficiente.

---

## 11. Notas finales (directas)

- Subí los MD y seguí el checklist en la sección 9. Yo los leeré y puedo: crear los issues automáticamente en texto listo para pegar, generar los artifacts de Sprint 0 (docker-stack, ci.yml, worker.py) y preparar el scaffold del repo.
- Si querés, ahora mismo genero los 10 issues en formato markdown listo para pegar en el Proyecto o te genero los archivos técnicos del Sprint 0. Dime cuál prefieres y lo pongo en el siguiente mensaje.

---

Documento generado para Max — práctico, sin vueltas. (2025-10-01)

