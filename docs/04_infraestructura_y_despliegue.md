# 🖥️ Infraestructura y Despliegue -- Visión Arquitectónica

> **Ubicación sugerida:** `/docs/v2/04_infraestructura_y_despliegue.md`\
> **Propósito:** Describir la capa de infraestructura que soporta el
> sistema, sus garantías (alta disponibilidad, aislamiento,
> persistencia, trazabilidad) y las decisiones técnicas que definen cómo
> se ejecuta el MVP v2 en producción.\
> **Nota:** Este documento NO es una guía paso a paso de instalación. Es
> el porqué y el cómo conceptual de la plataforma.

------------------------------------------------------------------------

## 1. Objetivo de la Infraestructura

La infraestructura está diseñada para sostener un sistema multi-agente
que:

-   Ejecute múltiples servicios en paralelo (orquestador + agentes +
    monitoreo).
-   Escale horizontalmente bajo carga (más réplicas, no más CPU en una
    sola instancia).
-   Se recupere de fallos sin intervención manual (self-healing).
-   Mantenga trazabilidad total (qué pasó, cuándo, y por qué).
-   Garantice que el entorno de ejecución del código generado por IA
    esté aislado y auditado.

En otras palabras: **no es una "app web", es una fábrica de software
autónoma supervisada.**

------------------------------------------------------------------------

## 2. Topología Lógica de la Plataforma

A nivel lógico, tenemos cuatro dominios de infraestructura:

1.  **Dominio de Ejecución de Servicios**
    -   Orchestrator (FastAPI)
    -   Agentes (DevAgent, QAAgent, ReviewAgent, RefactorAgent)
    -   PairCoordinator (subcomponente lógico del orquestador)
2.  **Dominio de Datos y Mensajería**
    -   Postgres (estado del sistema, auditoría, métricas de performance
        XP)
    -   Redis Streams (cola de trabajo, coordinación entre agentes)
    -   MinIO (artefactos de trabajo, snapshots, adjuntos de PR, etc.)
3.  **Dominio de Observabilidad**
    -   Prometheus (métricas)
    -   Grafana (dashboards)
    -   Jaeger (distributed tracing)
4.  **Dominio de Entrada / Exposición**
    -   Traefik (reverse proxy + TLS)
    -   GitHub Webhooks (evento de entrada que convierte "intención" en
        "tarea")
    -   Portainer / panel operativo interno (gestión de servicios)

Cada dominio puede evolucionar de forma independiente, pero todos deben
mantenerse coordinados por el orquestador.

------------------------------------------------------------------------

## 3. Plataforma de Ejecución

La plataforma objetivo es un entorno basado en **Docker Swarm** en un
servidor controlado (por ejemplo, Contabo).\
Razones arquitectónicas para usar Swarm en este MVP:

-   **Simplicidad operativa:** una sola máquina física puede comportarse
    "como un cluster", con redes lógicas, balanceo interno e incluso
    auto-restart de servicios.
-   **Declaratividad:** los servicios se describen como una pila (stack)
    y Swarm los mantiene vivos según esa definición.
-   **Escalado horizontal por servicio:** `replicas: 3` en el
    orquestador es suficiente para alta disponibilidad dentro del mismo
    host (o entre hosts si se amplía).
-   **Compatibilidad con Traefik y Portainer:** monitoreo visual y
    certificados TLS automatizados.

> Decisión: no se usa Kubernetes en esta etapa porque agrega complejidad
> operativa y cognitiva que no es necesaria para el alcance actual del
> MVP.

------------------------------------------------------------------------

## 4. Redes Internas y Superficies Expuestas

### 4.1 Redes Lógicas

La infraestructura define al menos dos redes overlay dentro del cluster
Swarm:

-   `labstack_net`\
    Uso: comunicación interna entre servicios críticos del sistema
    (orchestrator, agentes, redis, postgres, minio).\
    Propiedad: tráfico de aplicación.

-   `labstack_monitoring`\
    Uso: Prometheus, Grafana, Jaeger y futuros servicios de
    auditoría/alerting.\
    Propiedad: telemetría y observabilidad.

Separar las redes permite: - Limitar qué servicios quedan accesibles
entre sí (aislamiento por función). - Reducir superficie de ataque (no
todo puede hablar con todo). - Controlar mejor qué termina expuesto vía
Traefik.

