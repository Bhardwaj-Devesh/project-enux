from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Supabase Configuration
    supabase_url: str = "https://yluwquzlkygjtufideqn.supabase.co"
    supabase_key: str = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlsdXdxdXpsa3lnanR1ZmlkZXFuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3MjUxNTUsImV4cCI6MjA2OTMwMTE1NX0.07qhp61zY-qxC-oWiFDhRPQFJoFUNAYT6z58IUOYojk'
    supabase_service_role_key: str = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlsdXdxdXpsa3lnanR1ZmlkZXFuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzcyNTE1NSwiZXhwIjoyMDY5MzAxMTU1fQ.Gj0gnkPdFoyn_BRVtJhfR0-hry1_vBE4rXwg0HJlp9o'
    
    # Google Gemini Configuration
    google_api_key: str = "AIzaSyD-9tSrQWAB_Zjz91N_7jrwHelC_Y3ym4"
    gemini_model: str = "gemini-1.5-flash"
    
    # Application Configuration
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Storage Configuration
    storage_bucket_name: str = "playbooks"
    max_file_size: int = 10485760  # 10MB in bytes
    
    # Vector Database Configuration
    vector_dimension: int = 768  # Gemini embedding dimension
    
    # Allowed file types
    allowed_file_types: list = [
        "application/pdf",
        "text/plain",
        "text/markdown",
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/json",
        "application/xml",
        "text/xml",
        "text/html",
        "application/zip",
        "application/x-zip-compressed"
    ]
    
    # File extensions mapping
    file_extensions: dict = {
        "application/pdf": ".pdf",
        "text/plain": ".txt",
        "text/markdown": ".md",
        "text/csv": ".csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "application/vnd.ms-excel": ".xls",
        "application/json": ".json",
        "application/xml": ".xml",
        "text/xml": ".xml",
        "text/html": ".html",
        "application/zip": ".zip",
        "application/x-zip-compressed": ".zip"
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 
