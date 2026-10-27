"""Tests for the texts of the TBR widget in the status bar."""

from datetime import date

import status_summary as ss


def _tr(text):
    return text


HINT = 'Whole library · click to open the burn-up chart'

# Owner's library on 2026-10-27 (two snapshots of export_snapshots())
OWNER_ROWS = [
    (date(2025, 9, 30), 1860, 390, 1470),
    (date(2025, 10, 31), 1878, 398, 1480),
    (date(2026, 9, 30), 2100, 470, 1630),
    (date(2026, 10, 27), 2125, 473, 1652),
]


def test_owner_example():
    text, tooltip = ss.status_summary(OWNER_ROWS, _tr, ['Pace line.'])
    assert text == 'TBR: 1652 ▲172'
    assert tooltip.split('\n') == [
        '2125 books, 473 of them read (22 %)',
        '12 months ago: 1480 (+172)',
        'Pace line.',
        HINT,
    ]


def test_shrinking_backlog():
    rows = [(date(2025, 1, 31), 100, 10, 90),
            (date(2026, 1, 15), 100, 30, 70)]
    text, tooltip = ss.status_summary(rows, _tr)
    assert text == 'TBR: 70 ▼20'
    assert '12 months ago: 90 (−20)' in tooltip


def test_unchanged_backlog_has_no_arrow():
    rows = [(date(2025, 1, 31), 100, 10, 90),
            (date(2026, 1, 15), 100, 10, 90)]
    text, tooltip = ss.status_summary(rows, _tr)
    assert text == 'TBR: 90'
    assert '12 months ago: 90 (±0)' in tooltip


def test_gap_uses_last_older_snapshot():
    # No events in the trend month: the snapshot before still holds.
    rows = [(date(2024, 6, 30), 50, 0, 50),
            (date(2026, 3, 31), 80, 10, 70),
            (date(2026, 4, 2), 80, 10, 70)]
    assert ss.backlog_trend(rows) == (50, 20)


def test_young_library_has_no_trend():
    rows = [(date(2026, 3, 31), 10, 1, 9), (date(2026, 4, 2), 10, 2, 8)]
    assert ss.backlog_trend(rows) is None
    text, tooltip = ss.status_summary(rows, _tr)
    assert text == 'TBR: 8'
    assert tooltip.split('\n') == ['10 books, 2 of them read (20 %)', HINT]


def test_months_back_clamps_day_and_crosses_year():
    assert ss._months_back(date(2026, 2, 10), 12) == date(2025, 2, 28)
    assert ss._months_back(date(2026, 1, 31), 1) == date(2025, 12, 31)
    assert ss._months_back(date(2024, 3, 1), 1) == date(2024, 2, 29)


def test_no_books_counts_zero_percent():
    text, tooltip = ss.status_summary([(date(2026, 1, 1), 0, 0, 0)], _tr)
    assert text == 'TBR: 0'
    assert tooltip.startswith('0 books, 0 of them read (0 %)')


def test_empty_summary():
    assert ss.empty_summary(_tr) == (
        'TBR: 0', 'No data available for this analysis.\n' + HINT)


def test_problem_summary():
    text, tooltip = ss.problem_summary(('Column #x is missing.',), _tr)
    assert text == 'TBR: –'
    assert tooltip.split('\n') == [
        'Column #x is missing.',
        'You can change the column names in the plugin settings.']


def test_error_summary():
    assert ss.error_summary(_tr) == ('TBR: ?', 'Could not read the library.')
