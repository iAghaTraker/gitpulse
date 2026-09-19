"""Core analysis logic for GitPulse.

This module wraps the ``git`` command line tool with :func:`subprocess`
and exposes a small, dependency-free API for extracting metrics from a
git repository. Only read-only git commands are ever executed.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

_GIT_LOG_FIELDS = "%H|%an|%ae|%ad"
_COMMIT_MARKER = "@@COMMIT@@"


class GitError(RuntimeError):
    """Raised when a git command fails."""


@dataclass(frozen=True)
class Commit:
    """A single commit's essential metadata."""

    hash: str
    author: str
    email: str
    date: datetime


@dataclass(frozen=True)
class Contributor:
    """Aggregated numbers for one author."""

    name: str
    email: str
    commits: int

    def share(self, total: int) -> float:
        """Fraction ``[0, 1]`` of ``total`` commits made by this author."""
        if total <= 0:
            return 0.0
        return self.commits / total


@dataclass(frozen=True)
class FileStats:
    """Lines added/removed for one path."""

    path: str
    added: int
    removed: int

    @property
    def changed(self) -> int:
        """Total lines touched (added + removed)."""
        return self.added + self.removed


@dataclass(frozen=True)
class WeekActivity:
    """Commit count for a calendar week (keyed by the Monday of that week)."""

    week_start: date
    commits: int


@dataclass
class Summary:
    """High-level repository summary."""

    path: str
    branch: str
    total_commits: int
    total_authors: int
    total_added: int
    total_removed: int
    files_touched: int
    first_commit: datetime | None
    last_commit: datetime | None
    bus_factor: int
    avg_commits_per_week: float


