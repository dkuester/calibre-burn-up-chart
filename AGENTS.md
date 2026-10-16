# AGENTS.md

Calibre-Plugin „Reading Progress“: zeigt den Lesefortschritt als Burn-up-Chart.
Details siehe [README.md](README.md).

## Build & Deployment

```bash
# Plugin neu bauen (nach jeder Code-Änderung nötig)
calibre-customize -r "Reading Progress"
calibre-customize -b readingprogress
```

Calibre danach neu starten. Das Plugin wird nicht hot-reloaded.

## Architektur-Constraints

- **Eine Python-Umgebung:** Das gesamte Plugin läuft in Calibres
  eingebettetem Python (kein `pip`, kein `matplotlib`). Das Chart wird
  direkt mit Qt `QPainter` in `chart_dialog.py` gezeichnet – es gibt
  keinen Subprozess und keine externen Abhängigkeiten.
- **Keine neuen Abhängigkeiten** in `main.py`, `chart_dialog.py`,
  `config_dialog.py`, `export_reading_status.py` oder `localization.py` –
  Calibres Python hat keinen Paketmanager.
- **`plugin-import-name-readingprogress.txt` darf nicht gelöscht werden.**
  Sie ist leer, aber essenziell für den Plugin-Import.

## Dateien nicht anfassen

- `.DS_Store` – macOS-Systemdatei
- `/tmp/readingprogress_log.csv`, `/tmp/readingprogress_log.csv.tmp` – generiert
  (nur im Standalone-Debug von `export_reading_status.py`)
- `/tmp/readingprogress_paint_error.log` – generiert (Fehlerprotokoll
  aus `chart_dialog.py`)
- `readingprogress_*.mo` im tempdir – generierter Lokalisierungs-Cache
  (`localization.py`)
