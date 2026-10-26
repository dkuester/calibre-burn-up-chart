#!/usr/bin/env python3
"""
Reads the reading status from a Calibre library.

As a module:  from ... import export_snapshots;  export_snapshots(db_api, ...)
Standalone:   calibre-debug -e export_reading_status.py

export_snapshots() returns the monthly snapshots as a list of
(date, total, read, backlog) tuples. A CSV file is only written when a
log_path is passed explicitly.
"""

import csv
import os
import warnings
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, timedelta

warnings.filterwarnings(
    "ignore", category=SyntaxWarning,
    module=r"calibre_plugins\.kobo_metadata")

# --- Configuration ---
READ_COLUMN      = "#gelesen"
LAST_READ_COLUMN = "#last_read"

# Only for standalone use via calibre-debug -e
STANDALONE_LIBRARY = os.path.expanduser("~/Calibre-Bibliothek")
STANDALONE_LOG     = "/tmp/readingprogress_log.csv"


def to_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def month_end(year, month):
    return date(year, month, monthrange(year, month)[1])


def _write_csv(log_path, rows):
    """Writes the snapshots as CSV (for debugging)."""
    target_dir = os.path.dirname(log_path)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)
    tmp = log_path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "total", "read", "backlog"])
        for r in rows:
            w.writerow([r[0].isoformat(), r[1], r[2], r[3]])
    os.replace(tmp, log_path)


def export_snapshots(db_api, read_column=None, last_read_column=None,
                     log_path=None, today=None):
    """
    Reads the library and returns the monthly snapshots.

    :param db_api:           Calibre ``new_api`` instance
    :param read_column:      Name of the yes/no column (default: '#gelesen')
    :param last_read_column: Name of the date column (default: '#last_read')
    :param log_path:         Optional CSV path (debug only)
    :param today:            Reference date (default: date.today()); only
                             needed for tests and period selection
    :return: dict with 'rows' (list of tuples) and diagnostic counters
    """
    if read_column is None:
        read_column = READ_COLUMN
    if last_read_column is None:
        last_read_column = LAST_READ_COLUMN

    all_ids = db_api.all_book_ids()
    added_map     = db_api.all_field_for("timestamp", all_ids)
    read_map      = db_api.all_field_for(read_column, all_ids)
    last_read_map = db_api.all_field_for(last_read_column, all_ids)

    added_events = defaultdict(int)
    read_events  = defaultdict(int)

    missing_timestamp      = 0
    missing_last_read      = 0
    last_read_before_added = 0

    for book_id in all_ids:
        added     = to_date(added_map.get(book_id))
        is_read   = read_map.get(book_id) is True
        last_read = to_date(last_read_map.get(book_id))

        if added is None:
            missing_timestamp += 1
            continue
        added_events[added] += 1

        if is_read:
            if last_read is None:
                missing_last_read += 1
                read_events[added] += 1
            elif last_read < added:
                last_read_before_added += 1
                read_events[added] += 1
            else:
                read_events[last_read] += 1

    events = []
    for d, n in added_events.items():
        events.append((d, "added", n))
    for d, n in read_events.items():
        events.append((d, "read", n))
    events.sort()

    if not events:
        raise RuntimeError("No usable events found.")

    if today is None:
        today = date.today()

    month_keys = {(d.year, d.month) for (d, _, _) in events}
    month_keys.add((today.year, today.month))
    months = sorted(month_keys)

    idx = 0
    current_added = 0
    current_read  = 0
    rows = []

    for (y, m) in months:
        end = month_end(y, m)
        if end > today:
            end = today
        while idx < len(events) and events[idx][0] <= end:
            _, typ, n = events[idx]
            if typ == "added":
                current_added += n
            else:
                current_read += n
            idx += 1
        rows.append((end, current_added, current_read,
                     current_added - current_read))

    if log_path:
        _write_csv(log_path, rows)

    last = rows[-1]
    return {
        "rows":                   rows,
        "month_count":            len(rows),
        "total":                  last[1],
        "read":                   last[2],
        "backlog":                last[3],
        "missing_timestamp":      missing_timestamp,
        "missing_last_read":      missing_last_read,
        "last_read_before_added": last_read_before_added,
    }


def _no_forecast():
    return {
        "slope": 0.0,
        "intercept": 0.0,
        "anchor": None,
        "zero_date": None,
        "count": 0,
        "ok": False,
    }


