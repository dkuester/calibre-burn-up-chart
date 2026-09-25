# AGENTS.md

Calibre-Plugin, das den Lesefortschritt als Burn-up-Chart zeigt.
Details siehe [README.md](README.md).

## Build & Deployment

```bash
# Plugin neu bauen (nach jeder Code-Änderung nötig)
calibre-customize -r "Lesefortschritt"
calibre-customize -b lesefortschritt
```

Calibre danach neu starten. Das Plugin wird nicht hot-reloaded.

## Architektur-Constraints

- **Eine Python-Umgebung:** Das gesamte Plugin läuft in Calibres
  eingebettetem Python (kein `pip`, kein `matplotlib`). Das Chart wird
  direkt mit Qt `QPainter` in `chart_dialog.py` gezeichnet – es gibt
  keinen Subprozess und keine externen Abhängigkeiten.
- **Keine neuen Abhängigkeiten** in `main.py`, `chart_dialog.py`,
  `config_dialog.py`, `export_lesestatus.py` oder `localization.py` –
  Calibres Python hat keinen Paketmanager.
- **`plugin-import-name-lesefortschritt.txt` darf nicht gelöscht werden.**
  Sie ist leer, aber essenziell für den Plugin-Import.

## Dateien nicht anfassen

- `.DS_Store` – macOS-Systemdatei
- `/tmp/burndown_log.csv`, `/tmp/burndown_log.csv.tmp` – generiert
  (nur im Standalone-Debug von `export_lesestatus.py`)
- `/tmp/lesefortschritt_paint_error.log` – generiert (Fehlerprotokoll
  aus `chart_dialog.py`)
- `lesefortschritt_*.mo` im tempdir – generierter Lokalisierungs-Cache
  (`localization.py`)
