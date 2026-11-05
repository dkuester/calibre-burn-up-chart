"""Tests for required_pace() and the pace texts of the report/chart."""

from datetime import date, timedelta

import export_reading_status as ers
import pytest
import report

TODAY = date(2026, 10, 26)
TARGET = date(2050, 9, 4)


def _tr(text):
    return text


def _rates(added, read):
    """robust_rates()-style dict."""
    return {'status': ers.FORECAST_OK, 'months': 24, 'added': added,
            'read': read, 'spread': 0.0}


def _months(target=TARGET):
    return (target - TODAY).days / ers.DAYS_PER_MONTH


def test_owner_example():
    pace = ers.required_pace(1655, _rates(248 / 12, 73 / 12), TODAY, TARGET)
    months = _months()
    assert pace['status'] == ers.PACE_OK
    assert pace['months'] == pytest.approx(months)
    assert pace['reduction'] == pytest.approx(1655 / months)
    assert pace['read_needed'] == pytest.approx(248 / 12 + 1655 / months)
    assert pace['max_added'] == pytest.approx(73 / 12 - 1655 / months)
    assert pace['mix_added'] == pytest.approx(124 / 12)
    assert pace['mix_read_needed'] == pytest.approx(124 / 12 + 1655 / months)
    assert report.pace_text(pace, _tr, ',') == \
        'read 26,4 books/month (buying stays at 20,7) or buy at most ' \
        '0,3 books/month (reading stays at 6,1)'


def test_gentle_reduction_target():
    pace = ers.required_pace(1655, _rates(248 / 12, 73 / 12), TODAY, TARGET,
                             target_backlog=828)
    assert pace['target_backlog'] == 828
    assert pace['reduction'] == pytest.approx(827 / _months())


def test_buying_stopped_is_not_enough():
    pace = ers.required_pace(1000, _rates(10.0, 1.0), TODAY,
                             TODAY + timedelta(days=3653))
    assert pace['max_added'] < 0
    assert report.pace_text(pace, _tr) == (
        'read {} books/month (buying stays at 10.0) or buy nothing and '
        'still read {} books/month'.format(
            report.pace_number(pace['read_needed']),
            report.pace_number(pace['reduction'])))


def test_max_added_exactly_zero_counts_as_buy_nothing():
    pace = {'status': ers.PACE_OK, 'read_needed': 3.0, 'max_added': 0.0,
            'reduction': 2.0, 'added_rate': 2.5, 'read_rate': 1.0}
    assert report.pace_text(pace, _tr) == (
        'read 3.0 books/month (buying stays at 2.5) or buy nothing and '
        'still read 2.0 books/month')


@pytest.mark.parametrize('backlog, target_backlog', [(0, 0), (5, 5), (3, 5)])
def test_goal_reached(backlog, target_backlog):
    pace = ers.required_pace(backlog, _rates(2.0, 1.0), TODAY, TARGET,
                             target_backlog)
    assert pace['status'] == ers.PACE_REACHED
    assert pace['mix_added'] is None
    assert report.pace_text(pace, _tr) == 'already reached'


@pytest.mark.parametrize('days', [-30, 0, 30])
def test_target_date_too_close(days):
    pace = ers.required_pace(100, _rates(2.0, 1.0), TODAY,
                             TODAY + timedelta(days=days))
    assert pace['status'] == ers.PACE_TOO_CLOSE
    assert report.pace_text(pace, _tr).startswith('target date too close')


def test_one_month_left_is_enough():
    pace = ers.required_pace(100, _rates(2.0, 1.0), TODAY,
                             TODAY + timedelta(days=31))
    assert pace['status'] == ers.PACE_OK


def test_without_enough_data_only_the_reduction_is_known():
    rates = ers.robust_rates([])
    pace = ers.required_pace(100, rates, TODAY,
                             TODAY + timedelta(days=3653))
    assert pace['added_rate'] is None
    assert pace['read_needed'] is None
    assert pace['mix_added'] is None
    assert pace['reduction'] == pytest.approx(100 / 120, rel=1e-3)
    assert report.pace_text(pace, _tr) == \
        'reduce the TBR by 0.8 books/month'


def test_rates_from_robust_rates():
    rates = [(ers.month_end(2025, m), 4 + (m == 6) * 100, 1, 0.0, 0.0)
             for m in range(1, 13)] + [(TODAY, 0, 0, 0.0, 0.0)]
    pace = ers.required_pace(4, ers.robust_rates(rates), TODAY, TARGET)
    assert (pace['added_rate'], pace['read_rate']) == (4.0, 1.0)


@pytest.mark.parametrize('value, expected', [
    (0.0, '0,0'), (0.01, '< 0,1'), (0.049, '< 0,1'), (0.05, '0,1'),
    (26.44, '26,4'), (-0.01, '-0,0'),
])
def test_pace_number(value, expected):
    assert report.pace_number(value, ',') == expected


def test_pace_help():
    text = report.pace_help(_rates(2.5, 1.0), _tr, ',')
    assert 'trimmed mean of the last 24 full months' in text
    assert 'Currently that is 2,5 bought / 1,0 read per month.' in text
    assert 'two halves with different assumptions' in text
    assert 'band that covers 80 % of cases' in text


def test_pace_help_without_enough_data_omits_current_rates():
    text = report.pace_help(ers.robust_rates([]), _tr)
    assert 'Currently that is' not in text
    assert 'trimmed mean' in text


def _pace_table_goals():
    rates = _rates(248 / 12, 73 / 12)
    return [
        (0, ers.required_pace(1655, rates, TODAY, TARGET)),
        (828, ers.required_pace(1655, rates, TODAY, TARGET, 828)),
    ]


def test_pace_table_without_target():
    goals = _pace_table_goals()
    columns, rows = report.pace_table(_tr, goals, None, ',')
    assert columns == ['Only read more', 'Only buy less',
                       'Mixed (buy → read)']
    assert rows[0][0] == 'TBR = 0'
    assert rows[1][0] == 'TBR = 828'
    pace = goals[0][1]
    assert rows[0][1] == [
        report.pace_number(pace['read_needed'], ','),
        report.pace_number(pace['max_added'], ','),
        '{} → {}'.format(report.pace_number(pace['mix_added'], ','),
                         report.pace_number(pace['mix_read_needed'], ',')),
    ]


def test_pace_table_with_target():
    goals = [
        (0, ers.pace_for_target(1655, 2.0, TODAY, TARGET)),
        (828, ers.pace_for_target(1655, 2.0, TODAY, TARGET, 828)),
    ]
    columns, rows = report.pace_table(_tr, goals, 2.0, ',')
    assert columns == ['Read (purchase target 2,0/month)']
    assert rows[0][0] == 'TBR = 0'
    assert rows[0][1] == [report.pace_number(
        goals[0][1]['read_needed'], ',')]


def test_pace_table_reached_and_without_rates():
    reached = ers.required_pace(0, _rates(2.0, 1.0), TODAY, TARGET)
    _columns, rows = report.pace_table(_tr, [(0, reached)], None)
    assert rows[0][1] == ['already reached', '', '']
    no_rates = ers.required_pace(100, ers.robust_rates([]), TODAY, TARGET)
    _columns, rows = report.pace_table(_tr, [(0, no_rates)], None)
    assert rows[0][1] == ['–', '', '']


def test_pace_table_too_close():
    pace = ers.required_pace(100, _rates(2.0, 1.0), TODAY,
                             TODAY + timedelta(days=10))
    _columns, rows = report.pace_table(_tr, [(0, pace)], None)
    assert rows[0][1] == ['–', '', '']
