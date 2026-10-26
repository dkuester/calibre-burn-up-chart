"""Tests for reading the data of the Reading Goal plugin."""

import json
from datetime import date, datetime, timezone

import pytest
import reading_goal

UTC = timezone.utc


def _dt(text):
    return {'__class__': 'datetime.datetime', '__value__': text}


def _book(status=100, day='2026-03-10T12:00:00+00:00', pages=300,
          read_pages=None, last_year=0, title='Dawn',
          authors=('Octavia E. Butler',)):
    return {
        'authors': list(authors), 'challenges': ['Annual'],
        'date': _dt(day) if day else None, 'genre': ['Fiction'],
        'last_year_pages': last_year, 'page_count': pages,
        'read_pages': pages if read_pages is None else read_pages,
        'records': {}, 'reread_count': 0, 'series': None,
        'shelf': 'Read' if status == 100 else 'Reading',
        'status': status, 'title': title, 'title_sort': title,
    }


def _raw():
    return {
        '2025': {
            '5': _book(day='2025-06-01T12:00:00+00:00'),
            'summary': {'goal_books_count': 1},
        },
        '2026': {
            '1': _book(day='2026-01-15T12:00:00+00:00', pages=200),
            '2': _book(day='2026-03-10T12:00:00+00:00', title='Kindred'),
            '3': _book(status=40, day='2026-09-25T06:00:00+00:00',
                       pages=1000, read_pages=400),
            '4': _book(status=0, day=None, pages=100, read_pages=0),
            'summary': {
                'goal_books_count': 4,
                'challenges_dict': {
                    'Annual': {'count': 4, 'progress': 50},
                    ' TBR Challenge': {
                        'count': 2, 'progress': 100,
                        'start': _dt('2025-12-31T23:00:00+00:00'),
                        'end': _dt('2026-12-30T23:00:00+00:00')},
                    'Broken': 'x',
                },
            },
        },
        '2027': {'summary': {'goal_books_count': 0}},
        'general_info': {'schema_version': 1.5},
    }


def test_goal_data_path():
    path = reading_goal.goal_data_path('/cfg', 'abc-123')
    assert path == '/cfg/plugins/Reading_Goal_Data_abc-123.json'


def test_load_goal_data_reads_file(tmp_path):
    path = tmp_path / 'data.json'
    path.write_text(json.dumps(_raw()), encoding='utf-8')
    years = reading_goal.load_goal_data(str(path), UTC)
    assert sorted(years) == [2025, 2026]


def test_load_goal_data_missing_or_broken(tmp_path):
    assert reading_goal.load_goal_data(str(tmp_path / 'nope.json')) is None
    broken = tmp_path / 'broken.json'
    broken.write_text('{not json', encoding='utf-8')
    assert reading_goal.load_goal_data(str(broken)) is None


def test_parse_year_fields():
    year = reading_goal.parse_goal_data(_raw(), UTC)[2026]
    assert year['goal'] == 4
    assert [b['title'] for b in year['read']] == ['Dawn', 'Kindred']
    assert year['read'][0] == {'date': date(2026, 1, 15), 'book_id': 1,
                               'title': 'Dawn',
                               'authors': 'Octavia E. Butler'}
    assert year['undated'] == 0
    assert year['goal_pages'] == 200 + 300 + 1000 + 100
    assert year['read_pages'] == 200 + 300 + 400
    assert year['challenges'] == [{
        'name': 'TBR Challenge', 'count': 2, 'progress': 100,
        'start': date(2025, 12, 31), 'end': date(2026, 12, 30)}]


def test_parse_pages_minus_last_year():
    raw = {'2026': {'1': _book(pages=500, read_pages=500, last_year=200)}}
    year = reading_goal.parse_goal_data(raw)[2026]
    assert year['goal_pages'] == 300
    assert year['read_pages'] == 300


