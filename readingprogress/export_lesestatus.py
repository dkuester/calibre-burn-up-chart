#!/usr/bin/env python3
"""
Liest den Lesestatus aus einer Calibre-Bibliothek.

Als Modul:   from ... import exportiere;  exportiere(db_api, ...)
Standalone:  calibre-debug -e export_lesestatus.py

Die Funktion exportiere() liefert die monatlichen Snapshots als Liste
von (date, gesamt, gelesen, backlog)-Tupeln zurück. Eine CSV-Datei wird
nur geschrieben, wenn explizit ein log_pfad übergeben wird.
"""

import csv
import os
import warnings
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime

warnings.filterwarnings(
    "ignore", category=SyntaxWarning,
    module=r"calibre_plugins\.kobo_metadata")

# --- Konfiguration ---
SPALTE_GELESEN   = "#gelesen"
SPALTE_LAST_READ = "#last_read"

# Nur für den Standalone-Betrieb via calibre-debug -e
STANDALONE_LIBRARY = os.path.expanduser("~/Calibre-Bibliothek")
STANDALONE_LOG     = "/tmp/burndown_log.csv"


def to_date(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return None


def monatsende(jahr, monat):
    return date(jahr, monat, monthrange(jahr, monat)[1])


def _schreibe_csv(log_pfad, rows):
    """Schreibt die Snapshots als CSV (für Debug-Zwecke)."""
    ziel_dir = os.path.dirname(log_pfad)
    if ziel_dir:
        os.makedirs(ziel_dir, exist_ok=True)
    tmp = log_pfad + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["datum", "gesamt", "gelesen", "backlog"])
        for r in rows:
            w.writerow([r[0].isoformat(), r[1], r[2], r[3]])
    os.replace(tmp, log_pfad)


def exportiere(db_api, spalte_gelesen=None, spalte_last_read=None,
               log_pfad=None, heute=None):
    """
    Liest die Bibliothek und liefert die monatlichen Snapshots.

    :param db_api:           Calibre ``new_api``-Instanz
    :param spalte_gelesen:   Name der Ja/Nein-Spalte (Default: '#gelesen')
    :param spalte_last_read: Name der Datum-Spalte (Default: '#last_read')
    :param log_pfad:         Optionaler CSV-Pfad (nur für Debug)
    :param heute:            Referenzdatum (Default: date.today()); nur für
                             Tests und Zeitraum-Auswahl nötig
    :return: dict mit 'rows' (Liste von Tupeln) und Diagnosezählern
    """
    if spalte_gelesen is None:
        spalte_gelesen = SPALTE_GELESEN
    if spalte_last_read is None:
        spalte_last_read = SPALTE_LAST_READ

    alle_ids = db_api.all_book_ids()
    added_map     = db_api.all_field_for("timestamp", alle_ids)
    gelesen_map   = db_api.all_field_for(spalte_gelesen, alle_ids)
    last_read_map = db_api.all_field_for(spalte_last_read, alle_ids)

    added_events = defaultdict(int)
    read_events  = defaultdict(int)

    ohne_timestamp      = 0
    ohne_last_read      = 0
    last_read_vor_added = 0

    for book_id in alle_ids:
        added     = to_date(added_map.get(book_id))
        gelesen   = gelesen_map.get(book_id) is True
        last_read = to_date(last_read_map.get(book_id))

        if added is None:
            ohne_timestamp += 1
            continue
        added_events[added] += 1

        if gelesen:
            if last_read is None:
                ohne_last_read += 1
                read_events[added] += 1
            elif last_read < added:
                last_read_vor_added += 1
                read_events[added] += 1
            else:
                read_events[last_read] += 1

    events = []
    for d, n in added_events.items():
        events.append((d, "added", n))
    for d, n in read_events.items():
        events.append((d, "read", n))
    events.sort()

    if not events:
        raise RuntimeError("No usable events found.")

    if heute is None:
        heute = date.today()

    monat_keys = {(d.year, d.month) for (d, _, _) in events}
    monat_keys.add((heute.year, heute.month))
    monate = sorted(monat_keys)

    idx = 0
    current_added = 0
    current_read  = 0
    rows = []

    for (y, m) in monate:
        ende = monatsende(y, m)
        if ende > heute:
            ende = heute
        while idx < len(events) and events[idx][0] <= ende:
            _, typ, n = events[idx]
            if typ == "added":
                current_added += n
            else:
                current_read += n
            idx += 1
        rows.append((ende, current_added, current_read,
                     current_added - current_read))

    if log_pfad:
        _schreibe_csv(log_pfad, rows)

    letzter = rows[-1]
    return {
        "rows":               rows,
        "monatswerte":        len(rows),
        "gesamt":             letzter[1],
        "gelesen":            letzter[2],
        "backlog":            letzter[3],
        "ohne_timestamp":     ohne_timestamp,
        "ohne_last_read":     ohne_last_read,
        "last_read_vor_added": last_read_vor_added,
    }


