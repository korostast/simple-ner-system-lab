"""
Configuration management for NER System
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "your_neo4j_password"

    # Different pre-downloaded language models
    gliner_model: str = "urchade/gliner_medium-v2.1"
    gliner_model_path: str = "/app/models/gliner"
    stanza_models_dir: str = "/app/models/stanza"

    # LLM API Configuration
    llm_api_url: str = "http://llamacpp:8080/v1"
    llm_api_key: str = ""
    llm_model: str = "Qwen3-1.7B-Q8_0"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.7
    llm_top_p: float = 0.8

    # Application Configuration
    log_level: str = "INFO"
    app_host: str = "0.0.0.0"
    app_port: int = 8011


settings = Settings()
