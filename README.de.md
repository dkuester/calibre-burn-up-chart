<div align="center">

# Reading Progress für calibre

**Sieh direkt in calibre, wie deine Bibliothek, deine gelesenen Bücher und dein Stapel ungelesener Bücher wachsen.**

[![Release](https://img.shields.io/github/v/release/dkuester/calibre-burn-up-chart?label=release)](https://github.com/dkuester/calibre-burn-up-chart/releases/latest)
[![CI](https://github.com/dkuester/calibre-burn-up-chart/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/dkuester/calibre-burn-up-chart/actions/workflows/ci.yml)
[![calibre](https://img.shields.io/badge/calibre-5.0%2B-informational)](#voraussetzungen)
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
| **Prognose** | Schreibt den SuB-Trend der letzten 12 Monate fort (lineare Regression), gestrichelt, und markiert das Datum, an dem der SuB tatsächlich 0 erreichen würde. |
| **Kaufrate vs. Leserate** | Zugänge und gelesene Bücher pro Monat als Mittel über 12 Monate; die Fläche dazwischen zeigt, ob der SuB schrumpft oder wächst. |
| **Leseverzögerung** | Für jedes gelesene Buch die Zeit zwischen Aufnahme in calibre und Lesen, als Streudiagramm mit Median und Mittelwert. |
| **Zeitraum** | Alles zeigen oder nur die letzten 5 bzw. 2 Jahre bis heute. |
| **Interaktiv** | Tooltips an jedem Datenpunkt, Zoom per Mausrad, Verschieben per Ziehen, Doppelklick setzt zurück. |
| **Export** | Beide Charts als PNG speichern oder in die Zwischenablage kopieren, genau wie angezeigt (Zoom, Verschiebung, Theme). |
| **Eigene Farben, passendes Theme** | Jede Datenreihe und Referenzlinie lässt sich umfärben. Die Charts folgen dem hellen oder dunklen Theme von calibre. |
| **Zweisprachig** | Deutsche und englische Oberfläche, je nach Sprache von calibre. Weitere Sprachen lassen sich unter `translations/<lang>/` ergänzen. |

## Voraussetzungen

- calibre 5.0 oder neuer
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

Der Knopf in der Werkzeugleiste öffnet ein Menü mit drei Charts:

- **Burn-up-Chart**: Bestand, gelesene Bücher und SuB im Zeitverlauf.
- **Zeit zwischen Kauf und Lesen**: die Leseverzögerung pro Buch.
- **Kaufrate vs. Leserate**: Zugänge und gelesene Bücher pro Monat.

## Einstellungen

*Einstellungen → Erweitert → Erweiterungen → Reading Progress → Erweiterung anpassen*:

| Einstellung | Bedeutung |
|---|---|
| Zieldatum | Der Tag, an dem der SuB 0 erreichen soll. |
| Sanfter Abbau (Faktor) | Anteil des SuB, der am Zieldatum übrig ist. `0.50` heißt: bis dahin halbiert. |
| Prognoselinie anzeigen | Zeichnet die Prognoselinie (standardmäßig an). |
| Farben | Farbe jeder Datenreihe und Referenzlinie. Leer heißt „dem Theme folgen“; *Farben auf Theme-Standard zurücksetzen* entfernt alle eigenen Farben. |
| Benutzerdefinierte Spalte „gelesen“ / „zuletzt gelesen“ | Suchnamen der beiden Spalten, falls deine anders heißen. |

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
├── chart_dialog.py          # Burn-up-Chart-Dialog (QPainter)
├── rates_dialog.py          # Dialog für Kaufrate vs. Leserate
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
