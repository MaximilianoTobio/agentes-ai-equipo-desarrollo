"""
Orchestrator FastAPI Application.
Coordinates all agents and manages task lifecycle.
"""
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import (
    Counter, Histogram, Gauge, 
    CollectorRegistry, generate_latest,
    CONTENT_TYPE_LATEST
)

from orchestrator.app.core.config import settings
from orchestrator.app.models.schemas import HealthCheckResponse, ServiceHealth
from orchestrator.app.models.database import init_db, close_db, health_check_db
from orchestrator.app.services.redis_client import redis_client

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics registry
registry = CollectorRegistry()

# Define metrics
task_counter = Counter(
    'orchestrator_tasks_created_total',
    'Total number of tasks created',
    ['task_type'],
    registry=registry
)

task_duration = Histogram(
    'orchestrator_task_duration_seconds',
    'Task processing duration',
    ['agent_type', 'status'],
    registry=registry
)

active_tasks_gauge = Gauge(
    'orchestrator_active_tasks',
    'Number of active tasks',
    registry=registry
)

health_check_counter = Counter(
    'orchestrator_health_checks_total',
    'Total health check requests',
    ['status'],
    registry=registry
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    Initialize connections on startup, cleanup on shutdown.
    """
    # === STARTUP ===
    logger.info(f"Starting {settings.app_name} v{settings.app_version}...")
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await init_db()
        logger.info("Database initialized successfully")
        
        # Connect to Redis
        logger.info("Connecting to Redis...")
        await redis_client.connect()
        
        # Create consumer groups (idempotent)
        await redis_client.create_consumer_group(
            settings.stream_task_key, 
            settings.consumer_group_name
        )
        await redis_client.create_consumer_group(
            settings.stream_result_key, 
            settings.consumer_group_name
        )
        logger.info("Redis Streams consumer groups ready")
        
        logger.info(f"{settings.app_name} started successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # === SHUTDOWN ===
    logger.info(f"Shutting down {settings.app_name}...")
    
    try:
        # Disconnect from Redis
        await redis_client.disconnect()
        logger.info("Redis disconnected")
        
        # Close database connections
        await close_db()
        logger.info("Database closed")
        
        logger.info(f"{settings.app_name} shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-Agent XP System Orchestrator",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    tags=["Monitoring"]
)
async def health_check():
    """
    Health check endpoint.
    Verifies all critical services are operational.
    
    Returns:
        HealthCheckResponse with status and service states
    """
    try:
        # Check Redis
        redis_healthy = await redis_client.health_check()
        
        # Check Database
        db_healthy = await health_check_db()
        
        # Determine overall status
        all_healthy = redis_healthy and db_healthy
        overall_status = "healthy" if all_healthy else "degraded"
        
        # Update metrics
        health_check_counter.labels(status=overall_status).inc()
        
        return HealthCheckResponse(
            status=overall_status,
            version=settings.app_version,
            timestamp=datetime.utcnow(),
            services=[
                ServiceHealth(
                    name="redis",
                    status="healthy" if redis_healthy else "unhealthy",
                    details={"message": "Redis Streams operational" if redis_healthy else "Redis connection failed"}
                ),
                ServiceHealth(
                    name="postgres",
                    status="healthy" if db_healthy else "unhealthy",
                    details={"message": "Database operational" if db_healthy else "Database connection failed"}
                ),
                ServiceHealth(
                    name="orchestrator",
                    status="healthy",
                    details={"message": "Orchestrator core operational"}
                )
            ]
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        health_check_counter.labels(status="unhealthy").inc()
        
        return HealthCheckResponse(
            status="unhealthy",
            version=settings.app_version,
            timestamp=datetime.utcnow(),
            services=[
                ServiceHealth(
                    name="redis",
                    status="unknown",
                    details={"message": "Check failed"}
                ),
                ServiceHealth(
                    name="postgres",
                    status="unknown",
                    details={"message": "Check failed"}
                ),
                ServiceHealth(
                    name="orchestrator", 
                    status="degraded", 
                    details={"message": f"Error: {str(e)}"}
                )
            ]
        )


@app.get(
    "/metrics",
    tags=["Monitoring"]
)
async def metrics():
    """
    Prometheus metrics endpoint.
    Exposes application metrics in Prometheus format.
    
    Returns:
        Prometheus-formatted metrics
    """
    metrics_data = generate_latest(registry)
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )


@app.get(
    "/",
    tags=["Root"]
)
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs": "/docs" if settings.debug else None,
        "health": "/health",
        "metrics": "/metrics"
    }


# Error handler for uncaught exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "error": "Internal server error",
        "detail": str(exc) if settings.debug else "An error occurred"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "orchestrator.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
