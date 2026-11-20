"""Worker entry point: `uv run python -m exaktiv_worker.worker`."""

import signal
import threading

from dbos import DBOS
from exaktiv_core.settings import get_settings

from exaktiv_worker import smoke  # noqa: F401  (registers the workflows)
from exaktiv_worker.dbos_app import dbos_config


def main() -> None:
    DBOS(config=dbos_config(get_settings()))
    DBOS.launch()
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    stop.wait()
    DBOS.destroy()


if __name__ == "__main__":
    main()
