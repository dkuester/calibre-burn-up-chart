"""Tests for compute_reading_time()."""

from datetime import date, datetime

import export_reading_status as ers


def test_empty_library(make_db):
    res = ers.compute_reading_time(make_db({}))
    assert res == {"points": [], "statistics": None, "missing_data": 0}


def test_single_book(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 1),
                      "#gelesen": True,
                      "#last_read": date(2024, 1, 11)}})
    res = ers.compute_reading_time(db)
    assert res["missing_data"] == 0
    assert res["points"] == [(date(2024, 1, 11), 10, 1)]
    assert res["statistics"] == {"count": 1, "mean": 10.0,
                                 "median": 10.0, "min": 10, "max": 10}


def test_median_odd_count(make_db):
    books = {
        1: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 6)},    # 5 days
        2: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 11)},   # 10 days
        3: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 31)},   # 30 days
    }
    stat = ers.compute_reading_time(make_db(books))["statistics"]
    assert stat == {"count": 3, "mean": 15.0, "median": 10.0,
                    "min": 5, "max": 30}


def test_median_even_count(make_db):
    books = {
        1: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 6)},    # 5 days
        2: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 11)},   # 10 days
        3: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 21)},   # 20 days
        4: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 31)},   # 30 days
    }
    stat = ers.compute_reading_time(make_db(books))["statistics"]
    assert stat["median"] == 15.0
    assert stat["mean"] == 16.25
    assert stat["min"] == 5
    assert stat["max"] == 30


def test_last_read_before_added_is_skipped(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 10), "#gelesen": True,
                      "#last_read": date(2024, 1, 1)}})
    res = ers.compute_reading_time(db)
    assert res["points"] == []
    assert res["statistics"] is None
    assert res["missing_data"] == 1


def test_last_read_equal_added_counts_zero_days(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 10), "#gelesen": True,
                      "#last_read": date(2024, 1, 10)}})
    res = ers.compute_reading_time(db)
    assert res["points"] == [(date(2024, 1, 10), 0, 1)]
    assert res["statistics"]["min"] == 0
    assert res["statistics"]["max"] == 0


def test_unread_books_are_ignored(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 1), "#gelesen": False,
                      "#last_read": date(2024, 1, 11)}})
    res = ers.compute_reading_time(db)
    assert res["points"] == []
    assert res["missing_data"] == 0


def test_read_without_last_read_counts_as_missing(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 1), "#gelesen": True,
                      "#last_read": None}})
    assert ers.compute_reading_time(db)["missing_data"] == 1


def test_read_without_timestamp_counts_as_missing(make_db):
    db = make_db({1: {"timestamp": None, "#gelesen": True,
                      "#last_read": date(2024, 1, 11)}})
    assert ers.compute_reading_time(db)["missing_data"] == 1


def test_datetime_inputs_become_date(make_db):
    db = make_db({1: {"timestamp": datetime(2024, 1, 1, 9, 0),
                      "#gelesen": True,
                      "#last_read": datetime(2024, 1, 11, 20, 0)}})
    res = ers.compute_reading_time(db)
    assert res["points"] == [(date(2024, 1, 11), 10, 1)]


def test_points_sorted_by_read_date(make_db):
    books = {
        1: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 3, 1)},    # 60 days (leap year)
        2: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 15)},   # 14 days
    }
    res = ers.compute_reading_time(make_db(books))
    assert res["points"] == [(date(2024, 1, 15), 14, 2),
                             (date(2024, 3, 1), 60, 1)]


def test_custom_column_names(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 1), "read_yes": True,
                      "read_on": date(2024, 1, 11)}})
    res = ers.compute_reading_time(db, read_column="read_yes",
                                   last_read_column="read_on")
    assert res["statistics"]["mean"] == 10.0


def test_delay_statistics_direct():
    assert ers.delay_statistics([]) is None
    pts = [(None, 10, 1), (None, 30, 2), (None, 20, 3), (None, 40, 4)]
    s = ers.delay_statistics(pts)
    assert s == {"count": 4, "mean": 25.0, "median": 25.0,
                 "min": 10, "max": 40}
    assert ers.delay_statistics(pts[:3])["median"] == 20.0
