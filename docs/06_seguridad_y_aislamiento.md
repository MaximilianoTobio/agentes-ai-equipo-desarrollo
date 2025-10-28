# 🔐 Seguridad y Aislamiento de Ejecución

> **Ubicación sugerida:** `/docs/v2/06_seguridad_y_aislamiento.md`\
> **Propósito:** Describir el modelo de seguridad del sistema, el
> aislamiento en tiempo de ejecución del código generado por IA, la
> gestión de secretos y la trazabilidad/auditoría.\
> **Alcance:** Seguridad operacional del MVP v2. No cubre hardening del
> host ni políticas legales/contractuales.

------------------------------------------------------------------------

## 1. Principios de Seguridad del Sistema

El sistema está construido sobre cuatro principios fundamentales:

1.  **Ejecución Aislada**\
    El código que generan y ejecutan los agentes NUNCA se ejecuta con
    permisos del sistema host ni contra recursos de producción.

2.  **Mínimo privilegio**\
    Cada servicio (orchestrator, agentes, monitoreo, almacenamiento)
    solo tiene acceso a lo estrictamente necesario.

3.  **Trazabilidad Total**\
    Toda acción relevante (generar código, ejecutar tests, aprobar
    merge) deja registro auditable en Postgres.

4.  **Control de Superficie Expuesta**\
    Solo el Orchestrator recibe tráfico externo. Los agentes no son
    accesibles públicamente.

------------------------------------------------------------------------

## 2. Aislamiento de Ejecución (Sandbox)

### 2.1 Problema

DevAgent y QAAgent generan y ejecutan código dinámico. Ese código es
desconocido, potencialmente inseguro, y podría intentar acceder a red,
archivos o secretos.

### 2.2 Solución Arquitectónica

Todo código ejecutado por los agentes corre en un **sandbox seguro** con
estas propiedades:

-   Contenedor dedicado (throwaway / desechable).
-   Recursos limitados (CPU, memoria).
-   Sin acceso a red externa o interna crítica.
-   Sin volúmenes montados con secretos reales.
-   Eliminado al final de la sesión (no es persistente).

En términos prácticos:\
\> "El agente puede compilar, correr tests y medir cobertura, pero NO
puede tocar producción ni robar secretos."

### 2.3 Beneficios

-   Prevención de escape a host.
-   Aislamiento de ataques tipo RCE (remote code execution).
-   Auditoría clara: cada sandbox pertenece a una tarea conocida
    (`task_id` / `session_id`).

### 2.4 Estado futuro

En evoluciones posteriores, el sandbox puede fortalecerse con gVisor,
Firecracker u otra capa de virtualización ligera para endurecer aún más
el entorno donde se ejecuta el código de prueba.

------------------------------------------------------------------------

## 3. Gestión de Secretos

### 3.1 Regla General

Los agentes no almacenan secretos sensibles en su código generado ni en
los artefactos que publican a MinIO.

### 3.2 Dónde viven los secretos

-   En variables de entorno inyectadas solo en los servicios que
    realmente las necesitan.
-   En el orquestador, no en los agentes, cuando se trata de
    credenciales externas (por ejemplo, GitHub write access).
-   Nunca en texto plano en logs, audit trail ni snapshots.

### 3.3 Implicación arquitectónica

El Orchestrator actúa como proxy autorizado para ciertas acciones
sensibles.\
Ejemplo: crear un Pull Request en GitHub.\
- DevAgent NO tiene acceso a la credencial de GitHub.\
- DevAgent propone el diff.\
- Orchestrator recibe el diff y ejecuta la acción con su propia
credencial segura.\
- Eso queda registrado en el audit trail.

Este patrón garantiza: - Los agentes no pueden "auto-mergear" sin
supervisión de políticas. - La credencial crítica vive en un solo lugar
controlado.

------------------------------------------------------------------------

## 4. Control de Acceso y Exposición de Servicios

### 4.1 Diseño de superficie expuesta

-   **Traefik** es el único gateway HTTP(S) público.\
-   Solo enruta a servicios explícitamente aprobados: típicamente el
    Orchestrator, y opcionalmente paneles internos (Grafana/Portainer)
    bajo autenticación.

### 4.2 Agentes

-   DevAgent, QAAgent, ReviewAgent, RefactorAgent NO se exponen.\
-   Estos servicios solo hablan con:
    -   Redis Streams (lectura/escritura de mensajes)
    -   MinIO (subir/leer artefactos)
    -   Orchestrator (para reportar estado)

Esto reduce la superficie de ataque: un atacante externo no puede
"hablarle directamente" a un agente e inyectar trabajo arbitrario.

### 4.3 Rate limiting / throttling

El Orchestrator debe aplicar límites a endpoints sensibles (por ejemplo,
endpoints de ingesta de tareas vía webhook).\
Razón: evitar que un usuario externo fuerce al sistema a quemar
presupuesto de tokens (ataque de costo).

------------------------------------------------------------------------

## 5. Auditoría y Registro (Audit Trail)

### 5.1 Qué se audita

-   Quién generó código (agente, rol, timestamp).
-   Qué versión de prompts se utilizó.
-   Resultados de test y cobertura.
-   Decisiones de aprobación / rechazo de PRs.
-   Cambios producidos por RefactorAgent.