if __name__ == "__main__":
    from calibre.library import db as calibre_db_factory

    api = calibre_db_factory(STANDALONE_LIBRARY).new_api
    info = exportiere(api, log_pfad=STANDALONE_LOG)

    print(f"{info['monatswerte']} monthly snapshots written to "
          f"{STANDALONE_LOG}")
    print(f"Currently: {info['gelesen']}/{info['gesamt']} read "
          f"| backlog: {info['backlog']}")
    if info["ohne_timestamp"]:
        print(f"Note: {info['ohne_timestamp']} books without timestamp "
              f"skipped.")
    if info["ohne_last_read"]:
        print(f"Note: {info['ohne_last_read']} read books without "
              f"#last_read recorded at timestamp.")
    if info["last_read_vor_added"]:
        print(f"Note: {info['last_read_vor_added']} books with "
              f"last_read < timestamp recorded at timestamp.")

def berechne_lesezeit(db_api, spalte_gelesen=None, spalte_last_read=None):
    """
    Berechnet für jedes gelesene Buch die Zeitspanne zwischen Hinzufügen
    (timestamp) und Lesen (#last_read).

    :return: dict mit
        - punkte: Liste von (lese_datum, tage_bis_gelesen, book_id)
        - statistik: dict(anzahl, mittel, median, min, max) oder None
        - ohne_daten: Anzahl gelesener Bücher ohne verwertbare Daten
    """
    if spalte_gelesen is None:
        spalte_gelesen = SPALTE_GELESEN
    if spalte_last_read is None:
        spalte_last_read = SPALTE_LAST_READ

    alle_ids = db_api.all_book_ids()
    added_map     = db_api.all_field_for("timestamp", alle_ids)
    gelesen_map   = db_api.all_field_for(spalte_gelesen, alle_ids)
    last_read_map = db_api.all_field_for(spalte_last_read, alle_ids)

    punkte = []
    ohne_daten = 0

    for book_id in alle_ids:
        if gelesen_map.get(book_id) is not True:
            continue
        added     = to_date(added_map.get(book_id))
        last_read = to_date(last_read_map.get(book_id))
        if added is None or last_read is None:
            ohne_daten += 1
            continue
        if last_read < added:
            # Inkonsistenz – überspringen
            ohne_daten += 1
            continue
        tage = (last_read - added).days
        punkte.append((last_read, tage, book_id))

    punkte.sort()

    if not punkte:
        return {"punkte": [], "statistik": None, "ohne_daten": ohne_daten}

    werte = sorted(p[1] for p in punkte)
    n = len(werte)
    if n % 2 == 1:
        median = float(werte[n // 2])
    else:
        median = (werte[n // 2 - 1] + werte[n // 2]) / 2.0

    statistik = {
        "anzahl": n,
        "mittel": sum(werte) / n,
        "median": median,
        "min":    werte[0],
        "max":    werte[-1],
    }
    return {
        "punkte":    punkte,
        "statistik": statistik,
        "ohne_daten": ohne_daten,
    }