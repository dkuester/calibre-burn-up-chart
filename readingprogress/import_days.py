"""
Days on which many books were added at once from many sources: probably
a bulk import (moving or rebuilding the library), not a purchase.

On such a day the date added is the import date, not the date the book
was bought, which skews the burn-up chart, the buying rate, the backlog
age and the "read before added" cases. Buying many books at once is
normal, though: a bundle brings 10 to 30 books, but by one author or of
one series. So a day counts only if it has many books *and* many
groups, where a group is the book's series or, without one, its first
author. Uses only the standard library, so it is testable without
calibre; nothing here changes book data.
"""

from datetime import date, datetime

# A day is a bulk import with at least this many books ...
MIN_BOOKS = 20
# ... from at least this many groups (series, or first author without
# one). Bundles have 1 to 7.
MIN_GROUPS = 15


def _to_date(value, tz=None):
    # same as export_reading_status.to_date (kept here so this module
    # stays free of plugin imports)
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(tz)
        return value.date()
    if isinstance(value, date):
        return value
    return None


def _group(book_id, series, authors):
    if series:
        return series
    if authors:
        return authors[0]
    return book_id  # neither: a group of its own


def find_import_days(db_api, read_column, last_read_column,
                     min_books=MIN_BOOKS, min_groups=MIN_GROUPS):
    """Days whose added books look like a bulk import.

    :return: list of dicts, sorted by date, with ``added`` (date),
        ``book_ids`` (list), ``books``, ``authors`` (distinct authors),
        ``groups`` (distinct series, or first author without one),
        ``largest_group`` (name of the biggest group) and
        ``largest_count`` (its size), ``read``, ``read_before_added``,
        ``missing_last_read`` (read books without a read date) and
        ``without_file`` (books without any format).
    """
    all_ids = db_api.all_book_ids()
    added_map     = db_api.all_field_for("timestamp", all_ids)
    authors_map   = db_api.all_field_for("authors", all_ids)
    series_map    = db_api.all_field_for("series", all_ids)
    formats_map   = db_api.all_field_for("formats", all_ids)
    read_map      = db_api.all_field_for(read_column, all_ids)
    last_read_map = db_api.all_field_for(last_read_column, all_ids)

    by_day = {}
    for book_id in all_ids:
        added = _to_date(added_map.get(book_id))
        if added is not None:
            by_day.setdefault(added, []).append(book_id)

    days = []
    for added in sorted(by_day):
        book_ids = by_day[added]
        if len(book_ids) < min_books:
            continue
        groups = {}
        authors = set()
        for book_id in book_ids:
            book_authors = tuple(authors_map.get(book_id) or ())
            authors.update(book_authors)
            key = _group(book_id, series_map.get(book_id), book_authors)
            groups[key] = groups.get(key, 0) + 1
        if len(groups) < min_groups:
            continue
        largest = max(groups, key=lambda k: (groups[k], str(k)))
        read = before = missing = 0
        for book_id in book_ids:
            if read_map.get(book_id) is not True:
                continue
            read += 1
            last_read = _to_date(last_read_map.get(book_id))
            if last_read is None:
                missing += 1
            elif last_read < added:
                before += 1
        days.append({
            "added": added,
            "book_ids": book_ids,
            "books": len(book_ids),
            "authors": len(authors),
            "groups": len(groups),
            "largest_group": str(largest),
            "largest_count": groups[largest],
            "read": read,
            "read_before_added": before,
            "missing_last_read": missing,
            "without_file": sum(1 for book_id in book_ids
                                if not formats_map.get(book_id)),
        })
    return days


def problems_on_import_days(problems, days):
    """How many of ``find_date_problems()``'s cases were added on one of
    ``days`` (their date added is then probably the import date)."""
    dates = {d["added"] for d in days}
    return sum(1 for p in problems if p["added"] in dates)


def import_day_csv_rows(days, date_format):
    """Rows for a CSV export of :func:`find_import_days`."""
    return [[d["added"].strftime(date_format), d["books"], d["authors"],
             d["groups"], f'{d["largest_group"]} ({d["largest_count"]})',
             d["read"], d["read_before_added"], d["missing_last_read"],
             d["without_file"], " ".join(str(i) for i in d["book_ids"])]
            for d in days]
