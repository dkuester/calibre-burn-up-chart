# Roadmap

*[English version](ROADMAP.md)*

Diese Roadmap sammelt geplante Arbeiten und Ideen für das Plugin. Sie
ist ein lebendes Dokument – Einträge wandern zwischen den Abschnitten,
wenn sich Prioritäten verschieben.

Die Reihenfolge folgt einer einfachen Regel: **Pflege und Qualität vor
neuen Features.** Ein Feature, das bestehenden Code bricht, kostet mehr,
als es wert ist.

## Nächste Version

Fertig, noch nicht veröffentlicht:

- **Nötiges Tempo bis zum Ziel:** zwei Zeilen unter dem Titel des
  Burn-up-Charts und zwei Zeilen im Bericht, z. B. „Für SuB = 0 bis
  04.09.2050: 26,4 Bücher/Monat lesen oder höchstens 0,3 Bücher/Monat
  kaufen.“ Eine Zeile gilt für SuB = 0, eine für den sanften Abbau,
  beide bei der Kauf- und Leserate der letzten 12 Monate. Macht aus dem
  Ziel eine Monatszahl, nach der man handeln kann.
- **Jahresziel (mit dem Plugin „Reading Goal“):** Das Plugin „Reading
  Goal“ führt pro Bibliothek eine Jahresliste von Büchern
  (`plugins/Reading_Goal_Data_<Bibliotheks-ID>.json`); das Ziel ist
  diese Liste, keine eigene Zahl. Statt einer zweiten Ziel-Einstellung
  liest das Plugin diese Daten (nur lesend) und zeigt den Fortschritt
  gegenüber dem Soll als Chart und im Bericht, angereichert mit unseren
  Zahlen (alle gelesenen Bücher, Zugänge, SuB, Leseverzögerung).
  Erscheint nur, wenn „Reading Goal“ Daten für die aktuelle Bibliothek
  hat.
- **Reihen-Prüfung in der Datenqualität:** Ein Tab „Reihen“ listet
  Reihen unter mehreren Namen („Expanse“, „The Expanse-Serie“, „The
  Expanse“), doppelte Bandnummern innerhalb einer Reihe (Ausgaben in
  zwei Sprachen, Sammelbände oder keine gepflegte Nummer) und Lücken
  (ein früherer Band ungelesen, obwohl ein späterer gelesen ist). Namen
  gelten als dieselbe Reihe, wenn sie sich nur in Groß-/Kleinschreibung,
  Satzzeichen, einem Artikel am Anfang oder einem Wort wie „Serie“
  unterscheiden; ein Ähnlichkeitsvergleich wurde probiert und verworfen,
  weil er vor allem verschiedene Bände paarte („Black Panther
  (2005-2008)“ und „(2008-2010)“). Sauberere Reihen-Daten machen die
  Reihen-Auswertungen unten verlässlicher.

## Erledigt

### 1.7.0

Kommt mit 1.7.0:

- **PNG-Export und Zwischenablage:** Alle Chart-Dialoge bekommen die
  Knöpfe „Als PNG speichern…" und „In Zwischenablage kopieren". Sie
  erfassen das Chart so, wie es gerade zu sehen ist, also mit Zoom,
  Verschiebung und aktivem Theme.
- **Zeitraum (Burn-up-Chart):** „Alles", „Letzte 5 Jahre" oder „Letzte
  2 Jahre". Die begrenzten Zeiträume enden heute statt am Zieldatum.
- **Kaufrate vs. Leserate:** ein drittes Chart mit Zugängen und
  gelesenen Büchern pro Monat (Mittel über 12 Monate), gefärbt danach,
  ob der SuB schrumpft oder wächst.
- **Spalte „Tage im SuB“:** ein Knopf in den Einstellungen legt eine
  calibre-Spalte an, die calibre selbst berechnet. Sie ist damit immer
  aktuell, und es werden keine Werte in die Bibliothek geschrieben.