class GitRepository:
    """A thin, read-only wrapper around a git repository on disk."""

    def __init__(self, path: str | Path = ".") -> None:
        self.path = Path(path)

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.path), *args],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise GitError(result.stderr.strip() or "git command failed")
        return result.stdout

    # ------------------------------------------------------------------
    # basic facts
    # ------------------------------------------------------------------
    @property
    def is_repo(self) -> bool:
        """Whether ``path`` is inside a git work tree."""
        try:
            return self._git("rev-parse", "--is-inside-work-tree").strip() == "true"
        except GitError:
            return False

    @property
    def current_branch(self) -> str:
        """Name of the checked-out branch (or ``detached HEAD``)."""
        try:
            branch = self._git("branch", "--show-current").strip()
            return branch or "detached HEAD"
        except GitError:
            return "n/a"

    def _require_repo(self) -> None:
        if not self.is_repo:
            raise GitError(f"not a git repository: {self.path}")

    # ------------------------------------------------------------------
    # primitives
    # ------------------------------------------------------------------
    def commits(self) -> list[Commit]:
        """Every commit reachable from HEAD, oldest-first."""
        self._require_repo()
        raw = self._git(
            "log",
            "--date=iso-strict",
            "--pretty=format:" + _COMMIT_MARKER + _GIT_LOG_FIELDS,
        )
        commits: list[Commit] = []
        for line in raw.splitlines():
            if not line.startswith(_COMMIT_MARKER):
                continue
            prefix, author, email, when = line.split("|", 3)
            when = when[:-1] + "+00:00" if when.endswith("Z") else when
            commits.append(
                Commit(
                    hash=prefix[len(_COMMIT_MARKER):],
                    author=author,
                    email=email,
                    date=datetime.fromisoformat(when),
                )
            )
        commits.reverse()
        return commits

    def numstat(self) -> list[FileStats]:
        """Per-path lines added/removed across all commits."""
        self._require_repo()
        raw = self._git("log", "--numstat", "--pretty=format:")
        stats: list[FileStats] = []
        for line in raw.splitlines():
            try:
                added, removed, path = line.split("\t", 2)
            except ValueError:
                continue
            if added == "-" or removed == "-":  # binary file
                continue
            stats.append(FileStats(path=path, added=int(added), removed=int(removed)))
        return stats

    # ------------------------------------------------------------------
    # derived metrics
    # ------------------------------------------------------------------
    def contributors(self) -> list[Contributor]:
        """Authors sorted by commit count (most active first)."""
        counts: dict[tuple[str, str], int] = {}
        for commit in self.commits():
            key = (commit.author, commit.email)
            counts[key] = counts.get(key, 0) + 1
        return [
            Contributor(name=name, email=email, commits=count)
            for (name, email), count in sorted(
                counts.items(), key=lambda item: item[1], reverse=True
            )
        ]

    def weekly_activity(self, max_weeks: int | None = None) -> list[WeekActivity]:
        """Commit counts per calendar week, oldest first, gaps filled.

        When ``max_weeks`` is set, only the most recent ``max_weeks``
        weeks are kept (in addition to any week where work happened).
        """
        commits = self.commits()
        if not commits:
            return []

        by_week: dict[date, int] = {}
        for commit in commits:
            year, week, _ = commit.date.date().isocalendar()
            monday = date.fromisocalendar(year, week, 1)
            by_week[monday] = by_week.get(monday, 0) + 1

        start, end = min(by_week), max(by_week)
        cursor = start
        result: list[WeekActivity] = []
        while cursor <= end:
            result.append(
                WeekActivity(week_start=cursor, commits=by_week.get(cursor, 0))
            )
            cursor += timedelta(days=7)

        if max_weeks is not None and len(result) > max_weeks:
            result = result[-max_weeks:]
        return result

    def churn(self, top: int | None = None) -> list[FileStats]:
        """Files sorted by total lines changed, largest first."""
        stats = self.numstat()
        if not stats:
            return []

        merged: dict[str, FileStats] = {}
        for entry in stats:
            prev = merged.get(entry.path)
            if prev is None:
                merged[entry.path] = entry
            else:
                merged[entry.path] = FileStats(
                    path=entry.path,
                    added=prev.added + entry.added,
                    removed=prev.removed + entry.removed,
                )

        ordered = sorted(merged.values(), key=lambda f: f.changed, reverse=True)
        return ordered[:top] if top else ordered

    def bus_factor(self) -> int:
        """Minimum number of top authors covering 50% of all commits."""
        contributors = self.contributors()
        if not contributors:
            return 0
        total = sum(c.commits for c in contributors)
        if total == 0:
            return 0
        half = total / 2
        running = 0
        for index, contributor in enumerate(contributors, start=1):
            running += contributor.commits
            if running >= half:
                return index
        return 0

    def summary(self) -> Summary:
        """Aggregate the repository into a single :class:`Summary`."""
        self._require_repo()
        commits = self.commits()
        authors = self.contributors()
        numstat = self.numstat()

        if commits:
            first, last = commits[0].date, commits[-1].date
            total_added = sum(f.added for f in numstat)
            total_removed = sum(f.removed for f in numstat)
            files_touched = len({f.path for f in numstat})
            weeks = self.weekly_activity()
            avg_commits_per_week = len(commits) / len(weeks) if weeks else 0.0
        else:
            first = last = None
            total_added = total_removed = files_touched = 0
            avg_commits_per_week = 0.0

        return Summary(
            path=str(self.path),
            branch=self.current_branch,
            total_commits=len(commits),
            total_authors=len(authors),
            total_added=total_added,
            total_removed=total_removed,
            files_touched=files_touched,
            first_commit=first,
            last_commit=last,
            bus_factor=self.bus_factor(),
            avg_commits_per_week=round(avg_commits_per_week, 2),
        )


def instrument(func: Iterable[Commit]) -> int:
    """Return the number of commits in an iterable of :class:`Commit`.

    Provided as a tiny, dependency-free building block::

        repo = GitRepository(".")
        total = instrument(repo.commits())
    """
    return sum(1 for _ in func)


__all__ = [
    "Commit",
    "Contributor",
    "FileStats",
    "GitError",
    "GitRepository",
    "Summary",
    "WeekActivity",
    "instrument",
]