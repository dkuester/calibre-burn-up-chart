"""Tests for the Markdown/HTML report."""

from datetime import date

import report


def _tr(text):
    return text


def _data(**overrides):
    data = {
        'total': 200, 'read': 50, 'backlog': 150,
        'last12': {'added': 30, 'read': 12},
        'target_date': date(2050, 9, 4), 'target_tbr': 75,
        'forecast': {'ok': True, 'zero_date': date(2031, 5, 1)},
        'delay': {'count': 40, 'mean': 300.4, 'median': 120.0,
                  'min': 0, 'max': 2000},
        'age': {'median_years': 2.4,
                'buckets': [('< 1 year', 60), ('1–2 years', 90)]},
        'quality': {'missing': 3, 'before_added': 4},
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
    assert '| Forecast (last 12 months) | TBR = 0 on 01.05.2031 |' in text
    assert '| Gentle reduction | TBR = 75 on 04.09.2050 |' in text
    assert '| Median | 120 days |' in text
    assert '| Mean | 300 days |' in text
    assert '| Time in the TBR | Books | Share |' in text
    assert '|---|---:|---:|' in text
    assert '| 1–2 years | 90 | 60 % |' in text
    assert 'Median age: 2,4 years' in text


def test_forecast_variants():
    not_ok = report.build_sections(
        _data(forecast={'ok': False}), _tr, '%Y-%m-%d')
    growing = report.build_sections(
        _data(forecast={'ok': True, 'zero_date': None}), _tr, '%Y-%m-%d')
    assert ('Forecast (last 12 months)',
            'Not enough data for a forecast.') in not_ok[2]['rows']
    assert ('Forecast (last 12 months)',
            'The TBR is not shrinking at the current rate.') \
        in growing[2]['rows']


def test_optional_sections_left_out():
    sections = report.build_sections(
        _data(delay=None, age={'median_years': None, 'buckets': []},
              quality={'missing': 0, 'before_added': 0}, total=0, read=0),
        _tr, '%Y-%m-%d')
    headings = [s['heading'] for s in sections]
    assert headings == ['Library', 'Last 12 months', 'Goal and forecast']
    assert ('Read', '0 (–)') in sections[0]['rows']


def test_html_escapes_and_embeds_images():
    data = _data(age={'median_years': 1.0,
                      'buckets': [('<b>', 1), ('x', 0)]})
    text = report.build_report(data, report.HTML, _tr, '%Y-%m-%d',
                               title='A & B',
                               images=[('Chart <1>', 'QUJD')])
    assert text.startswith('<!DOCTYPE html>')
    assert '<title>A &amp; B</title>' in text
    assert '<td>&lt;b&gt;</td>' in text
    assert '<th class="num">Books</th>' in text
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
