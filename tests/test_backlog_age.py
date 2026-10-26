"""Tests for backlog_ages(), age_buckets() and median_age_years()."""

from datetime import date, datetime

import export_reading_status as ers
import pytest

TODAY = date(2026, 10, 26)


def test_backlog_ages_only_unread_with_date(make_db):
    books = {
        1: {"timestamp": date(2026, 1, 26), "#gelesen": False},
        2: {"timestamp": date(2020, 1, 1), "#gelesen": True},
        3: {"timestamp": datetime(2016, 10, 26, 9, 0)},      # no flag
        4: {"#gelesen": False},                              # no date
        5: {"timestamp": date(2026, 11, 1), "#gelesen": False},  # future
    }
    ages = ers.backlog_ages(make_db(books), today=TODAY)
    assert ages == [
        (1, date(2026, 1, 26), 273),
        (3, date(2016, 10, 26), (TODAY - date(2016, 10, 26)).days),
        (5, date(2026, 11, 1), 0),
    ]


def test_backlog_ages_custom_column_and_default_today(make_db):
    books = {1: {"timestamp": date.today(), "#read": True},
             2: {"timestamp": date.today(), "#read": None}}
    assert ers.backlog_ages(make_db(books), "#read") == \
        [(2, date.today(), 0)]


def test_age_buckets():
    ages = [(1, None, 10), (2, None, 364), (3, None, 366),
            (4, None, 800), (5, None, 4000), (6, None, 9000)]
    buckets = ers.age_buckets(ages, max_years=10)
    assert len(buckets) == 11
    assert buckets[0] == [1, 2]
    assert buckets[1] == [3]
    assert buckets[2] == [4]
    assert buckets[10] == [5, 6]          # 10.95 and 24.6 years
    assert all(not b for b in buckets[3:10])


def test_age_buckets_drop_trailing_empty():
    assert ers.age_buckets([(1, None, 30), (2, None, 400)]) == [[1], [2]]
    assert ers.age_buckets([]) == [[]]


def test_median_age_years():
    assert ers.median_age_years([]) is None
    assert ers.median_age_years([(1, None, 365.25)]) == pytest.approx(1)
    ages = [(i, None, d) for i, d in enumerate([0, 365.25, 730.5, 1461])]
    assert ers.median_age_years(ages) == pytest.approx(1.5)