### 4.2 Exposición Externa

Traefik es el gateway HTTP(S) hacia el exterior:

-   Termina TLS (certificados).
-   Hace routing basado en hostname (`orchestrator.labstation.dev`,
    `grafana.labstation.dev`, etc.).
-   Balancea carga entre múltiples réplicas del orquestador.

Ningún agente se expone públicamente.\
Solo el orquestador, paneles de observabilidad internos (opcional) y
Portainer pueden tener rutas públicas (idealmente con auth/whitelist).

**Principio:** "Los agentes no hablan con el mundo. El mundo habla con
el orquestador."

------------------------------------------------------------------------

## 5. Persistencia y Estado

### 5.1 Postgres (verdad canónica)

Postgres es el **source of truth** del sistema. Aquí se guardan:

-   Tareas
-   Estado de las sesiones de pair programming
-   Historial de PRs
-   Métricas de ejecución de agentes (tiempos, resultados, cobertura)
-   Audit trail inmutable (quién hizo qué y cuándo)

Se extiende con `pgvector` para almacenar embeddings o contexto
semántico usado por los agentes.

**Decisión arquitectónica clave:**\
\> "Nada es 'sólo en memoria'. Todo estado importante debe terminar en
Postgres."

### 5.2 Redis Streams (flujo operativo)

Redis no es la fuente de verdad. Redis es el **bus de trabajo**.

-   Los agentes consumen tareas desde streams (`XREADGROUP`).
-   Cada mensaje requiere ACK.
-   Los mensajes pendientes pueden ser reclamados si un agente muere
    (evita pérdida silenciosa de trabajo).
-   El orquestador orquesta la reasignación.

Esto da: - Paralelismo seguro (muchos workers). - Garantía de entrega al
menos una vez. - Capacidad de backpressure (si la cola crece, escalamos
workers).

### 5.3 MinIO (artefactos físicos)

MinIO actúa como almacenamiento S3-compat para: - Snapshots de sesiones
de pair programming - Archivos generados por los agentes (código
propuesto, diffs) - Adjuntos de validaciones QA (reportes, coverage,
etc.)

Esto hace posible auditar una entrega incluso meses después, aún si el
repo cambió.

### 5.4 Respaldo y Retención

-   Postgres → backups programados, retenidos fuera del disco principal.
-   MinIO → retención versionada de artefactos críticos.
-   Redis → persistencia configurada (`appendonly=yes`) para recuperar
    colas tras reinicio.

> Decisión crítica: "Perder Redis 1 minuto es tolerable si Postgres
> tiene el estado. Perder Postgres es inaceptable."

------------------------------------------------------------------------

## 6. Alta Disponibilidad y Recuperación

### 6.1 Orchestrator en Alta Disponibilidad

El orquestador corre en múltiples réplicas (ej. 3).\
Beneficios:

-   Si una réplica cae, Traefik reenvía requests a otra.
-   El healthcheck HTTP (`/health`) y readiness `/ready` definen si una
    réplica puede recibir tráfico.
-   Evita que el orquestador sea un único punto de falla (SPOF).

### 6.2 Agentes como Workers Escalables

Los agentes (DevAgent, QAAgent, etc.) son procesos consumiendo streams.

-   Cada agente puede tener N réplicas simultáneas.
-   Si sube la cola (`XLEN` crece), se pueden escalar réplicas de ese
    agente.
-   Si una réplica muere a mitad de trabajo, Redis marca mensajes como
    "pendientes sin ACK" → otro worker puede retomarlos.

Esto soporta picos de trabajo sin rediseñar nada.

### 6.3 Degradación Controlada

Si falla un subsistema: - Falla Redis → deja de haber trabajo nuevo,
pero no se corrompe el estado en Postgres. - Falla MinIO → se pausa el
almacenamiento de artefactos, pero los agentes pueden seguir generando y
la auditoría registra el intento fallido. - Falla Postgres → el sistema
entra en modo "no aceptar nuevas tareas", porque no se puede registrar
auditablemente nada.

Esta priorización protege la trazabilidad: si no podemos registrar lo
que pasa, preferimos no avanzar.

