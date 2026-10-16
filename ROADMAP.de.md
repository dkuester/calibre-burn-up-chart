# Roadmap

*[English version](ROADMAP.md)*

Diese Roadmap sammelt geplante Arbeiten und Ideen für das Plugin. Sie
ist ein lebendes Dokument – Einträge wandern zwischen den Abschnitten,
wenn sich Prioritäten verschieben.

Die Reihenfolge folgt einer einfachen Regel: **Pflege und Qualität vor
neuen Features.** Ein Feature, das bestehenden Code bricht, kostet mehr,
als es wert ist.

## Als Nächstes

Die unmittelbar anstehenden Schritte. Zielversion: v1.5.0.

### Unit-Tests

Automatisierte Tests für die beiden Datenverarbeitungs-Einstiegspunkte:

- `compute_reading_time()` – Median, Mittel, Ausreißer, leere Eingabe
- `export_snapshots()` – Snapshot-Erzeugung, Monatsgrenzen, Randfälle

Ausführung mit `pytest`. Synthetische Calibre-artige Wörterbücher, keine
echte Datenbank nötig.

### CI auf Codeberg

Forgejo-Actions-Workflow, der bei jedem Push läuft:

- Linting mit `ruff`
- Unit-Tests mit `pytest`
- Idealerweise: Workflow schlägt fehl, wenn Lint oder Tests fehlschlagen

Workflow-Datei liegt unter `.forgejo/workflows/`.

### Refactoring `ChartWidget`

`ChartWidget` in `chart_dialog.py` ist zu einer einzelnen Klasse mit
vielen Verantwortlichkeiten gewachsen. Aufteilung in kleinere Einheiten:

- `AxesRenderer` – Achsen, Raster, Achsenbeschriftungen
- `SeriesRenderer` – Datenlinien
- `LegendRenderer` – die Legendenbox
- `AnnotationRenderer` – „Heute: X ungelesen" und ähnliches

`ChartWidget` behält nur die Orchestrierung.

## Geplant

Features, die wir bauen wollen, aber ohne feste Zielversion.

### Kaufrate vs. Leserate

Zwei Linien: Wie viele Bücher kommen pro Monat dazu, wie viele werden
gelesen. Ergänzt das Burn-up-Chart um die zugrunde liegende Dynamik.

### Dunkelmodus

Anpassung der Chart-Farben an das aktuelle Calibre-Theme über
`palette().color(QPalette.Window)` und Verwandte. Aktuell geht das
Chart von einem hellen Theme aus.

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

### Prognoselinie

Lineare Regression über die letzten 12 Monate. Zeigt, wohin der Backlog
läuft, wenn die aktuelle Leserate bleibt. Hebt die Lücke zwischen
Wunsch-Zieldatum und realistischem Zieldatum hervor.

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

- Interaktive Tooltips an Datenpunkten
- Zoom und Pan
- Konfigurierbare Farben
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