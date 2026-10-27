"""
Series data of the library and the series checks of the data-quality
dialog.

Groups the books by calibre's ``series`` field and finds three kinds of
problems: the same series under several names, volume numbers used
twice within a series, and gaps (an earlier volume unread although a
later one is read). Also lists the started series with their next
volume. Uses only the standard library, so it is testable without
calibre; nothing here changes book data.
"""

import re
import unicodedata
from datetime import date, datetime

# Problem kinds reported by find_series_problems()
NAME_VARIANTS = "name_variants"
DUPLICATE_INDEX = "duplicate_index"
GAP = "gap"

# Leading articles and trailing words like "Series" that do not tell two
# series apart ("The Expanse-Serie" is "Expanse").
_ARTICLES = frozenset((
    "the", "a", "an",
    "der", "die", "das", "ein", "eine",
    "le", "la", "les", "l",
))
_SERIES_WORDS = frozenset((
    "series", "serie", "reihe", "saga", "zyklus",
    "trilogy", "trilogie", "cycle",
))


def collect_series(db_api, read_column, last_read_column=None):
    """Books per series.

    :return: dict mapping each series name to a list of dicts with
        ``book_id``, ``title``, ``authors`` (tuple), ``index`` (float,
        1.0 when calibre has none), ``read`` (bool) and ``last_read``
        (date from ``last_read_column``, ``None`` if missing or without
        that column); sorted by index, then title. Books without a
        series are left out.
    """
    all_ids = db_api.all_book_ids()
    series_map  = db_api.all_field_for("series", all_ids)
    index_map   = db_api.all_field_for("series_index", all_ids)
    read_map    = db_api.all_field_for(read_column, all_ids)
    title_map   = db_api.all_field_for("title", all_ids)
    authors_map = db_api.all_field_for("authors", all_ids)
    last_read_map = (db_api.all_field_for(last_read_column, all_ids)
                     if last_read_column else {})

    series = {}
    for book_id in all_ids:
        name = series_map.get(book_id)
        if not name:
            continue
        index = index_map.get(book_id)
        series.setdefault(name, []).append({
            "book_id": book_id,
            "title": title_map.get(book_id) or "",
            "authors": tuple(authors_map.get(book_id) or ()),
            "index": 1.0 if index is None else float(index),
            "read": read_map.get(book_id) is True,
            "last_read": _to_date(last_read_map.get(book_id)),
        })
    for books in series.values():
        books.sort(key=lambda b: (b["index"], b["title"].lower()))
    return series


