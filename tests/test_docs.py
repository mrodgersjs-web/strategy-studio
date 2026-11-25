"""Consistency tests: the README's accuracy numbers must match the data files."""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "src" / "strategy_studio" / "data"


def _count_jsonl(name: str) -> int:
    return sum(1 for line in (DATA / name).read_text(encoding="utf-8").splitlines() if line.strip())


def test_readme_counts_match_data_files() -> None:
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    methods = json.loads((DATA / "methods.json").read_text(encoding="utf-8"))["methods"]
    assert f"`data/labelled_questions.jsonl`, {_count_jsonl('labelled_questions.jsonl')} hand-written questions" in readme
    assert f"`data/holdout_questions.jsonl`, {_count_jsonl('holdout_questions.jsonl')} questions" in readme
    assert len(methods) == 11
    for m in methods:
        assert f"`{m['id']}`" in readme


def test_changelog_version_matches_package() -> None:
    changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    pkg_version = re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1)
    assert f"## [{pkg_version}]" in changelog
    assert "## [0.1.0]" in changelog


def test_readme_copy_rules() -> None:
    readme = (REPO / "README.md").read_text(encoding="utf-8").lower()
    for word in ("unlock", "empower", "synergy", "leverage", "disrupt",
                 "hustle", "utilize", "iterate", "optimize"):
        assert word not in readme, word
    assert "—" not in readme
