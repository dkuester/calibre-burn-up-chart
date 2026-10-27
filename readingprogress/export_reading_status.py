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
import math
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


class NoDataError(RuntimeError):
    """The library has no book with a date added, so there is nothing to
    chart."""


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
        raise NoDataError("No usable events found.")

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


# Average month length in days (Gregorian calendar)
DAYS_PER_MONTH = 365.2425 / 12

# Robust forecast (see forecast_backlog()). Back-tested on a real
# library: a trimmed mean of up to 24 full months predicts the TBR about
# ten times better than a regression; below 3 months no estimator can
# tell a bulk import from a normal month, below 12 the result is shaky.
FORECAST_MIN_MONTHS = 3
FORECAST_FULL_MONTHS = 12
FORECAST_MAX_MONTHS = 24
# Share of the months dropped at each end of the trimmed mean
TRIM_SHARE = 0.2
# Months scanned for the zero dates of the band (100 years)
FORECAST_HORIZON = 1200

# Statuses of robust_rates() and forecast_backlog()
FORECAST_NONE = "none"
FORECAST_PRELIMINARY = "preliminary"
FORECAST_OK = "ok"

# 90 % quantile of Student's t distribution by degrees of freedom: the
# band from the 10 % to the 90 % quantile holds 80 % of the outcomes.
T_QUANTILE_90 = {
    2: 1.886, 3: 1.638, 4: 1.533, 5: 1.476, 6: 1.440, 7: 1.415, 8: 1.397,
    9: 1.383, 10: 1.372, 11: 1.363, 12: 1.356, 13: 1.350, 14: 1.345,
    15: 1.341, 16: 1.337, 17: 1.333, 18: 1.330, 19: 1.328, 20: 1.325,
    21: 1.323, 22: 1.321, 23: 1.319,
}


def full_months(rates, exclude=None):
    """``(added, read)`` of the complete calendar months in ``rates``.

    ``rates`` is the list from :func:`compute_rates`. The first month
    holds the initial stock of the library and the current month is not
    over yet, so neither counts. ``exclude`` maps ``(year, month)`` to a
    number of books taken off that month's additions (e.g. known bulk
    imports).
    """
    exclude = exclude or {}
    months = []
    for i, (day, added, read) in enumerate(r[:3] for r in rates):
        if i == 0 or day < month_end(day.year, day.month):
            continue
        months.append((added - exclude.get((day.year, day.month), 0), read))
    return months


def trimmed_mean(values, share=TRIM_SHARE):
    """Mean without the ``share`` lowest and highest values – at least
    one at each end from three values on, so three or four values give
    the median. 0.0 for no values."""
    n = len(values)
    if n == 0:
        return 0.0
    cut = max(1, int(n * share)) if n >= 3 else 0
    kept = sorted(values)[cut:n - cut]
    return sum(kept) / len(kept)


def _quantile(values, p):
    """``p`` quantile of ``values`` with linear interpolation."""
    ordered = sorted(values)
    pos = (len(ordered) - 1) * p
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (pos - low)


def robust_rates(rates, exclude=None):
    """Typical purchase and reading rate per month.

    Trimmed means (:func:`trimmed_mean`) of the last
    :data:`FORECAST_MAX_MONTHS` full months (:func:`full_months`).

    :return: dict with ``status`` (:data:`FORECAST_NONE` below
        :data:`FORECAST_MIN_MONTHS` full months,
        :data:`FORECAST_PRELIMINARY` below :data:`FORECAST_FULL_MONTHS`,
        else :data:`FORECAST_OK`), ``months`` (full months used),
        ``added`` and ``read`` (books per month, ``None`` without enough
        data) and ``spread`` (robust standard deviation of the monthly
        TBR change: interquartile range / 1.349, but at least
        √(added + read) – book counts vary at least like random events,
        and a few equal months must not give a band of zero width).
    """
    months = full_months(rates, exclude)[-FORECAST_MAX_MONTHS:]
    n = len(months)
    result = {"status": FORECAST_NONE, "months": n, "added": None,
              "read": None, "spread": 0.0}
    if n < FORECAST_MIN_MONTHS:
        return result
    changes = [a - r for a, r in months]
    added = trimmed_mean([a for a, _ in months])
    read = trimmed_mean([r for _, r in months])
    iqr = _quantile(changes, 0.75) - _quantile(changes, 0.25)
    result.update({
        "status": (FORECAST_PRELIMINARY if n < FORECAST_FULL_MONTHS
                   else FORECAST_OK),
        "added": added,
        "read": read,
        "spread": max(iqr / 1.349, math.sqrt(max(0.0, added + read))),
    })
    return result


