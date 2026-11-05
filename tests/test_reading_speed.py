"""Tests for book_pages() and reading_speed()."""

from datetime import date

import export_reading_status as ers
import pytest

TODAY = date(2026, 6, 15)


def test_book_pages_keeps_only_positive_counts(make_db):
    db = make_db({
        1: {'pages': 300},
        2: {'pages': -1},      # calibre's "unknown" sentinel
        3: {'pages': 0},
        4: {'pages': None},
        5: {'pages': '250'},   # a text-typed custom column
        6: {'pages': 'x'},     # unusable value
    })
    assert ers.book_pages(db) == {1: 300, 5: 250}


def test_book_pages_uses_configured_column(make_db):
    db = make_db({1: {'#pagecount': 123}, 2: {'#pagecount': 0}})
    assert ers.book_pages(db, '#pagecount') == {1: 123}


def test_median_pages_odd_even_and_empty():
    assert ers.median_pages({}) is None
    assert ers.median_pages({1: 100}) == 100.0
    assert ers.median_pages({1: 100, 2: 300}) == 200.0
    assert ers.median_pages({1: 100, 2: 200, 3: 300}) == 200.0


def test_reading_speed_averages_full_months(make_db):
    # The earliest read month (January) and the current month (June) are
    # excluded; February to May (4 full months) count.
    books = {i: {'timestamp': date(2026, 1, 1), '#gelesen': True,
                 '#last_read': date(2026, m, 10), 'pages': 300}
             for i, m in enumerate((1, 2, 3, 4, 5), start=1)}
    speed = ers.reading_speed(make_db(books), '#gelesen', '#last_read',
                              today=TODAY)
    assert speed['status'] == ers.FORECAST_OK
    assert speed['months'] == 4
    assert speed['read_books'] == 4
    assert speed['known_books'] == 4
    assert speed['pages_per_month'] == pytest.approx(300.0)
    assert speed['pages_per_day'] == pytest.approx(300.0 / ers.DAYS_PER_MONTH)


def test_reading_speed_counts_idle_months_as_zero(make_db):
    books = {}
    for i, m in enumerate((1, 3, 4, 6, 7), start=1):
        books[i] = {'timestamp': date(2026, 1, 1), '#gelesen': True,
                    '#last_read': date(2026, m, 10), 'pages': 300}
    # January is the first month (excluded); the full months are
    # February to July, with no reading in February and May: six months,
    # 0, 300, 300, 0, 300, 300 pages.
    speed = ers.reading_speed(make_db(books), '#gelesen', '#last_read',
                              today=date(2026, 9, 15))
    assert speed['months'] == 6
    assert speed['pages_per_month'] == pytest.approx(225.0)
    assert speed['pages_per_month'] == pytest.approx(
        ers.trimmed_mean([0, 300, 300, 0, 300, 300]))


def test_reading_speed_reports_coverage(make_db):
    # A book without a usable read date counts at its date added.
    books = {i: {'timestamp': date(2026, 1, 1), '#gelesen': True,
                 '#last_read': date(2026, m, 10), 'pages': 300}
             for i, m in enumerate((1, 2, 3, 4), start=1)}
    # Two more read books in April, without a page count.
    books[5] = {'timestamp': date(2026, 1, 1), '#gelesen': True,
                '#last_read': date(2026, 4, 11)}
    books[6] = {'timestamp': date(2026, 1, 1), '#gelesen': True,
                '#last_read': date(2026, 4, 12), 'pages': None}
    speed = ers.reading_speed(make_db(books), '#gelesen', '#last_read',
                              today=TODAY)
    assert speed['status'] == ers.FORECAST_OK
    assert speed['read_books'] == 5
    assert speed['known_books'] == 3
    assert speed['pages_per_month'] == pytest.approx(300.0)


def test_reading_speed_dates_without_last_read_count_at_added(make_db):
    books = {i: {'timestamp': date(2026, m, 1), '#gelesen': True,
                 'pages': 300}   # no #last_read
             for i, m in enumerate((1, 2, 3, 4), start=1)}
    speed = ers.reading_speed(make_db(books), '#gelesen', '#last_read',
                              today=TODAY)
    assert speed['months'] == 3    # February to April, January is first
    assert speed['read_books'] == 3
    assert speed['pages_per_month'] == pytest.approx(300.0)


def test_reading_speed_none_below_minimum_months(make_db):
    books = {i: {'timestamp': date(2026, 1, 1), '#gelesen': True,
                 '#last_read': date(2026, m, 10), 'pages': 300}
             for i, m in enumerate((1, 2, 3), start=1)}
    speed = ers.reading_speed(make_db(books), '#gelesen', '#last_read',
                              today=TODAY)
    assert speed['status'] == ers.FORECAST_NONE
    assert speed['months'] == 2
    assert speed['pages_per_month'] is None


def test_reading_speed_without_read_books(make_db):
    db = make_db({1: {'timestamp': date(2026, 1, 1), '#gelesen': False}})
    speed = ers.reading_speed(db, '#gelesen', '#last_read', today=TODAY)
    assert speed == {'status': ers.FORECAST_NONE, 'months': 0,
                     'pages_per_month': None, 'pages_per_day': None,
                     'read_books': 0, 'known_books': 0, 'median_pages': None}


def test_reading_speed_uses_default_columns_and_today(make_db):
    db = make_db({1: {'timestamp': date(2026, 1, 1), '#gelesen': True,
                      '#last_read': date(2026, 2, 10), 'pages': 300}})
    speed = ers.reading_speed(db)   # default columns, today=date.today()
    assert set(speed) == {'status', 'months', 'pages_per_month',
                          'pages_per_day', 'read_books', 'known_books',
                          'median_pages'}


def test_reading_speed_estimates_missing_pages_with_the_median(make_db):
    books = {
        # Known page counts (100, 100, 300) give a median of 100.
        1: {'timestamp': date(2026, 1, 1), '#gelesen': True,
            '#last_read': date(2026, 1, 10), 'pages': 100},   # first month
        2: {'timestamp': date(2026, 1, 1), '#gelesen': True,
            '#last_read': date(2026, 2, 10), 'pages': 100},
        3: {'timestamp': date(2026, 1, 1), '#gelesen': True,
            '#last_read': date(2026, 3, 10), 'pages': 300},
        4: {'timestamp': date(2026, 1, 1), '#gelesen': True,
            '#last_read': date(2026, 4, 10)},   # no page count
    }
    speed = ers.reading_speed(make_db(books), '#gelesen', '#last_read',
                              today=TODAY)
    assert speed['median_pages'] == 100.0
    assert speed['known_books'] == 2
    assert speed['read_books'] == 3
    # February 100, March 300, April estimated with 100.
    assert speed['pages_per_month'] == pytest.approx(
        ers.trimmed_mean([100, 300, 100]))
