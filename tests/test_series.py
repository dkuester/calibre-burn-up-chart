"""Tests for series.py: series data and the series checks."""

from datetime import date, datetime

import pytest
import series as srs


def _book(series, index, read=False, title=None, authors=("A",)):
    return {"series": series, "series_index": index, "#gelesen": read,
            "title": title or "{} {}".format(series, index),
            "authors": authors}


def _library():
    return {
        # same series under three names; 6 unread although 13 is read
        1: _book("Expanse", 1.0, read=True),
        2: _book("The Expanse", 6.0),
        3: _book("The Expanse-Serie", 13.0, read=True),
        # two books numbered 1 (no number kept), all unread
        4: _book("Classics", 1.0, title="b"),
        5: _book("Classics", 1.0, title="A"),
        6: _book("Classics", 2.0),
        # clean series
        7: _book("Dune", 1.0, read=True),
        8: _book("Dune", 2.0),
        # no series
        9: {"title": "Single", "#gelesen": True},
        10: {"title": "Empty series", "series": "", "#gelesen": False},
    }


def test_collect_series(make_db):
    series = srs.collect_series(make_db(_library()), "#gelesen")
    assert sorted(series) == ["Classics", "Dune", "Expanse", "The Expanse",
                              "The Expanse-Serie"]
    # sorted by index, then title (case-insensitive)
    assert [b["book_id"] for b in series["Classics"]] == [5, 4, 6]
    assert series["Dune"][0] == {"book_id": 7, "title": "Dune 1.0",
                                 "authors": ("A",), "index": 1.0,
                                 "read": True, "last_read": None}
    assert series["Dune"][1]["read"] is False


def test_collect_series_defaults(make_db):
    books = {1: {"series": "S", "series_index": None, "#read": True},
             2: {"series": "S", "series_index": 3, "#read": "yes"}}
    books_s = srs.collect_series(make_db(books), "#read")["S"]
    assert books_s[0] == {"book_id": 1, "title": "", "authors": (),
                          "index": 1.0, "read": True, "last_read": None}
    assert books_s[1]["index"] == 3.0
    assert books_s[1]["read"] is False   # only True counts as read


@pytest.mark.parametrize("name, key", [
    ("The Expanse-Serie", "expanse"),
    ("Expanse", "expanse"),
    ("THE EXPANSE", "expanse"),
    ("The Mistborn Saga", "mistborn"),
    ("The Crossroads Trilogy", "crossroads"),
    ("Ein Kate Wise Mystery", "kate wise mystery"),
    ("A Kate Wise Mystery", "kate wise mystery"),
    ("Star Trek - Deep Space Nine", "star trek deep space nine"),
    ("Star Trek: Deep Space Nine", "star trek deep space nine"),
    ("Les Misérables", "miserables"),
    ("L'Épée", "epee"),
    ("Killerbot-Reihe Serie", "killerbot"),
    # never empty: a lone article or series word stays
    ("The", "the"),
    ("Saga", "saga"),
    ("The Saga", "saga"),
    # years and numbers tell series apart
    ("Black Panther (2005-2008)", "black panther 2005 2008"),
    ("Delphi Series Two", "delphi series two"),
])
def test_normalize_series_name(name, key):
    assert srs.normalize_series_name(name) == key


def test_format_index():
    assert srs.format_index(3.0) == "3"
    assert srs.format_index(1.5) == "1.5"


def test_find_name_variants(make_db):
    series = srs.collect_series(make_db(_library()), "#gelesen")
    assert srs.find_name_variants(series) == [{
        "kind": srs.NAME_VARIANTS,
        "series": ["Expanse", "The Expanse", "The Expanse-Serie"],
        "indices": [], "max_read": None, "book_ids": [1, 2, 3],
        "display": "Expanse",
    }]


def test_find_name_variants_display_most_books():
    series = {"Saga": [_vol(1, 1.0)], "The Saga": [_vol(2, 1.0),
                                                   _vol(3, 2.0)]}
    assert srs.find_name_variants(series)[0]["display"] == "The Saga"


def test_find_duplicate_indices(make_db):
    series = srs.collect_series(make_db(_library()), "#gelesen")
    assert srs.find_duplicate_indices(series) == [{
        "kind": srs.DUPLICATE_INDEX, "series": ["Classics"],
        "indices": [1.0], "max_read": None, "book_ids": [5, 4],
    }]


