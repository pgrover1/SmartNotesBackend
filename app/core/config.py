import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List

class Settings(BaseSettings):
    """Application settings"""
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Notes API"
    
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./notes_app.db"
    )
    
    # MongoDB settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "notes_app")
    
    # Always use MongoDB
    USE_MONGODB: bool = True
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # AI model settings
    AI_MODEL_PATH: Optional[str] = None
    ENABLE_AI_FEATURES: bool = True
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create global settings object
settings = Settings()
