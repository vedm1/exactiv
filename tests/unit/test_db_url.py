"""EXK0b: DATABASE_URL (Neon) is split into the POSTGRES_* parts. The URL holds a password (G9)."""

from urllib.parse import quote, urlsplit

import pytest
from exaktiv_core.db import PostgresSettings
from exaktiv_core.settings import Settings
from pydantic import ValidationError

PASSWORD = "p@ss/w:rd#1"  # characters that need percent-encoding in a URL (synthetic)
NEON = (
    f"postgresql://neonuser:{quote(PASSWORD, safe='')}"
    "@ep-test-123456.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)


def make(**over: object) -> PostgresSettings:
    return PostgresSettings(_env_file=None, **over)  # type: ignore[call-arg,arg-type]


def test_neon_url_is_split_into_parts() -> None:
    s = make(database_url=NEON)
    assert s.postgres_host == "ep-test-123456.eu-central-1.aws.neon.tech"
    assert s.postgres_port == 5432
    assert s.postgres_db == "neondb"
    assert s.postgres_user == "neonuser"
    assert s.postgres_password.get_secret_value() == PASSWORD
    assert s.postgres_ssl is True
    assert s.connect_kwargs() == {"ssl": "require"}


def test_explicit_port_and_postgres_scheme() -> None:
    s = make(database_url="postgres://u:pw@db.example.com:6543/app?sslmode=require")
    assert (s.postgres_host, s.postgres_port, s.postgres_db) == ("db.example.com", 6543, "app")


@pytest.mark.parametrize(
    ("query", "ssl", "kwargs"),
    [
        ("", False, {}),
        ("?sslmode=disable", False, {}),
        ("?sslmode=require", True, {"ssl": "require"}),
        ("?sslmode=verify-ca", True, {"ssl": "verify-ca"}),
        ("?sslmode=verify-full", True, {"ssl": "verify-full"}),
    ],
)
def test_sslmode_is_read_from_the_url(query: str, ssl: bool, kwargs: dict[str, str]) -> None:
    s = make(database_url=f"postgresql://u:pw@h.example.com/db{query}")
    assert s.postgres_ssl is ssl
    assert s.connect_kwargs() == kwargs


@pytest.mark.parametrize(
    "bad",
    [
        "mysql://u:pw@h/db",
        "postgresql://u:pw@/db",
        "postgresql://u:pw@h",
        "postgresql://u@h/db",
        "not a url",
        "postgresql://u:pw@h/db?sslmode=bogus",
    ],
)
def test_bad_url_is_refused_without_echoing_it(bad: str) -> None:
    with pytest.raises(ValidationError) as info:
        make(database_url=bad)
    assert "pw" not in str(info.value).replace("password", "")
    assert bad not in str(info.value)


def test_database_url_wins_over_the_parts() -> None:
    s = make(database_url=NEON, postgres_host="other", postgres_password="other-pw")
    assert s.postgres_host.endswith("neon.tech")
    assert s.postgres_password.get_secret_value() == PASSWORD


def test_blank_database_url_falls_back_to_the_parts() -> None:
    s = make(database_url="", postgres_password="pw-parts")
    assert s.postgres_host == "localhost"
    assert s.postgres_password.get_secret_value() == "pw-parts"


def test_a_password_or_a_url_is_required() -> None:
    with pytest.raises(ValidationError):
        make()


def test_dsn_percent_encodes_user_and_password() -> None:
    parts = urlsplit(make(database_url=NEON).dsn())
    assert parts.hostname == "ep-test-123456.eu-central-1.aws.neon.tech"
    from urllib.parse import unquote

    assert unquote(parts.password or "") == PASSWORD
    assert PASSWORD not in make(database_url=NEON).dsn()


def test_url_and_password_never_print() -> None:
    s = make(database_url=NEON)
    for text in (repr(s), str(s)):
        assert PASSWORD not in text and quote(PASSWORD, safe="") not in text
        assert "neon.tech/neondb" not in text


def test_core_settings_read_database_url_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", NEON)
    s = Settings(_env_file=None, minio_access_key="a", minio_secret_key="b")  # type: ignore[arg-type,call-arg]
    assert s.postgres_user == "neonuser" and s.connect_kwargs() == {"ssl": "require"}


POOLED = (
    "postgresql://neonuser:pw-sentinel@ep-test-123456-pooler.eu-central-1.aws.neon.tech/neondb"
    "?sslmode=require"
)


def test_pooler_host_is_detected() -> None:
    assert make(database_url=POOLED).uses_pooler is True
    assert make(database_url=NEON).uses_pooler is False
    assert make(postgres_password="pw", postgres_host="localhost").uses_pooler is False


def test_pooled_asyncpg_kwargs_turn_off_the_statement_cache() -> None:
    kwargs = make(database_url=POOLED).connect_kwargs()
    assert kwargs == {"ssl": "require", "statement_cache_size": 0}
    assert make(database_url=NEON).connect_kwargs() == {"ssl": "require"}


def test_pooled_sqlalchemy_options_for_alembic() -> None:
    url, connect_args = make(database_url=POOLED).sqlalchemy_options()
    assert url.startswith("postgresql+asyncpg://neonuser:")
    assert url.endswith("/neondb?prepared_statement_cache_size=0")
    assert connect_args["ssl"] == "require" and connect_args["statement_cache_size"] == 0
    name = connect_args["prepared_statement_name_func"]()
    assert name != connect_args["prepared_statement_name_func"]()  # unique for every statement
    assert name.startswith("__asyncpg_")


def test_direct_sqlalchemy_options_stay_plain() -> None:
    url, connect_args = make(database_url=NEON).sqlalchemy_options()
    assert "prepared_statement_cache_size" not in url
    assert connect_args == {"ssl": "require"}


def test_sqlalchemy_options_accept_a_database_override() -> None:
    url, _ = make(postgres_password="pw").sqlalchemy_options("other_db")
    assert url.endswith("/other_db")


def test_postgres_pooled_overrides_detection() -> None:
    assert make(postgres_password="pw", postgres_pooled=True).uses_pooler is True
    assert make(database_url=POOLED, postgres_pooled=False).uses_pooler is False
    assert make(postgres_password="pw", postgres_pooled=True).connect_kwargs() == {
        "statement_cache_size": 0
    }