def test_find_gaps():
    def books(*specs):
        return [{"book_id": i, "index": idx, "read": read}
                for i, (idx, read) in enumerate(specs, 1)]

    series = {
        "Gap": books((1.0, False), (2.0, False), (2.0, True),
                     (3.0, True), (4.0, False)),
        "Clean": books((1.0, True), (2.0, False)),
        "Unread": books((1.0, False), (2.0, False)),
    }
    assert srs.find_gaps(series) == [{
        "kind": srs.GAP, "series": ["Gap"], "indices": [1.0, 2.0],
        "max_read": 3.0, "book_ids": [1, 2],
    }]


def test_find_series_problems_order(make_db):
    lib = _library()
    lib[11] = _book("alpha", 2.0)
    lib[12] = _book("alpha", 2.0)
    problems = srs.find_series_problems(
        srs.collect_series(make_db(lib), "#gelesen"))
    assert [(p["kind"], p["series"][0]) for p in problems] == [
        (srs.NAME_VARIANTS, "Expanse"),
        (srs.DUPLICATE_INDEX, "alpha"),
        (srs.DUPLICATE_INDEX, "Classics"),
    ]
    assert srs.problem_counts(problems) == {
        "series_names": 1, "series_duplicates": 2, "series_gaps": 0}


def test_find_series_problems_gap_per_name(make_db):
    # Gaps are found within one series name; across names they show as a
    # name variant first.
    lib = {1: _book("S", 1.0), 2: _book("S", 2.0, read=True)}
    problems = srs.find_series_problems(
        srs.collect_series(make_db(lib), "#gelesen"))
    assert srs.problem_counts(problems) == {
        "series_names": 0, "series_duplicates": 0, "series_gaps": 1}


def test_series_csv_rows(make_db):
    problems = srs.find_series_problems(
        srs.collect_series(make_db(_library()), "#gelesen"))
    labels = {srs.NAME_VARIANTS: "names", srs.DUPLICATE_INDEX: "dup",
              srs.GAP: "gap"}
    rows = srs.series_csv_rows(problems, labels,
                               lambda p: "{} books".format(len(p["book_ids"])))
    assert rows == [
        ["names", "Expanse | The Expanse | The Expanse-Serie", "3 books", 3,
         "1 2 3"],
        ["dup", "Classics", "2 books", 2, "5 4"],
    ]


def test_collect_series_last_read(make_db):
    books = {1: {"series": "S", "#gelesen": True,
                 "#last_read": datetime(2024, 5, 6, 23, 0)},
             2: {"series": "S", "#gelesen": True,
                 "#last_read": date(2023, 1, 2)},
             3: {"series": "S", "#gelesen": True, "#last_read": "junk"}}
    books_s = srs.collect_series(make_db(books), "#gelesen", "#last_read")["S"]
    assert [b["last_read"] for b in books_s] == [
        date(2024, 5, 6), date(2023, 1, 2), None]


def _vol(book_id, index, read=False, last_read=None, title=None):
    return {"book_id": book_id, "title": title or "T{}".format(index),
            "authors": (), "index": index, "read": read,
            "last_read": last_read}


def test_started_series():
    series = {
        # gap: 2 unread below the highest read (4); 5 is the next after it
        "Gap": [_vol(1, 1.0, True, date(2020, 1, 1)), _vol(2, 2.0),
                _vol(3, 4.0, True, date(2022, 3, 1)), _vol(4, 4.0),
                _vol(5, 5.0)],
        # gap without anything after the highest read volume
        "Gap end": [_vol(6, 1.0), _vol(7, 2.0, True, date(2021, 1, 1))],
        # no gap: next is above the highest read volume
        "Plain": [_vol(8, 1.0, True, date(2025, 1, 1)), _vol(9, 2.0)],
        # no read dates at all
        "Undated": [_vol(10, 1.0, True), _vol(11, 2.0)],
        "Single": [_vol(12, 1.0)],
        "All read": [_vol(13, 1.0, True), _vol(14, 2.0, True)],
        "Unread": [_vol(15, 1.0), _vol(16, 2.0)],
    }
    started = srs.started_series(series)
    assert [s["series"] for s in started] == [
        "Undated", "Gap end", "Gap", "Plain"]
    undated, gap_end, gap, plain = started
    assert undated["last_read"] is None
    assert gap["read"] == 2 and gap["total"] == 5
    assert gap["next_book"]["book_id"] == 2
    assert gap["after_book"]["book_id"] == 5
    assert gap["last_read"] == date(2022, 3, 1)
    assert gap["book_ids"] == [1, 2, 3, 4, 5]
    assert gap_end["next_book"]["book_id"] == 6
    assert gap_end["after_book"] is None
    assert plain["next_book"]["book_id"] == 9
    assert plain["after_book"] is None


