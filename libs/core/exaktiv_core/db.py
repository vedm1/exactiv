"""Postgres connection settings shared by services and Alembic. Secrets never print (G9).

Two ways to configure the database. DATABASE_URL (Neon gives one) wins when it is set:
it is split into the POSTGRES_* parts and its sslmode sets the TLS mode.
Otherwise the POSTGRES_* variables are used (local Docker).
Neon is used through its POOLED host (`-pooler`, PgBouncer in transaction mode). That mode has no
session state between statements, so the pooled settings turn the prepared-statement cache off, for
asyncpg and for Alembic's SQLAlchemy engine. Transaction-level advisory locks still work.
"""

import uuid
from typing import Any, Literal, Self
from urllib.parse import parse_qs, quote, unquote, urlsplit

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SslMode = Literal["require", "verify-ca", "verify-full"]
NO_TLS = {"disable", "allow", "prefer"}  # "allow" and "prefer" may fall back to plain text: not TLS
TLS = {"require", "verify-ca", "verify-full"}


def parse_database_url(url: str) -> tuple[str, int, str, str, str, SslMode | None]:
    """(host, port, db, user, password, ssl mode). The ValueError never holds the URL."""
    try:
        parts = urlsplit(url.strip())
        host, user, password = parts.hostname, parts.username, parts.password
        port = parts.port or 5432
        mode = (parse_qs(parts.query).get("sslmode") or [""])[0]
    except ValueError:
        raise ValueError("DATABASE_URL is not a valid Postgres URL") from None
    db = parts.path[1:]
    if parts.scheme not in {"postgres", "postgresql"} or not (host and user and password and db):
        raise ValueError("DATABASE_URL needs postgresql://user:password@host/db")
    if mode and mode not in NO_TLS | TLS:
        raise ValueError("DATABASE_URL has an unknown sslmode")
    ssl: SslMode | None = mode if mode in TLS else None  # type: ignore[assignment]
    return host, port, unquote(db), unquote(user), unquote(password), ssl


class PostgresSettings(BaseSettings):
    # hide_input_in_errors: a validation error must never print the URL (it holds the password).
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    database_url: SecretStr | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5442
    postgres_db: str = "exaktiv"
    postgres_user: str = "exaktiv"
    postgres_password: SecretStr = SecretStr("")
    postgres_ssl: bool = False  # Neon needs TLS (EXK0b). Local Docker does not.
    postgres_ssl_mode: SslMode = "require"
    postgres_pooled: bool | None = None  # None: detect a Neon pooled host. True for any PgBouncer.

    @model_validator(mode="after")
    def _use_database_url(self) -> Self:
        url = self.database_url.get_secret_value() if self.database_url else ""
        if url:
            host, port, db, user, password, ssl = parse_database_url(url)
            self.postgres_host, self.postgres_port, self.postgres_db = host, port, db
            self.postgres_user = user
            self.postgres_password = SecretStr(password)
            self.postgres_ssl = ssl is not None
            if ssl is not None:
                self.postgres_ssl_mode = ssl
        elif not self.postgres_password.get_secret_value():
            raise ValueError("set DATABASE_URL or POSTGRES_PASSWORD")
        return self

    @property
    def uses_pooler(self) -> bool:
        """True behind PgBouncer: POSTGRES_POOLED, else a Neon pooled host (`-pooler.`)."""
        if self.postgres_pooled is not None:
            return self.postgres_pooled
        return "-pooler." in self.postgres_host

    def connect_kwargs(self) -> dict[str, Any]:
        """Extra asyncpg connect arguments: TLS when set, no statement cache behind the pooler."""
        kwargs: dict[str, Any] = {"ssl": self.postgres_ssl_mode} if self.postgres_ssl else {}
        if self.uses_pooler:
            kwargs["statement_cache_size"] = 0
        return kwargs

    def sqlalchemy_options(self, database: str | None = None) -> tuple[str, dict[str, Any]]:
        """(URL, connect_args) for Alembic's async engine."""
        url = self.dsn(database).replace("postgresql://", "postgresql+asyncpg://", 1)
        args = self.connect_kwargs()
        if self.uses_pooler:
            url += "?prepared_statement_cache_size=0"
            args["prepared_statement_name_func"] = lambda: f"__asyncpg_{uuid.uuid4()}__"
        return url, args

    def dsn(self, database: str | None = None) -> str:
        """asyncpg DSN. `database` overrides the configured one (used by throwaway test DBs)."""
        user = quote(self.postgres_user, safe="")
        password = quote(self.postgres_password.get_secret_value(), safe="")
        return (
            f"postgresql://{user}:{password}@{self.postgres_host}:{self.postgres_port}"
            f"/{database or self.postgres_db}"
        )
