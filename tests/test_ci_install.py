"""CI must install every pytest plugin its own commands use.

The smoke workflow runs `pytest --cov`, which needs pytest-cov. It used to install
the `test` extra, which lacks pytest-cov, so every CI run failed with
"unrecognized arguments: --cov". This test reads the workflow and pyproject and
fails locally before that can reach CI again.
"""
import re
from pathlib import Path

import pytest

tomllib = pytest.importorskip("tomllib")  # stdlib from 3.11; the 3.10 CI leg skips this check

ROOT = Path(__file__).resolve().parents[1]


def test_smoke_workflow_installs_pytest_cov_when_it_uses_cov():
    workflow = (ROOT / ".github/workflows/smoke.yml").read_text()
    if "--cov" not in workflow:
        return
    extra = re.search(r'pip install -e "\.\[(\w+)\]"', workflow).group(1)
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    deps = pyproject["project"]["optional-dependencies"][extra]
    assert any(d.startswith("pytest-cov") for d in deps), f"extra [{extra}] lacks pytest-cov"