def forecast_backlog(rows, months=12):
    """Linear regression of the backlog over the last ``months`` months.

    Fits ``backlog = slope * days + intercept`` with ``days`` measured
    relative to the last snapshot date. ``rows`` is the ``'rows'`` list
    from :func:`export_snapshots` – ``(date, total, read, backlog)``.

    :return: dict with ``slope`` (backlog change per day, negative =
        shrinking), ``intercept`` (fitted backlog at the last date),
        ``anchor`` (the last date), ``zero_date`` (date the trend reaches
        0, or ``None``), ``count`` (points in the window) and ``ok``
        (``False`` if fewer than two points are available).
    """
    if len(rows) < 2:
        return _no_forecast()

    anchor = rows[-1][0]
    cutoff = anchor - timedelta(days=months * 30)
    window = [r for r in rows if r[0] >= cutoff]
    if len(window) < 2:
        return _no_forecast()

    xs = [(r[0] - anchor).days for r in window]
    ys = [r[3] for r in window]
    n = len(xs)
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n

    sxx = sum((x - x_mean) ** 2 for x in xs)
    if sxx == 0:
        slope = 0.0
    else:
        sxy = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
        slope = sxy / sxx
    intercept = y_mean - slope * x_mean

    zero_date = None
    if slope < 0:
        days_to_zero = -intercept / slope
        if days_to_zero > 0:
            zero_date = anchor + timedelta(days=round(days_to_zero))

    return {
        "slope": slope,
        "intercept": intercept,
        "anchor": anchor,
        "zero_date": zero_date,
        "count": n,
        "ok": True,
    }



def _trailing_mean(values, window):
    """Mean of the last ``window`` values up to each position (fewer at
    the start, where not enough values exist yet)."""
    means = []
    for i in range(len(values)):
        part = values[max(0, i - window + 1):i + 1]
        means.append(sum(part) / len(part))
    return means


def compute_rates(rows, window=12):
    """Books added and books read per calendar month.

    ``rows`` is the ``'rows'`` list from :func:`export_snapshots` –
    cumulative ``(date, total, read, backlog)`` snapshots, which skip
    months without any event. Every month from the first to the last
    snapshot gets an entry; skipped months count 0.

    :return: list of ``(date, added, read, added_avg, read_avg)`` – the
        snapshot date (month end for skipped months), the month's counts
        and their trailing means over ``window`` months.
    """
    if not rows:
        return []
    by_month = {(r[0].year, r[0].month): r for r in rows}
    year, month = rows[0][0].year, rows[0][0].month
    last = (rows[-1][0].year, rows[-1][0].month)

    dates, added, read = [], [], []
    prev_total = prev_read = 0
    while (year, month) <= last:
        row = by_month.get((year, month))
        if row is None:
            dates.append(month_end(year, month))
            added.append(0)
            read.append(0)
        else:
            dates.append(row[0])
            added.append(row[1] - prev_total)
            read.append(row[2] - prev_read)
            prev_total, prev_read = row[1], row[2]
        month += 1
        if month > 12:
            year, month = year + 1, 1

    return list(zip(dates, added, read,
                    _trailing_mean(added, window),
                    _trailing_mean(read, window)))

if __name__ == "__main__":  # pragma: no cover  (standalone CLI, not unit-tested)
    from calibre.library import db as calibre_db_factory

    api = calibre_db_factory(STANDALONE_LIBRARY).new_api
    info = export_snapshots(api, log_path=STANDALONE_LOG)

    print(f"{info['month_count']} monthly snapshots written to "
          f"{STANDALONE_LOG}")
    print(f"Currently: {info['read']}/{info['total']} read "
          f"| backlog: {info['backlog']}")
    if info["missing_timestamp"]:
        print(f"Note: {info['missing_timestamp']} books without timestamp "
              f"skipped.")
    if info["missing_last_read"]:
        print(f"Note: {info['missing_last_read']} read books without "
              f"#last_read recorded at timestamp.")
    if info["last_read_before_added"]:
        print(f"Note: {info['last_read_before_added']} books with "
              f"last_read < timestamp recorded at timestamp.")


def compute_reading_time(db_api, read_column=None, last_read_column=None):
    """
    Computes, for each read book, the span between adding it (timestamp)
    and reading it (#last_read).

    :return: dict with
        - points: list of (read_date, days_to_read, book_id)
        - statistics: dict(count, mean, median, min, max) or None
        - missing_data: number of read books without usable data
    """
    if read_column is None:
        read_column = READ_COLUMN
    if last_read_column is None:
        last_read_column = LAST_READ_COLUMN

    all_ids = db_api.all_book_ids()
    added_map     = db_api.all_field_for("timestamp", all_ids)
    read_map      = db_api.all_field_for(read_column, all_ids)
    last_read_map = db_api.all_field_for(last_read_column, all_ids)

    points = []
    missing_data = 0

    for book_id in all_ids:
        if read_map.get(book_id) is not True:
            continue
        added     = to_date(added_map.get(book_id))
        last_read = to_date(last_read_map.get(book_id))
        if added is None or last_read is None:
            missing_data += 1
            continue
        if last_read < added:
            # Inconsistency — skip
            missing_data += 1
            continue
        days = (last_read - added).days
        points.append((last_read, days, book_id))

    points.sort()

    if not points:
        return {"points": [], "statistics": None, "missing_data": missing_data}

    values = sorted(p[1] for p in points)
    n = len(values)
    if n % 2 == 1:
        median = float(values[n // 2])
    else:
        median = (values[n // 2 - 1] + values[n // 2]) / 2.0

    statistics = {
        "count":  n,
        "mean":   sum(values) / n,
        "median": median,
        "min":    values[0],
        "max":    values[-1],
    }
    return {
        "points":      points,
        "statistics":  statistics,
        "missing_data": missing_data,
    }
