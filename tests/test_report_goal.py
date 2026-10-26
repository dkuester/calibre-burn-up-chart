"""Tests for the yearly-goal part of the report."""

from datetime import date

import report


def _tr(text):
    return text


def _summary(**overrides):
    months = [{'list': 0, 'read': 0, 'added': 0} for _ in range(12)]
    months[0] = {'list': 2, 'read': 5, 'added': 3}
    months[1] = {'list': 1, 'read': 2, 'added': 4}
    summary = {
        'year': 2026, 'goal': 30, 'read': 22,
        'read_books': [{}] * 22, 'state': 'running',
        'expected': 24.6, 'ahead': -2.6, 'needed_per_month': 3.64,
        'projection': 26.8, 'goal_pages': 12140, 'read_pages': 7574,
        'pages_per_day': 69.8, 'months': months, 'month_count': 2,
        'own_read': 58, 'own_on_list': 22, 'from_tbr': 18,
        'delay_median': 120.4, 'date_mismatches': 3,
        'challenges': [{'name': 'TBR Challenge', 'count': 12,
                        'progress': 100, 'start': date(2026, 1, 1),
                        'end': date(2026, 12, 31)},
                       {'name': 'Open', 'count': 0, 'progress': 0,
                        'start': None, 'end': None}],
    }
    summary.update(overrides)
    return summary


def _goal(**overrides):
    return {'summary': _summary(**overrides),
            'years': [{'year': 2026, 'goal': 30, 'read': 22,
                       'own_read': 58},
                      {'year': 2025, 'goal': 25, 'read': 22,
                       'own_read': 69}]}


def _text(goal, fmt=report.MARKDOWN):
    sections = report.goal_sections(goal, _tr, '%d.%m.%Y', ',')
    if fmt == report.HTML:
        return report.render_html('R', sections)
    return report.render_markdown('R', sections)


def test_goal_sections_running():
    text = _text(_goal())
    assert '## Reading goal 2026 (Reading Goal plugin)' in text
    assert '| Books on the list | 30 |' in text
    assert '| Read | 22 (73 %) |' in text
    assert '| Target today | 24,6 |' in text
    assert '| Status | 2,6 books behind the target |' in text
    assert '| Required pace | 3,6 books/month until 31.12.2026 |' in text
    assert '| Projection for 31.12.2026 | 27 books |' in text
    assert ('| Pages | 7574 of 12140 pages (62 %), 70 pages/day needed |'
            in text)
    assert ('| Read in 2026 in total (own data) | 58 books, 22 of them '
            'from the list |') in text
    assert ('| Read list books from the TBR | 18 of 22 (added before '
            '2026) |') in text
    assert '| Time between purchase and reading (median) | 120 days |' \
        in text
    assert '3 read list books have a different read date' in text
    assert '## Reading goal 2026 by month' in text
    assert '| Jan | 2 | 5 | 3 | -2 |' in text
    assert '| Feb | 1 | 2 | 4 | +2 |' in text
    assert '| Mar |' not in text
    assert '| TBR Challenge | 12 | 100 % | 01.01.2026 – 31.12.2026 |' \
        in text
    assert '| Open | 0 | 0 % | – |' in text
    assert '| 2025 | 25 | 22 | 88 % | 69 |' in text


def test_goal_sections_finished_without_extras():
    text = _text(_goal(state='finished', needed_per_month=None,
                       projection=None, pages_per_day=None,
                       delay_median=None, date_mismatches=0,
                       challenges=[], month_count=12, read=30))
    assert '| Status | Goal reached |' in text
    assert 'Target today' not in text
    assert 'Required pace' not in text
    assert 'Projection' not in text
    assert 'pages/day' not in text
    assert 'median' not in text
    assert 'different read date' not in text
    assert 'Other challenges' not in text
    assert '| Dec | 0 | 0 | 0 | +0 |' in text


def test_goal_sections_planned():
    text = _text(_goal(state='planned', month_count=0, read=0,
                       projection=None, needed_per_month=2.5))
    assert '| Status | The year has not started yet |' in text
    assert '| Required pace | 2,5 books/month until 31.12.2026 |' in text
    assert 'by month' not in text


def test_goal_status_texts():
    s = _summary(state='finished', read=25)
    assert report.goal_status_text(s, _tr) == '5 books short of the goal'
    assert report.goal_status_text(_summary(ahead=1.24), _tr, ',') == \
        '1,2 books ahead of the target'
    assert report.goal_status_text(_summary(ahead=0.01), _tr) == \
        'on target'


def test_goal_pace_reached():
    assert report.goal_pace_text(_summary(needed_per_month=0), _tr,
                                 '%d.%m.%Y') == 'goal already reached'


def test_goal_title_and_header():
    s = _summary()
    assert report.goal_title(s, _tr, ',') == \
        'Reading goal 2026: 22 of 30 books (73 %)'
    assert report.goal_header_lines(s, _tr, '%d.%m.%Y', ',') == [
        'Target today: 24,6 · 2,6 books behind the target · Required: '
        '3,6 books/month until 31.12.2026',
        'Pages: 7574 of 12140 pages (62 %), 70 pages/day needed',
        'Read in 2026 in total (own data): 58 books, 22 of them from '
        'the list',
    ]
    lines = report.goal_header_lines(
        _summary(state='finished', needed_per_month=None, read=31,
                 pages_per_day=None), _tr, '%d.%m.%Y')
    assert lines[0] == 'Goal reached'
    assert lines[1] == 'Pages: 7574 of 12140 pages (62 %)'


def test_month_name():
    assert report.month_name(_tr, 12) == 'Dec'


def test_html_contains_goal_table():
    assert '<td>Jan</td>' in _text(_goal(), report.HTML)


def test_build_report_places_goal_after_forecast():
    import test_report
    data = test_report._data(goal=_goal())
    text = report.build_report(data, report.MARKDOWN, _tr, '%d.%m.%Y')
    forecast = text.index('## Goal and forecast')
    goal = text.index('## Reading goal 2026 (Reading Goal plugin)')
    delay = text.index('## Time between purchase and reading')
    assert forecast < goal < delay
    assert '## Reading goal' not in report.build_report(
        test_report._data(goal=None), report.MARKDOWN, _tr, '%d.%m.%Y')
