"""Postgres connection settings shared by services and Alembic. Secrets never print (G9)."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_host: str = "localhost"
    postgres_port: int = 5442
    postgres_db: str = "exaktiv"
    postgres_user: str = "exaktiv"
    postgres_password: SecretStr

    def dsn(self, database: str | None = None) -> str:
        """asyncpg DSN. `database` overrides the configured one (used by throwaway test DBs)."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password.get_secret_value()}"
            f"@{self.postgres_host}:{self.postgres_port}/{database or self.postgres_db}"
        )