def test_started_series_ties_by_name():
    series = {name: [_vol(1, 1.0, True, date(2024, 1, 1)), _vol(2, 2.0)]
              for name in ("b", "A")}
    assert [s["series"] for s in srs.started_series(series)] == ["A", "b"]


def test_started_csv_rows():
    series = {
        "Gap": [_vol(1, 1.5, title="Half"), _vol(2, 3.0, True,
                date(2024, 2, 1)), _vol(3, 4.0, title="Four")],
        "Undated": [_vol(4, 1.0, True), _vol(5, 2.0, title="Two")],
    }
    rows = srs.started_csv_rows(srs.started_series(series), "%d.%m.%Y")
    assert rows == [
        ["Undated", 1, 2, "2", "Two", "", "", ""],
        ["Gap", 1, 3, "1.5", "Half", "4", "Four", "01.02.2024"],
    ]


def test_backlog_by_series():
    series = {
        "Big": [_vol(1, 1.0), _vol(2, 2.0), _vol(3, 3.0, True)],
        "b tie": [_vol(4, 1.0)],
        "A tie": [_vol(5, 1.0), _vol(6, 2.0, True)],
        "Read": [_vol(7, 1.0, True)],
    }
    result = srs.backlog_by_series(series, limit=2)
    assert result["top"] == [
        {"series": "Big", "unread": 2, "read": 1, "total": 3,
         "book_ids": [1, 2]},
        {"series": "A tie", "unread": 1, "read": 1, "total": 2,
         "book_ids": [5]},
    ]
    assert result["series_count"] == 3
    assert result["books"] == 4
    assert result["rest_series"] == 1
    assert result["rest_books"] == 1


def test_backlog_by_series_empty():
    assert srs.backlog_by_series({}) == {
        "top": [], "series_count": 0, "books": 0,
        "rest_series": 0, "rest_books": 0}


# ----------------------------------------------------------------------
# Merged series
# ----------------------------------------------------------------------
def test_parse_series_groups():
    text = ("Die Nebelgeborenen = Mistborn =The Mistborn Saga\n"
            "\n"
            "  = Solo =  \n"
            "A = a = B = \n")
    assert srs.parse_series_groups(text) == [
        ["Die Nebelgeborenen", "Mistborn", "The Mistborn Saga"],
        ["Solo"], ["A", "B"]]
    assert srs.parse_series_groups("") == []


def test_format_series_groups():
    groups = [["Die Nebelgeborenen", "Mistborn"], ["A", "B", "C"]]
    text = srs.format_series_groups(groups)
    assert text == "Die Nebelgeborenen = Mistborn\nA = B = C"
    assert srs.parse_series_groups(text) == groups


def test_series_group_problems():
    groups = [["A", "B"], ["Solo"], ["b", "C", "a"], ["A", "D"]]
    assert srs.series_group_problems(groups) == {
        "single": ["Solo"], "repeated": ["b", "a", "A"]}
    assert srs.series_group_problems([["A", "B"]]) == {
        "single": [], "repeated": []}


def test_add_series_group():
    groups = [["Die Nebelgeborenen", "Mistborn"]]
    # new group
    added = srs.add_series_group(groups, ["Expanse", "The Expanse"])
    assert added == [["Die Nebelgeborenen", "Mistborn"],
                     ["Expanse", "The Expanse"]]
    # extends the group that has one of the names; input unchanged
    added = srs.add_series_group(groups, ["mistborn", "The Mistborn Saga"])
    assert added == [["Die Nebelgeborenen", "Mistborn", "The Mistborn Saga"]]
    assert groups == [["Die Nebelgeborenen", "Mistborn"]]


def _editions():
    # Stormlight read up to 2 in German, 1 in English
    return {
        "Die Sturmlicht-Chroniken": [
            _vol(1, 1.0, True, date(2020, 1, 1), title="DE1"),
            _vol(2, 2.0, True, date(2021, 1, 1), title="DE2"),
            _vol(3, 3.0, title="DE3"), _vol(4, 4.0, title="DE4")],
        "The Stormlight Archive": [
            _vol(5, 1.0, True, date(2019, 1, 1), title="EN1"),
            _vol(6, 2.0, title="EN2")],
        "Other": [_vol(7, 1.0)],
    }


