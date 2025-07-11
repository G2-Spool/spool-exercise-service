"""Main FastAPI application for Exercise Service."""

from contextlib import asynccontextmanager
from typing import Dict, Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.dependencies import get_redis_cache
from app.core.database import init_database, close_database, get_database_manager
from app.langgraph.workflows import ExerciseWorkflow
from app.routers import exercise, evaluation, remediation

# Setup structured logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle manager."""
    # Startup
    logger.info("Starting Spool Exercise Service", version=settings.APP_VERSION)

    # Initialize services
    redis_cache = await get_redis_cache()
    workflow = ExerciseWorkflow()
    
    # Initialize database in production
    if settings.ENVIRONMENT == "production":
        await init_database()
        db_manager = await get_database_manager()
        app.state.db_manager = db_manager

    # Store in app state
    app.state.redis_cache = redis_cache
    app.state.workflow = workflow

    # Prometheus metrics are set up outside of lifespan

    logger.info("Exercise service initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down Spool Exercise Service")
    
    # Close database connection
    if settings.ENVIRONMENT == "production":
        await close_database()


# Create FastAPI app
app = FastAPI(
    title="Spool Exercise Service",
    description="Exercise generation, evaluation, and remediation with LangGraph orchestration",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Prometheus metrics (must be done before including routers)
if settings.ENABLE_METRICS:
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app, endpoint="/metrics")

# Include routers
app.include_router(exercise.router, prefix="/api/exercise", tags=["exercise"])
app.include_router(evaluation.router, prefix="/api/exercise", tags=["evaluation"])
app.include_router(
    remediation.router, prefix="/api/exercise/remediation", tags=["remediation"]
)


@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "service": "Spool Exercise Service",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational",
    }


@app.get("/health", tags=["health"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "service": "exercise-service",
        "version": settings.APP_VERSION,
        "checks": {},
    }

    # Check Redis
    try:
        if hasattr(request.app.state, "redis_cache"):
            await request.app.state.redis_cache.exists("health_check")
            health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check LangGraph workflow
    try:
        if hasattr(request.app.state, "workflow"):
            # Simple check that workflow is initialized
            _ = request.app.state.workflow.graph
            health_status["checks"]["langgraph"] = "healthy"
    except Exception as e:
        health_status["checks"]["langgraph"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
        
    # Check database (production only)
    if settings.ENVIRONMENT == "production":
        try:
            if hasattr(request.app.state, "db_manager"):
                is_healthy = await request.app.state.db_manager.health_check()
                health_status["checks"]["database"] = "healthy" if is_healthy else "unhealthy"
                if not is_healthy:
                    health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/config", tags=["debug"])
async def get_config() -> Dict[str, Any] | JSONResponse:
    """Get current configuration (development only)."""
    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            content={"error": "Not available in production"}, status_code=403
        )

    return {
        "environment": settings.ENVIRONMENT,
        "models": {
            "evaluation": settings.EVALUATION_MODEL,
            "generation": settings.GENERATION_MODEL,
        },
        "services": {
            "content": settings.CONTENT_SERVICE_URL,
            "profile": settings.PROFILE_SERVICE_URL,
        },
        "cache_ttl": settings.EXERCISE_CACHE_TTL,
        "workflow": {
            "max_retries": settings.MAX_RETRIES,
            "timeout": settings.WORKFLOW_TIMEOUT,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.ENVIRONMENT == "development",
        log_config=None,  # Use structlog instead
    )
