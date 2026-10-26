"""Tests for export_snapshots()."""

from datetime import date

import export_reading_status as ers
import pytest


def test_cumulative_snapshots_over_months(make_db):
    today = date(2024, 3, 15)
    books = {
        1: {"timestamp": date(2024, 1, 10), "#gelesen": True,
            "#last_read": date(2024, 2, 5)},
        2: {"timestamp": date(2024, 2, 20), "#gelesen": False},
        3: {"timestamp": date(2024, 3, 1), "#gelesen": True,
            "#last_read": date(2024, 3, 10)},
    }
    res = ers.export_snapshots(make_db(books), today=today)
    assert res["rows"] == [
        (date(2024, 1, 31), 1, 0, 1),
        (date(2024, 2, 29), 2, 1, 1),
        (date(2024, 3, 15), 3, 2, 1),
    ]
    assert res["total"] == 3
    assert res["read"] == 2
    assert res["backlog"] == 1
    assert res["month_count"] == 3


def test_month_boundary(make_db):
    today = date(2024, 2, 15)
    books = {
        1: {"timestamp": date(2024, 1, 31), "#gelesen": False},
        2: {"timestamp": date(2024, 2, 1), "#gelesen": False},
    }
    rows = ers.export_snapshots(make_db(books), today=today)["rows"]
    # January: only the book from the 31st.  February: both books.
    assert rows[0][1] == 1
    assert rows[1][1] == 2


def test_read_event_is_recorded_correctly(make_db):
    today = date(2024, 3, 31)
    books = {
        1: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": None},                       # at timestamp
        2: {"timestamp": date(2024, 2, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 15)},          # before timestamp
        3: {"timestamp": date(2024, 3, 1), "#gelesen": True,
            "#last_read": date(2024, 3, 20)},          # at last_read
    }
    res = ers.export_snapshots(make_db(books), today=today)
    assert res["missing_last_read"] == 1
    assert res["last_read_before_added"] == 1
    assert res["missing_timestamp"] == 0
    assert res["total"] == 3
    assert res["read"] == 3
    assert res["backlog"] == 0


def test_current_month_even_without_events(make_db):
    today = date(2024, 5, 20)
    db = make_db({1: {"timestamp": date(2024, 1, 5), "#gelesen": False}})
    rows = ers.export_snapshots(db, today=today)["rows"]
    assert rows[-1] == (date(2024, 5, 20), 1, 0, 1)
    assert len(rows) == 2


def test_missing_timestamp_is_counted(make_db):
    books = {
        1: {"timestamp": date(2024, 1, 1), "#gelesen": False},
        2: {"timestamp": None, "#gelesen": True,
            "#last_read": date(2024, 1, 5)},
    }
    res = ers.export_snapshots(make_db(books), today=date(2024, 2, 1))
    assert res["missing_timestamp"] == 1
    assert res["total"] == 1


def test_no_usable_events_raises(make_db):
    with pytest.raises(ers.NoDataError):
        ers.export_snapshots(make_db({}), today=date(2024, 1, 1))


def test_all_without_timestamp_raises(make_db):
    db = make_db({1: {"timestamp": None, "#gelesen": True}})
    with pytest.raises(ers.NoDataError):
        ers.export_snapshots(db, today=date(2024, 1, 1))


def test_custom_column_names(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 1), "read_yes": True,
                      "read_on": date(2024, 1, 10)}})
    res = ers.export_snapshots(db, read_column="read_yes",
                               last_read_column="read_on",
                               today=date(2024, 2, 1))
    assert res["read"] == 1
    assert res["backlog"] == 0


def test_log_path_writes_csv(make_db, tmp_path):
    db = make_db({1: {"timestamp": date(2024, 1, 1), "#gelesen": False}})
    path = tmp_path / "out.csv"
    ers.export_snapshots(db, log_path=str(path), today=date(2024, 2, 1))
    content = path.read_text(encoding="utf-8")
    assert "date,total,read,backlog" in content
    assert "2024-01-31,1,0,1" in content


def test_without_today_parameter_uses_date_today(make_db):
    db = make_db({1: {"timestamp": date(2000, 1, 1), "#gelesen": False}})
    res = ers.export_snapshots(db)
    assert res["rows"][-1][0] == date.today()
