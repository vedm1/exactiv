import pytest
from dbos import DBOSConfig  # noqa: F401  (import proves the package is installed)
from exaktiv_core.settings import Settings
from exaktiv_worker.dbos_app import dbos_config

PASSWORD = "pw-sentinel-9f3a"
POOLED = "postgresql://u:" + PASSWORD + "@ep-x-pooler.eu-central-1.aws.neon.tech/db?sslmode=require"
DIRECT = "postgresql://u:" + PASSWORD + "@ep-x.eu-central-1.aws.neon.tech/db?sslmode=require"


def make(**kw: object) -> Settings:
    base: dict[str, object] = {
        "_env_file": None,
        "postgres_password": PASSWORD,
        "minio_access_key": "ak",
        "minio_secret_key": "sk",
    }
    return Settings(**{**base, **kw})  # type: ignore[arg-type]


def test_dbos_system_url_local() -> None:
    url = make().dbos_system_url()
    assert url.startswith("postgresql+psycopg://")
    assert "localhost:5442/exaktiv" in url


def test_dbos_system_url_pooled_requires_override() -> None:
    with pytest.raises(ValueError, match="DBOS_DATABASE_URL") as err:
        make(database_url=POOLED).dbos_system_url()
    assert PASSWORD not in str(err.value)


def test_dbos_system_url_pooled_with_override() -> None:
    url = make(database_url=POOLED, dbos_database_url=DIRECT).dbos_system_url()
    assert "-pooler." not in url
    assert url.startswith("postgresql+psycopg://")
    assert "sslmode=require" in url


def test_dbos_config_no_conductor_no_otlp() -> None:
    cfg = dbos_config(make())
    assert "conductor_key" not in cfg
    assert cfg["enable_otlp"] is False
    assert type(cfg["serializer"]).__name__ == "DBOSPortableJSONSerializer"
    assert cfg["dbos_system_schema"] == "dbos"


def test_g9_dbos_url_not_in_repr() -> None:
    s = make(database_url=POOLED, dbos_database_url=DIRECT)
    assert PASSWORD not in repr(s)
    with pytest.raises(ValueError) as err:
        make(database_url=POOLED).dbos_system_url()
    assert PASSWORD not in str(err.value)


def test_smoke_result_holds_ids_only() -> None:
    from exaktiv_worker.smoke import SmokeResult

    r = SmokeResult(run_id="r", row_written=True, object_key="smoke/r.txt")
    assert set(r.to_dict()) == {"run_id", "row_written", "object_key"}
