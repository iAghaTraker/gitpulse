"""GitPulse - dependency-free git repository analytics.

Exposes a small library API plus a command line interface
(``gitpulse``) for turning a git repository into useful numbers.
"""

from .analyzer import (
    Commit,
    Contributor,
    FileStats,
    GitError,
    GitRepository,
    Summary,
    WeekActivity,
    instrument,
)

__version__ = "0.1.0"

__all__ = [
    "Commit",
    "Contributor",
    "FileStats",
    "GitError",
    "GitRepository",
    "Summary",
    "WeekActivity",
    "instrument",
    "__version__",
]