def forecast_backlog(rows, rates=None, exclude=None):
    """Robust TBR forecast with an 80 % uncertainty band.

    The TBR continues from today's value (the last of ``rows``, from
    :func:`export_snapshots`) by ``slope`` = typical purchase rate −
    typical reading rate per month (:func:`robust_rates`; ``rates``
    defaults to :func:`compute_rates` of ``rows``). After ``t`` months
    the band reaches ``± q · spread · √(t + t²/n)``: monthly noise plus
    the uncertainty of a rate estimated from ``n`` months, with ``q``
    from Student's t distribution – few months give a wide band.

    :return: the :func:`robust_rates` dict plus ``ok`` (a forecast
        exists), ``slope`` (books per month), ``anchor`` (today),
        ``start`` (today's TBR), ``quantile`` (``q``), ``zero_date``
        (the line reaches 0), ``zero_early`` and ``zero_late`` (the
        optimistic and pessimistic band edge reach 0); the dates are
        ``None`` if that never happens within 100 years.
    """
    if rates is None:
        rates = compute_rates(rows)
    fc = robust_rates(rates, exclude)
    fc.update({"ok": fc["status"] != FORECAST_NONE, "slope": 0.0,
               "anchor": rows[-1][0] if rows else None,
               "start": rows[-1][3] if rows else 0, "quantile": 0.0,
               "zero_date": None, "zero_early": None, "zero_late": None})
    if not fc["ok"]:
        return fc
    fc["slope"] = fc["added"] - fc["read"]
    fc["quantile"] = T_QUANTILE_90[fc["months"] - 1]
    if fc["start"] <= 0:
        return fc
    if fc["slope"] < 0:
        fc["zero_date"] = months_after(fc["anchor"],
                                       -fc["start"] / fc["slope"])
    for key, edge in (("zero_early", 0), ("zero_late", 2)):
        for t in range(1, FORECAST_HORIZON + 1):
            if forecast_at(fc, t)[edge] <= 0:
                fc[key] = months_after(fc["anchor"], t)
                break
    return fc


def months_after(day, months):
    """``day`` plus ``months`` average months."""
    return day + timedelta(days=round(months * DAYS_PER_MONTH))


def forecast_at(fc, months):
    """``(low, mid, high)`` TBR of forecast ``fc`` after ``months``
    months (not cut off at 0)."""
    mid = fc["start"] + fc["slope"] * months
    width = fc["quantile"] * fc["spread"] * math.sqrt(
        months + months * months / fc["months"])
    return mid - width, mid, mid + width


def forecast_line_end(fc, target_date):
    """``(date, tbr)`` where the forecast line ends: where it reaches 0,
    at the latest on ``target_date``."""
    if fc["zero_date"] is not None and fc["zero_date"] <= target_date:
        return fc["zero_date"], 0.0
    months = (target_date - fc["anchor"]).days / DAYS_PER_MONTH
    return target_date, max(0.0, forecast_at(fc, months)[1])


def forecast_band(fc, target_date, steps=120):
    """Outline of the band from today to ``target_date`` as
    ``(date, low, high)`` points, cut off at 0; the band ends early
    where its pessimistic edge reaches 0."""
    end = target_date
    if fc["zero_late"] is not None and fc["zero_late"] < end:
        end = fc["zero_late"]
    days = max(0, (end - fc["anchor"]).days)
    points = []
    for i in range(steps + 1):
        day = fc["anchor"] + timedelta(days=round(days * i / steps))
        low, _, high = forecast_at(fc, (day - fc["anchor"]).days
                                   / DAYS_PER_MONTH)
        points.append((day, max(0.0, low), max(0.0, high)))
    return points


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


# Statuses returned by required_pace()
PACE_OK = "ok"
PACE_REACHED = "reached"
PACE_TOO_CLOSE = "too_close"