### 5.2 Dónde se almacena

Se almacena en una tabla de auditoría particionada mensualmente en
Postgres. Ejemplo conceptual:

``` sql
CREATE TABLE audit_trail_2025_10 PARTITION OF audit_trail
FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
```

Ventajas: - Fácil consulta histórica. - No altera el rendimiento de
tablas "calientes" del sistema. - Mantiene trazabilidad legal y técnica.

### 5.3 Inmutabilidad lógica

El sistema está diseñado bajo la política:\
\> "Si algo entra al audit trail, no se borra ni se edita."

Esto permite reconstruir eventos en caso de incidente o revisión
externa.

------------------------------------------------------------------------

## 6. Seguridad del Flujo de Trabajo entre Agentes

### 6.1 Mensajería con Redis Streams

La comunicación entre agentes viaja por Redis Streams con grupos de
consumidores.\
Beneficios de seguridad indirectos: - Los mensajes quedan bajo control
del Orchestrator (quién consume qué). - El backpressure evita desborde y
denegación de servicio "accidental". - Permite reasignar trabajo sin
reenviar credenciales (sólo el contenido de la tarea).

### 6.2 Outbox Pattern

El Orchestrator usa un patrón de outbox transaccional: 1. Registra en
Postgres que cierto evento debe publicarse. 2. Un proceso confiable
publica ese evento en Redis Streams. 3. Marca el evento como despachado.

Ventaja: evita "mensajes fantasma" (código generado pero nunca auditado)
o "mensajes huérfanos" (tarea ejecutada sin registro).\
Seguridad = consistencia + trazabilidad.

------------------------------------------------------------------------

## 7. Validaciones de Seguridad en el Ciclo XP

### 7.1 QAAgent

Incluye validaciones de seguridad básicas tipo SAST (análisis
estático).\
Busca patrones peligrosos (inyección de eval, credenciales hardcodeadas,
etc.).

### 7.2 ReviewAgent

Actúa como el "gatekeeper" de seguridad antes del merge.\
Puede bloquear un PR si detecta: - Uso de librerías no autorizadas. -
Exposición accidental de endpoints internos. - Falta de sanitización de
entrada de usuario. - Dependencias con vulnerabilidades conocidas.

### 7.3 Política de DoD

El Definition of Done incluye explícitamente un punto de seguridad:\
\> "No deben existir findings críticos según las reglas definidas."

Esto convierte la seguridad en requisito de cierre, no en una etapa
"después vemos".

------------------------------------------------------------------------

## 8. Gestión de Costos como Control de Riesgo

### 8.1 Riesgo económico

Una de las amenazas de un sistema multi-agente autónomo es que puede
generar costos altos en LLM si se lo fuerza con entradas maliciosas o
muy densas.

### 8.2 Mitigación: Token Budget Manager

El sistema impone límites de tokens por agente y por sprint.\
Si un agente excede cierto presupuesto de tokens: - Se bloquean nuevas
tareas para ese agente. - Se envía alerta. - El Orchestrator
re-distribuye tareas a otros agentes o baja la complejidad del modelo
(model routing).

### 8.3 Seguridad = Costo

Controlar presupuesto también evita abusos tipo "ataque de agotamiento
económico", que en la práctica es equivalente a una denegación de
servicio.

------------------------------------------------------------------------

## 9. Post-Mortem e Incidentes

### 9.1 Cuando ocurre un incidente

Ejemplos de incidentes relevantes: - El sistema aprueba código
inseguro. - El sandbox ejecuta algo que intenta exfiltrar datos. - Se
sube un PR con credenciales expuestas.

### 9.2 Respuesta esperada

1.  El Orchestrator marca el incidente y congela merges automáticos.\
2.  Se genera un registro en audit trail con categoría `incident`.\
3.  Se vincula el incidente a la sesión de pair programming o a la tarea
    original.\
4.  RefactorAgent puede recibir una tarea de corrección inmediata con
    prioridad crítica.

### 9.3 Objetivo de la respuesta a incidentes

-   Contener el problema.\
-   Entender cómo ocurrió.\
-   Ajustar prompts / límites / reglas para que NO vuelva a ocurrir.\
-   Mantener evidencia forense (quién tomó qué decisión).

En este modelo, mejorar el sistema después del incidente NO es opcional:
es parte de la arquitectura viva.

------------------------------------------------------------------------

## 10. Resumen Ejecutivo de Seguridad

-   El sistema asume que el código generado por IA es **potencialmente
    peligroso** hasta que se demuestre lo contrario.\

-   Por eso se aíslan los entornos de ejecución, se aplican controles de
    aprobación y se fuerza la trazabilidad.

-   Los agentes no son libres: están regulados por políticas (DoD,
    budget de tokens, pairing, rotación de propiedad).\

-   La credencial crítica NO vive en los agentes.\

-   Toda acción con impacto (merge, cambio de código en repo) queda
    registrada con actor, timestamp y contexto técnico.

La seguridad acá **no es un parche**, es un atributo estructural del
diseño.

------------------------------------------------------------------------

**Versión:** v2.0 --- Octubre 2025\
**Autor:** Equipo de Ingeniería -- Proyecto Agentes AI