def test_parse_skips_unknown_entries():
    raw = {
        '2026': {
            '1': _book(),
            'x': _book(),            # no book id
            '2': 'garbage',          # no dict
            '3': _book(day=None),    # finished, but without a date
            '4': dict(_book(), status=True, page_count='300'),
            '5': dict(_book(), authors='not a list', title=None),
        },
        '26': {'1': _book()},        # no year
        '2025': ['list'],            # no dict
    }
    year = reading_goal.parse_goal_data(raw, UTC)[2026]
    assert year['goal'] == 4
    assert year['undated'] == 1
    assert [b['book_id'] for b in year['read']] == [1, 5]
    assert year['read'][1]['authors'] == ''
    assert year['read'][1]['title'] == ''


@pytest.mark.parametrize('raw', [None, [], {}, {'general_info': {}},
                                 {'2026': {'summary': {}}}])
def test_parse_without_goal_years(raw):
    assert reading_goal.parse_goal_data(raw) is None


def test_parse_challenges_without_dict():
    raw = {'2026': {'1': _book(), 'summary': {'challenges_dict': []}}}
    assert reading_goal.parse_goal_data(raw)[2026]['challenges'] == []
    raw = {'2026': {'1': _book(), 'summary': 'x'}}
    assert reading_goal.parse_goal_data(raw)[2026]['challenges'] == []


@pytest.mark.parametrize('value, expected', [
    (_dt('2026-02-28T13:42:22.344000+00:00'), date(2026, 2, 28)),
    (_dt('2026-02-28T23:30:00-02:00'), date(2026, 3, 1)),
    (_dt('2026-02-28T13:42:22'), date(2026, 2, 28)),
    (_dt('kaputt'), None),
    (_dt(5), None),
    ('2026-02-28', None),
    (None, None),
])
def test_parse_datetime(value, expected):
    assert reading_goal.parse_datetime(value, UTC) == expected


def test_default_year():
    years = {2024: {}, 2026: {}, 2027: {}}
    assert reading_goal.default_year(years, date(2026, 5, 1)) == 2026
    assert reading_goal.default_year({2024: {}, 2027: {}},
                                     date(2026, 5, 1)) == 2024
    assert reading_goal.default_year({2027: {}, 2028: {}},
                                     date(2026, 5, 1)) == 2027


def _db(make_db):
    def ts(text):
        return datetime.fromisoformat(text).replace(tzinfo=UTC)
    return make_db({
        1: {'timestamp': ts('2020-05-01T12:00:00'), '#read': True,
            '#last': ts('2026-01-15T12:00:00')},
        2: {'timestamp': ts('2026-02-01T12:00:00'), '#read': True,
            '#last': ts('2026-03-12T12:00:00')},
        3: {'timestamp': ts('2026-04-01T12:00:00'), '#read': True,
            '#last': None},
        4: {'timestamp': ts('2026-04-01T12:00:00'), '#read': True,
            '#last': ts('2025-01-01T12:00:00')},
        5: {'timestamp': None, '#read': True, '#last': None},
        6: {'timestamp': ts('2026-05-01T12:00:00'), '#read': False,
            '#last': ts('2026-05-02T12:00:00')},
        7: {'timestamp': date(2025, 1, 1), '#read': True,
            '#last': date(2025, 6, 1)},
    })


def test_library_events(make_db):
    events = reading_goal.library_events(_db(make_db), '#read', '#last',
                                         UTC)
    assert events['added'][1] == date(2020, 5, 1)
    assert 5 not in events['added']
    # 3 and 5 have no read date, 6 is not marked as read
    assert events['read'] == {1: date(2026, 1, 15), 2: date(2026, 3, 12),
                              4: date(2025, 1, 1), 7: date(2025, 6, 1)}


def _summary(make_db, today):
    years = reading_goal.parse_goal_data(_raw(), UTC)
    events = reading_goal.library_events(_db(make_db), '#read', '#last',
                                         UTC)
    return reading_goal.year_summary(years[2026], events, today)


