"""Tests for the gitpulse CLI."""

from __future__ import annotations

from pathlib import Path

from gitpulse.cli import main


def _run(repo: Path, *args: str, capsys) -> tuple[int, str]:
    code = main(["-p", str(repo), *args])
    captured = capsys.readouterr()
    return code, captured.out


def test_stats(repo: Path, capsys) -> None:
    code, out = _run(repo, "stats", capsys=capsys)
    assert code == 0
    assert "Commits" in out
    assert "Authors" in out
    assert "main" in out


def test_contributors(repo: Path, capsys) -> None:
    code, out = _run(repo, "contributors", capsys=capsys)
    assert code == 0
    assert "Zeus" in out
    assert "Athena" in out


def test_activity(repo: Path, capsys) -> None:
    code, out = _run(repo, "activity", capsys=capsys)
    assert code == 0
    assert "2024" in out


def test_churn(repo: Path, capsys) -> None:
    code, out = _run(repo, "churn", capsys=capsys)
    assert code == 0
    assert "app.py" in out


def test_report_to_stdout(repo: Path, capsys) -> None:
    code, out = _run(repo, "report", capsys=capsys)
    assert code == 0
    assert "GitPulse report" in out
    assert "| Commits | 4 |" in out


def test_report_to_file(repo: Path, tmp_path: Path, capsys) -> None:
    output = tmp_path / "report.md"
    code, out = _run(repo, "report", "-o", str(output), capsys=capsys)
    assert code == 0
    assert output.exists()
    assert "# GitPulse report" in output.read_text(encoding="utf-8")


def test_not_a_repo(tmp_path: Path, capsys) -> None:
    code = main(["-p", str(tmp_path), "stats"])
    captured = capsys.readouterr()
    assert code == 1
    assert "not a git repository" in captured.err