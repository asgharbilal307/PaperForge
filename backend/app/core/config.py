from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    groq_api_key: str
    github_token: str
    github_repo: str

    qdrant_path: str = "./qdrant_data"
    qdrant_collection: str = "uni_study_materials"

    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()