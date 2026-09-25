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