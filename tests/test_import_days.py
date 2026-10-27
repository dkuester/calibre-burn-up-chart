"""Tests for find_import_days() and its helpers."""

from datetime import date, datetime

import import_days as imd

IMPORT_DAY = date(2024, 10, 30)
BUNDLE_DAY = date(2022, 10, 12)
NORMAL_DAY = date(2023, 5, 1)


def _books():
    books = {}
    # Bulk import: 20 books, 17 groups (12 series of one book each,
    # 3 authors without series, one book with neither, 4 more of
    # "Green Lantern" so it is the largest group)
    for n in range(12):
        books[n + 1] = {"timestamp": datetime(2024, 10, 30, 9, n),
                        "authors": (f"Author {n}", "Co"),
                        "series": f"Series {n}", "formats": ("EPUB",)}
    for n in range(3):
        books[20 + n] = {"timestamp": IMPORT_DAY,
                         "authors": (f"Solo {n}",), "formats": ()}
    books[30] = {"timestamp": IMPORT_DAY}
    for n in range(4):
        books[40 + n] = {"timestamp": IMPORT_DAY, "authors": ("Taylor",),
                         "series": "Green Lantern", "formats": None}
    books[1].update({"#gelesen": True, "#last_read": date(2024, 9, 1)})
    books[2].update({"#gelesen": True})
    books[3].update({"#gelesen": True,
                     "#last_read": datetime(2024, 10, 30, 20, 0)})
    books[4].update({"#gelesen": False, "#last_read": date(2020, 1, 1)})
    # Bundle: 28 books, one author, one series
    for n in range(28):
        books[100 + n] = {"timestamp": BUNDLE_DAY, "authors": ("Kikuchi",),
                          "series": "Vampire Hunter D", "formats": ("EPUB",)}
    # Ordinary day and a book without a date added
    books[200] = {"timestamp": NORMAL_DAY, "authors": ("X",)}
    books[201] = {"authors": ("Y",)}
    return books


def test_finds_only_the_import_day(make_db):
    days = imd.find_import_days(make_db(_books()), "#gelesen", "#last_read")
    assert [d["added"] for d in days] == [IMPORT_DAY]


def test_day_details(make_db):
    day = imd.find_import_days(make_db(_books()), "#gelesen",
                               "#last_read")[0]
    assert sorted(day["book_ids"]) == (
        list(range(1, 13)) + [20, 21, 22, 30, 40, 41, 42, 43])
    assert day["books"] == 20
    assert day["authors"] == 12 + 1 + 3 + 1  # "Co" counted once
    assert day["groups"] == 17
    assert (day["largest_group"], day["largest_count"]) == (
        "Green Lantern", 4)
    assert day["read"] == 3
    assert day["read_before_added"] == 1
    assert day["missing_last_read"] == 1
    assert day["without_file"] == 3 + 1 + 4


def test_thresholds(make_db):
    db = make_db(_books())
    # a bundle passes the book count, but not the group count
    days = imd.find_import_days(db, "#gelesen", "#last_read", min_groups=1)
    assert [d["added"] for d in days] == [BUNDLE_DAY, IMPORT_DAY]
    assert imd.find_import_days(db, "#gelesen", "#last_read",
                                min_groups=18) == []
    assert imd.find_import_days(db, "#gelesen", "#last_read",
                                min_books=21) == []


def test_largest_group_ties_break_by_name(make_db):
    books = {n: {"timestamp": IMPORT_DAY, "authors": (name,)}
             for n, name in enumerate("BCA", start=1)}
    day = imd.find_import_days(make_db(books), "r", "lr", min_books=1,
                               min_groups=1)[0]
    assert (day["largest_group"], day["largest_count"]) == ("C", 1)


def test_problems_on_import_days():
    days = [{"added": IMPORT_DAY}]
    problems = [{"added": IMPORT_DAY}, {"added": NORMAL_DAY},
                {"added": IMPORT_DAY}]
    assert imd.problems_on_import_days(problems, days) == 2
    assert imd.problems_on_import_days(problems, []) == 0


def test_csv_rows(make_db):
    days = imd.find_import_days(make_db(_books()), "#gelesen", "#last_read")
    row = imd.import_day_csv_rows(days, "%d.%m.%Y")[0]
    assert row[:9] == ["30.10.2024", 20, 17, 17, "Green Lantern (4)",
                       3, 1, 1, 8]
    assert row[9].split() == [str(i) for i in days[0]["book_ids"]]
