import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for API Gateway"""
    
    # General settings
    PROJECT_NAME: str = "VaPtER API Gateway"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # Backend settings
    BACKEND_URL: str = "http://backend:8000"
    BACKEND_TIMEOUT: int = 30
    
    # CORS settings
    CORS_ALLOWED_ORIGINS: List[str] = [
        "http://vapter.szini.it:3000",
        "http://localhost:3000"
    ]
    
    # Authentication settings (for future use)
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Request settings
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    REQUEST_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse CORS origins if they come as a string
        if isinstance(self.CORS_ALLOWED_ORIGINS, str):
            self.CORS_ALLOWED_ORIGINS = [
                origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(',')
            ]


# Create global settings instance
settings = Settings()