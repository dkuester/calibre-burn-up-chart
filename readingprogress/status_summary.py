"""
Text and tooltip of the TBR widget in Calibre's status bar.

Qt-/Calibre-free: the caller reads the library and passes the
translation function, so the module stays unit-testable. Tests import
it flat (see ``tests/conftest.py``).
"""

import calendar

# Months back for the trend in the status bar and the tooltip
TREND_MONTHS = 12


def _signed(n):
    if n > 0:
        return '+{}'.format(n)
    if n < 0:
        return '−{}'.format(-n)
    return '±0'


def _months_back(day, months):
    """End of the month ``months`` before the month of ``day``."""
    index = day.year * 12 + day.month - 1 - months
    year, month = divmod(index, 12)
    month += 1
    return day.replace(year=year, month=month,
                       day=calendar.monthrange(year, month)[1])


def backlog_trend(rows, months=TREND_MONTHS):
    """Change of the TBR against the end of the month ``months`` back.

    ``rows`` are the monthly snapshots of ``export_snapshots()``
    ``(date, total, read, backlog)``; months without events are missing,
    so the last row at or before that month end holds its value.

    :return: ``(backlog_then, change)``, or ``None`` if the library has
        no snapshot that old.
    """
    cutoff = _months_back(rows[-1][0], months)
    older = [row for row in rows if row[0] <= cutoff]
    if not older:
        return None
    then = older[-1][3]
    return then, rows[-1][3] - then


def _hint(tr):
    return tr("Whole library · click to open the burn-up chart")


def status_summary(rows, tr, pace_lines=()):
    """``(text, tooltip)`` for the snapshots ``rows`` (see
    :func:`backlog_trend`). ``pace_lines`` are the required-pace
    sentences of the burn-up chart, appended to the tooltip."""
    _day, total, read, backlog = rows[-1]
    text = tr("TBR: {backlog}").format(backlog=backlog)
    lines = [tr("{total} books, {read} of them read ({percent} %)").format(
        total=total, read=read,
        percent=round(100 * read / total) if total else 0)]
    trend = backlog_trend(rows)
    if trend is not None:
        then, change = trend
        if change:
            text += ' {}{}'.format('▲' if change > 0 else '▼', abs(change))
        lines.append(tr("{months} months ago: {backlog} ({change})").format(
            months=TREND_MONTHS, backlog=then, change=_signed(change)))
    lines.extend(pace_lines)
    lines.append(_hint(tr))
    return text, '\n'.join(lines)


def empty_summary(tr):
    """``(text, tooltip)`` for a library without usable books."""
    return (tr("TBR: {backlog}").format(backlog=0),
            '\n'.join([tr("No data available for this analysis."),
                       _hint(tr)]))


def problem_summary(problem_lines, tr):
    """``(text, tooltip)`` when the configured columns are unusable;
    ``problem_lines`` come from ``describe_column_problems()``."""
    return (tr("TBR: {backlog}").format(backlog='–'),
            '\n'.join(list(problem_lines) + [
                tr("You can change the column names in the plugin "
                   "settings.")]))


def error_summary(tr):
    """``(text, tooltip)`` when reading the library failed."""
    return (tr("TBR: {backlog}").format(backlog='?'),
            tr("Could not read the library."))
