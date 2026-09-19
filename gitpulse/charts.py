"""ASCII chart rendering for GitPulse's terminal output."""

from __future__ import annotations

from typing import Iterable

_BAR = "\u2588"  # full block


def bar_chart(
    values: Iterable[tuple[str, int]],
    width: int = 40,
    max_items: int = 20,
    sort: bool = True,
) -> str:
    """Render a horizontal ASCII bar chart.

    ``values`` is an iterable of ``(label, value)`` pairs. Bars are scaled
    to ``width`` columns and, when ``sort`` is true, drawn largest-first.
    """
    rows = sorted(values, key=lambda row: row[1], reverse=True) if sort else list(values)
    rows = rows[:max_items]
    if not rows:
        return "(nothing to chart)"

    peak = max(count for _, count in rows)
    if peak == 0:
        return "(all values are zero)"

    width = max(width, 4)
    label_width = max((len(name) for name, _ in rows), default=0)
    lines: list[str] = []
    for name, count in rows:
        bar = _BAR * max(1, round(count / peak * width))
        lines.append(f"{name:<{label_width}} |{bar} {count}")
    return "\n".join(lines)