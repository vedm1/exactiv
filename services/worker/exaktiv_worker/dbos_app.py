"""DBOS configuration. One place, so the worker and the tests start DBOS the same way."""

from dbos import DBOSConfig
from dbos._serialization import DBOSPortableJSONSerializer
from exaktiv_core.settings import Settings


def dbos_config(s: Settings) -> DBOSConfig:
    # No Conductor key, no OTLP: workflow data stays in our Postgres, in our region (G7).
    # JSON serializer: the default is pickle, which can run code when it is read.
    return {
        "name": s.dbos_app_name,
        "system_database_url": s.dbos_system_url(),
        "dbos_system_schema": s.dbos_system_schema,
        "serializer": DBOSPortableJSONSerializer(),
        "use_listen_notify": True,
        "enable_otlp": False,
        "log_level": "INFO",
    }