------------------------------------------------------------------------

## 7. Observabilidad y Auditoría

### 7.1 Métricas Técnicas

Prometheus recolecta métricas de: - Salud del orquestador - Latencia de
endpoints - Tamaño de la cola en Redis - Tasa de fallos de QA - Uso de
tokens por agente / sprint

Estas métricas alimentan dashboards en Grafana y sirven para: - Ver
cuello de botella inmediato (cola creciendo → necesitamos más
DevAgent) - Ver degradación de calidad (fallos de QA en aumento) - Ver
patrones de costo (excesivo consumo de tokens en tareas simples)

### 7.2 Trazas Distribuidas

Jaeger + OpenTelemetry rastrean una tarea extremo a extremo: - Webhook
recibido - Asignación a DevAgent - QAAgent ejecutando validaciones -
ReviewAgent decidiendo merge

Beneficio: cuando algo sale mal, se puede ver en qué punto específico se
rompió la cadena.

### 7.3 Auditoría Operativa

El sistema escribe un audit trail inmutable en Postgres, con particiones
mensuales.\
Esto nos permite contestar preguntas como:

-   ¿Quién (qué agente) aprobó este merge?\
-   ¿Con qué cobertura de tests?\
-   ¿Cuál era el estado de la cola en ese momento?\
-   ¿Con qué prompt generó el código?

Este punto es esencial para compliance interno, debugging y
post-mortems.

------------------------------------------------------------------------

## 8. Seguridad y Aislamiento en Ejecución

### 8.1 Aislamiento de Ejecución de Código

El código propuesto por DevAgent (o revisado en QAAgent) **no se ejecuta
directamente en el host**.\
Se ejecuta dentro de un entorno aislado ("sandbox seguro") con:

-   Contenedor dedicado
-   Límite de CPU y memoria
-   Red restringida o totalmente cerrada
-   Sin acceso a secretos de producción

Razón: el agente está generando código dinámicamente. Ese código debe
tratarse como no confiable.

### 8.2 Gestión de Secrets

Las credenciales sensibles (API keys, tokens de GitHub, claves JWT) no
viajan entre agentes en claro. - Viven como variables de entorno
inyectadas en cada servicio en desplegue. - No se exponen dentro de los
artefactos en MinIO. - No se guardan en logs ni en audit trail.

### 8.3 Control de Acceso

Traefik + reglas de enrutamiento + autenticación en endpoints de
administración limitan quién puede: - Ver dashboards de Grafana -
Iniciar un despliegue seguro - Forzar un rollback

------------------------------------------------------------------------

## 9. Filosofía Operativa

1.  **Nada es manual, todo es reproducible.**
    -   Si hay que hacer algo manual y urgente (ej. rollback), debe
        quedar registrado y tener un script equivalente documentado.
2.  **El sistema debe poder contarse a sí mismo.**
    -   A través de métricas, trazas y audit trails, el sistema puede
        explicar qué hizo, por qué lo hizo y con qué confiabilidad.
3.  **Los agentes son trabajadores reemplazables, no fuentes de
    verdad.**
    -   Podemos matar y recrear agentes libremente.\
    -   No pueden poseer estado único en memoria.\
    -   El estado importante vive en Postgres y MinIO.
4.  **El orquestador es el juez, no el ejecutor.**
    -   Orquesta, valida, bloquea, libera, audita.\
    -   No es quien genera el código final ni quien lo prueba.\
    -   Esto mantiene responsabilidades claras y auditables.

------------------------------------------------------------------------

## 10. Estado Actual y Evolución Esperada

-   La plataforma actual soporta un MVP robusto (v2) en un único nodo
    Swarm con alta disponibilidad lógica.
-   Puede ampliarse a múltiples nodos sin rediseñar conceptos clave
    (réplicas, redes overlay, Traefik, Redis Streams).
-   A futuro (Sprint 3+), se evalúa:
    -   Canary releases por servicio
    -   Auto-escalado reactivo basado en tamaño de cola y latencia QA
    -   Feature flags para versiones de agentes
    -   Separación física de entornos (staging vs producción)

------------------------------------------------------------------------

**Versión:** v2.0 --- Octubre 2025\
**Autor:** Equipo de Ingeniería -- Proyecto Agentes AI
