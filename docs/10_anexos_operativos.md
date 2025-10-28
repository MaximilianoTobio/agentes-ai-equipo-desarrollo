# 🧭 Anexos Operativos y Runbooks

> **Ubicación sugerida:** `/docs/v2/10_anexos_operativos.md`\
> **Propósito:** Reunir procedimientos de operación, recuperación,
> incidentes y mantenimiento del sistema multi-agente.\
> **Enfoque:** guía práctica para DevOps, con pasos reproducibles y
> trazables.

------------------------------------------------------------------------

## 1. Runbooks Principales

Los **runbooks** son guías rápidas y reproducibles para tareas
críticas.\
Cada procedimiento debe ejecutarse siguiendo los principios XP:
trazabilidad, reversibilidad y validación posterior.

------------------------------------------------------------------------

### 1.1 Reinicio Controlado del Sistema

**Objetivo:** reiniciar todos los servicios sin perder estado ni tareas
en curso.

**Comando (Docker Swarm):**

``` bash
docker stack rm agentes_ai && sleep 15 && docker stack deploy -c docker-stack.yml agentes_ai
```

**Verificación:**

``` bash
docker service ls | grep agentes_ai
# Todos los servicios deben aparecer con REPLICAS = 1/1 o más
```

**Criterio de éxito:**\
Todos los healthchecks del Orchestrator responden 200 en `/health`.

------------------------------------------------------------------------

### 1.2 Backup Manual de Postgres

**Objetivo:** crear backup inmediato y verificable de la base de datos.

``` bash
docker exec -it postgres pg_dump -U postgres agentes_ai > /backups/pg/agentes_ai_$(date +%F_%H-%M).sql
ls -lh /backups/pg/
```

**Validar integridad:**

``` bash
head -n 5 /backups/pg/agentes_ai_2025-10-25_*.sql
# Debe comenzar con -- PostgreSQL database dump
```

------------------------------------------------------------------------

### 1.3 Restauración de Backup

``` bash
cat /backups/pg/agentes_ai_2025-10-25_*.sql | docker exec -i postgres psql -U postgres agentes_ai
```

**Criterio de éxito:**\
El comando termina sin errores `psql:` y la aplicación se reconecta
correctamente.

------------------------------------------------------------------------

### 1.4 Regenerar Certificados TLS (Traefik)

**Comando:**

``` bash
docker exec -it traefik traefik renew --certificatesresolvers letsencrypt
```

**Verificación:**

``` bash
curl -v https://orchestrator.labstation.dev | grep "SSL connection"
```

------------------------------------------------------------------------

### 1.5 Despliegue Seguro de Nueva Versión

``` bash
git pull origin main
docker stack deploy -c docker-stack.yml agentes_ai
```

**Checklist previo:** - \[ \] Todos los tests de CI pasaron.\
- \[ \] PR aprobado por ReviewAgent.\
- \[ \] Backups recientes verificados.\
- \[ \] Tokens dentro del presupuesto.\
- \[ \] Traefik operativo.

------------------------------------------------------------------------

## 2. Protocolo de Incidentes

Los incidentes se clasifican por **severidad (S1--S4)**:

  -----------------------------------------------------------------------
  Nivel               Ejemplo                      Acción
  ------------------- ---------------------------- ----------------------
  **S1 -- Crítico**   Pérdida de datos o PRs       Parar merges + iniciar
                      erróneos                     post-mortem

  **S2 -- Alto**      Caída del orquestador        Reinicio controlado +
                                                   rollback

  **S3 -- Medio**     PRs lentos o fallos de QA    Diagnóstico y ajustes
                      intermitentes                XP

  **S4 -- Bajo**      Métricas incorrectas, logs   Registrar ticket +
                      incompletos                  refactor futuro
  -----------------------------------------------------------------------

### 2.1 Proceso Estandarizado

1.  **Detección:** alerta Prometheus / logs.\
2.  **Contención:** detener merges automáticos.\
3.  **Diagnóstico:** revisar `audit_trail` y `jaeger trace`.\
4.  **Corrección:** revertir commits o reiniciar servicio.\
5.  **Post-mortem:** redactar informe y registrar aprendizajes.

### 2.2 Plantilla Post-Mortem