def required_pace(backlog, rates, today, target_date, target_backlog=0):
    """Monthly pace needed to bring the backlog to ``target_backlog`` by
    ``target_date``.

    ``rates`` is the dict from :func:`robust_rates` – the typical
    purchase and reading rates the forecast uses as well. Either reading
    must rise to ``read_needed`` (buying as before) or buying must drop
    to ``max_added`` (reading as before); ``max_added <= 0`` means even
    buying nothing is not enough at the current reading rate. Without
    enough data for the rates, ``added_rate``, ``read_rate``,
    ``read_needed`` and ``max_added`` are ``None`` and only
    ``reduction`` is known.

    :return: dict with ``status`` (:data:`PACE_OK`, :data:`PACE_REACHED`
        if the backlog is already at or below the goal,
        :data:`PACE_TOO_CLOSE` if less than one month is left),
        ``target_backlog``, ``months`` (left until ``target_date``),
        ``reduction`` (backlog decrease needed per month),
        ``added_rate``, ``read_rate``, ``read_needed`` and ``max_added``
        (books per month).
    """
    added_rate = rates["added"]
    read_rate = rates["read"]
    months = (target_date - today).days / DAYS_PER_MONTH
    pace = {
        "status": PACE_OK,
        "target_backlog": target_backlog,
        "months": months,
        "reduction": 0.0,
        "added_rate": added_rate,
        "read_rate": read_rate,
        "read_needed": read_rate,
        "max_added": added_rate,
    }
    if backlog <= target_backlog:
        pace["status"] = PACE_REACHED
        return pace
    if months < 1:
        pace["status"] = PACE_TOO_CLOSE
        return pace
    reduction = (backlog - target_backlog) / months
    pace["reduction"] = reduction
    if added_rate is not None:
        pace["read_needed"] = added_rate + reduction
        pace["max_added"] = read_rate - reduction
    return pace


# Problem kinds reported by find_date_problems()
MISSING_LAST_READ = "missing_last_read"
READ_BEFORE_ADDED = "read_before_added"


def find_date_problems(db_api, read_column=None, last_read_column=None):
    """Read books whose read date the charts cannot use as is.

    Two kinds, the same ones :func:`export_snapshots` counts (and then
    records at the date added): read books without ``last_read_column``
    and read books whose read date lies before the date added.

    :return: list of dicts with ``book_id``, ``problem``
        (:data:`MISSING_LAST_READ` or :data:`READ_BEFORE_ADDED`),
        ``title``, ``authors`` (tuple), ``added``, ``last_read``
        (``None`` if missing) and ``days_before`` (days between the read
        date and the date added, ``None`` if missing); sorted by date
        added, then title.
    """
    if read_column is None:
        read_column = READ_COLUMN
    if last_read_column is None:
        last_read_column = LAST_READ_COLUMN

    all_ids = db_api.all_book_ids()
    added_map     = db_api.all_field_for("timestamp", all_ids)
    read_map      = db_api.all_field_for(read_column, all_ids)
    last_read_map = db_api.all_field_for(last_read_column, all_ids)
    title_map     = db_api.all_field_for("title", all_ids)
    authors_map   = db_api.all_field_for("authors", all_ids)

    problems = []
    for book_id in all_ids:
        added = to_date(added_map.get(book_id))
        if added is None or read_map.get(book_id) is not True:
            continue
        last_read = to_date(last_read_map.get(book_id))
        if last_read is None:
            problem, days_before = MISSING_LAST_READ, None
        elif last_read < added:
            problem, days_before = READ_BEFORE_ADDED, (added - last_read).days
        else:
            continue
        problems.append({
            "book_id": book_id,
            "problem": problem,
            "title": title_map.get(book_id) or "",
            "authors": tuple(authors_map.get(book_id) or ()),
            "added": added,
            "last_read": last_read,
            "days_before": days_before,
        })
    problems.sort(key=lambda p: (p["added"], p["title"].lower()))
    return problems


