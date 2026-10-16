# Calibre Burn-up Chart Plugin

*[English version](README.md)*

Ein Calibre-Plugin, das den Lesefortschritt als Burn-up-Chart anzeigt.
Es rekonstruiert die historische Zeitreihe aus den Calibre-Metadaten
(`timestamp` und benutzerdefinierte Spalten) und zeichnet den Verlauf
von Gesamtbestand, gelesenen Büchern und SuB (Backlog).

## Funktionen

- **Historische Zeitreihe:** Monatliche Snapshots aus den Buch-Metadaten,
  rückwirkend bis zum ältesten Buch in der Bibliothek.
- **Burn-up-Chart:** Gesamtbestand, kumuliert Gelesenes und SuB im
  Zeitverlauf.
- **Konfigurierbares Zieldatum:** Zielgerade „SuB = 0 am …" mit frei
  wählbarem Datum über die Plugin-Einstellungen.
- **Sanfter Abbau:** Zusätzliche Referenzlinie für ein realistischeres
  Szenario (SuB halbiert bis zum Zieldatum, Faktor einstellbar).
- **In-GUI-Anzeige:** Das Chart öffnet sich als Dialog in Calibre, mit
  automatischer Skalierung auf die Bildschirmgröße.
- **Zweisprachig:** Deutsche und englische Oberfläche, abhängig von
  Calibres Spracheinstellung. Weitere Sprachen können über
  `translations/<lang>/` ergänzt werden.
- **Lese-Verzögerung:** Für jedes gelesene Buch wird die Zeitspanne
  zwischen Hinzufügen und Lesen berechnet. Das Ergebnis wird als
  Streudiagramm mit Median- und Mittelwertlinie dargestellt.

## Voraussetzungen

- Calibre 5.0 oder neuer
- Keine externe Python-Installation nötig. Alles läuft innerhalb von Calibre.
- Zwei benutzerdefinierte Spalten in Calibre:
  - `#gelesen` (Ja/Nein) – markiert gelesene Bücher
  - `#last_read` (Datum) – Datum des letzten Lesens

## Installation

1. Repository klonen:

   ```bash
   git clone <repo-url> ~/GitHub/calibre-burn-up-chart
   ```

2. Plugin in Calibre installieren:

   ```bash
   calibre-customize -b ~/GitHub/calibre-burn-up-chart/readingprogress
   ```

3. Calibre neu starten.

4. Die Aktion zur Toolbar hinzufügen:
   *Einstellungen → Oberfläche → Symbolleisten & Menüs → Die
   Hauptsymbolleiste* → „Burn-up Chart" aus der Liste der verfügbaren
   Aktionen hinzufügen.

## Benutzung

Ein Klick auf den Toolbar-Button öffnet ein Dropdown-Menü mit zwei
Optionen:

- **Burn-up-Chart** – der historische Verlauf von Bestand, gelesenen
  Büchern und SuB.
- **Zeit zwischen Kauf und Lesen** – Verzögerungsstatistik pro Buch.

### Konfiguration

Unter *Einstellungen → Erweitert → Erweiterungen → Reading Progress →
Anpassen* lassen sich einstellen:

- **Zieldatum:** Der Tag, an dem der SuB auf 0 sein soll.
- **Sanfter Abbau (Faktor):** Anteil des SuB, der am Zieldatum noch
  übrig bleibt. `0.50` bedeutet: SuB halbiert bis zum Zieldatum.

Die Werte werden in
`~/Library/Preferences/calibre/plugins/readingprogress.json` gespeichert
und bleiben über Calibre-Neustarts erhalten.

## Versionierung

Dieses Plugin folgt [Semantic Versioning](https://semver.org/lang/de/).
Die aktuelle Version ist in `readingprogress/__init__.py` als
`__version__`-Tupel gepflegt und wird von Calibre in der
Erweiterungsliste angezeigt. Alle Änderungen sind im
[CHANGELOG.md](CHANGELOG.md) dokumentiert
([deutsche Version](CHANGELOG.de.md)).

Releases werden im Git als annotierte Tags mit `v`-Präfix gesetzt
(z.B. `v1.0.0`). Um die Version zu erhöhen:

1. `__version__` in `readingprogress/__init__.py` anpassen.
2. Eintrag in `CHANGELOG.md` ergänzen.
3. Plugin neu bauen und testen.
4. Committen und taggen:

   ```bash
   git commit -am "Release v1.0.1"
   git tag -a v1.0.1 -m "Kurze Beschreibung"
   ```

Geplante Features und Ideen stehen in [ROADMAP.de.md](ROADMAP.de.md).

## Projektstruktur

```
calibre-burn-up-chart/
├── .forgejo/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── README.md
├── README.de.md
├── LICENSE
├── AGENTS.md
├── CHANGELOG.md
├── CHANGELOG.de.md
├── ROADMAP.md
├── ROADMAP.de.md
├── make_icon.py
├── pyproject.toml
├── requirements-dev.txt
├── tests/
│   ├── conftest.py
│   ├── test_helpers.py
│   ├── test_compute_reading_time.py
│   └── test_export_snapshots.py
└── readingprogress/
    ├── __init__.py                          # Plugin-Metadaten, Version
    ├── plugin-import-name-readingprogress.txt
    ├── localization.py                      # gettext-Setup
    ├── main.py                              # GUI-Integration
    ├── config_dialog.py                     # Einstellungsdialog
    ├── chart_dialog.py                      # Chart-Anzeigedialog
    ├── delay_dialog.py                      # Verzögerungs-Chart-Dialog
    ├── export_reading_status.py             # Datenbeschaffung aus Calibre
    ├── images/
    │   └── icon.png                         # Plugin-Icon
    └── translations/
        └── de/LC_MESSAGES/
            ├── readingprogress.po
            └── readingprogress.mo
```

## Technische Hinweise

- `export_reading_status.py` läuft **innerhalb** des Calibre-Prozesses und
  nutzt die Live-Datenbank (`self.gui.current_db.new_api`).

## Entwicklung

Test-Suite und Linter in einer virtuellen Umgebung ausführen:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
.venv/bin/ruff check .
```

Ein Forgejo-Actions-Workflow (`.forgejo/workflows/ci.yml`) führt dieselben
Prüfungen bei jedem Push und Pull Request aus.

## Lizenz

GNU General Public License v3.0 – siehe [LICENSE](LICENSE).