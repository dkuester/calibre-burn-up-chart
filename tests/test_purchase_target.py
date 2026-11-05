"""Tests for purchase_adherence() and pace_for_target()."""

from datetime import date, timedelta

import export_reading_status as ers
import pytest


def _rates(added_per_month):
    """compute_rates()-style rows, one per month from January 2024 on,
    each dated at the month's end."""
    rates = []
    for i, added in enumerate(added_per_month):
        day = ers.month_end(2024 + i // 12, i % 12 + 1)
        rates.append((day, added, 0, 0.0, 0.0))
    return rates


def test_purchase_adherence_basic():
    # Full months exclude January (the first); February to April count.
    adh = ers.purchase_adherence(_rates([10, 20, 30, 40]), 20.0)
    assert adh['status'] == ers.FORECAST_OK
    assert adh['months'] == 3
    assert adh['actual'] == pytest.approx(30.0)
    assert adh['difference'] == pytest.approx(10.0)
    assert adh['over_plan'] == pytest.approx(30.0)   # 0 + 10 + 20
    assert adh['over_months'] == 2


def test_purchase_adherence_window():
    adh = ers.purchase_adherence(_rates([0, 1, 2, 3, 4, 5]), 2.0, window=2)
    assert adh['months'] == 2
    assert adh['actual'] == pytest.approx(4.5)        # May and June


def test_purchase_adherence_under_target():
    adh = ers.purchase_adherence(_rates([10, 1, 1, 1]), 2.0)
    assert adh['over_plan'] == 0
    assert adh['over_months'] == 0
    assert adh['difference'] == pytest.approx(-1.0)


def test_purchase_adherence_trims_outliers():
    # Full months: 5, 5, 5, 200 (a partner's bulk day).
    adh = ers.purchase_adherence(_rates([0, 5, 5, 5, 200]), 2.0)
    assert adh['actual'] == pytest.approx(5.0)          # trimmed mean
    # The spike still counts in full as 'over plan'.
    assert adh['over_plan'] == pytest.approx(3 * 3 + 198)


def test_purchase_adherence_without_full_months():
    rates = [(date(2024, 1, 15), 5, 0, 0.0, 0.0)]   # not a month end
    adh = ers.purchase_adherence(rates, 2.0)
    assert adh['status'] == ers.FORECAST_NONE
    assert adh['months'] == 0
    assert adh['actual'] is None


def test_purchase_adherence_empty():
    adh = ers.purchase_adherence([], 2.0)
    assert adh['status'] == ers.FORECAST_NONE


TODAY = date(2026, 10, 26)
TARGET = date(2050, 9, 4)


def _months():
    return (TARGET - TODAY).days / ers.DAYS_PER_MONTH


def test_pace_for_target():
    pace = ers.pace_for_target(1000, 2.0, TODAY, TARGET)
    assert pace['status'] == ers.PACE_OK
    assert pace['added_rate'] == 2.0
    assert pace['months'] == pytest.approx(_months())
    assert pace['reduction'] == pytest.approx(1000 / _months())
    assert pace['read_needed'] == pytest.approx(2.0 + 1000 / _months())


def test_pace_for_target_reached():
    pace = ers.pace_for_target(0, 2.0, TODAY, TARGET)
    assert pace['status'] == ers.PACE_REACHED
    assert pace['read_needed'] == 0.0


def test_pace_for_target_too_close():
    pace = ers.pace_for_target(100, 2.0, TODAY, TODAY + timedelta(days=10))
    assert pace['status'] == ers.PACE_TOO_CLOSE
    assert pace['read_needed'] is None


def test_pace_for_target_generalises_the_extremes():
    rates = {'status': ers.FORECAST_OK, 'months': 24, 'added': 3.0,
             'read': 1.0, 'spread': 0.0}
    base = ers.required_pace(1000, rates, TODAY, TARGET)
    at_added = ers.pace_for_target(1000, rates['added'], TODAY, TARGET)
    at_max = ers.pace_for_target(1000, base['max_added'], TODAY, TARGET)
    # Buying as before → the same reading rate as 'only read more';
    # buying the maximum → reading stays at the typical rate.
    assert at_added['read_needed'] == pytest.approx(base['read_needed'])
    assert at_max['read_needed'] == pytest.approx(rates['read'])
