"""
EROS - EMS Route Optimization System
Main FastAPI Application

This is the entry point for the backend API.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.routers import incidents, vehicles, hospitals, routes, status_updates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    
    On startup:
    - Initialize database tables
    - Seed demo data if empty
    
    On shutdown:
    - Clean up resources
    """
    # Startup
    print("🚑 EROS Starting up...")
    init_db()
    
    # Seed demo data if database is empty
    from app.services.seeder import seed_demo_data
    seed_demo_data()
    
    print("✅ EROS Ready!")
    
    yield
    
    # Shutdown
    print("👋 EROS Shutting down...")


def create_app() -> FastAPI:
    """
    Application factory for creating the FastAPI app.
    
    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()
    
    app = FastAPI(
        title="EROS - EMS Route Optimization System",
        description="""
        A unified EMS Dispatcher System that processes real-time data 
        to optimize emergency response routing and hospital selection.
        
        ## Features
        
        - **Intelligent Routing**: Optimal path-finding for EMS vehicles
        - **Hospital Recommendations**: Capacity + distance-based destination selection
        - **Real-time Tracking**: Live vehicle positions and incident status
        - **Dispatch Dashboard**: Unified view for EMS dispatchers
        """,
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers
    app.include_router(
        incidents.router,
        prefix="/api/v1/incidents",
        tags=["Incidents"]
    )
    app.include_router(
        vehicles.router,
        prefix="/api/v1/vehicles",
        tags=["Vehicles"]
    )
    app.include_router(
        hospitals.router,
        prefix="/api/v1/hospitals",
        tags=["Hospitals"]
    )
    app.include_router(
        routes.router,
        prefix="/api/v1/routes",
        tags=["Routes"]
    )
    app.include_router(
        status_updates.router,
        prefix="/api/v1/status-updates",
        tags=["Status Updates"]
    )
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for monitoring."""
        return {"status": "healthy", "service": "eros-backend"}
    
    # Root redirect to docs
    @app.get("/", include_in_schema=False)
    async def root():
        """Redirect root to API documentation."""
        return JSONResponse(
            content={
                "message": "Welcome to EROS API",
                "docs": "/api/docs",
                "health": "/health"
            }
        )
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
