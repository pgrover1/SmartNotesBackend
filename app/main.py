from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import notes, categories
from app.core.config import settings

# Create FastAPI app instance
app = FastAPI(
    title="Notes API",
    description="A backend API for a notes application with AI features and MongoDB support",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint to confirm API is running"""
    return {
        "status": "healthy",
        "database": "MongoDB" if settings.USE_MONGODB else "SQLite/PostgreSQL"
    }

@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API info"""
    return {
        "app_name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "database": "MongoDB" if settings.USE_MONGODB else "SQLite/PostgreSQL",
        "ai_enabled": settings.ENABLE_AI_FEATURES
    }