# Calibre Burn-up Chart Plugin

Ein Calibre-Plugin, das den Lesefortschritt als Burn-up-Chart anzeigt.
Es rekonstruiert die historische Zeitreihe aus den Calibre-Metadaten
(`timestamp` und benutzerdefinierte Spalten) und zeichnet den Verlauf
von Gesamtbestand, gelesenen Büchern und SuB (Backlog).

## Funktionen

- **Historische Zeitreihe:** Monatliche Snapshots aus den Buch-Metadaten,
  rückwirkend bis zum ältesten Buch in der Bibliothek.
- **Burn-up-Chart:** Gesamtbestand, kumuliert Gelesenes und SuB im Zeitverlauf.
- **Konfigurierbares Zieldatum:** Zielgerade „SuB = 0 am …" mit frei wählbarem
  Datum über die Plugin-Einstellungen.
- **Sanfter Abbau:** Zusätzliche Referenzlinie für ein realistischeres Szenario
  (SuB halbiert bis zum Zieldatum, Faktor einstellbar).
- **In-GUI-Anzeige:** Das Chart öffnet sich als Dialog in Calibre, mit
  automatischer Skalierung auf die Bildschirmgröße.

## Voraussetzungen

- Calibre 5.0 oder neuer
- Homebrew-Python 3 mit matplotlib (`brew install python-matplotlib`)
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
   calibre-customize -b ~/GitHub/calibre-burn-up-chart/lesefortschritt
   ```

3. Calibre neu starten.

4. Die Aktion zur Toolbar hinzufügen:
   *Einstellungen → Oberfläche → Symbolleisten & Menüs → Die Hauptsymbolleiste*
   → „Burn-up Chart" aus der Liste der verfügbaren Aktionen hinzufügen.

## Benutzung

Nach dem Klick auf den Button **„Burn-up Chart"** in der Haupttoolbar läuft
folgender Ablauf:

1. Die CSV mit den monatlichen Snapshots wird erzeugt (`/tmp/burndown_log.csv`).
2. Das Chart wird gezeichnet (`/tmp/lesefortschritt.png`).
3. Ein Dialog öffnet sich mit dem fertigen Chart.

### Konfiguration

Unter *Einstellungen → Erweitert → Erweiterungen → Lesefortschritt → Anpassen*
lassen sich einstellen:

- **Zieldatum:** Der Tag, an dem der SuB auf 0 sein soll.
- **Sanfter Abbau (Faktor):** Anteil des SuB, der am Zieldatum noch übrig
  bleibt. `0.50` bedeutet: SuB halbiert bis zum Zieldatum.

Die Werte werden in `~/Library/Preferences/calibre/plugins/lesefortschritt.json`
gespeichert und bleiben über Calibre-Neustarts erhalten.

- **Zweisprachig:** Deutsche und englische Oberfläche, abhängig von
  Calibres Spracheinstellung. Weitere Sprachen können über
  `translations/<lang>/` ergänzt werden.

## Versionierung

Dieses Plugin folgt [Semantic Versioning](https://semver.org/lang/de/).
Die aktuelle Version ist in `lesefortschritt/__init__.py` als
`__version__`-Tupel gepflegt und wird von Calibre in der Erweiterungsliste
angezeigt. Alle Änderungen sind im [CHANGELOG.md](CHANGELOG.md) dokumentiert.

Releases werden im Git als annotierte Tags mit `v`-Präfix gesetzt
(z.B. `v1.0.0`). Um die Version zu erhöhen:

1. `__version__` in `lesefortschritt/__init__.py` anpassen.
2. Eintrag in `CHANGELOG.md` ergänzen.
3. Plugin neu bauen und testen.
4. Committen und taggen:

   ```bash
   git commit -am "Release v1.0.1"
   git tag -a v1.0.1 -m "Kurze Beschreibung"
   ```

## Projektstruktur

```
calibre-burn-up-chart/
├── .gitignore
├── README.md
├── LICENSE
├── AGENTS.md
├── CHANGELOG.md
├── make_icon.py
└── lesefortschritt/
    ├── __init__.py                          # Plugin-Metadaten, Version
    ├── plugin-import-name-lesefortschritt.txt
    ├── main.py                              # GUI-Integration
    ├── config_dialog.py                     # Einstellungsdialog
    ├── chart_dialog.py                      # Chart-Anzeigedialog
    ├── export_lesestatus.py                 # Datenbeschaffung aus Calibre
    ├── zeichne_chart.py                     # Chart-Erzeugung (matplotlib)
    └── images/
        └── icon.png                         # Plugin-Icon
```

## Technische Hinweise

- `export_lesestatus.py` läuft **innerhalb** des Calibre-Prozesses und nutzt
  die Live-Datenbank (`self.gui.current_db.new_api`).
- `zeichne_chart.py` läuft **außerhalb** als Subprozess unter Homebrew-Python,
  weil Calibres eingebettetes Python kein matplotlib enthält.
- Die Kommunikation zwischen beiden läuft über `/tmp`-Dateien:
  `/tmp/burndown_log.csv` (Daten) und `/tmp/lesefortschritt.png` (Chart).

## Lizenz

GNU General Public License v3.0 – siehe [LICENSE](LICENSE).