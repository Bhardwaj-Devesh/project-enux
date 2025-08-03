from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from pathlib import Path
from scripts.setup_database import setup_database
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    try:
        # Startup
        from pathlib import Path
        import asyncio

        setup_database_script = Path(__file__).parent.parent / "scripts" / "setup_database.py"

        if setup_database_script.exists():
            try:
                
                await setup_database()
                # asyncio.run(setup_database())
            except Exception as e:
                logger.error(f"❌ Failed to run setup_database: {e}")
        else:
            logger.warning(f"⚠️ Setup script not found at {setup_database_script}. Skipping database setup.")

        logger.info("🚀 Starting Playbook API...")
        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Shutdown
        logger.info("👋 Shutting down Playbook API...")


# Create FastAPI app
app = FastAPI(
    title="Playbook API",
    description="A GitHub-like repository system for managing playbooks with AI-powered content analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, playbooks
app.include_router(auth.router, prefix="/api/v1")
app.include_router(playbooks.router, prefix="/api/v1")
# Include routers (lazy import to avoid startup issues)
@app.on_event("startup")
async def startup_event():
    """Startup event to import routers"""
    try:
        
        # from app.api import auth, playbooks
        # app.include_router(auth.router, prefix="/api/v1")
        # app.include_router(playbooks.router, prefix="/api/v1")
        # app.include_router(router, prefix="/test")
        logger.info("✅ Routers loaded successfully")
    except Exception as e:
        logger.error(f"❌ Error loading routers: {e}")
        raise



@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Playbook API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "playbook-api"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 