def normalize_series_name(name):
    """Comparison key for series names.

    Ignores case, accents, punctuation, a leading article and trailing
    words like "Series" or "Reihe": "The Expanse-Serie", "Expanse" and
    "the expanse" all become ``"expanse"``. A name that would become
    empty keeps its words.
    """
    text = unicodedata.normalize("NFKD", name.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    words = re.sub(r"[\W_]+", " ", text).split()
    if len(words) > 1 and words[0] in _ARTICLES:
        words = words[1:]
    while len(words) > 1 and words[-1] in _SERIES_WORDS:
        words = words[:-1]
    return " ".join(words)


def format_index(index):
    """Volume number for display: 3.0 → "3", 1.5 → "1.5"."""
    return "{:g}".format(index)


def find_name_variants(series):
    """Series names that :func:`normalize_series_name` maps together.

    :return: list of dicts with ``kind`` (:data:`NAME_VARIANTS`),
        ``series`` (the names, sorted), ``indices`` (empty), ``max_read``
        (``None``) and ``book_ids`` (all books of these series).
    """
    groups = {}
    for name in series:
        groups.setdefault(normalize_series_name(name), []).append(name)
    problems = []
    for names in groups.values():
        if len(names) < 2:
            continue
        names.sort(key=str.lower)
        problems.append(_problem(
            NAME_VARIANTS, names,
            [b["book_id"] for name in names for b in series[name]]))
    return problems


def find_duplicate_indices(series):
    """Volume numbers used by more than one book of a series.

    :return: list of dicts with ``kind`` (:data:`DUPLICATE_INDEX`),
        ``series`` (one name), ``indices`` (the duplicate numbers,
        ascending), ``max_read`` (``None``) and ``book_ids`` (the books
        with these numbers).
    """
    problems = []
    for name, books in series.items():
        counts = {}
        for b in books:
            counts[b["index"]] = counts.get(b["index"], 0) + 1
        duplicates = sorted(i for i, n in counts.items() if n > 1)
        if duplicates:
            problems.append(_problem(
                DUPLICATE_INDEX, [name],
                [b["book_id"] for b in books if b["index"] in duplicates],
                indices=duplicates))
    return problems


def find_gaps(series):
    """Unread volumes numbered below the highest read volume.

    :return: list of dicts with ``kind`` (:data:`GAP`), ``series`` (one
        name), ``indices`` (numbers of the unread volumes, ascending,
        each once), ``max_read`` (highest read number) and ``book_ids``
        (the unread volumes).
    """
    problems = []
    for name, books in series.items():
        read = [b["index"] for b in books if b["read"]]
        if not read:
            continue
        max_read = max(read)
        missing = [b for b in books if not b["read"] and b["index"] < max_read]
        if missing:
            problems.append(_problem(
                GAP, [name], [b["book_id"] for b in missing],
                indices=sorted({b["index"] for b in missing}),
                max_read=max_read))
    return problems


def find_series_problems(series):
    """All series problems: name variants, duplicate numbers, gaps.

    Each kind is sorted by series name (case-insensitive); see the
    ``find_*`` functions for the dict layout.
    """
    problems = []
    for find in (find_name_variants, find_duplicate_indices, find_gaps):
        problems += sorted(find(series),
                           key=lambda p: [n.lower() for n in p["series"]])
    return problems


def problem_counts(problems):
    """Number of problems per kind, as ``series_*`` keys for the report."""
    return {
        "series_names": sum(1 for p in problems if p["kind"] == NAME_VARIANTS),
        "series_duplicates": sum(
            1 for p in problems if p["kind"] == DUPLICATE_INDEX),
        "series_gaps": sum(1 for p in problems if p["kind"] == GAP),
    }


def series_csv_rows(problems, labels, describe):
    """Rows for a CSV export of :func:`find_series_problems`.

    ``labels`` maps each problem kind to its (translated) text,
    ``describe(problem)`` returns the (translated) details.
    """
    return [[labels[p["kind"]], " | ".join(p["series"]), describe(p),
             len(p["book_ids"]), " ".join(str(i) for i in p["book_ids"])]
            for p in problems]


def started_series(series):
    """Series begun but not finished, with the next volume to read.

    A series counts as started when it has at least two books, at least
    one of them read and at least one unread.

    :return: list of dicts with ``series`` (name), ``read`` and ``total``
        (number of books), ``next_book`` (the lowest unread volume),
        ``after_book`` (the first unread volume above the highest read
        one if ``next_book`` lies below it – a gap –, else ``None``),
        ``last_read`` (latest read date in the series, ``None`` if no
        read book has one) and ``book_ids`` (all books of the series).
        Books are dicts from :func:`collect_series`. Sorted by
        ``last_read``, oldest first and series without a read date
        before all others, so stalled series come first; ties by name.
    """
    result = []
    for name, books in series.items():
        read = [b for b in books if b["read"]]
        unread = [b for b in books if not b["read"]]
        if len(books) < 2 or not read or not unread:
            continue
        max_read = max(b["index"] for b in read)
        next_book = unread[0]
        after_book = None
        if next_book["index"] < max_read:
            after_book = next(
                (b for b in unread if b["index"] > max_read), None)
        dates = [b["last_read"] for b in read if b["last_read"]]
        result.append({
            "series": name,
            "read": len(read),
            "total": len(books),
            "next_book": next_book,
            "after_book": after_book,
            "last_read": max(dates) if dates else None,
            "book_ids": [b["book_id"] for b in books],
        })
    result.sort(key=lambda s: (
        s["last_read"] is not None,
        s["last_read"].toordinal() if s["last_read"] else 0,
        s["series"].lower()))
    return result


def started_csv_rows(started, date_format):
    """Rows for a CSV export of :func:`started_series`.

    Columns: series, read, total, next volume number and title, number
    and title of the first volume after the highest read one (empty
    without a gap), last read (empty if unknown).
    """
    rows = []
    for s in started:
        after = s["after_book"]
        rows.append([
            s["series"], s["read"], s["total"],
            format_index(s["next_book"]["index"]), s["next_book"]["title"],
            format_index(after["index"]) if after else "",
            after["title"] if after else "",
            s["last_read"].strftime(date_format) if s["last_read"] else "",
        ])
    return rows


def backlog_by_series(series, limit=20):
    """Series that make up the largest part of the TBR.

    :return: dict with ``top`` (the ``limit`` series with the most
        unread books, most first, ties by name; each a dict with
        ``series``, ``unread``, ``read``, ``total`` and ``book_ids`` of
        the unread books), ``series_count`` and ``books`` (all series
        with unread books and their unread books) and ``rest_series``
        and ``rest_books`` (the same for the series not in ``top``).
    """
    entries = []
    for name, books in series.items():
        unread = [b["book_id"] for b in books if not b["read"]]
        if unread:
            entries.append({
                "series": name,
                "unread": len(unread),
                "read": len(books) - len(unread),
                "total": len(books),
                "book_ids": unread,
            })
    entries.sort(key=lambda e: (-e["unread"], e["series"].lower()))
    top, rest = entries[:limit], entries[limit:]
    return {
        "top": top,
        "series_count": len(entries),
        "books": sum(e["unread"] for e in entries),
        "rest_series": len(rest),
        "rest_books": sum(e["unread"] for e in rest),
    }


def _to_date(value, tz=None):
    # Same as export_reading_status.to_date(); the Qt-free modules do not
    # import each other (their import path differs inside calibre).
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(tz)
        return value.date()
    if isinstance(value, date):
        return value
    return None


def _problem(kind, names, book_ids, indices=(), max_read=None):
    return {
        "kind": kind,
        "series": list(names),
        "indices": list(indices),
        "max_read": max_read,
        "book_ids": book_ids,
    }