``` markdown
# Informe Post-Mortem – Incidente S1
**Fecha:** YYYY-MM-DD HH:MM  
**Impacto:**  
**Servicios afectados:**  
**Causa raíz:**  
**Solución aplicada:**  
**Prevención futura:**  
**Responsable:**  
**Evidencias:** (enlace a logs, trace, PR)
```

------------------------------------------------------------------------

## 3. Rollback de Cambios

### 3.1 Rollback de Último Despliegue

``` bash
git log --oneline | head -n 5
git revert <commit_hash>
docker stack deploy -c docker-stack.yml agentes_ai
```

### 3.2 Rollback de Servicio Individual

``` bash
docker service update --rollback agentes_ai_orchestrator
```

**Verificación:**\
`docker service ps agentes_ai_orchestrator` muestra versión anterior
activa.

------------------------------------------------------------------------

## 4. Scripts de Mantenimiento Preventivo

  -----------------------------------------------------------------------------------------------
  Tarea              Frecuencia                     Comando
  ------------------ ------------------------------ ---------------------------------------------
  Limpieza Redis     Semanal                        `redis-cli XTRIM tasks:stream MAXLEN 10000`
  Streams                                           

  Compactar base de  Mensual                        `VACUUM FULL;`
  datos                                             

  Validar backups    Semanal                        `pg_restore --list backup.sql`

  Rotar logs de      Diario                         `find /logs/agents -mtime +7 -delete`
  agentes                                           

  Check presupuesto  Diario                         `/scripts/check_token_budget.sh`
  tokens                                            
  -----------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 5. Checklist de Auditoría Técnica (Mensual)

  Elemento                                     Verificación            Estado
  -------------------------------------------- ----------------------- --------
  **Backups**                                  Último \< 24h           ✅
  **Certificados TLS**                         No expiran en 30 días   ✅
  **Coverage promedio**                        \> 80%                  ✅
  **TDD compliance**                           \> 90%                  ✅
  **Cache hit rate**                           \> 40%                  ⚠️
  **Alertas Prometheus activas**               OK                      ✅
  **Traefik + Portainer acceso restringido**   OK                      ✅

------------------------------------------------------------------------

## 6. Scripts Auxiliares (Conceptuales)

### 6.1 Verificar Integridad XP

``` bash
pytest -q && flake8 && coverage run -m pytest && coverage report -m
```

### 6.2 Regenerar Dashboards Grafana

``` bash
docker exec -it grafana grafana-cli dashboards import /dashboards/xp_metrics.json
```

### 6.3 Test de Performance

``` bash
ab -n 500 -c 10 https://orchestrator.labstation.dev/api/tasks
```

**Objetivo:** P95 \< 500ms.

------------------------------------------------------------------------

## 7. Indicadores de Salud del Sistema

  Indicador                  Fuente           Umbral   Acción
  -------------------------- ---------------- -------- -------------------------
  `queue_length`             Redis            \>100    Escalar agentes
  `token_budget_remaining`   Prometheus       \<10%    Reducir modelo
  `ci_failures_total`        GitHub Actions   \>10%    Revisar DevAgent
  `refactor_pending`         SonarQube        \>10     RefactorAgent on-demand
  `pair_sessions_failed`     DB               \>20%    Revisar prompts

------------------------------------------------------------------------

## 8. Mantenimiento y Evolución del Sistema

1.  **Documentar cada incidente** como parte del aprendizaje XP.\
2.  **Actualizar scripts** tras cada cambio de versión.\
3.  **Evitar automatismos ciegos**: siempre validar antes del merge.\
4.  **Monitorear consumo de tokens y cobertura.**\
5.  **Priorizar refactors preventivos** sobre correcciones tardías.

------------------------------------------------------------------------

## 9. Resumen Final

> "Un sistema vivo se mantiene por disciplina, no por suerte."

La capa operativa garantiza que el sistema multi-agente siga funcionando
sin degradarse, manteniendo trazabilidad, reproducibilidad y capacidad
de mejora continua.

------------------------------------------------------------------------

**Versión:** v2.0 --- Octubre 2025\
**Autor:** Equipo de Ingeniería -- Proyecto Agentes AI
