"""
Application configuration.

All secrets (DB credentials, JWT secret, OpenAI key) are read from environment
variables / a .env file. Nothing is ever hardcoded here.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    database_url: str = "postgresql://postgres:postgres@db:5432/venture_analyst"

    # --- Auth ---
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h

    # --- OpenAI ---
    # The user supplies their own key. We never bake a key into the image.
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4.1"
    openai_embedding_model: str = "text-embedding-3-small"

    # --- Uploads ---
    upload_dir: str = "uploads"
    max_upload_mb: int = 25

    # --- CORS ---
    frontend_origin: str = "http://localhost:3000"


settings = Settings()
