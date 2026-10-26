"""
Read-only access to the data of the "Reading Goal" plugin.

The separately installed calibre plugin "Reading Goal" (Thiago Oliveira)
keeps one yearly list of books per library in
``<config_dir>/plugins/Reading_Goal_Data_<library_id>.json``. Its goal is
that list: ``goal_books_count`` is the number of books on it, a book
counts as read at status 100, and ``date`` is the read date. This module
reads the file (never writes it), checks it field by field and compares
it with the library's own read data.

Qt-/Calibre-free and independent of the other plugin modules, so it is
unit-testable outside calibre. Tests import it flat (see
``tests/conftest.py``).
"""

import json
import os
from datetime import date, datetime

GOAL_FILE = 'Reading_Goal_Data_{}.json'

# Status (percent) of a finished book
READ_STATUS = 100

# Challenge that every book belongs to; it is the goal itself
ANNUAL_CHALLENGE = 'Annual'


def goal_data_path(config_dir, library_id):
    """Path of the Reading Goal data file of the library ``library_id``."""
    return os.path.join(config_dir, 'plugins', GOAL_FILE.format(library_id))


def load_goal_data(path, tz=None):
    """Parsed goal years from ``path`` (see :func:`parse_goal_data`), or
    ``None`` if the file is missing, unreadable or has no usable year."""
    try:
        with open(path, encoding='utf-8') as f:
            raw = json.load(f)
    except (OSError, ValueError):
        return None
    return parse_goal_data(raw, tz)


def parse_datetime(value, tz=None):
    """Local date of a calibre-JSON datetime
    (``{"__class__": "datetime.datetime", "__value__": "<ISO>"}``), or
    ``None``. ``tz`` defaults to the local time zone, as Reading Goal
    uses it for its months."""
    if not isinstance(value, dict):
        return None
    text = value.get('__value__')
    if not isinstance(text, str):
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(tz)
    return parsed.date()


