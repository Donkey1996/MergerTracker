from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog
from contextlib import asynccontextmanager

from api.routes import api_router
from config.settings import settings
from config.database import init_db
from services.database_service import initialize_database_service, shutdown_database_service
from services.scheduler_service import initialize_scheduler_service, shutdown_scheduler_service

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting MergerTracker API", environment=settings.ENVIRONMENT)
    
    # Initialize database services
    try:
        await init_db()
        await initialize_database_service()
        logger.info("Database services initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database services", error=str(e))
        raise
    
    # Initialize scheduler service
    try:
        await initialize_scheduler_service()
        logger.info("Scheduler service initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize scheduler service", error=str(e))
        # Scheduler failure shouldn't prevent API startup
    
    logger.info("MergerTracker API startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MergerTracker API")
    
    # Shutdown services
    try:
        await shutdown_scheduler_service()
        await shutdown_database_service()
        logger.info("All services shut down successfully")
    except Exception as e:
        logger.error("Error during service shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title="MergerTracker API",
    description="M&A News Scraping and Analysis Platform",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database service
        from services.database_service import get_database_service
        db_service = await get_database_service()
        db_health = await db_service.health_check()
        
        # Check scheduler service
        from services.scheduler_service import get_scheduler_service
        scheduler_service = await get_scheduler_service()
        scheduler_health = {
            'status': 'healthy' if scheduler_service._running else 'stopped',
            'active_jobs': len(await scheduler_service.list_jobs())
        }
        
        overall_status = "healthy" if (
            db_health.get('status') == 'healthy' and 
            scheduler_health.get('status') == 'healthy'
        ) else "degraded"
        
        return {
            "status": overall_status,
            "service": "MergerTracker API",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "services": {
                "database": db_health,
                "scheduler": scheduler_health
            }
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "service": "MergerTracker API",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "error": str(e)
        }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to MergerTracker API",
        "docs": "/api/v1/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )