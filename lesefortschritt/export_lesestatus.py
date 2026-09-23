#!/usr/bin/env python3
"""
Liest den Lesestatus aus einer Calibre-Bibliothek und schreibt monatliche
Snapshots als CSV.

Als Modul:   from ... import exportiere;  exportiere(db_api)
Standalone:  calibre-debug -e export_lesestatus.py
"""

import csv
import os
import warnings
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime

warnings.filterwarnings("ignore", category=SyntaxWarning)

# --- Konfiguration ---
LOG              = "/tmp/burndown_log.csv"
SPALTE_GELESEN   = "#gelesen"
SPALTE_LAST_READ = "#last_read"

# Nur für den Standalone-Betrieb via calibre-debug -e
STANDALONE_LIBRARY = os.path.expanduser("~/Calibre-Bibliothek")


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


def exportiere(db_api, log_pfad=None):
    if log_pfad is None:
        log_pfad = LOG

    alle_ids = db_api.all_book_ids()
    added_map     = db_api.all_field_for("timestamp", alle_ids)
    gelesen_map   = db_api.all_field_for(SPALTE_GELESEN, alle_ids)
    last_read_map = db_api.all_field_for(SPALTE_LAST_READ, alle_ids)

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
        raise RuntimeError("Keine verwertbaren Ereignisse gefunden.")

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

    letzter = rows[-1]
    return {
        "log_pfad":           log_pfad,
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
    info = exportiere(api)

    print(f"{info['monatswerte']} Monatswerte geschrieben nach {info['log_pfad']}")
    print(f"Aktuell: {info['gelesen']}/{info['gesamt']} gelesen "
          f"| Backlog: {info['backlog']}")
    if info["ohne_timestamp"]:
        print(f"Hinweis: {info['ohne_timestamp']} Bücher ohne timestamp "
              f"übersprungen.")
    if info["ohne_last_read"]:
        print(f"Hinweis: {info['ohne_last_read']} gelesene Bücher ohne "
              f"#last_read am timestamp verbucht.")
    if info["last_read_vor_added"]:
        print(f"Hinweis: {info['last_read_vor_added']} Bücher mit "
              f"last_read < timestamp am timestamp verbucht.")