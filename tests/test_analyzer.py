"""Tests for the gitpulse.analyzer module."""

from __future__ import annotations

from pathlib import Path

import pytest

from gitpulse.analyzer import GitError, GitRepository, instrument


def test_is_repo(repo: Path) -> None:
    assert GitRepository(repo).is_repo is True
    workspace = Path(repo) / "src" / "app"
    workspace.mkdir(parents=True)
    assert GitRepository(workspace).is_repo is True


def test_is_repo_false(tmp_path: Path) -> None:
    assert GitRepository(tmp_path).is_repo is False


def test_commits_are_oldest_first(repo: Path) -> None:
    commits = GitRepository(repo).commits()
    assert len(commits) == 4
    assert commits[0].author == "Zeus"
    assert commits[-1].author == "Athena"
    assert commits[0].date < commits[-1].date


def test_instrument(repo: Path) -> None:
    repo_obj = GitRepository(repo)
    assert instrument(repo_obj.commits()) == 4


def test_contributors_ordered_by_activity(repo: Path) -> None:
    contributors = GitRepository(repo).contributors()
    assert [(c.name, c.commits) for c in contributors] == [
        ("Zeus", 3),
        ("Athena", 1),
    ]
    assert contributors[0].share(4) == pytest.approx(0.75)


def test_numstat(repo: Path) -> None:
    stats = GitRepository(repo).numstat()
    added = sum(f.added for f in stats)
    removed = sum(f.removed for f in stats)
    assert added == 4
    assert removed == 2


def test_churn_order(repo: Path) -> None:
    churn = GitRepository(repo).churn()
    assert churn[0].path == "app.py"
    assert churn[0].added == 3
    assert churn[0].removed == 2
    assert {f.path for f in churn} == {"app.py", "README.md"}


def test_weekly_activity(repo: Path) -> None:
    weekly = GitRepository(repo).weekly_activity()
    assert sum(w.commits for w in weekly) == 4
    assert weekly[0].commits == 3  # Zeus's week
    assert weekly[-1].commits == 1  # Athena's week


def test_summary(repo: Path) -> None:
    summary = GitRepository(repo).summary()
    assert summary.total_commits == 4
    assert summary.total_authors == 2
    assert summary.total_added == 4
    assert summary.total_removed == 2
    assert summary.files_touched == 2
    assert summary.bus_factor == 1
    assert summary.avg_commits_per_week > 0
    assert summary.branch == "main"


def test_empty_repository(tmp_path: Path) -> None:
    git = GitRepository(tmp_path)
    with pytest.raises(GitError):
        git.commits()