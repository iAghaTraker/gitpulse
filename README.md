# GitPulse

> Dependency-free git repository analytics: a **library** and a **CLI**.

GitPulse turns any git repository into useful numbers — contributors, weekly
activity, file churn, bus factor — in plain Python with **zero dependencies**.
It only executes read-only `git` commands, so it works on any repository with
git installed.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://img.shields.io/badge/CI-github%20actions-blue)](.github/workflows/ci.yml)

---

## Features

- **Dependency-free** core — only the Python standard library + `git`.
- Rich CLI with subcommands (`stats`, `contributors`, `activity`, `churn`, `report`).
- Reusable Python API for embedding analytics in your own tools.
- ASCII bar charts for terminal-friendly visualization.
- Markdown report generation for CI badges/issues/notebooks.
- Tested against Python 3.10 → 3.13 on GitHub Actions.

---

## Installation

```bash
pip install git+https://github.com/aghatraker/gitpulse.git
```

Or, to develop locally:

```bash
pip install -e ".[dev]"
```

---

## CLI usage

Run from inside any git repository:

```console
$ gitpulse stats
Repository : .
Branch     : main
Commits    : 1284
Authors    : 23
Bus factor : 2
Lines added  : +48213
Lines removed: -19244
Files touched: 214
First commit : 2021-04-12
Last commit  : 2026-01-03
Avg commits/week: 6.31
```

```console
$ gitpulse contributors
Author                    Commits  Share
Ava Hernandez <a@example>  581    45.2%
Liam Chen <l@example>      320    24.9%
...
```

```console
$ gitpulse activity
2025-07-07  |████████████████████████ 47
2025-07-14  |██████████████ 31
...
```

```console
$ gitpulse churn
Path                                       Added  Removed  Changed
src/engine/core.py                          5120    3481     8601
src/api/handlers.py                         2102    1040     3142
```

```console
$ gitpulse report -o report.md     # writes a Markdown report
```

Point it at any repository with `-p /path/to/repo`.

---

## Library usage

```python
from gitpulse import GitRepository, instrument

repo = GitRepository(".")

summary = repo.summary()
print(summary.total_commits, summary.total_authors, summary.bus_factor)

for c in repo.contributors():
    print(c.name, c.commits, f"{c.share(summary.total_commits) * 100:.1f}%")

weeks = repo.weekly_activity(max_weeks=12)
top = repo.churn(top=5)

# tiny dependency-free helper
total = instrument(repo.commits())
```

All the metrics you get from the CLI are available as plain data classes:
`Commit`, `Contributor`, `FileStats`, `WeekActivity`, `Summary`.

---

## What each metric means

| Metric | Meaning |
| --- | --- |
| Bus factor | People who'd have to be hit by a bus to lose 50% of the work — how fragile is the project? |
| Churn | Total lines added + removed per file; high churn files change often. |
| Weekly activity | Commit counts per calendar week, gaps filled for clean charts. |
| Avg commits / week | Total commits over the number of weeks the project was active. |

---

## Development

```bash
pip install -e ".[dev]"
python -m pytest
```

Contributions are welcome — open an issue or a pull request.

## License

MIT — see [LICENSE](LICENSE).