"""Tests for the Markdown/HTML report."""

from datetime import date

import pytest
import report


def _tr(text):
    return text


def _pace(target, read_needed, max_added, added_rate, read_rate,
          status='ok'):
    return {'status': status, 'target_backlog': target,
            'read_needed': read_needed, 'max_added': max_added,
            'reduction': read_needed - added_rate,
            'added_rate': added_rate, 'read_rate': read_rate}


def _forecast(**overrides):
    fc = {'status': 'ok', 'ok': True, 'months': 24, 'start': 150,
          'slope': -2.0, 'zero_date': date(2032, 1, 1),
          'zero_early': date(2031, 5, 1), 'zero_late': date(2034, 11, 1)}
    fc.update(overrides)
    return fc


def _data(**overrides):
    data = {
        'total': 200, 'read': 50, 'backlog': 150,
        'last12': {'added': 30, 'read': 12},
        'target_date': date(2050, 9, 4), 'target_tbr': 75,
        'forecast': _forecast(),
        'pace': _pace(0, 4.0, 1.5, 2.5, 1.0),
        'pace_soft': _pace(75, 3.2, 2.3, 2.5, 1.0),
        'delay': {'count': 40, 'mean': 300.4, 'median': 120.0,
                  'min': 0, 'max': 2000},
        'age': {'median_years': 2.4, 'max_years': 10, 'counts': [60, 90]},
        'quality': {'missing': 3, 'before_added': 4, 'series_names': 0,
                    'series_duplicates': 0, 'series_gaps': 0},
    }
    data.update(overrides)
    return data


def test_markdown_contains_all_sections():
    text = report.build_report(_data(), report.MARKDOWN, _tr, '%d.%m.%Y',
                               ',', title='Report')
    assert text.startswith('# Report\n')
    for heading in ('## Library', '## Last 12 months', '## Goal and forecast',
                    '## Time between purchase and reading',
                    '## Age of the TBR', '## Data quality'):
        assert heading in text
    assert '| Read | 50 (25 %) |' in text
    assert '| Change of the TBR | +18 |' in text
    assert ('| Forecast (typical month of the last 24 months) | TBR = 0 '
            'between 05.2031 and 11.2034 |') in text
    assert '| Gentle reduction | TBR = 75 on 04.09.2050 |' in text
    assert ('| Required pace (TBR = 0) | Read 4,0 books/month or buy at '
            'most 1,5 books/month |') in text
    assert ('| Required pace (TBR = 75) | Read 3,2 books/month or buy at '
            'most 2,3 books/month |') in text
    assert ('Required pace at the typical purchase rate (2,5) and reading '
            'rate (1,0) per month: mean of the last 24 full months') in text
    assert '| Median | 120 days |' in text
    assert '| Mean | 300 days |' in text
    assert '| Time in the TBR | Books | Share |' in text
    assert '|---|---:|---:|' in text
    assert '| 1–2 years | 90 | 60 % |' in text
    assert 'Median age: 2,4 years' in text


@pytest.mark.parametrize('overrides, label, text', [
    ({'status': 'none', 'ok': False, 'months': 2}, 'Forecast',
     'Not enough data for a forecast (2 of 3 full months).'),
    ({'status': 'preliminary', 'months': 5},
     'Forecast (preliminary, 5 months)', 'TBR = 0 between 2031-05 and 2034-11'),
    ({'zero_late': None}, None, 'TBR = 0 at the earliest in 2031-05'),
    ({'slope': 5.75, 'zero_date': None}, None,
     'TBR grows by about 5.8 books/month'),
    ({'slope': 0.0, 'zero_date': None}, None,
     'The TBR is not shrinking at the current rate.'),
    ({'start': 0}, None, 'The TBR is already empty.'),
])
def test_forecast_variants(overrides, label, text):
    fc = _forecast(**overrides)
    assert report.forecast_text(fc, _tr, '%Y-%m-%d') == text
    if label is not None:
        assert report.forecast_label(fc, _tr) == label


def test_no_rate_note_without_enough_data():
    pace = dict(_pace(0, 4.0, 1.5, 2.5, 1.0), added_rate=None,
                read_rate=None, read_needed=None, max_added=None)
    sections = report.build_sections(
        _data(forecast=_forecast(status='none', ok=False, months=1),
              pace=pace, pace_soft=pace), _tr, '%Y-%m-%d')
    assert sections[2]['note'] is None
    assert ('Required pace (TBR = 0)',
            'Reduce the TBR by 1.5 books/month') in sections[2]['rows']


