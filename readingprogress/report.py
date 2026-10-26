"""
Key-figures report as Markdown or HTML.

Qt-/Calibre-free: the caller collects the figures (see ``build_report``)
and passes the translation function, so the module stays unit-testable.
Tests import it flat (see ``tests/conftest.py``).
"""

import html

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
    - ``quality``: dict with ``missing`` and ``before_added``
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
    if q['missing'] or q['before_added']:
        sections.append({
            'heading': tr("Data quality"),
            'rows': [
                (tr("Read books without a read date"), str(q['missing'])),
                (tr("Read before being added"), str(q['before_added'])),
            ],
            'note': tr("The charts count these books as read on the day "
                       "they were added."),
        })

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
