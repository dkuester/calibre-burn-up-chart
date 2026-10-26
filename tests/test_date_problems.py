"""Tests for find_date_problems(), id_search() and problem_csv_rows()."""

import re
from datetime import date, datetime

import export_reading_status as ers


def _books():
    return {
        1: {"title": "Fine", "authors": ("A",), "timestamp": date(2024, 1, 5),
            "#gelesen": True, "#last_read": date(2024, 2, 1)},
        2: {"title": "No date", "authors": ("B", "C"),
            "timestamp": date(2023, 6, 1), "#gelesen": True},
        3: {"title": "early", "authors": ("D",),
            "timestamp": datetime(2024, 10, 30, 12, 0),
            "#gelesen": True, "#last_read": datetime(2024, 9, 30, 8, 0)},
        4: {"title": "Unread", "authors": ("E",),
            "timestamp": date(2020, 1, 1), "#gelesen": False},
        5: {"title": "No timestamp", "authors": ("F",), "#gelesen": True},
        6: {"title": "Same day", "authors": ("G",),
            "timestamp": date(2024, 3, 3), "#gelesen": True,
            "#last_read": date(2024, 3, 3)},
        7: {"title": "Also early", "authors": None,
            "timestamp": date(2024, 10, 30), "#gelesen": True,
            "#last_read": date(2024, 10, 1)},
    }


def test_finds_both_kinds_sorted_by_added_then_title(make_db):
    problems = ers.find_date_problems(make_db(_books()))
    assert [(p["book_id"], p["problem"]) for p in problems] == [
        (2, ers.MISSING_LAST_READ),
        (7, ers.READ_BEFORE_ADDED),
        (3, ers.READ_BEFORE_ADDED),
    ]


def test_problem_details(make_db):
    by_id = {p["book_id"]: p for p in ers.find_date_problems(make_db(_books()))}
    assert by_id[2]["authors"] == ("B", "C")
    assert by_id[2]["last_read"] is None
    assert by_id[2]["days_before"] is None
    assert by_id[3]["added"] == date(2024, 10, 30)
    assert by_id[3]["last_read"] == date(2024, 9, 30)
    assert by_id[3]["days_before"] == 30
    assert by_id[7]["authors"] == ()


def test_custom_columns(make_db):
    books = {1: {"title": "X", "timestamp": date(2024, 1, 1),
                 "#read": True, "#done": date(2023, 12, 1)}}
    problems = ers.find_date_problems(make_db(books), "#read", "#done")
    assert problems[0]["problem"] == ers.READ_BEFORE_ADDED
    assert problems[0]["days_before"] == 31


def test_no_problems(make_db):
    assert ers.find_date_problems(make_db({})) == []


def test_id_search():
    assert ers.id_search([3, 7]) == "id:3 or id:7"
    assert ers.id_search([]) == ""


def test_id_search_groups_long_lists():
    ids = list(range(1, 2201))
    query = ers.id_search(ids, group_size=50)
    assert sorted(int(t) for t in re.findall(r"id:(\d+)", query)) == ids
    # No flat or-chain longer than the group size anywhere.
    for part in re.split(r"[()]", query):
        assert part.count(" or ") < 50
    # Nesting stays shallow.
    depth = max_depth = 0
    for ch in query:
        depth += {"(": 1, ")": -1}.get(ch, 0)
        max_depth = max(max_depth, depth)
    assert max_depth <= 2


def test_problem_csv_rows(make_db):
    problems = ers.find_date_problems(make_db(_books()))
    labels = {ers.MISSING_LAST_READ: "missing",
              ers.READ_BEFORE_ADDED: "early"}
    rows = ers.problem_csv_rows(problems, "%d.%m.%Y", labels)
    assert rows[0] == [2, "missing", "No date", "B & C", "01.06.2023", "", ""]
    assert rows[2] == [3, "early", "early", "D", "30.10.2024", "30.09.2024",
                       30]
