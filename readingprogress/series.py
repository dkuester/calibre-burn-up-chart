"""
Series data of the library and the series checks of the data-quality
dialog.

Groups the books by calibre's ``series`` field and finds three kinds of
problems: the same series under several names, volume numbers used
twice within a series, and gaps (an earlier volume unread although a
later one is read). Uses only the standard library, so it is testable
without calibre; nothing here changes book data.
"""

import re
import unicodedata

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


def collect_series(db_api, read_column):
    """Books per series.

    :return: dict mapping each series name to a list of dicts with
        ``book_id``, ``title``, ``authors`` (tuple), ``index`` (float,
        1.0 when calibre has none) and ``read`` (bool); sorted by index,
        then title. Books without a series are left out.
    """
    all_ids = db_api.all_book_ids()
    series_map  = db_api.all_field_for("series", all_ids)
    index_map   = db_api.all_field_for("series_index", all_ids)
    read_map    = db_api.all_field_for(read_column, all_ids)
    title_map   = db_api.all_field_for("title", all_ids)
    authors_map = db_api.all_field_for("authors", all_ids)

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


def _problem(kind, names, book_ids, indices=(), max_read=None):
    return {
        "kind": kind,
        "series": list(names),
        "indices": list(indices),
        "max_read": max_read,
        "book_ids": book_ids,
    }
