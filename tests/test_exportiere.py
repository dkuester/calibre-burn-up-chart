"""Tests für exportiere()."""

from datetime import date

import export_lesestatus as ee
import pytest


def test_kumulative_snapshots_ueber_monate(make_db):
    heute = date(2024, 3, 15)
    books = {
        1: {"timestamp": date(2024, 1, 10), "#gelesen": True,
            "#last_read": date(2024, 2, 5)},
        2: {"timestamp": date(2024, 2, 20), "#gelesen": False},
        3: {"timestamp": date(2024, 3, 1), "#gelesen": True,
            "#last_read": date(2024, 3, 10)},
    }
    res = ee.exportiere(make_db(books), heute=heute)
    assert res["rows"] == [
        (date(2024, 1, 31), 1, 0, 1),
        (date(2024, 2, 29), 2, 1, 1),
        (date(2024, 3, 15), 3, 2, 1),
    ]
    assert res["gesamt"] == 3
    assert res["gelesen"] == 2
    assert res["backlog"] == 1
    assert res["monatswerte"] == 3


def test_monatsgrenze(make_db):
    heute = date(2024, 2, 15)
    books = {
        1: {"timestamp": date(2024, 1, 31), "#gelesen": False},
        2: {"timestamp": date(2024, 2, 1), "#gelesen": False},
    }
    rows = ee.exportiere(make_db(books), heute=heute)["rows"]
    # Januar: nur das Buch vom 31.  Februar: beide Bücher.
    assert rows[0][1] == 1
    assert rows[1][1] == 2


def test_read_event_wird_richtig_verbucht(make_db):
    heute = date(2024, 3, 31)
    books = {
        1: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": None},                       # am timestamp
        2: {"timestamp": date(2024, 2, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 15)},          # vor timestamp
        3: {"timestamp": date(2024, 3, 1), "#gelesen": True,
            "#last_read": date(2024, 3, 20)},          # am last_read
    }
    res = ee.exportiere(make_db(books), heute=heute)
    assert res["ohne_last_read"] == 1
    assert res["last_read_vor_added"] == 1
    assert res["ohne_timestamp"] == 0
    assert res["gesamt"] == 3
    assert res["gelesen"] == 3
    assert res["backlog"] == 0


def test_aktueller_monat_auch_ohne_events(make_db):
    heute = date(2024, 5, 20)
    db = make_db({1: {"timestamp": date(2024, 1, 5), "#gelesen": False}})
    rows = ee.exportiere(db, heute=heute)["rows"]
    assert rows[-1] == (date(2024, 5, 20), 1, 0, 1)
    assert len(rows) == 2


def test_ohne_timestamp_wird_gezaehlt(make_db):
    books = {
        1: {"timestamp": date(2024, 1, 1), "#gelesen": False},
        2: {"timestamp": None, "#gelesen": True,
            "#last_read": date(2024, 1, 5)},
    }
    res = ee.exportiere(make_db(books), heute=date(2024, 2, 1))
    assert res["ohne_timestamp"] == 1
    assert res["gesamt"] == 1


def test_keine_verwertbaren_events(make_db):
    with pytest.raises(RuntimeError):
        ee.exportiere(make_db({}), heute=date(2024, 1, 1))


def test_alle_ohne_timestamp_wirft(make_db):
    db = make_db({1: {"timestamp": None, "#gelesen": True}})
    with pytest.raises(RuntimeError):
        ee.exportiere(db, heute=date(2024, 1, 1))


def test_benutzerdefinierte_spaltennamen(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 1), "gelesen_ja": True,
                      "gelesen_am": date(2024, 1, 10)}})
    res = ee.exportiere(db, spalte_gelesen="gelesen_ja",
                        spalte_last_read="gelesen_am",
                        heute=date(2024, 2, 1))
    assert res["gelesen"] == 1
    assert res["backlog"] == 0


def test_log_pfad_schreibt_csv(make_db, tmp_path):
    db = make_db({1: {"timestamp": date(2024, 1, 1), "#gelesen": False}})
    pfad = tmp_path / "out.csv"
    ee.exportiere(db, log_pfad=str(pfad), heute=date(2024, 2, 1))
    content = pfad.read_text(encoding="utf-8")
    assert "datum,gesamt,gelesen,backlog" in content
    assert "2024-01-31,1,0,1" in content


def test_ohne_heute_parameter_nimmt_date_today(make_db):
    db = make_db({1: {"timestamp": date(2000, 1, 1), "#gelesen": False}})
    res = ee.exportiere(db)
    assert res["rows"][-1][0] == date.today()
