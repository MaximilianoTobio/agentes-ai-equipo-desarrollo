# services/orchestrator/app/main.py
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI(title="Orchestrator", version="0.1.0")

@app.get("/health")
async def health():
    # health básico usado por Traefik / Swarm / deploy_safe.sh
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/detailed")
async def health_detailed():
    # placeholders por ahora; luego vamos a cablear Postgres/Redis/MinIO
    checks = {
        "postgres": {"status": "unknown"},
        "redis": {"status": "unknown"},
        "minio": {"status": "unknown"},
        "agents": {"status": "unknown"},
    }
    all_healthy = False  # más adelante será True si todo responde

    return JSONResponse(
        status_code=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "degraded" if not all_healthy else "healthy",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