def test_merge_series():
    series = _editions()
    groups = [["Die Sturmlicht-Chroniken", "the stormlight archive",
               "Not in library"],
              ["Other"],                       # single: ignored
              ["Missing", "Other"]]
    merged = srs.merge_series(series, groups)
    # display name is the first of the group, even if not in the library
    assert sorted(merged) == ["Die Sturmlicht-Chroniken", "Missing"]
    books = merged["Die Sturmlicht-Chroniken"]
    assert [b["title"] for b in books] == [
        "DE1", "EN1", "DE2", "EN2", "DE3", "DE4"]
    assert books[1]["source"] == "The Stormlight Archive"
    assert merged["Missing"][0]["source"] == "Other"
    # the input is not changed
    assert "source" not in series["Other"][0]
    assert len(series["Die Sturmlicht-Chroniken"]) == 4


def test_merge_series_first_group_wins():
    series = {"A": [_vol(1, 1.0)], "B": [_vol(2, 1.0)]}
    merged = srs.merge_series(series, [["A", "B"], ["C", "B"]])
    assert list(merged) == ["A"]
    assert srs.merge_series(series, []) == {
        "A": [dict(_vol(1, 1.0), source="A")],
        "B": [dict(_vol(2, 1.0), source="B")]}


def test_started_series_merged_editions():
    groups = [["Die Sturmlicht-Chroniken", "The Stormlight Archive"]]
    started = srs.started_series(srs.merge_series(_editions(), groups))
    assert len(started) == 1
    s = started[0]
    # EN2 is left out: volume 2 is read in German
    assert (s["read"], s["total"]) == (3, 5)
    assert s["next_book"]["title"] == "DE3"
    assert s["after_book"] is None
    assert s["last_read"] == date(2021, 1, 1)
    assert sorted(s["book_ids"]) == [1, 2, 3, 4, 5, 6]


def test_started_series_same_name_duplicates_stay():
    # two books numbered 1 under one name are not editions of each other
    series = {"S": [_vol(1, 1.0, True), _vol(2, 1.0), _vol(3, 2.0)]}
    s = srs.started_series(srs.merge_series(series, []))[0]
    assert (s["read"], s["total"]) == (1, 3)
    assert s["next_book"]["book_id"] == 2


def test_started_series_merged_unnumbered():
    # "1" twice under one name and read there: a volume of its own, even
    # though 1 is read under the other name too
    series = {"Killerbot": [_vol(1, 1.0, True)],
              "Murderbot": [_vol(2, 1.0, True), _vol(3, 1.0, title="Home"),
                            _vol(4, 2.0)]}
    merged = srs.merge_series(series, [["Killerbot", "Murderbot"]])
    s = srs.started_series(merged)[0]
    assert (s["read"], s["total"]) == (2, 4)
    assert s["next_book"]["title"] == "Home"


def test_series_problems_merged(make_db):
    lib = {
        1: _book("Die Nebelgeborenen", 1.0, read=True),
        2: _book("Die Nebelgeborenen", 3.0, read=True),
        3: _book("Mistborn", 1.0),           # read in German: no gap
        4: _book("Mistborn", 2.0),           # unread in both: gap
        5: _book("The Mistborn Saga", 3.0, read=True),
        6: _book("Expanse", 1.0),
        7: _book("The Expanse", 1.0),
        8: _book("The Expanse-Serie", 2.0),
    }
    series = srs.collect_series(make_db(lib), "#gelesen")
    groups = [["Die Nebelgeborenen", "Mistborn", "The Mistborn Saga"],
              ["Expanse", "The Expanse"]]
    problems = srs.find_series_problems(series, groups)
    assert [(p["kind"], p["series"], p["book_ids"]) for p in problems] == [
        # the merged "Expanse" and the unlisted name are still variants
        (srs.NAME_VARIANTS, ["Expanse", "The Expanse-Serie"], [6, 7, 8]),
        (srs.GAP, ["Die Nebelgeborenen"], [4]),
    ]
    # without the list: two variant groups; Expanse 1 twice across names
    # is no duplicate, and "Mistborn" alone has nothing read
    kinds = [p["kind"] for p in srs.find_series_problems(series)]
    assert kinds == [srs.NAME_VARIANTS, srs.NAME_VARIANTS]


def test_backlog_by_series_merged():
    groups = [["Die Sturmlicht-Chroniken", "The Stormlight Archive"]]
    top = srs.backlog_by_series(srs.merge_series(_editions(), groups))["top"]
    # books, as in the TBR chart: EN2 is still unread
    assert top[0] == {"series": "Die Sturmlicht-Chroniken", "unread": 3,
                      "read": 3, "total": 6, "book_ids": [6, 3, 4]}

