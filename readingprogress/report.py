"""
Key-figures report as Markdown or HTML.

Qt-/Calibre-free: the caller collects the figures (see ``build_report``)
and passes the translation function, so the module stays unit-testable.
Tests import it flat (see ``tests/conftest.py``).
"""

import html
from datetime import date

MARKDOWN = 'md'
HTML = 'html'


def _number(value, decimals, decimal_sep):
    return '{:.{}f}'.format(value, decimals).replace('.', decimal_sep)


def _percent(part, whole, decimal_sep):
    if not whole:
        return '–'
    return _number(100 * part / whole, 0, decimal_sep) + ' %'


def pace_number(value, decimal_sep='.'):
    """Books per month with one decimal; tiny positive values as '< 0.1'
    instead of a misleading '0.0'."""
    if 0 < value < 0.05:
        return '< ' + _number(0.1, 1, decimal_sep)
    return _number(value, 1, decimal_sep)


def pace_text(pace, tr, decimal_sep='.'):
    """What to do to reach the goal of ``pace``, a dict from
    ``export_reading_status.required_pace()`` – e.g. 'read 4.6 books/month
    or buy at most 2.1 books/month'. ``tr`` translates the templates."""
    if pace['status'] == 'reached':
        return tr("already reached")
    if pace['status'] == 'too_close':
        return tr("target date too close – choose a later date in the "
                  "settings")
    read = pace_number(pace['read_needed'], decimal_sep)
    if pace['max_added'] > 0:
        return tr("read {read} books/month or buy at most {added} "
                  "books/month").format(
            read=read, added=pace_number(pace['max_added'], decimal_sep))
    return tr("read {read} books/month or buy nothing and still read "
              "{reduction} books/month").format(
        read=read, reduction=pace_number(pace['reduction'], decimal_sep))


def pace_line(pace, tr, date_str, decimal_sep='.'):
    """Full sentence for the burn-up chart: 'For TBR = 0 by <date>: …'."""
    return tr("For TBR = {tbr} by {date}: {pace}.").format(
        tbr=pace['target_backlog'], date=date_str,
        pace=pace_text(pace, tr, decimal_sep))


def _capitalize(text):
    return text[:1].upper() + text[1:]


def pace_rows(data, tr, decimal_sep='.'):
    """Report rows for ``data['pace']`` and, unless it has the same goal,
    ``data['pace_soft']``."""
    paces = [data['pace']]
    if data['pace_soft']['target_backlog'] != data['pace']['target_backlog']:
        paces.append(data['pace_soft'])
    return [(tr("Required pace (TBR = {tbr})").format(
                tbr=pace['target_backlog']),
             _capitalize(pace_text(pace, tr, decimal_sep)))
            for pace in paces]


def bucket_label(tr, index, bucket_count, max_years):
    """Label of age bucket ``index`` (see ``age_buckets()``): '< 1 year',
    '2–3 years' or, for a capped last bucket, '10+ years'."""
    if index == 0:
        return tr("< 1 year")
    if index == max_years and index == bucket_count - 1:
        return tr("{years}+ years").format(years=index)
    return tr("{start}–{end} years").format(start=index, end=index + 1)


# Month abbreviations, translated where they are shown
MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

# |ahead| below this counts as on target (books)
ON_TARGET = 0.05


def month_name(tr, month):
    """Translated abbreviation of ``month`` (1–12)."""
    return tr(MONTH_NAMES[month - 1])


def goal_title(summary, tr, decimal_sep='.'):
    """'Reading goal 2026: 22 of 30 books (73 %)' for a
    ``reading_goal.year_summary()``."""
    return tr("Reading goal {year}: {read} of {goal} books "
              "({percent})").format(
        year=summary['year'], read=summary['read'], goal=summary['goal'],
        percent=_percent(summary['read'], summary['goal'], decimal_sep))


def goal_status_text(summary, tr, decimal_sep='.'):
    """Where the goal stands: ahead of or behind the target for today,
    or how a finished year ended."""
    if summary['state'] == 'planned':
        return tr("the year has not started yet")
    if summary['state'] == 'finished':
        missing = summary['goal'] - summary['read']
        if missing <= 0:
            return tr("goal reached")
        return tr("{books} books short of the goal").format(books=missing)
    ahead = summary['ahead']
    if ahead >= ON_TARGET:
        return tr("{books} books ahead of the target").format(
            books=_number(ahead, 1, decimal_sep))
    if ahead <= -ON_TARGET:
        return tr("{books} books behind the target").format(
            books=_number(-ahead, 1, decimal_sep))
    return tr("on target")


