"""Runtime settings from the environment and a local .env. Secrets never print (G9)."""

from functools import lru_cache
from urllib.parse import quote

from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict

from exaktiv_core.db import PostgresSettings, parse_database_url


class Settings(PostgresSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: SecretStr
    minio_secret_key: SecretStr
    minio_bucket: str = "exaktiv-smoke"

    # DBOS (EXK0-dbos). The system tables live in schema `dbos` of the same database.
    # DBOS needs a DIRECT host (session advisory lock, LISTEN/NOTIFY): never the pooled host.
    dbos_database_url: SecretStr | None = None
    dbos_app_name: str = "exaktiv"
    dbos_system_schema: str = "dbos"

    def dbos_system_url(self) -> str:
        """SQLAlchemy URL (psycopg) for the DBOS system database. The error never holds the URL."""
        override = self.dbos_database_url.get_secret_value() if self.dbos_database_url else ""
        if override:
            host, port, db, user, password, ssl = parse_database_url(override)
        elif self.uses_pooler:
            raise ValueError("DBOS needs a direct host: set DBOS_DATABASE_URL")
        else:
            host, port, db, user = (
                self.postgres_host,
                self.postgres_port,
                self.postgres_db,
                self.postgres_user,
            )
            password = self.postgres_password.get_secret_value()
            ssl = self.postgres_ssl_mode if self.postgres_ssl else None
        url = (
            f"postgresql+psycopg://{quote(user, safe='')}:{quote(password, safe='')}"
            f"@{host}:{port}/{quote(db, safe='')}"
        )
        return f"{url}?sslmode={ssl}" if ssl else url


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