@pytest.mark.parametrize('fmt, expected', [
    ('%d.%m.%Y', '%m.%Y'), ('%Y-%m-%d', '%Y-%m'), ('%m/%d/%Y', '%m/%Y'),
])
def test_month_format(fmt, expected):
    assert report.month_format(fmt) == expected


def test_optional_sections_left_out():
    sections = report.build_sections(
        _data(delay=None, age={'median_years': None, 'max_years': 10,
                              'counts': [0]},
              quality={'missing': 0, 'before_added': 0, 'series_names': 0,
                       'series_duplicates': 0, 'series_gaps': 0},
              total=0, read=0),
        _tr, '%Y-%m-%d')
    headings = [s['heading'] for s in sections]
    assert headings == ['Library', 'Last 12 months', 'Goal and forecast']
    assert ('Read', '0 (–)') in sections[0]['rows']


def _quality_section(**quality):
    counts = {'missing': 0, 'before_added': 0, 'series_names': 0,
              'series_duplicates': 0, 'series_gaps': 0}
    counts.update(quality)
    sections = report.build_sections(_data(quality=counts), _tr, '%Y-%m-%d')
    return next(s for s in sections if s['heading'] == 'Data quality')


def test_quality_lists_only_nonzero_counts():
    section = _quality_section(missing=3, series_names=6, series_gaps=5)
    assert section['rows'] == [
        ('Read books without a read date', '3'),
        ('Series under several names', '6'),
        ('Series with gaps', '5'),
    ]
    assert 'read on the day they were added' in section['note']


def test_quality_series_only_has_no_read_date_note():
    section = _quality_section(series_duplicates=32)
    assert section['rows'] == [('Series with duplicate volume numbers', '32')]
    assert 'note' not in section


def test_html_escapes_and_embeds_images():
    data = _data(age={'median_years': 1.0, 'max_years': 10,
                      'counts': [1, 0]})
    text = report.build_report(data, report.HTML, lambda t: '<b>' + t,
                               '%Y-%m-%d',
                               title='A & B',
                               images=[('Chart <1>', 'QUJD')])
    assert text.startswith('<!DOCTYPE html>')
    assert '<title>A &amp; B</title>' in text
    assert '<td>&lt;b&gt;&lt; 1 year</td>' in text
    assert '<th class="num">&lt;b&gt;Books</th>' in text
    assert '<p class="note">' in text
    assert 'alt="Chart &lt;1&gt;" src="data:image/png;base64,QUJD"' in text
    assert text.rstrip().endswith('</body></html>')


def test_markdown_ignores_images():
    text = report.build_report(_data(), report.MARKDOWN, _tr, '%Y-%m-%d',
                               images=[('Chart', 'QUJD')])
    assert 'base64' not in text


def test_report_format():
    assert report.report_format('/x/report.md') == report.MARKDOWN
    assert report.report_format('/x/report.MARKDOWN') == report.MARKDOWN
    assert report.report_format('/x/report.html') == report.HTML
    assert report.report_format('/x/report') == report.HTML


def test_bucket_label():
    assert report.bucket_label(_tr, 0, 11, 10) == '< 1 year'
    assert report.bucket_label(_tr, 3, 11, 10) == '3–4 years'
    assert report.bucket_label(_tr, 10, 11, 10) == '10+ years'
    # A last bucket below the cap is an ordinary one-year bucket
    assert report.bucket_label(_tr, 4, 5, 10) == '4–5 years'


def test_pace_rows_skip_soft_goal_equal_to_zero_goal():
    data = _data(pace_soft=_pace(0, 4.0, 1.5, 2.5, 1.0))
    assert report.pace_rows(data, _tr) == [
        ('Required pace (TBR = 0)',
         'Read 4.0 books/month or buy at most 1.5 books/month')]


def test_pace_rows_reached():
    data = _data(pace=_pace(0, 1.0, 2.5, 2.5, 1.0, status='reached'),
                 pace_soft=_pace(0, 1.0, 2.5, 2.5, 1.0, status='reached'))
    assert report.pace_rows(data, _tr) == [
        ('Required pace (TBR = 0)', 'Already reached')]
