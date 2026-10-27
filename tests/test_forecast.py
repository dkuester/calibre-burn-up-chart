"""Tests for the robust forecast: full_months(), trimmed_mean(),
robust_rates(), forecast_backlog() and its band helpers."""

import math
from datetime import date, timedelta

import export_reading_status as ers
import pytest

TODAY = date(2026, 10, 27)


def _rates(months, today=TODAY):
    """compute_rates()-style list from ``(added, read)`` per month: the
    first entry is the start month, the last one the current month."""
    year, month = today.year, today.month
    keys = []
    for _ in months:
        keys.append((year, month))
        year, month = (year, month - 1) if month > 1 else (year - 1, 12)
    keys.reverse()
    out = []
    for (y, m), (added, read) in zip(keys, months):
        day = today if (y, m) == (today.year, today.month) \
            else ers.month_end(y, m)
        out.append((day, added, read, 0.0, 0.0))
    return out


def _rows(start, today=TODAY):
    return [(today, 0, 0, start)]


def _library(make_db, first, today, per_month=(5, 3), imports=None):
    """Library with ``per_month`` books added/read on the 10th of every
    month from ``first`` to ``today`` plus ``imports`` {date: books}."""
    books = {}
    day = first
    while day <= today:
        added, read = per_month
        for i in range(added):
            books[len(books) + 1] = {
                'timestamp': day, '#gelesen': i < read,
                '#last_read': day if i < read else None}
        day = (day.replace(day=28) + timedelta(days=4)).replace(day=10)
    for when, count in (imports or {}).items():
        for _ in range(count):
            books[len(books) + 1] = {'timestamp': when, '#gelesen': False}
    return make_db(books)


# --- full_months() --------------------------------------------------------

def test_full_months_drop_first_and_partial_current_month():
    rates = _rates([(500, 0), (4, 2), (6, 1), (3, 3)])
    assert ers.full_months(rates) == [(4, 2), (6, 1)]


def test_full_months_count_a_current_month_ending_today():
    today = date(2026, 9, 30)
    rates = _rates([(500, 0), (4, 2), (6, 1)], today=today)
    assert ers.full_months(rates) == [(4, 2), (6, 1)]


def test_full_months_exclude_known_imports():
    rates = _rates([(500, 0), (104, 2), (6, 1), (3, 3)])
    assert ers.full_months(rates, {(2026, 8): 100}) == [(4, 2), (6, 1)]


# --- trimmed_mean() -------------------------------------------------------

@pytest.mark.parametrize('values, expected', [
    ([], 0.0),
    ([7], 7.0),
    ([1, 9], 5.0),
    ([1, 2, 600], 2.0),                     # three values: median
    ([1, 2, 4, 600], 3.0),                  # four values: median
    (list(range(10)), 4.5),                 # 2 cut at each end
    ([5] * 20 + [600, 300, 200, 100, 0], 5.0),
])
def test_trimmed_mean(values, expected):
    assert ers.trimmed_mean(values) == pytest.approx(expected)


# --- robust_rates() -------------------------------------------------------

def test_robust_rates_need_three_full_months():
    rates = _rates([(500, 0), (4, 2), (6, 1), (3, 3)])
    rr = ers.robust_rates(rates)
    assert rr == {'status': ers.FORECAST_NONE, 'months': 2, 'added': None,
                  'read': None, 'spread': 0.0}


def test_robust_rates_preliminary_and_ok():
    few = ers.robust_rates(_rates([(9, 0)] + [(5, 3)] * 3 + [(0, 0)]))
    assert few['status'] == ers.FORECAST_PRELIMINARY
    assert few['months'] == 3
    full = ers.robust_rates(_rates([(9, 0)] + [(5, 3)] * 12 + [(0, 0)]))
    assert full['status'] == ers.FORECAST_OK
    assert (full['added'], full['read']) == (5, 3)


def test_robust_rates_window_is_capped_at_24_months():
    old = [(50, 0)] * 30
    recent = [(4, 1)] * 24
    rr = ers.robust_rates(_rates([(9, 0)] + old + recent + [(0, 0)]))
    assert rr['months'] == 24
    assert (rr['added'], rr['read']) == (4, 1)


def test_robust_rates_ignore_a_bulk_import():
    months = [(5, 3)] * 23 + [(603, 3)]
    rr = ers.robust_rates(_rates([(9, 0)] + months + [(0, 0)]))
    assert rr['added'] == 5
    # the import does not widen the band: equal months give the floor
    assert rr['spread'] == pytest.approx(math.sqrt(8))


def test_robust_rates_spread_is_iqr_based():
    months = [(c, 0) for c in (0, 2, 4, 6, 8)]
    rr = ers.robust_rates(_rates([(9, 0)] + months + [(0, 0)]))
    assert rr['spread'] == pytest.approx(4 / 1.349)


# --- forecast_backlog() ---------------------------------------------------

def _fc(months, start):
    return ers.forecast_backlog(_rows(start), _rates(
        [(0, 0)] + months + [(0, 0)]))


def test_forecast_without_enough_data():
    fc = _fc([(5, 3)] * 2, 100)
    assert fc['ok'] is False
    assert fc['status'] == ers.FORECAST_NONE
    assert fc['zero_date'] is None


def test_forecast_without_rows():
    fc = ers.forecast_backlog([])
    assert fc['ok'] is False
    assert fc['anchor'] is None


