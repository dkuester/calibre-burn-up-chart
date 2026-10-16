"""Tests for forecast_backlog()."""

from datetime import date, timedelta

import export_reading_status as ers


def _rows(points):
    """Build (date, total, read, backlog) rows from (date, backlog)."""
    return [(d, 0, 0, b) for d, b in points]


def test_linear_shrinking_backlog():
    anchor = date(2024, 3, 1)
    rows = _rows([
        (date(2024, 1, 1), 100),    # day -60
        (date(2024, 1, 31), 90),    # day -30
        (anchor, 80),               # day 0
    ])
    fc = ers.forecast_backlog(rows)
    assert fc["ok"] is True
    assert fc["count"] == 3
    # backlog drops 20 books over 60 days -> slope = -1/3 per day
    assert abs(fc["slope"] - (-20 / 60)) < 1e-9
    assert abs(fc["intercept"] - 80) < 1e-9
    # 80 books at 1/3 per day -> 240 days
    assert fc["zero_date"] == anchor + timedelta(days=240)


def test_flat_backlog():
    anchor = date(2024, 3, 1)
    rows = _rows([
        (date(2024, 1, 1), 50),
        (date(2024, 2, 1), 50),
        (anchor, 50),
    ])
    fc = ers.forecast_backlog(rows)
    assert fc["ok"] is True
    assert fc["slope"] == 0.0
    assert fc["intercept"] == 50.0
    assert fc["zero_date"] is None


def test_growing_backlog():
    anchor = date(2024, 3, 1)
    rows = _rows([
        (date(2024, 1, 1), 10),
        (date(2024, 2, 1), 20),
        (anchor, 30),
    ])
    fc = ers.forecast_backlog(rows)
    assert fc["ok"] is True
    assert fc["slope"] > 0
    assert fc["zero_date"] is None


def test_backlog_already_zero():
    anchor = date(2024, 3, 1)
    rows = _rows([
        (date(2024, 1, 1), 20),     # day -60
        (date(2024, 1, 31), 10),    # day -30
        (anchor, 0),                # day 0
    ])
    fc = ers.forecast_backlog(rows)
    assert fc["ok"] is True
    assert fc["slope"] < 0
    assert fc["intercept"] == 0.0
    assert fc["zero_date"] is None  # already at zero


def test_single_row_not_enough():
    rows = _rows([(date(2024, 1, 1), 50)])
    fc = ers.forecast_backlog(rows)
    assert fc["ok"] is False
    assert fc["zero_date"] is None


def test_window_too_small_returns_no_forecast():
    anchor = date(2024, 3, 1)
    rows = _rows([
        (anchor - timedelta(days=400), 1000),  # outside the 12-month window
        (anchor, 80),                          # only 1 point left in window
    ])
    fc = ers.forecast_backlog(rows)
    assert fc["ok"] is False
    assert fc["zero_date"] is None


def test_duplicate_dates_zero_variance():
    anchor = date(2024, 3, 1)
    rows = _rows([
        (anchor, 80),
        (anchor, 80),   # same date -> zero x-variance -> guard against /0
    ])
    fc = ers.forecast_backlog(rows)
    assert fc["ok"] is True
    assert fc["slope"] == 0.0
    assert fc["zero_date"] is None


def test_window_excludes_old_points():
    anchor = date(2024, 3, 1)
    rows = _rows([
        (anchor - timedelta(days=400), 1000),  # outlier, outside window
        (anchor - timedelta(days=30), 90),
        (anchor, 80),
    ])
    fc = ers.forecast_backlog(rows)
    assert fc["count"] == 2  # only the two recent points
    # slope based on the last two points: -10 over 30 days
    assert abs(fc["slope"] - (-10 / 30)) < 1e-9
    assert abs(fc["intercept"] - 80) < 1e-9
