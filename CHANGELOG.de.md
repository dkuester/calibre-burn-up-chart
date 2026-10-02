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