def goal_pace_text(summary, tr, date_format, decimal_sep='.'):
    """Books per month still needed by 31 December, or ``None`` once the
    year is over."""
    needed = summary['needed_per_month']
    if needed is None:
        return None
    if needed == 0:
        return tr("goal already reached")
    return tr("{books} books/month until {date}").format(
        books=pace_number(needed, decimal_sep),
        date=date(summary['year'], 12, 31).strftime(date_format))


def goal_pages_text(summary, tr, decimal_sep='.'):
    """'7574 of 12140 pages (62 %)', plus the pages per day still
    needed while the year runs."""
    text = tr("{read} of {goal} pages ({percent})").format(
        read=summary['read_pages'], goal=summary['goal_pages'],
        percent=_percent(summary['read_pages'], summary['goal_pages'],
                         decimal_sep))
    if summary['pages_per_day']:
        text += ', ' + tr("{pages} pages/day needed").format(
            pages=_number(summary['pages_per_day'], 0, decimal_sep))
    return text


def goal_own_text(summary, tr):
    """'58 books, 22 of them from the list' (own data)."""
    return tr("{books} books, {on_list} of them from the list").format(
        books=summary['own_read'], on_list=summary['own_on_list'])


def goal_header_lines(summary, tr, date_format, decimal_sep='.'):
    """Key-figure lines below the title of the yearly-goal chart."""
    status = goal_status_text(summary, tr, decimal_sep)
    if summary['state'] == 'running':
        first = tr("Target today: {expected} · {status}").format(
            expected=_number(summary['expected'], 1, decimal_sep),
            status=status)
    else:
        first = _capitalize(status)
    pace = goal_pace_text(summary, tr, date_format, decimal_sep)
    if pace is not None:
        first += ' · ' + tr("Required: {pace}").format(pace=pace)
    return [
        first,
        tr("Pages: {pages}").format(
            pages=goal_pages_text(summary, tr, decimal_sep)),
        tr("Read in {year} in total (own data): {own}").format(
            year=summary['year'], own=goal_own_text(summary, tr)),
    ]


def _period(challenge, date_format):
    if challenge['start'] is None or challenge['end'] is None:
        return '–'
    return '{} – {}'.format(challenge['start'].strftime(date_format),
                            challenge['end'].strftime(date_format))


def goal_sections(goal, tr, date_format, decimal_sep='.'):
    """Report sections for ``goal``, the dict from
    ``reading_goal.report_data()``."""
    s = goal['summary']
    year = s['year']
    rows = [
        (tr("Books on the list"), str(s['goal'])),
        (tr("Read"), '{} ({})'.format(
            s['read'], _percent(s['read'], s['goal'], decimal_sep))),
    ]
    if s['state'] == 'running':
        rows.append((tr("Target today"),
                     _number(s['expected'], 1, decimal_sep)))
    rows.append((tr("Status"),
                 _capitalize(goal_status_text(s, tr, decimal_sep))))
    pace = goal_pace_text(s, tr, date_format, decimal_sep)
    if pace is not None:
        rows.append((tr("Required pace"), _capitalize(pace)))
    if s['projection'] is not None:
        rows.append((tr("Projection for {date}").format(
                        date=date(year, 12, 31).strftime(date_format)),
                     tr("{books} books").format(
                         books=_number(s['projection'], 0, decimal_sep))))
    rows.append((tr("Pages"), goal_pages_text(s, tr, decimal_sep)))
    rows.append((tr("Read in {year} in total (own data)").format(year=year),
                 goal_own_text(s, tr)))
    rows.append((tr("Read list books from the TBR"),
                 tr("{books} of {read} (added before {year})").format(
                     books=s['from_tbr'], read=len(s['read_books']),
                     year=year)))
    if s['delay_median'] is not None:
        rows.append((tr("Time between purchase and reading (median)"),
                     tr("{days} days").format(
                         days=int(round(s['delay_median'])))))
    note = tr("Reading Goal counts only the books on its yearly list; "
              "the figures marked as own data come from your library.")
    if s['date_mismatches']:
        note += ' ' + tr("{books} read list books have a different read "
                         "date in your library or are not marked as "
                         "read there.").format(books=s['date_mismatches'])
    sections = [{
        'heading': tr("Reading goal {year} (Reading Goal plugin)").format(
            year=year),
        'rows': rows,
        'note': note,
    }]

    if s['month_count']:
        sections.append({
            'heading': tr("Reading goal {year} by month").format(year=year),
            'table': (
                [tr("Month"), tr("From the list"), tr("Read in total"),
                 tr("Added"), tr("Change of the TBR")],
                [[month_name(tr, i + 1), str(m['list']), str(m['read']),
                  str(m['added']), '{:+d}'.format(m['added'] - m['read'])]
                 for i, m in enumerate(s['months'][:s['month_count']])],
            ),
            'note': tr("Read in total and added: own data. Read books "
                       "without a read date are not counted."),
        })

    if s['challenges']:
        sections.append({
            'heading': tr("Other challenges {year}").format(year=year),
            'table': (
                [tr("Challenge"), tr("Books"), tr("Progress"),
                 tr("Period")],
                [[c['name'], str(c['count']), '{} %'.format(c['progress']),
                  _period(c, date_format)] for c in s['challenges']],
            ),
        })

    sections.append({
        'heading': tr("Reading goals by year"),
        'table': (
            [tr("Year"), tr("Books on the list"), tr("Read"), tr("Share"),
             tr("Read in total (own data)")],
            [[str(r['year']), str(r['goal']), str(r['read']),
              _percent(r['read'], r['goal'], decimal_sep),
              str(r['own_read'])] for r in goal['years']],
        ),
    })
    return sections