def test_robust_rates_spread_floor_for_few_equal_months():
    months = [(5, 5), (6, 9), (2, 5), (5, 8), (5, 10)]
    rr = ers.robust_rates(_rates([(9, 0)] + months + [(0, 0)]))
    # changes 0, -3, -3, -3, -5: interquartile range 0
    assert rr['spread'] == pytest.approx(math.sqrt(5 + 22 / 3))


def test_forecast_shrinking_without_noise():
    fc = _fc([(0, 2)] * 24, 100)
    assert fc['ok'] is True
    assert fc['slope'] == -2
    assert fc['spread'] == pytest.approx(math.sqrt(2))
    assert fc['quantile'] == ers.T_QUANTILE_90[23]
    assert fc['zero_date'] == ers.months_after(TODAY, 50)
    assert fc['zero_early'] < fc['zero_date'] < fc['zero_late']


def test_forecast_band_brackets_the_line():
    months = [(2, r) for r in (2, 3, 4, 5, 6) * 4]
    fc = _fc(months, 100)
    assert fc['slope'] == -2
    assert fc['zero_early'] < fc['zero_date'] < fc['zero_late']
    low, mid, high = ers.forecast_at(fc, 12)
    width = fc['quantile'] * fc['spread'] * math.sqrt(12 + 144 / 20)
    assert mid == 100 - 24
    assert (low, high) == pytest.approx((mid - width, mid + width))


def test_forecast_pessimistic_edge_never_reaches_zero():
    months = [(2, r) for r in (0, 1, 2, 3, 4, 5, 6)]
    fc = _fc(months, 1000)
    assert fc['status'] == ers.FORECAST_PRELIMINARY
    assert fc['slope'] < 0
    assert fc['zero_early'] is not None
    assert fc['zero_late'] is None


def test_forecast_growing():
    fc = _fc([(6, 2)] * 12, 100)
    assert fc['slope'] == 4
    assert fc['zero_date'] is None
    assert fc['zero_early'] is None


def test_forecast_backlog_already_empty():
    fc = _fc([(2, 4)] * 12, 0)
    assert fc['ok'] is True
    assert fc['zero_date'] is None


def test_forecast_computes_rates_from_rows():
    rows = [(ers.month_end(2025, m), 10 * m, 3 * m, 7 * m)
            for m in range(1, 13)]
    rows.append((date(2026, 1, 15), 125, 37, 88))
    fc = ers.forecast_backlog(rows)
    assert fc['months'] == 11
    assert fc['slope'] == 7
    assert fc['start'] == 88


def test_forecast_line_end():
    fc = _fc([(2, 4)] * 24, 100)
    assert ers.forecast_line_end(fc, date(2050, 1, 1)) == \
        (fc['zero_date'], 0.0)
    day, value = ers.forecast_line_end(fc, ers.months_after(TODAY, 10))
    assert value == pytest.approx(80, abs=0.1)
    growing = _fc([(6, 2)] * 12, 100)
    assert ers.forecast_line_end(growing, ers.months_after(TODAY, 10))[1] \
        == pytest.approx(140, abs=0.1)


def test_forecast_band_points():
    months = [(2, r) for r in (2, 3, 4, 5, 6) * 4]
    fc = _fc(months, 100)
    points = ers.forecast_band(fc, date(2050, 1, 1), steps=10)
    assert len(points) == 11
    assert points[0] == (TODAY, 100, 100)
    assert points[-1] == (fc['zero_late'], 0.0, 0.0)
    assert all(low <= high for _, low, high in points)
    short = ers.forecast_band(fc, ers.months_after(TODAY, 6), steps=4)
    assert short[-1][0] == ers.months_after(TODAY, 6)
    assert short[-1][1] > 0


def test_forecast_band_with_target_in_the_past():
    fc = _fc([(2, 4)] * 12, 100)
    points = ers.forecast_band(fc, TODAY - timedelta(days=30), steps=2)
    assert [p[0] for p in points] == [TODAY] * 3


# --- History lengths through export_snapshots() ---------------------------

@pytest.mark.parametrize('first, status, months', [
    (TODAY, ers.FORECAST_NONE, 0),                          # 0 days
    (TODAY - timedelta(days=14), ers.FORECAST_NONE, 0),     # 2 weeks
    (date(2026, 7, 27), ers.FORECAST_NONE, 2),              # 3 months
    (date(2025, 9, 27), ers.FORECAST_OK, 12),               # 13 months
    (date(2011, 10, 27), ers.FORECAST_OK, 24),              # 15 years
])
def test_history_lengths(make_db, first, status, months):
    db = _library(make_db, first, TODAY, imports={first: 300})
    info = ers.export_snapshots(db, today=TODAY)
    fc = ers.forecast_backlog(info['rows'])
    assert fc['status'] == status
    assert fc['months'] == months
    if status != ers.FORECAST_NONE:
        assert fc['slope'] == 2
        assert fc['start'] == info['backlog']


def test_five_months_are_preliminary(make_db):
    db = _library(make_db, date(2026, 5, 3), TODAY,
                  imports={date(2026, 7, 2): 120})
    fc = ers.forecast_backlog(ers.export_snapshots(db, today=TODAY)['rows'])
    assert fc['status'] == ers.FORECAST_PRELIMINARY
    assert fc['months'] == 4
    assert fc['slope'] == 2          # the import month is cut off
