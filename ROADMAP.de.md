# Roadmap

*[English version](ROADMAP.md)*

Diese Roadmap sammelt geplante Arbeiten und Ideen für das Plugin. Sie
ist ein lebendes Dokument – Einträge wandern zwischen den Abschnitten,
wenn sich Prioritäten verschieben.

Die Reihenfolge folgt einer einfachen Regel: **Pflege und Qualität vor
neuen Features.** Ein Feature, das bestehenden Code bricht, kostet mehr,
als es wert ist.

## Erledigt

### Nächste Version

In `main` gemergt, kommt mit der nächsten Version:

- **PNG-Export und Zwischenablage:** Beide Chart-Dialoge bekommen die
  Knöpfe „Als PNG speichern…" und „In Zwischenablage kopieren". Sie
  erfassen das Chart so, wie es gerade zu sehen ist, also mit Zoom,
  Verschiebung und aktivem Theme.
- **Tests und CI:** 66 `pytest`-Tests mit Pflicht-Coverage von 100 %
  auf den Qt-freien Modulen (`chart_common`, `config_helpers`,
  `export_reading_status`). Die CI führt `ruff` und `pytest` unter
  Python 3.10 und 3.12 bei jedem Push auf `main` und jedem Pull-Request
  aus. Ein Tag `v*` veröffentlicht das Release.
- **Umzug auf GitHub:** Bis Oktober 2026 lag das Projekt auf Codeberg
  und nutzte Forgejo Actions. Das Codeberg-Repo ist archiviert.

### Veröffentlicht

Details im [Changelog](CHANGELOG.de.md).

- **1.6.0:** Dunkelmodus für beide Charts.
- **1.5.0:** Prognoselinie, interaktive Tooltips, Zoom und Pan sowie
  konfigurierbare Farben (alles im Burn-up-Chart). `ChartWidget` in
  Renderer-Klassen aufgeteilt. Erste Unit-Tests und CI.
- **1.4.0:** Analyse der Leseverzögerung („Zeit zwischen Kauf und
  Lesen").
- **1.3.0:** Charts direkt mit QPainter gezeichnet, ohne matplotlib.

## Geplant

Features, die wir bauen wollen, aber ohne feste Zielversion.

### Kaufrate vs. Leserate

Zwei Linien: Wie viele Bücher kommen pro Monat dazu, wie viele werden
gelesen. Ergänzt das Burn-up-Chart um die zugrunde liegende Dynamik.

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