def build_sections(data, tr, date_format, decimal_sep='.'):
    """Report content as a list of sections.

    Each section is a dict with ``heading`` and either ``rows`` (label,
    value pairs) or ``table`` (header list, row lists), plus an optional
    ``note``. ``data`` holds the figures:

    - ``total``, ``read``, ``backlog``: current library counts
    - ``last12``: dict with ``added`` and ``read`` of the last 12 months
    - ``target_date``, ``target_tbr``: goal from the settings
    - ``forecast``: dict from ``forecast_backlog()``
    - ``pace``, ``pace_soft``: dicts from ``required_pace()`` for TBR = 0
      and for the gentle reduction
    - ``delay``: dict from ``delay_statistics()`` or ``None``
    - ``age``: dict with ``median_years`` (or ``None``), ``max_years``
      and ``counts``, the number of books per ``age_buckets()`` bucket
    - ``quality``: dict with ``missing`` and ``before_added`` (read
      dates) and ``series_names``, ``series_duplicates`` and
      ``series_gaps`` (optional, from ``series.problem_counts()``); only
      non-zero counts are listed
    - ``goal`` (optional): dict from ``reading_goal.report_data()``, or
      ``None`` without Reading Goal data (see :func:`goal_sections`)
    """
    sections = []

    sections.append({
        'heading': tr("Library"),
        'rows': [
            (tr("Books in total"), str(data['total'])),
            (tr("Read"), '{} ({})'.format(
                data['read'],
                _percent(data['read'], data['total'], decimal_sep))),
            (tr("Unread (TBR)"), str(data['backlog'])),
        ],
    })

    added, read = data['last12']['added'], data['last12']['read']
    sections.append({
        'heading': tr("Last 12 months"),
        'rows': [
            (tr("Books added"), str(added)),
            (tr("Read"), str(read)),
            (tr("Change of the TBR"), '{:+d}'.format(added - read)),
        ],
    })

    fc = data['forecast']
    if not fc.get('ok'):
        forecast = tr("Not enough data for a forecast.")
    elif fc.get('zero_date') is not None:
        forecast = tr("TBR = 0 on {date}").format(
            date=fc['zero_date'].strftime(date_format))
    else:
        forecast = tr("The TBR is not shrinking at the current rate.")
    sections.append({
        'heading': tr("Goal and forecast"),
        'rows': [
            (tr("Goal"), tr("TBR = 0 on {date}").format(
                date=data['target_date'].strftime(date_format))),
            (tr("Gentle reduction"), tr("TBR = {tbr} on {date}").format(
                tbr=data['target_tbr'],
                date=data['target_date'].strftime(date_format))),
            (tr("Forecast (last 12 months)"), forecast),
        ] + pace_rows(data, tr, decimal_sep),
        'note': tr("Required pace at the current purchase rate ({added}) "
                   "and reading rate ({read}) per month, mean of the last "
                   "12 months.").format(
            added=pace_number(data['pace']['added_rate'], decimal_sep),
            read=pace_number(data['pace']['read_rate'], decimal_sep)),
    })

    if data.get('goal'):
        sections += goal_sections(data['goal'], tr, date_format,
                                  decimal_sep)

    delay = data['delay']
    if delay is not None:
        sections.append({
            'heading': tr("Time between purchase and reading"),
            'rows': [
                (tr("Median"), tr("{days} days").format(
                    days=int(round(delay['median'])))),
                (tr("Mean"), tr("{days} days").format(
                    days=int(round(delay['mean'])))),
                (tr("Range"), tr("{min}–{max} days").format(
                    min=delay['min'], max=delay['max'])),
                (tr("Books"), str(delay['count'])),
            ],
        })

    age = data['age']
    if age['median_years'] is not None:
        counts = age['counts']
        buckets = [(bucket_label(tr, i, len(counts), age['max_years']), n)
                   for i, n in enumerate(counts)]
        total = sum(counts)
        sections.append({
            'heading': tr("Age of the TBR"),
            'table': (
                [tr("Time in the TBR"), tr("Books"), tr("Share")],
                [[label, str(count), _percent(count, total, decimal_sep)]
                 for label, count in buckets],
            ),
            'note': tr("Median age: {years} years").format(
                years=_number(age['median_years'], 1, decimal_sep)),
        })

    q = data['quality']
    rows = [(label, str(q.get(key, 0))) for key, label in (
        ('missing', tr("Read books without a read date")),
        ('before_added', tr("Read before being added")),
        ('series_names', tr("Series under several names")),
        ('series_duplicates', tr("Series with duplicate volume numbers")),
        ('series_gaps', tr("Series with gaps")),
    ) if q.get(key)]
    if rows:
        section = {'heading': tr("Data quality"), 'rows': rows}
        if q['missing'] or q['before_added']:
            section['note'] = tr("The charts count books without a usable "
                                 "read date as read on the day they were "
                                 "added.")
        sections.append(section)

    return sections


