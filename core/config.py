from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )
    # --- Application Configuration ---
    APP_NAME: str = "Zentist"
    APP_VERSION: str = "0.1.0"

    # --- CORS ---
    FRONTEND_URL: str
    
    # --- Supabase Configuration ---
    SUPABASE_KEY: str
    SUPABASE_URL: str
    SUPABASE_JWT_SECRET: str

    # --- Database Configuration ---
    DATABASE_URL: str
    DB_CONNECT_ARGS: dict = {"sslmode": "prefer"}
    
    # --- Redis ---
    REDIS_URL: str

    # --- Models Configuration ---
    DEFAULT_MODEL: str = "groq/llama-3.3-70b-versatile"
    GROQ_API_KEY: str

    # --- Sendgrid Email ---
    SENDGRID_FROM_NAME: str = "Bright Smiles Dental"
    SENDGRID_FROM_EMAIL: str
    SENDGRID_API_KEY: str

@lru_cache()
def get_settings():
    return Settings()

@lru_cache()
def get_clinic_config():
    """Loads the clinic configuration from the JSON file."""
    with open("data/clinic_info.json", "r") as f:
        return json.load(f)

clinic_config = get_clinic_config()