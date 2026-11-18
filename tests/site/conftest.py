import shutil
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

MINI = ROOT / "tests" / "fixtures" / "site" / "mini"
BRAND = ROOT / "brand"


@pytest.fixture
def mini(tmp_path: Path) -> Path:
    """A writable copy of the synthetic mini-site."""
    dst = tmp_path / "site"
    shutil.copytree(MINI, dst)
    return dst


@pytest.fixture
def build_mini(mini: Path, tmp_path: Path) -> Callable[..., Path]:
    import build_site

    def run(*, launch: bool = False, names_file: Path | None = None) -> Path:
        out = tmp_path / "dist"
        build_site.build(mini, BRAND, out, launch=launch, names_file=names_file)
        return out

    return run
