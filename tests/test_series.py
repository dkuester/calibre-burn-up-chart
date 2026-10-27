"""Tests for series.py: series data and the series checks."""

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
                                 "read": True}
    assert series["Dune"][1]["read"] is False


def test_collect_series_defaults(make_db):
    books = {1: {"series": "S", "series_index": None, "#read": True},
             2: {"series": "S", "series_index": 3, "#read": "yes"}}
    books_s = srs.collect_series(make_db(books), "#read")["S"]
    assert books_s[0] == {"book_id": 1, "title": "", "authors": (),
                          "index": 1.0, "read": True}
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
    }]


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
