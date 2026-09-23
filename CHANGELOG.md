# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei
dokumentiert. Das Format orientiert sich an
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionierung folgt [Semantic Versioning](https://semver.org/lang/de/).

## [1.2.0] – 2026-09-23

### Hinzugefügt

- Benutzerdefinierte Spaltennamen (`#gelesen`, `#last_read`) sind jetzt
  über den Einstellungsdialog konfigurierbar. Damit funktioniert das
  Plugin auch für Nutzer, deren Calibre-Spalten anders heißen.
- Automatische Suche nach einem Python-3-Interpreter mit matplotlib.
  Unterstützt Homebrew (Apple Silicon und Intel), System-Python und
  `PATH`.
- Klarere Fehlermeldung, wenn matplotlib fehlt.

### Geändert

- Alle temporären Dateien (CSV, PNG, Cache) liegen jetzt in
  `tempfile.gettempdir()`. Das Plugin läuft damit auch unter Windows.
- Datumsformat in Chart und Einstellungsdialog passt sich der Sprache
  an: `TT.MM.JJJJ` auf Deutsch, `JJJJ-MM-TT` sonst.
- `.mo`-Cache-Dateinamen enthalten einen Hash der Quell-ZIP, um
  Kollisionen bei parallel installierten Versionen zu vermeiden.
- `SyntaxWarning`-Filter greift nur noch für das Kobo-Plugin statt
  prozessweit.

### Entfernt

- Hardcodierte Pfade (`/Users/daniel/...`, `/opt/homebrew/bin/python3`)
  sind aus `main.py` verschwunden.

## [1.1.0] – 2026-09-23

### Hinzugefügt

- Mehrsprachigkeit über gettext. Englisch ist die Quellsprache,
  Deutsch als erste Übersetzung enthalten.
- Übersetzungsdatei `translations/de/LC_MESSAGES/lesefortschritt.po`
  mit den deutschen Strings für Plugin-Oberfläche, Dialoge und Chart.

### Geändert

- Alle benutzersichtbaren Strings in `main.py`, `config_dialog.py`,
  `chart_dialog.py` und `zeichne_chart.py` sind jetzt über `_()`
  übersetzbar.
- `zeichne_chart.py` nimmt optional `--translation-mo` entgegen, damit
  die Chart-Beschriftungen in der von Calibre gewählten Sprache
  erscheinen.

## [1.0.0] – 2026-09-23

### Hinzugefügt

- Historische Zeitreihe des Lesestatus aus der Calibre-Bibliothek,
  monatliche Snapshots rückwirkend bis zum ältesten Buch.
- Burn-up-Chart mit Gesamtbestand, kumuliert Gelesenem und SuB.
- Konfigurierbares Zieldatum und Abbau-Faktor über die Plugin-Einstellungen.
- Chart-Dialog mit automatischer Skalierung auf die Bildschirmgröße.
- Eigenes Plugin-Icon (Burn-up-Motiv).
- Toolbar-Integration über Calibres InterfaceAction-API.