- **Datenqualität prüfen:** listet gelesene Bücher ohne Lesedatum oder
  mit Lesedatum vor der Aufnahme (die Charts zählen sie als am
  Aufnahmetag gelesen) und zeigt sie zum Korrigieren in der Bücherliste
  von calibre an.
- **Altersverteilung des SuB:** ein Balkendiagramm der ungelesenen
  Bücher nach ganzen Jahren seit der Aufnahme; ein Klick auf einen
  Balken zeigt diese Bücher in calibre.
- **Verzögerungs-Chart angeglichen:** Tooltips mit dem Buch, Klick
  zeigt es in calibre, Zoom und Verschieben, Zeitraum mit eigenem
  Median und Mittelwert, die einstellbare Farbe von „Gelesen" und
  PNG-/Zwischenablage-Export.
- **Bericht:** speichert die Kennzahlen aller Charts als Markdown oder
  als einzelne HTML-Seite mit eingebettetem Burn-up- und Raten-Chart.
- **Setzt calibre 8.0 voraus:** Das Plugin nutzt nur noch Qt 6, der
  Kompatibilitätscode für Qt 5 ist entfallen.
- **Tests und CI:** 110 `pytest`-Tests mit Pflicht-Coverage von 100 %
  auf den Qt-freien Modulen (`chart_common`, `config_helpers`,
  `export_reading_status`, `report`). Die CI führt `ruff` und `pytest`
  unter Python 3.10 und 3.12 bei jedem Push auf `main` und jedem
  Pull-Request aus. Ein Tag `v*` veröffentlicht das Release.
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

### Angefangene Reihen mit dem nächsten Band

Eine Liste der angefangenen, aber nicht beendeten Reihen: Reihe,
Fortschritt („60/76“), der nächste ungelesene Band (Nummer und Titel)
und wann zuletzt etwas aus der Reihe gelesen wurde, damit
liegengebliebene Reihen auffallen. Ein Klick zeigt den nächsten Band in
calibre, wie bei Datenqualität und Altersverteilung. Reihen mit nur
einem Band in der Bibliothek bleiben außen vor. Bei Lücken werden der
niedrigste ungelesene Band und der erste nach dem höchsten gelesenen
gezeigt.

### SuB nach Reihen

Welche Reihen den größten Teil des SuB ausmachen, als Balken. Hilft bei
der Entscheidung, was man abbaut – oder was man gar nicht mehr lesen
will.

### Reihen-Fortschritt als Chart

Ein gestapelter Balken (gelesen/ungelesen) pro angefangener Reihe,
sortiert nach Fortschritt. Visuell schön, inhaltlich aber nah an
„Angefangene Reihen“.

## Ideen

Breiteres Spektrum, nichts davon zugesagt.

### Weitere Analysen

- Lesequote pro Monat / Jahr (Balkendiagramm)
- Genre- und Kategorie-Auswertung
- Seitenzahl-basierte Analyse
- Autoren-Analyse
- Aktivitäts-Heatmap (GitHub-Contributions-Stil)

### UX-Verbesserungen

- Statusbar-Widget mit permanent sichtbarem Backlog

## Nicht geplant

Ideen, die erwogen und verworfen wurden. Hier gelistet, damit sie nicht
immer wieder aufpoppen.

### Kontextmenü „wie lange ungelesen?" und Regal „lange ungelesen"

Beides deckt die Spalte „Tage im SuB" ab: danach sortieren oder eine
virtuelle Bibliothek mit der Suche `#days_in_tbr:>1000 and
#gelesen:false` anlegen (mit deiner Lese-Spalte).

### Massenbearbeitung von `#last_read` aus Statusänderungen

calibre speichert keinen Verlauf, wann ein Buch als gelesen markiert
wurde, es gibt also nichts, woraus man nachtragen könnte. Stattdessen
listet die Datenqualitäts-Prüfung die betroffenen Bücher, damit man sie
von Hand korrigieren kann.

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