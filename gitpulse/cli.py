"""Command line interface for GitPulse.

Usage::

    gitpulse stats
    gitpulse contributors
    gitpulse activity [--weeks N] [--width N]
    gitpulse churn [-n N]
    gitpulse report [-o FILE]
    gitpulse -p /path/to/repo <subcommand>
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .analyzer import GitError, GitRepository
from .charts import bar_chart
from .reporter import render_markdown


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gitpulse",
        description="Dependency-free git repository analytics.",
    )
    parser.add_argument(
        "-p",
        "--path",
        default=".",
        help="path to the git repository (default: current directory)",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("stats", help="show an aggregate repository summary")

    sub.add_parser("contributors", help="list authors by commit count")

    activity = sub.add_parser("activity", help="show commits per week")
    activity.add_argument(
        "--weeks", type=int, default=26, help="number of recent weeks to show"
    )
    activity.add_argument("--width", type=int, default=40, help="chart width")

    churn = sub.add_parser("churn", help="show files with the most line changes")
    churn.add_argument("-n", type=int, default=10, help="number of files to show")

    report = sub.add_parser("report", help="write a Markdown report")
    report.add_argument("-o", "--output", help="output file (default: stdout)")
    return parser


def _print_table(rows: list[tuple[str, str]]) -> None:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    for row in rows:
        print("  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip())


def _cmd_stats(repo: GitRepository) -> int:
    summary = repo.summary()
    first = summary.first_commit.strftime("%Y-%m-%d") if summary.first_commit else "-"
    last = summary.last_commit.strftime("%Y-%m-%d") if summary.last_commit else "-"
    print(f"Repository : {summary.path}")
    print(f"Branch     : {summary.branch}")
    print(f"Commits    : {summary.total_commits}")
    print(f"Authors    : {summary.total_authors}")
    print(f"Bus factor : {summary.bus_factor}")
    print(f"Lines added  : +{summary.total_added}")
    print(f"Lines removed: -{summary.total_removed}")
    print(f"Files touched: {summary.files_touched}")
    print(f"First commit : {first}")
    print(f"Last commit  : {last}")
    print(f"Avg commits/week: {summary.avg_commits_per_week}")
    return 0


def _cmd_contributors(repo: GitRepository) -> int:
    contributors = repo.contributors()
    if not contributors:
        print("no commits yet.")
        return 0
    total = sum(c.commits for c in contributors)
    rows: list[tuple[str, str, str]] = [("Author", "Commits", "Share")]
    for contributor in contributors:
        rows.append(
            (
                f"{contributor.name} <{contributor.email}>",
                str(contributor.commits),
                f"{contributor.share(total) * 100:.1f}%",
            )
        )
    _print_table(rows)
    return 0


def _cmd_activity(repo: GitRepository, weeks: int, width: int) -> int:
    weekly = repo.weekly_activity(max_weeks=weeks)
    if not weekly:
        print("no commits yet.")
        return 0
    values = [(w.week_start.isoformat(), w.commits) for w in weekly]
    print(bar_chart(values, width=width, max_items=weeks, sort=False))
    return 0


def _cmd_churn(repo: GitRepository, top: int) -> int:
    churn = repo.churn(top=top)
    if not churn:
        print("no changes yet.")
        return 0
    rows: list[tuple[str, str, str, str]] = [
        ("Path", "Added", "Removed", "Changed")
    ]
    for file_stats in churn:
        rows.append(
            (
                file_stats.path,
                str(file_stats.added),
                str(file_stats.removed),
                str(file_stats.changed),
            )
        )
    _print_table(rows)
    return 0


def _cmd_report(repo: GitRepository, output: str | None) -> int:
    report = render_markdown(repo)
    if output:
        with open(output, "w", encoding="utf-8") as handle:
            handle.write(report)
        print(f"report written to {output}")
    else:
        print(report)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    repo = GitRepository(args.path)
    try:
        if not repo.is_repo:
            raise GitError(f"not a git repository: {args.path}")
        if args.command == "stats":
            return _cmd_stats(repo)
        if args.command == "contributors":
            return _cmd_contributors(repo)
        if args.command == "activity":
            return _cmd_activity(repo, args.weeks, args.width)
        if args.command == "churn":
            return _cmd_churn(repo, args.n)
        if args.command == "report":
            return _cmd_report(repo, args.output)
    except GitError as error:
        print(f"gitpulse: error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())