"""Tests for compute_rates()."""

from datetime import date

import export_reading_status as ers
import pytest


def test_empty():
    assert ers.compute_rates([]) == []


def test_monthly_differences():
    rows = [
        (date(2024, 1, 31), 10, 2, 8),
        (date(2024, 2, 29), 13, 5, 8),
        (date(2024, 3, 15), 14, 9, 5),   # last snapshot = "today"
    ]
    rates = ers.compute_rates(rows)
    assert [(r[0], r[1], r[2]) for r in rates] == [
        (date(2024, 1, 31), 10, 2),
        (date(2024, 2, 29), 3, 3),
        (date(2024, 3, 15), 1, 4),
    ]


def test_skipped_months_count_zero():
    rows = [
        (date(2023, 11, 30), 5, 1, 4),
        (date(2024, 2, 29), 8, 4, 4),
    ]
    rates = ers.compute_rates(rows)
    assert [(r[0], r[1], r[2]) for r in rates] == [
        (date(2023, 11, 30), 5, 1),
        (date(2023, 12, 31), 0, 0),
        (date(2024, 1, 31), 0, 0),
        (date(2024, 2, 29), 3, 3),
    ]


def test_trailing_mean():
    rows = [
        (date(2024, 1, 31), 6, 0, 6),
        (date(2024, 2, 29), 9, 3, 6),
        (date(2024, 3, 31), 9, 9, 0),
        (date(2024, 4, 30), 12, 9, 3),
    ]
    # added per month: 6, 3, 0, 3 ; read per month: 0, 3, 6, 0
    rates = ers.compute_rates(rows, window=3)
    assert [r[3] for r in rates] == pytest.approx([6, 4.5, 3, 2])
    assert [r[4] for r in rates] == pytest.approx([0, 1.5, 3, 3])


def test_default_window_is_twelve_months():
    rows = [(date(2023, m, 1), m, 0, m) for m in range(1, 13)]
    rows.append((date(2024, 1, 1), 113, 0, 113))
    rates = ers.compute_rates(rows)
    # added: 1 per month in 2023, then 101 in Jan 2024.
    # Last window: Feb..Dec 2023 (11 x 1) + Jan 2024 (101) -> 112 / 12
    assert rates[-1][3] == pytest.approx(112 / 12)
