"""Tests for the pure helper functions."""

import csv
import os
from datetime import date, datetime

import export_reading_status as ers


def test_to_date_none():
    assert ers.to_date(None) is None


def test_to_date_from_date():
    assert ers.to_date(date(2024, 1, 15)) == date(2024, 1, 15)


def test_to_date_from_datetime():
    assert ers.to_date(datetime(2024, 1, 15, 10, 30)) == date(2024, 1, 15)


def test_to_date_from_other_type():
    assert ers.to_date("2024-01-15") is None


def test_month_end():
    assert ers.month_end(2024, 1) == date(2024, 1, 31)
    assert ers.month_end(2024, 4) == date(2024, 4, 30)


def test_month_end_leap_year():
    assert ers.month_end(2024, 2) == date(2024, 2, 29)
    assert ers.month_end(2023, 2) == date(2023, 2, 28)


def test_write_csv(tmp_path):
    log_path = str(tmp_path / 'sub' / 'log.csv')
    rows = [(date(2024, 1, 31), 10, 5, 5), (date(2024, 2, 29), 12, 7, 5)]
    ers._write_csv(log_path, rows)
    assert os.path.exists(log_path)
    assert not os.path.exists(log_path + '.tmp')   # atomic replace done
    with open(log_path, newline='', encoding='utf-8') as f:
        data = list(csv.reader(f))
    assert data == [
        ['date', 'total', 'read', 'backlog'],
        ['2024-01-31', '10', '5', '5'],
        ['2024-02-29', '12', '7', '5'],
    ]