def id_search(book_ids, group_size=50):
    """calibre search expression that matches exactly ``book_ids``.

    calibre's query parser recurses once per ``or``, so a flat chain
    hits its recursion limit at a few hundred terms. Longer lists are
    split into parenthesized groups of at most ``group_size`` terms
    (recursively, so the nesting stays shallow).
    """
    book_ids = list(book_ids)
    if len(book_ids) <= group_size:
        return " or ".join("id:{}".format(i) for i in book_ids)
    chunk = -(-len(book_ids) // group_size)   # ceil division
    return " or ".join(
        "({})".format(id_search(book_ids[k:k + chunk], group_size))
        for k in range(0, len(book_ids), chunk))


def problem_csv_rows(problems, date_format, labels):
    """Rows for a CSV export of :func:`find_date_problems`.

    ``labels`` maps each problem kind to its (translated) text.
    """
    rows = []
    for p in problems:
        rows.append([
            p["book_id"],
            labels[p["problem"]],
            p["title"],
            " & ".join(p["authors"]),
            p["added"].strftime(date_format),
            p["last_read"].strftime(date_format) if p["last_read"] else "",
            "" if p["days_before"] is None else p["days_before"],
        ])
    return rows


def backlog_ages(db_api, read_column=None, today=None):
    """Age of every unread book (TBR), as counted by the burn-up chart.

    :return: list of ``(book_id, added, age_days)`` for books that are
        not marked as read and have a date added.
    """
    if read_column is None:
        read_column = READ_COLUMN
    if today is None:
        today = date.today()

    all_ids = db_api.all_book_ids()
    added_map = db_api.all_field_for("timestamp", all_ids)
    read_map  = db_api.all_field_for(read_column, all_ids)

    ages = []
    for book_id in all_ids:
        added = to_date(added_map.get(book_id))
        if added is None or read_map.get(book_id) is True:
            continue
        ages.append((book_id, added, max(0, (today - added).days)))
    return ages


# Books at least this many years old share the last age bucket
MAX_AGE_YEARS = 10


def age_buckets(ages, max_years=MAX_AGE_YEARS):
    """Groups :func:`backlog_ages` into whole years of age.

    Bucket ``n`` holds the books aged ``n`` to ``n + 1`` years; the last
    bucket (``max_years``) also holds everything older. Trailing empty
    buckets are dropped.

    :return: list of book-id lists, one per bucket (at least one).
    """
    buckets = [[] for _ in range(max_years + 1)]
    for book_id, _added, age_days in ages:
        years = min(int(age_days / 365.25), max_years)
        buckets[years].append(book_id)
    while len(buckets) > 1 and not buckets[-1]:
        buckets.pop()
    return buckets


def median_age_years(ages):
    """Median age in years of :func:`backlog_ages`, or ``None``."""
    if not ages:
        return None
    days = sorted(a[2] for a in ages)
    mid = len(days) // 2
    median = days[mid] if len(days) % 2 else (days[mid - 1] + days[mid]) / 2
    return median / 365.25

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
    return {
        "points":      points,
        "statistics":  delay_statistics(points),
        "missing_data": missing_data,
    }


def delay_statistics(points):
    """Count, mean, median, min and max of the days in ``points``
    (``(read_date, days, book_id)`` tuples), or ``None`` if empty."""
    if not points:
        return None
    values = sorted(p[1] for p in points)
    n = len(values)
    if n % 2 == 1:
        median = float(values[n // 2])
    else:
        median = (values[n // 2 - 1] + values[n // 2]) / 2.0
    return {
        "count":  n,
        "mean":   sum(values) / n,
        "median": median,
        "min":    values[0],
        "max":    values[-1],
    }


def collect_report_data(db_api, read_column, last_read_column, target_date,
                        reduction_factor, today=None):
    """All figures of the report (see ``report.build_sections``).

    ``forecast`` is :func:`forecast_backlog`; ``pace`` and ``pace_soft``
    are :func:`required_pace` with its rates for TBR = 0 and for the
    gentle reduction. Also holds ``rows`` (from
    :func:`export_snapshots`), ``rates`` (from :func:`compute_rates`) for
    the charts embedded in the HTML report.
    Raises :class:`NoDataError` for a library without dates added.
    """
    info = export_snapshots(db_api, read_column, last_read_column,
                            today=today)
    rates = compute_rates(info["rows"])
    ages = backlog_ages(db_api, read_column, today=today)
    problems = find_date_problems(db_api, read_column, last_read_column)
    missing = sum(1 for p in problems if p["problem"] == MISSING_LAST_READ)
    last12 = rates[-12:]
    target_tbr = round(info["backlog"] * reduction_factor)
    today = info["rows"][-1][0]
    forecast = forecast_backlog(info["rows"], rates)
    return {
        "total": info["total"],
        "read": info["read"],
        "backlog": info["backlog"],
        "last12": {"added": sum(r[1] for r in last12),
                   "read": sum(r[2] for r in last12)},
        "target_date": target_date,
        "target_tbr": target_tbr,
        "forecast": forecast,
        "pace": required_pace(info["backlog"], forecast, today,
                              target_date),
        "pace_soft": required_pace(info["backlog"], forecast, today,
                                   target_date, target_tbr),
        "delay": compute_reading_time(
            db_api, read_column, last_read_column)["statistics"],
        "age": {
            "median_years": median_age_years(ages),
            "max_years": MAX_AGE_YEARS,
            "counts": [len(ids) for ids in age_buckets(ages)],
        },
        "quality": {"missing": missing,
                    "before_added": len(problems) - missing},
        "rows": info["rows"],
        "rates": rates,
    }


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
