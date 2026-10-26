"""Tests for collect_report_data(): the figures behind the report."""

from datetime import date

import export_reading_status as ers
import pytest
import report

TODAY = date(2026, 10, 26)


def _library(make_db):
    return make_db({
        1: {'timestamp': date(2024, 1, 10), '#gelesen': True,
            '#last_read': date(2024, 6, 1)},
        2: {'timestamp': date(2025, 12, 1), '#gelesen': True,
            '#last_read': date(2026, 3, 1)},
        3: {'timestamp': date(2026, 2, 1), '#gelesen': True},     # no date
        4: {'timestamp': date(2026, 5, 1), '#gelesen': True,
            '#last_read': date(2026, 1, 1)},                      # too early
        5: {'timestamp': date(2013, 1, 1), '#gelesen': False},
        6: {'timestamp': date(2026, 9, 1), '#gelesen': False},
    })


def test_collect_report_data(make_db):
    data = ers.collect_report_data(_library(make_db), '#gelesen',
                                   '#last_read', date(2030, 1, 1), 0.5,
                                   today=TODAY)
    assert (data['total'], data['read'], data['backlog']) == (6, 4, 2)
    # Nov 2025 … Oct 2026: books 2, 3, 4, 6 added; 2, 3, 4 read
    assert data['last12'] == {'added': 4, 'read': 3}
    assert data['target_date'] == date(2030, 1, 1)
    assert data['target_tbr'] == 1
    assert data['forecast']['ok'] is True
    assert data['pace']['target_backlog'] == 0
    assert data['pace_soft']['target_backlog'] == 1
    assert data['pace']['added_rate'] == pytest.approx(4 / 12)
    assert data['pace']['read_rate'] == pytest.approx(3 / 12)
    assert data['pace']['months'] == pytest.approx(
        (date(2030, 1, 1) - TODAY).days / ers.DAYS_PER_MONTH)
    assert data['delay']['count'] == 2
    assert data['age']['max_years'] == ers.MAX_AGE_YEARS
    assert data['age']['counts'][0] == 1          # book 6
    assert data['age']['counts'][-1] == 1         # book 5, 13 years
    assert data['age']['median_years'] == pytest.approx(
        ((TODAY - date(2013, 1, 1)).days + 55) / 2 / 365.25)
    assert data['quality'] == {'missing': 1, 'before_added': 1}
    assert data['rows'][-1][0] == TODAY
    assert data['rates'][-1][0] == TODAY


def test_collected_data_renders(make_db):
    data = ers.collect_report_data(_library(make_db), '#gelesen',
                                   '#last_read', date(2030, 1, 1), 0.5,
                                   today=TODAY)
    text = report.build_report(data, report.MARKDOWN, lambda t: t,
                               '%Y-%m-%d')
    assert '| 10+ years | 1 | 50 % |' in text
    assert '| Read before being added | 1 |' in text


def test_collect_report_data_empty_library(make_db):
    with pytest.raises(ers.NoDataError):
        ers.collect_report_data(make_db({}), '#gelesen', '#last_read',
                                date(2030, 1, 1), 0.5, today=TODAY)
