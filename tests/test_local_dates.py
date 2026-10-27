"""Days are taken in local time, as the calibre book list shows them.

calibre returns its datetimes as UTC, so a book added in the evening
(German time) has the previous day in UTC. The Qt-free modules each
keep a copy of the conversion; all copies must agree.
"""

import time
from datetime import date, datetime, timedelta, timezone

import export_reading_status as ers
import import_days as imd
import pytest
import reading_goal
import series as srs

UTC = timezone.utc
CEST = timezone(timedelta(hours=2))
CET = timezone(timedelta(hours=1))

CONVERTERS = [ers.to_date, imd._to_date, reading_goal._local_date,
              srs._to_date]

CASES = [
    # evening in Germany: previous day in UTC
    (datetime(2022, 10, 12, 22, 0, tzinfo=UTC), CEST, date(2022, 10, 13)),
    # across a month and a year boundary
    (datetime(2025, 8, 31, 23, 30, tzinfo=UTC), CET, date(2025, 9, 1)),
    (datetime(2025, 12, 31, 23, 0, tzinfo=UTC), CET, date(2026, 1, 1)),
    # daytime: same day
    (datetime(2024, 5, 6, 12, 0, tzinfo=UTC), CEST, date(2024, 5, 6)),
    # west of UTC: earlier day
    (datetime(2024, 5, 6, 2, 0, tzinfo=UTC), timezone(timedelta(hours=-5)),
     date(2024, 5, 5)),
    # naive datetimes and dates are taken as they are
    (datetime(2024, 5, 6, 23, 0), CEST, date(2024, 5, 6)),
    (date(2024, 5, 6), CEST, date(2024, 5, 6)),
    (None, CEST, None),
    ("2024-05-06", CEST, None),
]


@pytest.mark.parametrize("convert", CONVERTERS,
                         ids=lambda f: f.__module__)
@pytest.mark.parametrize("value, tz, expected", CASES)
def test_local_day(convert, value, tz, expected):
    assert convert(value, tz) == expected


@pytest.fixture
def berlin(monkeypatch):
    """System time zone Central European Time (POSIX rule, no tzdata
    needed)."""
    monkeypatch.setenv("TZ", "CET-1CEST,M3.5.0,M10.5.0/3")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def test_default_is_system_time_zone(berlin):
    evening = datetime(2022, 10, 12, 22, 0, tzinfo=UTC)
    winter = datetime(2025, 12, 13, 23, 30, tzinfo=UTC)
    for convert in CONVERTERS:
        assert convert(evening) == date(2022, 10, 13)
        assert convert(winter) == date(2025, 12, 14)


def test_snapshots_use_local_month(berlin, make_db):
    # added 1 Oct 00:30 local time = 30 Sep 22:30 UTC
    books = {1: {"timestamp": datetime(2025, 9, 30, 22, 30, tzinfo=UTC),
                 "#gelesen": True,
                 "#last_read": datetime(2025, 10, 31, 23, 15, tzinfo=UTC)},
             2: {"timestamp": datetime(2025, 9, 1, 8, 0, tzinfo=UTC)}}
    rows = ers.export_snapshots(make_db(books), "#gelesen",
                                "#last_read")["rows"]
    # September has only book 2, October adds book 1, it is read on
    # 1 November local time (31 October 23:15 UTC)
    assert rows[:2] == [(date(2025, 9, 30), 1, 0, 1),
                        (date(2025, 10, 31), 2, 0, 2)]
    assert rows[2] == (date(2025, 11, 30), 2, 1, 1)


def test_read_before_added_in_local_days(berlin, make_db):
    # same local day (13 Oct): not read before added
    books = {1: {"timestamp": datetime(2022, 10, 12, 22, 0, tzinfo=UTC),
                 "#gelesen": True,
                 "#last_read": datetime(2022, 10, 13, 9, 0, tzinfo=UTC)}}
    assert ers.find_date_problems(make_db(books), "#gelesen",
                                  "#last_read") == []


def test_import_day_is_local_day(berlin, make_db):
    books = {n: {"timestamp": datetime(2020, 9, 3, 22, 0, tzinfo=UTC),
                 "authors": (f"Author {n}",), "formats": ("EPUB",)}
             for n in range(1, imd.MIN_BOOKS + 1)}
    days = imd.find_import_days(make_db(books), "#gelesen", "#last_read")
    assert [d["added"] for d in days] == [date(2020, 9, 4)]


def test_series_last_read_is_local_day(berlin, make_db):
    books = {1: {"series": "S", "#gelesen": True,
                 "#last_read": datetime(2026, 4, 29, 22, 44, tzinfo=UTC)}}
    books_s = srs.collect_series(make_db(books), "#gelesen",
                                 "#last_read")["S"]
    assert books_s[0]["last_read"] == date(2026, 4, 30)
