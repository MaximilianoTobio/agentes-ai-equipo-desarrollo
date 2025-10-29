# Etapa 1: build base
FROM python:3.12-slim AS base

# Seguridad mínima y performance:
# - No escribir bytecode (.pyc) en disco
# - Forzar stdout sin buffer para logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Crear directorio de la app
WORKDIR /app

# Instalar dependencias del sistema mínimas (puede ajustarse luego si agregamos libs C)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copiar requirements si los tenemos separados
# Si más adelante tenemos un requirements.txt específico para orchestrator lo usaremos aquí.
# Por ahora asumimos que el proyecto tiene un requirements común en la raíz o en este servicio.
# Puedes ajustar esta ruta si en tu repo real está distinto.
COPY services/orchestrator/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar el código del servicio
COPY services/orchestrator /app/services/orchestrator

# Exponer el puerto interno donde corre uvicorn
EXPOSE 8000

# Comando de arranque (producción, sin --reload)
CMD ["uvicorn", "services.orchestrator.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
