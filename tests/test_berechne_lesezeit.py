"""Tests für berechne_lesezeit()."""

from datetime import date, datetime

import export_lesestatus as ee


def test_leere_bibliothek(make_db):
    res = ee.berechne_lesezeit(make_db({}))
    assert res == {"punkte": [], "statistik": None, "ohne_daten": 0}


def test_ein_buch(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 1),
                      "#gelesen": True,
                      "#last_read": date(2024, 1, 11)}})
    res = ee.berechne_lesezeit(db)
    assert res["ohne_daten"] == 0
    assert res["punkte"] == [(date(2024, 1, 11), 10, 1)]
    assert res["statistik"] == {"anzahl": 1, "mittel": 10.0,
                                "median": 10.0, "min": 10, "max": 10}


def test_median_ungerade_anzahl(make_db):
    books = {
        1: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 6)},    # 5 Tage
        2: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 11)},   # 10 Tage
        3: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 31)},   # 30 Tage
    }
    stat = ee.berechne_lesezeit(make_db(books))["statistik"]
    assert stat == {"anzahl": 3, "mittel": 15.0, "median": 10.0,
                    "min": 5, "max": 30}


def test_median_gerade_anzahl(make_db):
    books = {
        1: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 6)},    # 5 Tage
        2: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 11)},   # 10 Tage
        3: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 21)},   # 20 Tage
        4: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 31)},   # 30 Tage
    }
    stat = ee.berechne_lesezeit(make_db(books))["statistik"]
    assert stat["median"] == 15.0
    assert stat["mittel"] == 16.25
    assert stat["min"] == 5
    assert stat["max"] == 30


def test_last_read_vor_added_wird_uebersprungen(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 10), "#gelesen": True,
                      "#last_read": date(2024, 1, 1)}})
    res = ee.berechne_lesezeit(db)
    assert res["punkte"] == []
    assert res["statistik"] is None
    assert res["ohne_daten"] == 1


def test_last_read_gleich_added_zaehlt_null_tage(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 10), "#gelesen": True,
                      "#last_read": date(2024, 1, 10)}})
    res = ee.berechne_lesezeit(db)
    assert res["punkte"] == [(date(2024, 1, 10), 0, 1)]
    assert res["statistik"]["min"] == 0
    assert res["statistik"]["max"] == 0


def test_ungelesene_buecher_werden_ignoriert(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 1), "#gelesen": False,
                      "#last_read": date(2024, 1, 11)}})
    res = ee.berechne_lesezeit(db)
    assert res["punkte"] == []
    assert res["ohne_daten"] == 0


def test_gelesen_ohne_last_read_zahlt_als_ohne_daten(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 1), "#gelesen": True,
                      "#last_read": None}})
    assert ee.berechne_lesezeit(db)["ohne_daten"] == 1


def test_gelesen_ohne_timestamp_zahlt_als_ohne_daten(make_db):
    db = make_db({1: {"timestamp": None, "#gelesen": True,
                      "#last_read": date(2024, 1, 11)}})
    assert ee.berechne_lesezeit(db)["ohne_daten"] == 1


def test_datetime_eingaben_werden_zu_date(make_db):
    db = make_db({1: {"timestamp": datetime(2024, 1, 1, 9, 0),
                      "#gelesen": True,
                      "#last_read": datetime(2024, 1, 11, 20, 0)}})
    res = ee.berechne_lesezeit(db)
    assert res["punkte"] == [(date(2024, 1, 11), 10, 1)]


def test_punkte_nach_lesedatum_sortiert(make_db):
    books = {
        1: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 3, 1)},    # 60 Tage (Schaltjahr)
        2: {"timestamp": date(2024, 1, 1), "#gelesen": True,
            "#last_read": date(2024, 1, 15)},   # 14 Tage
    }
    res = ee.berechne_lesezeit(make_db(books))
    assert res["punkte"] == [(date(2024, 1, 15), 14, 2),
                             (date(2024, 3, 1), 60, 1)]


def test_benutzerdefinierte_spaltennamen(make_db):
    db = make_db({1: {"timestamp": date(2024, 1, 1), "gelesen_ja": True,
                      "gelesen_am": date(2024, 1, 11)}})
    res = ee.berechne_lesezeit(db, spalte_gelesen="gelesen_ja",
                               spalte_last_read="gelesen_am")
    assert res["statistik"]["mittel"] == 10.0
