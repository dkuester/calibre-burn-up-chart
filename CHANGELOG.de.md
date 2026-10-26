## [Unveröffentlicht]

### Hinzugefügt

- **PNG-Export und Zwischenablage:** Knöpfe „Als PNG speichern…" und
  „In Zwischenablage kopieren" in beiden Chart-Dialogen. Sie erfassen
  das Chart so, wie es gerade zu sehen ist, also mit Zoom, Verschiebung
  und aktivem Theme.

### Geändert

- Projekt von Codeberg zu GitHub umgezogen; CI und Releases laufen
  jetzt über GitHub Actions.
- Testsuite auf 66 Tests erweitert, mit Pflicht-Coverage von 100 % auf
  den Qt-freien Modulen; die CI läuft unter Python 3.10 und 3.12.
- Konfigurations-Standards und Migrationen von `__init__.py` nach
  `main.py` verschoben, damit der Build mit `calibre-customize -b` nicht
  mehr bricht, wenn ein neuer Helfer hinzukommt.

## [1.6.0] – 2026-10-16

### Hinzugefügt

- **Dunkelmodus:** Beide Charts folgen jetzt dem aktuellen Calibre-Theme.
  Bei dunkler Farbpalette wechselt die Chart-Optik (Hintergrund, Achsen,
  Raster, Text, Legenden-/Hinweis-Boxen) auf helle Farben auf dunklem
  Grund, und die konfigurierbaren Serienfarben fallen auf kontrastreichere
  Dunkeltheme-Standards zurück – außer der Nutzer hat eine Farbe explizit
  gewählt. Auch die festen Farben des Verzögerungs-Charts bekommen
  dunkle Varianten.

### Geändert

- Serienfarben folgen jetzt standardmäßig dem Theme (leerer Wert) statt
  festen Hex-Werten; nur explizit gewählte Farben werden gespeichert.
  Ein neuer Button „Farben auf Theme-Standard zurücksetzen" setzt
  eigene Farben zurück.
- Einmal-Migration der Farben: Wer nie eine Farbe angepasst hat (noch
  auf den alten Light-Standards), wird auf „auto" umgestellt, damit der
  Dunkelmodus greift.

## [1.5.0] – 2026-10-16

### Hinzugefügt

- **Prognoselinie:** Lineare Regression über die letzten 12 Monate des
  Backlogs (SuB), als gestrichelte Linie gezeichnet, mit Angabe des
  realistischen Datums, an dem der SuB 0 erreicht – neben dem
  Wunsch-Zieldatum. Abschaltbar über „Prognoselinie anzeigen"
  (standardmäßig an).
- **Interaktive Tooltips:** Beim Überfahren eines Datenpunkts erscheinen
  Datum und Gesamt/Gelesen/SuB.
- **Zoom und Pan:** Mausrad zoomt um den Cursor, Ziehen verschiebt,
  Doppelklick setzt die Ansicht zurück.
- **Konfigurierbare Farben:** Jede Datenreihe und Referenzlinie lässt
  sich in den Plugin-Einstellungen umfärben.
- Unit-Test-Suite (`pytest`, 34 Tests) für die
  Datenverarbeitungs-Funktionen.
- Forgejo-Actions-CI-Workflow (`ruff` + `pytest` bei jedem Push und
  Pull Request).

### Geändert

- Plugin umbenannt zu **„Reading Progress"** (vorher „Lesefortschritt").
  Die Konfiguration wird automatisch vom alten Plugin übernommen.
- Oberfläche vollständig internationalisiert: englische Bezeichner,
  Docstrings und Kommentare; deutsche und englische UI-Texte.
- `ChartWidget`-Zeichnung in Renderer-Klassen aufgeteilt
  (`AxesRenderer`, `SeriesRenderer`, `LegendRenderer`,
  `AnnotationRenderer`).
- Version auf 1.5.0 angehoben.

## [1.4.0] – 2026-10-02

### Hinzugefügt

- Zweite Auswertungsoption: „Zeit zwischen Kauf und Lesen". Für jedes
  als gelesen markierte Buch berechnet das Plugin die Zeitspanne
  zwischen dem Hinzufügen zu Calibre und dem letzten Lesedatum. Das
  Ergebnis erscheint als Streudiagramm mit Median- und Mittelwertlinie
  sowie einer Kopfzeile mit Kennzahlen (Median, Mittel, Spanne,
  Anzahl).
- Dropdown-Menü am Toolbar-Button zur Wahl zwischen Burn-up-Chart und
  Lese-Verzögerungs-Analyse.
- Neue Hilfsfunktion `berechne_lesezeit()` in `export_lesestatus.py`.
- Neues Modul `delay_dialog.py` mit Widget und Dialog für das
  Verzögerungs-Chart.

### Geändert

- Version auf 1.4.0 angehoben.

## [1.3.0] – 2026-09-25

### Geändert

- Das Chart wird jetzt direkt in Calibre über QPainter gezeichnet.
  Der gesamte matplotlib-Subprozess ist entfallen, ebenso die
  Zwischen-CSV und die PNG-Ausgabe. Das Plugin benötigt keine externe
  Python-Installation mehr.
- `main.py` wurde deutlich vereinfacht: Es holt nur noch die Daten aus
  der Live-Bibliothek und öffnet den Chart-Dialog.

### Entfernt

- `zeichne_chart.py` (ersetzt durch eine QPainter-Implementierung im
  Calibre-Prozess).
- Die Zwischen-CSV (`/tmp/burndown_log.csv`).
- Die gerenderte PNG-Datei (`/tmp/lesefortschritt.png`).
- Der Cache für `zeichne_chart.py` im Temp-Verzeichnis.
- Alle `subprocess`-Aufrufe und die Python-Interpreter-Suche.
- Die Parameter `--log-pfad` und `--ausgabe-pfad`.