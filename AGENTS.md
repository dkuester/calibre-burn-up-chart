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

- **Zwei Python-Umgebungen:** `export_lesestatus.py` und `main.py` laufen in
  Calibres eingebettetem Python (kein `pip`, kein `matplotlib`).
  `zeichne_chart.py` läuft als Subprozess unter `/opt/homebrew/bin/python3`
  und ist die **einzige** Datei, die matplotlib importieren darf.
- **Keine neuen Abhängigkeiten** in `main.py`, `chart_dialog.py`,
  `config_dialog.py` oder `export_lesestatus.py` – Calibres Python hat
  keinen Paketmanager.
- **`plugin-import-name-lesefortschritt.txt` darf nicht gelöscht werden.**
  Sie ist leer, aber essenziell für den Plugin-Import.

## Dateien nicht anfassen

- `.DS_Store` – macOS-Systemdatei
- `/tmp/burndown_log.csv`, `/tmp/lesefortschritt.png` – generiert
- `.zeichne_chart_cache.py` – wird aus dem Plugin-ZIP extrahiert