def render_markdown(title, sections):
    lines = ['# ' + title, '']
    for section in sections:
        lines += ['## ' + section['heading'], '']
        if 'rows' in section:
            lines += ['| | |', '|---|---:|']
            lines += ['| {} | {} |'.format(label, value)
                      for label, value in section['rows']]
        else:
            headers, rows = section['table']
            lines.append('| ' + ' | '.join(headers) + ' |')
            lines.append('|---|' + '---:|' * (len(headers) - 1))
            lines += ['| ' + ' | '.join(row) + ' |' for row in rows]
        if section.get('note'):
            lines += ['', section['note']]
        lines.append('')
    return '\n'.join(lines)


_HTML_STYLE = (
    'body{font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;'
    'max-width:920px;margin:2em auto;padding:0 1em;color:#222;'
    'background:#fff;line-height:1.45}'
    'h1{font-size:1.6em}h2{font-size:1.2em;margin-top:1.8em}'
    'table{border-collapse:collapse;min-width:24em}'
    'td,th{border-bottom:1px solid #ddd;padding:.3em .8em;text-align:left}'
    'td.num,th.num{text-align:right}'
    'img{max-width:100%;border:1px solid #ddd;margin:.5em 0}'
    '.note{color:#666}'
)


def render_html(title, sections, images=None):
    """HTML page; ``images`` is a list of (caption, base64 PNG)."""
    esc = html.escape
    parts = ['<!DOCTYPE html>', '<html><head><meta charset="utf-8">',
             '<title>{}</title>'.format(esc(title)),
             '<style>{}</style>'.format(_HTML_STYLE), '</head><body>',
             '<h1>{}</h1>'.format(esc(title))]
    for section in sections:
        parts.append('<h2>{}</h2>'.format(esc(section['heading'])))
        parts.append('<table>')
        if 'rows' in section:
            for label, value in section['rows']:
                parts.append('<tr><td>{}</td><td class="num">{}</td></tr>'
                             .format(esc(label), esc(value)))
        else:
            headers, rows = section['table']
            parts.append('<tr>' + ''.join(
                '<th{}>{}</th>'.format(' class="num"' if i else '', esc(h))
                for i, h in enumerate(headers)) + '</tr>')
            for row in rows:
                parts.append('<tr>' + ''.join(
                    '<td{}>{}</td>'.format(' class="num"' if i else '',
                                           esc(c))
                    for i, c in enumerate(row)) + '</tr>')
        parts.append('</table>')
        if section.get('note'):
            parts.append('<p class="note">{}</p>'.format(
                esc(section['note'])))
    for caption, png_base64 in images or ():
        parts.append('<h2>{}</h2>'.format(esc(caption)))
        parts.append('<img alt="{}" src="data:image/png;base64,{}">'.format(
            esc(caption), png_base64))
    parts.append('</body></html>')
    return '\n'.join(parts) + '\n'


def build_report(data, fmt, tr, date_format, decimal_sep='.', title='',
                 images=None):
    """Complete report text in ``fmt`` (:data:`MARKDOWN` or :data:`HTML`).

    Images are only embedded in HTML.
    """
    sections = build_sections(data, tr, date_format, decimal_sep)
    if fmt == HTML:
        return render_html(title, sections, images)
    return render_markdown(title, sections)


def report_format(path):
    """:data:`MARKDOWN` for a .md/.markdown path, else :data:`HTML`."""
    lower = path.lower()
    if lower.endswith('.md') or lower.endswith('.markdown'):
        return MARKDOWN
    return HTML
