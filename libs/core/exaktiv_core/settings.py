"""Runtime settings from the environment and a local .env. Secrets never print (G9)."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict

from exaktiv_core.db import PostgresSettings


class Settings(PostgresSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: SecretStr
    minio_secret_key: SecretStr
    minio_bucket: str = "exaktiv-smoke"

    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "exaktiv-smoke"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
