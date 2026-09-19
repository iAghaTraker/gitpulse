"""Tests for gitpulse.charts."""

from __future__ import annotations

from gitpulse.charts import bar_chart


def test_bar_chart_scales_to_peak() -> None:
    chart = bar_chart([("a", 10), ("b", 5)], width=10)
    lines = chart.splitlines()
    assert lines[0].startswith("a")
    assert "█" * 10 in lines[0]
    assert "█" * 5 in lines[1]


def test_bar_chart_sorts_descending() -> None:
    chart = bar_chart([("a", 1), ("b", 9)], width=10)
    lines = chart.splitlines()
    assert lines[0].startswith("b")


def test_bar_chart_empty() -> None:
    assert bar_chart([]) == "(nothing to chart)"


def test_bar_chart_zero_values() -> None:
    assert bar_chart([("a", 0)]) == "(all values are zero)"