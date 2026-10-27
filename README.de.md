<div align="center">

# Reading Progress für calibre

**Sieh direkt in calibre, wie deine Bibliothek, deine gelesenen Bücher und dein Stapel ungelesener Bücher wachsen.**

[![Release](https://img.shields.io/github/v/release/dkuester/calibre-burn-up-chart?label=release)](https://github.com/dkuester/calibre-burn-up-chart/releases/latest)
[![CI](https://github.com/dkuester/calibre-burn-up-chart/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/dkuester/calibre-burn-up-chart/actions/workflows/ci.yml)
[![calibre](https://img.shields.io/badge/calibre-8.0%2B-informational)](#voraussetzungen)
[![Lizenz](https://img.shields.io/github/license/dkuester/calibre-burn-up-chart)](LICENSE)

[Installation](#installation) · [Funktionen](#funktionen) · [Einstellungen](#einstellungen) · [Entwicklung](#entwicklung) · [Änderungen](CHANGELOG.de.md) · [Roadmap](ROADMAP.de.md) · [English](README.md)

</div>

Reading Progress ist ein calibre-Plugin, das deinen Lesefortschritt als
Burn-up-Chart zeigt. Es rekonstruiert den Verlauf aus den Metadaten deiner
Bibliothek (Datum der Aufnahme und zwei benutzerdefinierte Spalten) und zeigt
Monat für Monat, wie sich Gesamtbestand, gelesene Bücher und Stapel
ungelesener Bücher (SuB/TBR) entwickelt haben, zurück bis zum ältesten Buch
der Bibliothek. Alles läuft innerhalb von calibre; eine eigene
Python-Installation ist nicht nötig.

---

## Funktionen

| Funktion | Beschreibung |
|---|---|
| **Burn-up-Chart** | Gesamtbestand, kumuliert gelesene Bücher und SuB im Zeitverlauf, als monatliche Stände. |
| **Zieldatum** | Eine Ziellinie „SuB = 0 am …“ mit frei wählbarem Datum. |
| **Sanfter Abbau** | Eine zweite, realistischere Referenzlinie, z. B. SuB bis zum Zieldatum halbiert (Faktor einstellbar). |
| **Nötiges Tempo** | Unter dem Titel: wie viele Bücher pro Monat man lesen oder höchstens kaufen darf, um das Ziel (SuB = 0 und sanfter Abbau) bis zum Zieldatum zu erreichen, gemessen an denselben typischen Kauf- und Leseraten wie die Prognose. |
| **Prognose** | Schreibt den heutigen SuB mit dem typischen Monat fort (Mittel der letzten 24 vollen Monate ohne die 20 % höchsten und niedrigsten, damit Sammel-Importe kaum zählen), gestrichelt, mit einem schattierten Band für 80 % der Fälle und der realistischen Monatsspanne für SuB = 0 – oder wie schnell er wächst. Braucht 3 volle Monate; unter 12 als vorläufig gekennzeichnet. |
| **Jahresziel** | Mit dem separat installierten Plugin [„Reading Goal“](https://www.mobileread.com/forums/showthread.php?t=355769): gelesene Listenbücher gegen das Soll über das Jahr, Hochrechnung, nötiges Tempo, Seiten, Monatswerte, Vorjahresvergleich und alle gelesenen Bücher aus den eigenen Daten. Die Daten von „Reading Goal“ werden nur gelesen. |
| **Kaufrate vs. Leserate** | Zugänge und gelesene Bücher pro Monat als Mittel über 12 Monate; die Fläche dazwischen zeigt, ob der SuB schrumpft oder wächst. |
| **Spalte „Tage im SuB“** | Ein Klick in den Einstellungen legt eine calibre-Spalte mit den Tagen jedes Buchs im SuB an, immer aktuell und sortierbar. |
| **Altersverteilung des SuB** | Ungelesene Bücher nach ganzen Jahren seit der Aufnahme; ein Klick auf einen Balken zeigt diese Bücher in calibre. |
| **Angefangene Reihen** | Angefangene, aber nicht beendete Reihen mit Fortschritt, dem nächsten ungelesenen Band und wann zuletzt aus der Reihe gelesen wurde, liegengebliebene zuerst; zeigt den nächsten Band in calibre. |
| **SuB nach Reihen** | Die 20 Reihen mit den meisten ungelesenen Büchern als Balken, mit ihrem Anteil am SuB; ein Klick auf einen Balken zeigt die ungelesenen Bücher der Reihe in calibre. |
| **SuB in der Statusleiste** | Dauerhaft „SuB: 1652 ▲172“ mit der Veränderung gegenüber vor 12 Monaten; Tooltip mit gelesen/gesamt und nötigem Tempo, Klick öffnet das Burn-up-Chart. Abschaltbar. |
| **Reihen zusammenfassen** | Eine Reihe unter mehreren Namen, z. B. mal auf Deutsch, mal auf Englisch gelesen (`Die Nebelgeborenen = Mistborn`), zählt in den Reihen-Auswertungen als eine; ein in einer Sprache gelesener Band gilt als gelesen. Gruppen aus der Datenqualität lassen sich mit einem Klick übernehmen. Die Seriennamen in calibre bleiben unverändert. |
| **Bericht** | Speichert die Kennzahlen als Markdown oder als einzelne HTML-Seite mit Burn-up- und Raten-Chart, mit „Reading Goal“ auch mit Jahresziel. |
| **Datenqualität** | Listet gelesene Bücher ohne Lesedatum oder mit Lesedatum vor der Aufnahme sowie Auffälligkeiten bei Reihen: eine Reihe unter mehreren Namen, doppelte Bandnummern und Lücken (ein früherer Band ungelesen, obwohl ein späterer gelesen ist), dazu Tage, die nach einem Sammel-Import aussehen (viele Bücher aus vielen Reihen und von vielen Autoren) und deren Aufnahmedatum vermutlich falsch ist. Zeigt die Bücher zum Korrigieren in der Bücherliste von calibre an. |
| **Leseverzögerung** | Für jedes gelesene Buch die Zeit zwischen Aufnahme in calibre und Lesen, als Streudiagramm mit Median und Mittelwert; Tooltip nennt das Buch, Klick zeigt es in calibre. |
| **Zeitraum** | Alles zeigen oder nur die letzten 5 bzw. 2 Jahre bis heute. |
| **Interaktiv** | Tooltips in jedem Chart. Im Burn-up- und im Verzögerungs-Chart Zoom per Mausrad, Verschieben per Ziehen, Doppelklick setzt zurück. |
| **Export** | Jedes Chart als PNG speichern oder in die Zwischenablage kopieren, genau wie angezeigt (Zoom, Verschiebung, Theme). |
| **Eigene Farben, passendes Theme** | Jede Datenreihe und Referenzlinie lässt sich umfärben. Die Charts folgen dem hellen oder dunklen Theme von calibre. |
| **Zweisprachig** | Deutsche und englische Oberfläche, je nach Sprache von calibre. Weitere Sprachen lassen sich unter `translations/<lang>/` ergänzen. |

## Voraussetzungen

- calibre 8.0 oder neuer
- Zwei benutzerdefinierte Spalten in der Bibliothek (Namen in den Einstellungen änderbar):

| Spalte | Typ | Zweck |
|---|---|---|
| `#gelesen` | Ja/Nein | Markiert ein Buch als gelesen |
| `#last_read` | Datum | Datum, an dem das Buch zuletzt gelesen wurde |

## Installation

1. `ReadingProgress-<version>.zip` aus dem [neuesten Release](https://github.com/dkuester/calibre-burn-up-chart/releases/latest) herunterladen.
2. In calibre: *Einstellungen → Erweitert → Erweiterungen → Erweiterung aus Datei laden*, die ZIP auswählen.
3. calibre neu starten.
4. Den Knopf zur Werkzeugleiste hinzufügen: *Einstellungen → Benutzeroberfläche →
   Werkzeugleisten & Menüs → Die Hauptwerkzeugleiste*, dort **Burn-up-Chart**
   aus den verfügbaren Aktionen hinzufügen.

> [!TIP]
> Die Installation aus einem Klon geht auch:
> `calibre-customize -b <pfad-zum-klon>/readingprogress`.

## Benutzung

Der Knopf in der Werkzeugleiste öffnet ein Menü mit vier Charts (fünf mit „Reading Goal“), einer Datenprüfung und einem Bericht:

- **Burn-up-Chart**: Bestand, gelesene Bücher und SuB im Zeitverlauf.
- **Jahresziel**: Fortschritt der Jahresliste des Plugins „Reading Goal“ gegenüber dem Soll. Erscheint nur, wenn das Plugin Daten für die aktuelle Bibliothek hat.
- **Zeit zwischen Kauf und Lesen**: die Leseverzögerung pro Buch.
- **Kaufrate vs. Leserate**: Zugänge und gelesene Bücher pro Monat.
- **Altersverteilung des SuB**: ungelesene Bücher nach Jahren seit der Aufnahme.
- **Angefangene Reihen**: angefangene, aber nicht beendete Reihen mit dem nächsten Band.
- **SuB nach Reihen**: die Reihen mit den meisten ungelesenen Büchern.
- **Datenqualität prüfen**: gelesene Bücher ohne brauchbares Lesedatum und Auffälligkeiten bei Reihen (mehrere Namen, doppelte Bandnummern, Lücken) sowie Sammel-Import-Tage, um sie in calibre zu korrigieren; Reihen unter mehreren Namen lassen sich dort zusammenfassen.
- **Bericht speichern…**: die Kennzahlen als Markdown oder als HTML-Seite mit Charts.

Rechts in der Statusleiste steht dauerhaft der SuB, z. B. „SuB: 1652 ▲172“
(Pfeil: Veränderung gegenüber vor 12 Monaten). Der Tooltip nennt
gelesen/gesamt und das nötige Tempo, ein Klick öffnet das Burn-up-Chart.

## Einstellungen

*Einstellungen → Erweitert → Erweiterungen → Reading Progress → Erweiterung anpassen*:

| Einstellung | Bedeutung |
|---|---|
| Zieldatum | Der Tag, an dem der SuB 0 erreichen soll. |
| Sanfter Abbau (Faktor) | Anteil des SuB, der am Zieldatum übrig ist. `0.50` heißt: bis dahin halbiert. |
| Prognoselinie anzeigen | Zeichnet die Prognoselinie mit Unsicherheitsband und Hinweis (standardmäßig an). |
| SuB in der Statusleiste anzeigen | Zeigt den SuB der ganzen Bibliothek rechts in der Statusleiste von calibre (standardmäßig an). |
| Farben | Farbe jeder Datenreihe und Referenzlinie. Leer heißt „dem Theme folgen“; *Farben auf Theme-Standard zurücksetzen* entfernt alle eigenen Farben. |
| Benutzerdefinierte Spalte „gelesen“ / „zuletzt gelesen“ | Suchnamen der beiden Spalten, falls deine anders heißen. |
| Spalte „Tage im SuB“ anlegen | Legt eine Spalte `#days_in_tbr` an, die calibre selbst berechnet: bei gelesenen Büchern die Tage zwischen Aufnahme und Lesen, bei ungelesenen die Tage seit der Aufnahme. Danach sortiert findest du die Bücher, die du am längsten besitzt, ohne sie gelesen zu haben. Danach calibre neu starten. |
| Reihen zusammenfassen | Eine Reihe pro Zeile, ihre Namen in calibre mit `=` getrennt, z. B. `Die Nebelgeborenen = Mistborn`. Angezeigt wird der erste Name. „Angefangene Reihen“, „SuB nach Reihen“, die Reihen-Prüfung und der Bericht zählen sie als eine Reihe. |

Die Einstellungen liegen in `plugins/readingprogress.json` im
Konfigurationsordner von calibre und bleiben über Neustarts erhalten.

## Entwicklung

```bash
git clone https://github.com/dkuester/calibre-burn-up-chart.git
cd calibre-burn-up-chart
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest      # Tests, Mindest-Coverage wird geprüft
.venv/bin/ruff check .          # Lint
```

Die CI führt ruff und pytest (Python 3.10 und 3.12) bei jedem Push auf `main`
und jedem Pull-Request aus.

<details>
<summary><strong>Projektstruktur</strong></summary>

```
readingprogress/
├── __init__.py              # Plugin-Metadaten, Version
├── main.py                  # GUI-Einbindung (Aktion, Menü)
├── config_dialog.py         # Einstellungsdialog
├── config_helpers.py        # Qt-freie Konfigurations-, Locale- und Migrationshilfen
├── chart_common.py          # Qt-freie Chart-Berechnung und Farben
├── age_dialog.py            # Dialog für die Altersverteilung des SuB
├── chart_dialog.py          # Burn-up-Chart-Dialog (QPainter)
├── goal_dialog.py           # Dialog für das Jahresziel
├── import_days.py           # Qt-frei, erkennt Sammel-Import-Tage
├── quality_dialog.py        # Dialog für die Datenqualität
├── rates_dialog.py          # Dialog für Kaufrate vs. Leserate
├── reading_goal.py          # Qt-frei, liest die Daten von „Reading Goal“ (nur lesend)
├── report.py                # Qt-freier Markdown-/HTML-Bericht
├── series.py                # Qt-frei, Reihen-Daten, Reihen zusammenfassen, Reihen-Prüfung, angefangene Reihen, SuB nach Reihen
├── series_backlog_dialog.py # Dialog für SuB nach Reihen
├── status_summary.py        # Qt-frei, Text und Tooltip des SuB in der Statusleiste
├── started_dialog.py        # Dialog für die angefangenen Reihen
├── delay_dialog.py          # Dialog für die Leseverzögerung
├── export_reading_status.py # liest die laufende calibre-Datenbank
├── localization.py          # gettext-Setup
├── images/icon.png
└── translations/de/LC_MESSAGES/readingprogress.{po,mo}
tests/                       # pytest-Suite
```

`export_reading_status.py` läuft im calibre-Prozess und nutzt die laufende
Datenbank (`self.gui.current_db.new_api`). Die Charts zeichnet Qts QPainter.

</details>

<details>
<summary><strong>Release erstellen</strong></summary>

Das Plugin folgt [Semantic Versioning](https://semver.org/). Die Version ist das
Tupel `__version__` in `readingprogress/__init__.py`.

1. `__version__` anheben und einen Eintrag in [CHANGELOG.md](CHANGELOG.md) und
   [CHANGELOG.de.md](CHANGELOG.de.md) ergänzen.
2. Per Pull-Request nach `main` mergen.
3. Den Merge-Commit taggen: `git tag -a v1.7.0 -m "…" && git push origin v1.7.0`.
4. Die CI baut `ReadingProgress-<version>.zip` und veröffentlicht das Release.

</details>

## Support

| | |
|---|---|
| Fehler und Ideen | [Issues](https://github.com/dkuester/calibre-burn-up-chart/issues). Bitte calibre-Version und Betriebssystem angeben. |
| Downloads und Änderungen | [Releases](https://github.com/dkuester/calibre-burn-up-chart/releases) · [CHANGELOG.de.md](CHANGELOG.de.md) |
| Geplante Funktionen | [ROADMAP.de.md](ROADMAP.de.md) |
| Frühere Historie | Pull-Requests bis v1.6.0 liegen im [archivierten Codeberg-Repo](https://codeberg.org/hortizept/calibre-burn-up-chart). |
| Mitwirken | Pull-Requests gegen `main`; die CI muss grün sein. |

## KI-Unterstützung

Dieses Plugin wird mit Hilfe von KI-Programmierassistenten entwickelt.
Entwurfsentscheidungen, Review und Tests in calibre liegen bei einem Menschen.

## Lizenz

[GNU General Public License v3.0](LICENSE)
