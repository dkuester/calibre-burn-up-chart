#!/usr/bin/env python3
"""
Zeichnet das Burn-up-Chart aus der CSV burndown_log.csv.

Ausführen mit: python3 zeichne_chart.py [--log-pfad PFAD]
                                        [--ziel-datum YYYY-MM-DD]
                                        [--abbau-faktor 0.0..1.0]
                                        [--ausgabe-pfad PFAD]
                                        [--translation-mo PFAD]
Voraussetzung: matplotlib (brew install python-matplotlib)
"""

import argparse
import csv
import gettext
import os
from datetime import date, datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- Konfiguration (Defaults, per CLI überschreibbar) ---
LOG_DEFAULT          = "/tmp/burndown_log.csv"
CHART_DEFAULT        = "/tmp/lesefortschritt.png"
ZIEL_DATUM_DEFAULT   = date(2050, 9, 4)
ABBAU_FAKTOR_DEFAULT = 0.5

# --- Kommandozeilenargumente ---
parser = argparse.ArgumentParser()
parser.add_argument(
    '--log-pfad', default=LOG_DEFAULT,
    help='Pfad zur CSV-Datei (Default: %(default)s)')
parser.add_argument(
    '--ziel-datum', default=ZIEL_DATUM_DEFAULT.isoformat(),
    help='Zieldatum im Format YYYY-MM-DD (Default: %(default)s)')
parser.add_argument(
    '--abbau-faktor', type=float, default=ABBAU_FAKTOR_DEFAULT,
    help='Anteil des SuB, der am Zieldatum übrig bleibt '
         '(Default: %(default)s)')
parser.add_argument(
    '--ausgabe-pfad', default=CHART_DEFAULT,
    help='Zielpfad der PNG-Datei (Default: %(default)s)')
parser.add_argument(
    '--translation-mo', default=None,
    help='Pfad zur kompilierten .mo-Übersetzungsdatei (optional)')
args = parser.parse_args()

# --- Übersetzung laden ---
if args.translation_mo and os.path.exists(args.translation_mo):
    with open(args.translation_mo, 'rb') as f:
        _ = gettext.GNUTranslations(f).gettext
else:
    _ = lambda s: s


LOG          = args.log_pfad
ZIEL_DATUM   = datetime.fromisoformat(args.ziel_datum).date()
ABBAU_FAKTOR = args.abbau_faktor
CHART        = args.ausgabe_pfad

# --- CSV einlesen ---
if not os.path.exists(LOG):
    raise SystemExit(f"Log file not found: {LOG}")

daten = []
with open(LOG, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        daten.append((
            datetime.fromisoformat(row["datum"]).date(),
            int(row["gesamt"]),
            int(row["gelesen"]),
            int(row["backlog"]),
        ))

if len(daten) < 2:
    raise SystemExit("Not enough data points for a chart.")

tage    = [d[0] for d in daten]
gesamt  = [d[1] for d in daten]
gelesen = [d[2] for d in daten]
backlog = [d[3] for d in daten]

heute            = tage[-1]
heutiger_backlog = backlog[-1]

ziel_sanft   = heutiger_backlog * ABBAU_FAKTOR
ziel_sanft_i = round(ziel_sanft)

datum_str   = ZIEL_DATUM.strftime('%d.%m.%Y')
jahr_str    = ZIEL_DATUM.strftime('%Y')

# --- Chart aufbauen ---
fig, ax = plt.subplots(figsize=(13, 7))

ax.plot(tage, gesamt,  label=_("Total library"),
        color="#888888", linewidth=1.6)
ax.plot(tage, gelesen, label=_("Read (cumulative)"),
        color="#2a9d8f", linewidth=2.0)
ax.plot(tage, backlog, label=_("Backlog (TBR)"),
        color="#e76f51", linewidth=2.3)

ax.plot([heute, ZIEL_DATUM], [heutiger_backlog, 0],
        linestyle="--", color="#264653", linewidth=2,
        label=_("Goal: TBR = 0 on {date}").format(date=datum_str))

ax.plot([heute, ZIEL_DATUM], [heutiger_backlog, heutiger_backlog],
        linestyle=":", color="#f4a261", linewidth=1.8,
        label=_("Constant library (buy rate = read rate)"))

ax.plot([heute, ZIEL_DATUM], [heutiger_backlog, ziel_sanft],
        linestyle="-.", color="#8ecae6", linewidth=1.8,
        label=_("Gentle reduction to TBR = {tbr} by {year}").format(
            tbr=ziel_sanft_i, year=jahr_str))

ax.annotate(
    _("Today: {count} unread").format(count=heutiger_backlog),
    xy=(heute, heutiger_backlog),
    xytext=(-160, 40), textcoords="offset points",
    arrowprops=dict(arrowstyle="->", color="#333"),
    fontsize=10, color="#333",
    bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#ccc"),
)

ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_xlim(tage[0], ZIEL_DATUM)
ax.set_ylim(bottom=0)
ax.set_ylabel(_("Number of books"))
ax.set_xlabel(_("Year"))

titel = _("Reading progress for TBR = {tbr} on {date}").format(
    tbr=ziel_sanft_i, date=datum_str)
ax.set_title(titel, fontsize=14, pad=15)

ax.grid(alpha=0.25)
ax.legend(loc="upper left", framealpha=0.95)

plt.tight_layout()
plt.savefig(CHART, dpi=150)
plt.close(fig)
print(f"Chart saved: {CHART}")