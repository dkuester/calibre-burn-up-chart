# Roadmap

*[English version](ROADMAP.md)*

Diese Roadmap sammelt geplante Arbeiten und Ideen für das Plugin. Sie
ist ein lebendes Dokument – Einträge wandern zwischen den Abschnitten,
wenn sich Prioritäten verschieben.

Die Reihenfolge folgt einer einfachen Regel: **Pflege und Qualität vor
neuen Features.** Ein Feature, das bestehenden Code bricht, kostet mehr,
als es wert ist.

## Erledigt

Im aktuellen Entwicklungszyklus abgeschlossen, kommt mit der nächsten
Version:

### Unit-Tests

Eine `pytest`-Suite (28 Tests) deckt die beiden
Datenverarbeitungs-Einstiegspunkte ab:

- `compute_reading_time()` – Median, Mittel, leere Eingabe, Randfälle
- `export_snapshots()` – Snapshot-Erzeugung, Monatsgrenzen, Randfälle

Sie läuft gegen synthetische Calibre-artige Wörterbücher, keine echte
Datenbank nötig.

### CI auf Codeberg

Ein Forgejo-Actions-Workflow (`.forgejo/workflows/ci.yml`) führt `ruff`
und `pytest` bei jedem Push und Pull Request aus.

### Refactoring `ChartWidget`

`ChartWidget` in `chart_dialog.py` ist jetzt in Renderer-Klassen
aufgeteilt: `AxesRenderer` (Achsen, Raster, Achsenbeschriftungen),
`SeriesRenderer` (Datenlinien), `LegendRenderer` (die Legendenbox) und
`AnnotationRenderer` („Heute: X ungelesen" und ähnliches). `ChartWidget`
behält nur die Orchestrierung.

### Prognoselinie

Eine gestrichelte Prognoselinie extrapoliert den Backlog-Trend (lineare
Regression über die letzten 12 Monate) und zeigt, wohin der SuB läuft,
wenn die aktuelle Leserate bleibt. Sie ist konfigurierbar
(„Prognoselinie anzeigen", standardmäßig an) und markiert das
realistische Datum, an dem der Backlog 0 erreicht, neben dem
Wunsch-Zieldatum.

### Interaktive Tooltips (Burn-up-Chart)

Beim Überfahren eines Datenpunkts erscheinen Datum und die Werte für
Gesamt/Gelesen/SuB an diesem Punkt.

### Zoom und Pan (Burn-up-Chart)

Mausrad zoomt um den Cursor, Ziehen verschiebt, Doppelklick setzt die
Ansicht zurück.

### Konfigurierbare Farben (Burn-up-Chart)

Die Farben aller Datenreihen und Referenzlinien lassen sich in den
Plugin-Einstellungen ändern (mit sinnvollen Standardwerten).

### Dunkelmodus

Die Charts passen sich dem aktuellen Calibre-Theme an. Bei dunkler
Farbpalette wechselt die Chart-Optik (Hintergrund, Achsen, Raster,
Text, Legenden-/Hinweis-Boxen) auf helle Farben auf dunklem Grund, und
die konfigurierbaren Serienfarben fallen auf kontrastreichere
Dunkeltheme-Standards zurück – außer der Nutzer hat eine Farbe
explizit gewählt.

## Geplant

Features, die wir bauen wollen, aber ohne feste Zielversion.

### Kaufrate vs. Leserate

Zwei Linien: Wie viele Bücher kommen pro Monat dazu, wie viele werden
gelesen. Ergänzt das Burn-up-Chart um die zugrunde liegende Dynamik.

### PNG-Export

Ein Button im Chart-Dialog: „Als PNG speichern". Verwendet
`widget.render(QPixmap)`, um das aktuelle Chart in eine Datei zu
schreiben. Nützlich für Reports oder zum Teilen.

### Zeitraum wählbar

Optionen „Letzte 2 Jahre", „Letzte 5 Jahre", „Alles". Wird besonders
nützlich, wenn die Bibliothek wächst und die frühen Jahre zu einer
flachen Linie werden.

### Export in Calibre-Spalte

Berechnete Werte in eine benutzerdefinierte Spalte schreiben, z.B.
„Tage bis zum Lesen" pro Buch. Dann kann die Calibre-Oberfläche selbst
danach sortieren und filtern – z.B. „zeig mir die Bücher, die ich am
längsten besitze, ohne sie gelesen zu haben".

## Ideen

Breiteres Spektrum, nichts davon zugesagt.

### Weitere Analysen

- Lesequote pro Monat / Jahr (Balkendiagramm)
- Genre- und Kategorie-Auswertung
- Seitenzahl-basierte Analyse
- Autoren-Analyse
- Altersverteilung des Backlogs
- Aktivitäts-Heatmap (GitHub-Contributions-Stil)

### UX-Verbesserungen

- Parity für das Verzögerungs-Chart (Tooltips, Zoom/Pan, konfigurierbare
  Farben), das derzeit feste Farben und keine Interaktion hat
- Statusbar-Widget mit permanent sichtbarem Backlog
- Kontextmenü für ausgewählte Bücher: „wie lange ist dieses Buch
  ungelesen?"
- Automatisches virtuelles Regal „lange ungelesen" (> 1000 Tage)

### Datenqualität

- Dialog mit Liste der Bücher ohne `#last_read`
- Massenbearbeitung für `#last_read` (Nachtrag aus Statusänderungen)

### Teilen

- Chart in die Zwischenablage kopieren
- Markdown-/HTML-Report der wichtigsten Kennzahlen

## Nicht geplant

Ideen, die erwogen und verworfen wurden. Hier gelistet, damit sie nicht
immer wieder aufpoppen.

### Gestapeltes Balkendiagramm

Ein alternatives Chart-Design, bei dem gelesene Bücher und Backlog als
gestapelte Jahresbalken erscheinen, mit dem Gesamtbestand als Linie.
Während der v1.3.0-Entwicklung als matplotlib-Prototyp gebaut, aber die
reine Liniendarstellung erwies sich als optisch klarer. Der Prototyp
ist in der Entwicklungshistorie dokumentiert, aber nicht implementiert.

### Externe Charting-Bibliotheken

matplotlib wurde bis Version 1.2.0 verwendet, um das Chart als PNG in
einem Subprozess zu rendern. In 1.3.0 entfernt, weil es eine externe
Python-Installation erforderte und unnötige Dateisystem-Umwege
einführte. Die aktuelle Implementierung zeichnet direkt in Calibre mit
QPainter.

### QtCharts

Als Alternative zu QPainter erwogen. Nicht in der offiziellen
Calibre-Distribution enthalten, würde also ohne zusätzliche
Paketinstallation nicht funktionieren. Verworfen zugunsten des
QPainter-Ansatzes, der keine externen Abhängigkeiten hat.