def _int(value):
    """``value`` as int if it is a number (not a bool), else 0."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return int(value)


def _parse_challenges(summary, tz):
    """Challenges other than the annual goal, sorted by name, as dicts
    with ``name``, ``count``, ``progress`` (percent) and ``start``/``end``
    (dates or ``None``)."""
    challenges = summary.get('challenges_dict') if isinstance(
        summary, dict) else None
    if not isinstance(challenges, dict):
        return []
    result = []
    for name, info in challenges.items():
        if name == ANNUAL_CHALLENGE or not isinstance(info, dict):
            continue
        result.append({
            'name': str(name).strip(),
            'count': _int(info.get('count')),
            'progress': _int(info.get('progress')),
            'start': parse_datetime(info.get('start'), tz),
            'end': parse_datetime(info.get('end'), tz),
        })
    result.sort(key=lambda c: c['name'].lower())
    return result


def _parse_year(year, entries, tz):
    """One year of the data file (see :func:`parse_goal_data`)."""
    books = 0
    read = []
    undated = 0
    page_count = read_pages = last_year_pages = 0
    for key, entry in entries.items():
        if key == 'summary' or not isinstance(entry, dict):
            continue
        try:
            book_id = int(key)
        except ValueError:
            continue
        books += 1
        page_count += _int(entry.get('page_count'))
        read_pages += _int(entry.get('read_pages'))
        last_year_pages += _int(entry.get('last_year_pages'))
        if _int(entry.get('status')) != READ_STATUS:
            continue
        day = parse_datetime(entry.get('date'), tz)
        if day is None:
            undated += 1
            continue
        authors = entry.get('authors')
        read.append({
            'date': day,
            'book_id': book_id,
            'title': str(entry.get('title') or ''),
            'authors': ' & '.join(str(a) for a in authors)
            if isinstance(authors, list) else '',
        })
    read.sort(key=lambda b: (b['date'], b['book_id']))
    return {
        'year': year,
        'goal': books,
        'read': read,
        'undated': undated,
        'goal_pages': max(0, page_count - last_year_pages),
        'read_pages': max(0, read_pages - last_year_pages),
        'challenges': _parse_challenges(entries.get('summary'), tz),
    }


def parse_goal_data(raw, tz=None):
    """Goal years from the decoded JSON of a Reading Goal data file.

    :return: ``{year: dict}`` for every year with at least one book on
        its list, or ``None`` if there is none (or ``raw`` has an unknown
        format). Each year has ``year``, ``goal`` (books on the list),
        ``read`` (finished books with ``date``, ``book_id``, ``title`` and
        ``authors``, sorted by date), ``undated`` (finished books without
        a usable date), ``goal_pages``/``read_pages`` (minus the pages
        read the year before) and ``challenges``.
    """
    if not isinstance(raw, dict):
        return None
    years = {}
    for key, entries in raw.items():
        if not (isinstance(key, str) and len(key) == 4 and key.isdigit()):
            continue
        if not isinstance(entries, dict):
            continue
        year = _parse_year(int(key), entries, tz)
        if year['goal']:
            years[year['year']] = year
    return years or None


def default_year(years, today):
    """The year to show first: the current one if it has a list, else the
    latest year up to today, else the earliest planned one."""
    if today.year in years:
        return today.year
    past = [y for y in years if y < today.year]
    return max(past) if past else min(years)


def _local_date(value, tz=None):
    """Local date of a calibre field value (datetime or date)."""
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(tz)
        return value.date()
    if isinstance(value, date):
        return value
    return None


def library_events(db_api, read_column, last_read_column, tz=None):
    """The library's own dates for the comparison with Reading Goal.

    :return: dict with ``added`` (``{book_id: date added}``) and ``read``
        (``{book_id: read date}`` of the books marked as read). Read books
        without a read date are left out: unlike the burn-up chart, which
        has to place every read book somewhere, yearly counts must not
        invent a date.
    """
    ids = db_api.all_book_ids()
    added_map = db_api.all_field_for('timestamp', ids)
    read_map = db_api.all_field_for(read_column, ids)
    last_read_map = db_api.all_field_for(last_read_column, ids)
    added, read = {}, {}
    for book_id in ids:
        day_added = _local_date(added_map.get(book_id), tz)
        if day_added is not None:
            added[book_id] = day_added
        if read_map.get(book_id) is not True:
            continue
        day_read = _local_date(last_read_map.get(book_id), tz)
        if day_read is not None:
            read[book_id] = day_read
    return {'added': added, 'read': read}


def _days_in_year(year):
    return (date(year + 1, 1, 1) - date(year, 1, 1)).days


def _median(values):
    values = sorted(values)
    if not values:
        return None
    n = len(values)
    if n % 2:
        return float(values[n // 2])
    return (values[n // 2 - 1] + values[n // 2]) / 2.0


def year_summary(goal_year, events, today):
    """Progress of one goal year against its target, plus the library's
    own figures for that year.

    The target grows evenly from 0 on 1 January to ``goal`` on
    31 December. ``events`` is from :func:`library_events`.

    :return: dict with
        - ``year``, ``goal``, ``read`` (finished list books, dated or
          not), ``read_books`` (the dated ones from the year data)
        - ``state``: ``'running'``, ``'finished'`` (year over) or
          ``'planned'`` (year not started)
        - ``expected``: target for today (``goal`` once the year is over)
        - ``ahead``: ``read - expected`` (negative = behind)
        - ``needed_per_month``: books per month for the rest of the year,
          ``None`` once it is over
        - ``projection``: books by 31 December at the pace so far, only
          while the year runs
        - ``goal_pages``, ``read_pages``, ``pages_per_day`` (rest of the
          year, ``None`` once it is over)
        - ``months``: 12 dicts with ``list`` (list books read),
          ``read`` (all books read with a read date, own data) and
          ``added`` (own data)
        - ``month_count``: months that have begun (12 for a past year)
        - ``own_read``: all books read in the year (own data);
          ``own_on_list``: how many of them Reading Goal has as read
        - ``from_tbr``: read list books added before the year began
        - ``delay_median``: median days from adding to reading the read
          list books, or ``None``
        - ``date_mismatches``: read list books that the library does not
          have as read on the same day
        - ``challenges``: as in the year data
    """
    year = goal_year['year']
    start = date(year, 1, 1)
    days_total = _days_in_year(year)
    elapsed = min(max((today - start).days + 1, 0), days_total)
    remaining_days = days_total - elapsed
    if elapsed == days_total:
        state = 'finished'
    elif elapsed == 0:
        state = 'planned'
    else:
        state = 'running'

    goal = goal_year['goal']
    books = goal_year['read']
    read = len(books) + goal_year['undated']
    expected = goal * elapsed / days_total
    remaining = max(0, goal - read)
    if remaining_days:
        needed = remaining / (remaining_days * 12.0 / days_total)
        remaining_pages = max(0, goal_year['goal_pages']
                              - goal_year['read_pages'])
        pages_per_day = remaining_pages / float(remaining_days)
    else:
        needed = pages_per_day = None
    projection = (read * days_total / float(elapsed)
                  if state == 'running' else None)

    months = [{'list': 0, 'read': 0, 'added': 0} for _ in range(12)]
    for book in books:
        if book['date'].year == year:
            months[book['date'].month - 1]['list'] += 1
    own_ids = set()
    for book_id, day in events['read'].items():
        if day.year == year:
            months[day.month - 1]['read'] += 1
            own_ids.add(book_id)
    for day in events['added'].values():
        if day.year == year:
            months[day.month - 1]['added'] += 1

    list_ids = {b['book_id'] for b in books}
    added = events['added']
    delays = [(b['date'] - added[b['book_id']]).days for b in books
              if b['book_id'] in added
              and b['date'] >= added[b['book_id']]]
    mismatches = sum(1 for b in books
                     if events['read'].get(b['book_id']) != b['date'])

    return {
        'year': year,
        'goal': goal,
        'read': read,
        'read_books': books,
        'state': state,
        'expected': expected,
        'ahead': read - expected,
        'needed_per_month': needed,
        'projection': projection,
        'goal_pages': goal_year['goal_pages'],
        'read_pages': goal_year['read_pages'],
        'pages_per_day': pages_per_day,
        'months': months,
        'month_count': (12 if state == 'finished' else
                        0 if state == 'planned' else today.month),
        'own_read': len(own_ids),
        'own_on_list': len(own_ids & list_ids),
        'from_tbr': sum(1 for b in books if b['book_id'] in added
                        and added[b['book_id']] < start),
        'delay_median': _median(delays),
        'date_mismatches': mismatches,
        'challenges': goal_year['challenges'],
    }


def year_overview(years, events):
    """One row per goal year, newest first: dicts with ``year``,
    ``goal``, ``read`` (Reading Goal) and ``own_read`` (all books read
    that year, own data)."""
    own = {}
    for day in events['read'].values():
        own[day.year] = own.get(day.year, 0) + 1
    return [{'year': y,
             'goal': years[y]['goal'],
             'read': len(years[y]['read']) + years[y]['undated'],
             'own_read': own.get(y, 0)}
            for y in sorted(years, reverse=True)]


def cumulative_dates(days, year):
    """Step points ``(date, count)`` of the books read on ``days`` within
    ``year``: one point per day with the running total."""
    points = []
    count = 0
    for day in sorted(d for d in days if d.year == year):
        count += 1
        if points and points[-1][0] == day:
            points[-1] = (day, count)
        else:
            points.append((day, count))
    return points


def report_data(years, events, today):
    """Figures for the report section: ``summary`` (see
    :func:`year_summary`, for :func:`default_year`) and ``years`` (see
    :func:`year_overview`)."""
    year = default_year(years, today)
    return {
        'summary': year_summary(years[year], events, today),
        'years': year_overview(years, events),
    }
