"""Tests für die reinen Hilfsfunktionen."""

from datetime import date, datetime

import export_lesestatus as ee


def test_to_date_none():
    assert ee.to_date(None) is None


def test_to_date_aus_date():
    assert ee.to_date(date(2024, 1, 15)) == date(2024, 1, 15)


def test_to_date_aus_datetime():
    assert ee.to_date(datetime(2024, 1, 15, 10, 30)) == date(2024, 1, 15)


def test_to_date_aus_fremdtyp():
    assert ee.to_date("2024-01-15") is None


def test_monatsende():
    assert ee.monatsende(2024, 1) == date(2024, 1, 31)
    assert ee.monatsende(2024, 4) == date(2024, 4, 30)


def test_monatsende_schaltjahr():
    assert ee.monatsende(2024, 2) == date(2024, 2, 29)
    assert ee.monatsende(2023, 2) == date(2023, 2, 28)
