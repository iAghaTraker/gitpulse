"""Shared fixtures for GitPulse tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A tiny git repository with known history.

    Commits:
      1..3  Zeus  <zeus@example.com>  edits app.py  (Jan 1-3, 2024)
      4      Athena <athena@example.com>  adds README.md (Feb 1, 2024)
    """
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "Zeus")
    _git(tmp_path, "config", "user.email", "zeus@example.com")

    for i in range(3):
        (tmp_path / "app.py").write_text(f"print({i})\n", encoding="utf-8")
        _git(tmp_path, "add", ".")
        _git(
            tmp_path,
            "commit",
            "-q",
            "-m",
            f"commit {i}",
            "--date",
            f"2024-01-{i + 1:02d}T10:00:00+00:00",
        )

    (tmp_path / "README.md").write_text("# hello\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(
        tmp_path,
        "-c",
        "user.name=Athena",
        "-c",
        "user.email=athena@example.com",
        "commit",
        "-q",
        "-m",
        "add readme",
        "--date",
        "2024-02-01T10:00:00+00:00",
    )
    return tmp_path