def test_year_summary_running(make_db):
    today = date(2026, 7, 2)   # day 183 of 365
    s = _summary(make_db, today)
    assert s['state'] == 'running'
    assert s['goal'] == 4 and s['read'] == 2
    assert s['expected'] == pytest.approx(4 * 183 / 365)
    assert s['ahead'] == pytest.approx(2 - 4 * 183 / 365)
    assert s['needed_per_month'] == pytest.approx(2 / (182 * 12 / 365))
    assert s['projection'] == pytest.approx(2 * 365 / 183)
    assert s['pages_per_day'] == pytest.approx((1600 - 900) / 182)
    assert s['month_count'] == 7
    assert s['months'][0] == {'list': 1, 'read': 1, 'added': 0}
    assert s['months'][2] == {'list': 1, 'read': 1, 'added': 0}
    assert s['months'][3] == {'list': 0, 'read': 0, 'added': 2}
    assert s['own_read'] == 2
    assert s['own_on_list'] == 2      # books 1 and 2 are on the list
    assert s['from_tbr'] == 1         # book 1 was added in 2020
    assert s['delay_median'] == pytest.approx(
        ((date(2026, 1, 15) - date(2020, 5, 1)).days
         + (date(2026, 3, 10) - date(2026, 2, 1)).days) / 2)
    assert s['date_mismatches'] == 1  # book 2: 10.03. vs. 12.03.
    assert [c['name'] for c in s['challenges']] == ['TBR Challenge']


def test_year_summary_finished_and_planned(make_db):
    s = _summary(make_db, date(2027, 1, 5))
    assert s['state'] == 'finished'
    assert s['expected'] == 4
    assert s['needed_per_month'] is None
    assert s['pages_per_day'] is None
    assert s['projection'] is None
    assert s['month_count'] == 12

    s = _summary(make_db, date(2025, 12, 1))
    assert s['state'] == 'planned'
    assert s['expected'] == 0
    assert s['needed_per_month'] == pytest.approx(2 / 12)
    assert s['projection'] is None
    assert s['month_count'] == 0


def test_year_summary_goal_reached_and_no_delays():
    year = {'year': 2026, 'goal': 1, 'undated': 0, 'goal_pages': 10,
            'read_pages': 10, 'challenges': [],
            'read': [{'date': date(2025, 12, 30), 'book_id': 9,
                      'title': '', 'authors': ''}]}
    events = {'added': {9: date(2026, 1, 1)}, 'read': {}}
    s = reading_goal.year_summary(year, events, date(2026, 3, 1))
    assert s['needed_per_month'] == 0
    assert s['pages_per_day'] == 0
    assert s['delay_median'] is None   # read before added
    assert s['months'][0] == {'list': 0, 'read': 0, 'added': 1}
    assert sum(m['list'] for m in s['months']) == 0
    assert s['from_tbr'] == 0


def test_median_odd():
    assert reading_goal._median([3, 1, 2]) == 2.0


def test_year_overview(make_db):
    years = reading_goal.parse_goal_data(_raw(), UTC)
    events = reading_goal.library_events(_db(make_db), '#read', '#last',
                                         UTC)
    assert reading_goal.year_overview(years, events) == [
        {'year': 2026, 'goal': 4, 'read': 2, 'own_read': 2},
        {'year': 2025, 'goal': 1, 'read': 1, 'own_read': 2},
    ]


def test_cumulative_dates():
    days = [date(2026, 3, 1), date(2026, 1, 5), date(2026, 3, 1),
            date(2025, 12, 31)]
    assert reading_goal.cumulative_dates(days, 2026) == [
        (date(2026, 1, 5), 1), (date(2026, 3, 1), 3)]


def test_report_data(make_db):
    years = reading_goal.parse_goal_data(_raw(), UTC)
    events = reading_goal.library_events(_db(make_db), '#read', '#last',
                                         UTC)
    data = reading_goal.report_data(years, events, date(2026, 7, 2))
    assert data['summary']['year'] == 2026
    assert [r['year'] for r in data['years']] == [2026, 2025]
