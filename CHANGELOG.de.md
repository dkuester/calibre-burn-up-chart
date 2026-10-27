## [Unveröffentlicht]

### Hinzugefügt

- **Nötiges Tempo bis zum Ziel:** Zwei Zeilen unter dem Titel des
  Burn-up-Charts sagen, was es braucht, um das Ziel bis zum Zieldatum
  zu erreichen, z. B. „Für SuB = 0 bis 04.09.2050: 26,4 Bücher/Monat
  lesen oder höchstens 0,3 Bücher/Monat kaufen.“ Eine Zeile gilt für
  SuB = 0, eine für den sanften Abbau. Die nötige Leserate setzt die
  typische Kaufrate voraus, die Kaufgrenze die typische Leserate
  (dieselben robusten Raten wie die Prognose, siehe unten). Reicht
  selbst ein Kaufstopp nicht,
  nennt die Zeile, wie viel man dann lesen muss. Die Zeilen bleiben
  auch in der 5- und 2-Jahres-Ansicht stehen. Der Bericht zeigt
  dieselben Zahlen unter „Ziel und Prognose“.
- **Jahresziel (mit dem Plugin „Reading Goal“):** Hat das separat
  installierte Plugin „Reading Goal“ Daten für die aktuelle Bibliothek,
  bekommt das Menü den Eintrag „Jahresziel“. Das Ziel ist dort eine
  Jahresliste von Büchern; das Chart zeigt die gelesenen Listenbücher
  über das Jahr gegen ein Soll, das gleichmäßig bis zum Ziel am
  31. Dezember steigt, dazu die Hochrechnung beim bisherigen Tempo, alle
  gelesenen Bücher laut eigenen Daten (grau) und darunter die Bücher pro
  Monat. Der Kopf nennt das Soll für heute, den Vorsprung oder Rückstand,
  die nötigen Bücher pro Monat und die Seiten. Dazu kommen eine
  Jahresauswahl, ein Vorjahresvergleich, Tooltips mit den Büchern (Klick
  zeigt sie in calibre) und PNG-/Zwischenablage-Export. Der Bericht
  bekommt dieselben Zahlen, dazu die Monate, weitere Challenges, alle
  Zieljahre und wie viele Listenbücher aus dem SuB kamen. Die Dateien
  von „Reading Goal“ werden nur gelesen, nie geschrieben.
- **Reihen-Prüfung in der Datenqualität:** „Datenqualität prüfen“
  bekommt neben dem Lesedatum einen Tab „Reihen“. Er listet Reihen unter
  mehreren Namen („Expanse“, „The Expanse“, „The Expanse-Serie“; Namen,
  die sich nur in Groß-/Kleinschreibung, Satzzeichen, einem Artikel am
  Anfang oder einem Wort wie „Serie“ unterscheiden), Bandnummern, die in
  einer Reihe mehrfach vorkommen, und Lücken (ein früherer Band
  ungelesen, obwohl ein späterer gelesen ist). Ein Doppelklick zeigt die
  Bücher in calibre, der Tab lässt sich als CSV speichern. Der Bericht
  zählt die drei Arten im Abschnitt „Datenqualität“. Es wird nichts
  geändert.
- **Sammel-Import-Tage in der Datenqualität:** Ein Tab „Sammel-Importe“
  listet Tage, an denen mindestens 20 Bücher aus mindestens 15
  verschiedenen Reihen oder von verschiedenen Autoren (Reihe, ohne
  Reihe der erste Autor) aufgenommen wurden, typisch bei Umzug oder
  Neuaufbau der Bibliothek. Ihr Aufnahmedatum ist vermutlich das
  Importdatum, nicht das Kaufdatum. Bundles (viele Bücher eines Autors
  oder einer Reihe) zählen nicht. Pro Tag stehen Bücher, Reihen/Autoren,
  die größte Gruppe und wie viele gelesen, vor der Aufnahme gelesen,
  ohne Lesedatum und ohne Datei sind (die CSV hat zusätzlich die Zahl
  der Autoren und die Buch-IDs). Ein Doppelklick
  zeigt die Bücher des Tages in calibre, der Tab lässt sich als CSV
  speichern. Der Tab zum Lesedatum sagt, wie viele seiner Fälle an
  einem solchen Tag aufgenommen wurden. Es wird nichts geändert.
- **Angefangene Reihen:** Ein neuer Menüeintrag listet die angefangenen,
  aber nicht beendeten Reihen (mindestens zwei Bücher, teils gelesen,
  teils ungelesen): Fortschritt („60/76“), den nächsten ungelesenen Band
  mit Nummer und Titel und wann zuletzt etwas aus der Reihe gelesen
  wurde. Die am längsten liegengebliebenen Reihen stehen oben. Bei einer
  Lücke zeigt eine zweite Spalte den ersten Band nach dem höchsten
  gelesenen. Ein Doppelklick zeigt den nächsten Band in calibre; Knöpfe
  zeigen den nächsten Band oder die ganze Reihe, und die Liste lässt
  sich als CSV speichern.
- **SuB nach Reihen:** Ein neues Chart zeigt die 20 Reihen mit den
  meisten ungelesenen Büchern als liegende Balken. Der Kopf sagt, wie
  viele ungelesene Bücher überhaupt zu einer Reihe gehören und welchen
  Anteil am SuB die 20 größten ausmachen. Der Tooltip ergänzt
  gelesen/gesamt und den Anteil am SuB; ein Klick auf einen Balken zeigt
  die ungelesenen Bücher der Reihe in calibre. PNG-/Zwischenablage-Export
  wie in den anderen Charts.
- **SuB in der Statusleiste:** Rechts in der Statusleiste von calibre
  steht dauerhaft der aktuelle SuB mit der Veränderung gegenüber vor
  12 Monaten, z. B. „SuB: 1652 ▲172“. Der Tooltip nennt gelesen/gesamt,
  den SuB vor 12 Monaten und das nötige Tempo; ein Klick öffnet das
  Burn-up-Chart. Die Zahl folgt der ganzen Bibliothek (wie die Charts)
  und aktualisiert sich etwa eine Sekunde nach neuen, gelöschten oder
  als gelesen markierten Büchern sowie beim Bibliothekswechsel. Sind die
  Spalten nicht nutzbar, steht dort „SuB: –“ mit dem Grund im Tooltip.
  Abschaltbar in den Einstellungen.

### Geändert

- **Robuste Prognose mit Unsicherheitsband:** Die Prognose fittet keine
  Regression über die letzten 12 Monate mehr, die Sammel-Importe und
  große Käufe stark kippten. Sie schreibt jetzt den heutigen SuB mit dem
  *typischen* Monat fort: Kauf- und Leserate als Mittel der letzten
  24 vollen Monate ohne die 20 % höchsten und niedrigsten Monate. Im
  Rückwärtstest mit einer echten Bibliothek sagt das den SuB etwa
  zehnmal genauer voraus. Ein schattiertes Band zeigt, wo der SuB in
  80 % der Fälle liegen wird; es wird mit der Zeit und bei kurzer
  Historie breiter. Statt eines exakten Tages nennen Chart und Bericht
  eine Monatsspanne („Realistisch: SuB = 0 zwischen 03.2031 und
  11.2034“), „frühestens …“ oder wie schnell der SuB wächst. Mit
  weniger als 3 vollen Monaten (der erste Monat mit dem
  Anfangsbestand und der laufende Monat zählen nicht) gibt es keine
  Prognose, sondern einen Hinweis; unter 12 Monaten ist sie als
  vorläufig gekennzeichnet. „Prognoselinie anzeigen“ schaltet Linie,
  Band und Hinweis.
- **Legende des Burn-up-Charts aus dem Weg:** Die Legende steht jetzt
  links oben, wo die kumulierten Linien meist niedrig beginnen, und
  verdeckt so keine steigende Prognose mehr. Würde sie dort mehr
  Linien verdecken als rechts oben, rückt sie nach rechts.

## [1.7.0] – 2026-10-26

### Hinzugefügt

- **PNG-Export und Zwischenablage:** Knöpfe „Als PNG speichern…“ und
  „In Zwischenablage kopieren“ in allen Chart-Dialogen. Sie erfassen
  das Chart so, wie es gerade zu sehen ist, also mit Zoom, Verschiebung
  und aktivem Theme.
- **Bericht:** „Bericht speichern…“ im Menü der Werkzeugleiste schreibt
  die Kennzahlen (Bibliothek, letzte 12 Monate, Ziel und Prognose,
  Leseverzögerung, Altersverteilung des SuB, Datenqualität) als
  Markdown oder als einzelne HTML-Seite, die zusätzlich das Burn-up-
  und das Kaufraten-Chart enthält.
- **Altersverteilung des SuB:** Ein neues Chart zeigt die ungelesenen
  Bücher nach ganzen Jahren seit der Aufnahme (ab 10 Jahren in einem
  gemeinsamen Balken), mit Anzahl, Anteil und Median-Alter. Ein Klick
  auf einen Balken zeigt dessen Bücher in der Bücherliste von calibre.
  PNG-/Zwischenablage-Export wie bei den anderen Charts.
- **Datenqualität prüfen:** Ein neuer Menüeintrag listet gelesene
  Bücher, deren Lesedatum die Charts nicht nutzen können (kein
  Lesedatum oder gelesen vor der Aufnahme), sortierbar nach
  Aufnahmedatum, um Sammel-Importe zu erkennen. Ausgewählte oder alle
  lassen sich in der Bücherliste von calibre anzeigen oder als CSV
  speichern. In der Bibliothek wird nichts verändert.
- **Spalte „Tage im SuB“:** Ein Knopf in den Plugin-Einstellungen legt
  eine calibre-Spalte `#days_in_tbr` an, die calibre selbst aus
  Aufnahmedatum und den Lese-Spalten berechnet: bei gelesenen Büchern
  die Tage zwischen Aufnahme und Lesen, bei ungelesenen die Tage seit
  der Aufnahme. Sie ist immer aktuell, sortiert numerisch und verändert
  keine Buchdaten.
- **Kaufrate vs. Leserate:** Ein drittes Chart, aufrufbar über das
  Menü am Werkzeugleisten-Knopf. Es zeigt Zugänge und gelesene Bücher
  pro Monat als Mittel über 12 Monate und färbt die Fläche dazwischen
  danach, ob der SuB schrumpft oder wächst. Eine Kennzahlenzeile fasst
  die letzten 12 Monate zusammen, der Tooltip zeigt die Werte jedes
  Monats. Zeitraum-Auswahl und PNG-/Zwischenablage-Export wie beim
  Burn-up-Chart.
- **Zeitraum (Burn-up-Chart):** Eine Auswahl „Zeitraum“ im
  Chart-Dialog: „Alles", „Letzte 5 Jahre", „Letzte 2 Jahre". Die
  begrenzten Zeiträume enden heute, damit der jüngere Verlauf das Chart
  füllt; der Titel nennt dann den Zeitraum, und die Legende zeigt nur
  die Datenreihen. Zoom und Verschieben bleiben im Zeitraum, und die
  Wahl wird gespeichert.

### Geändert

- **Verzögerungs-Chart** funktioniert jetzt wie die anderen Charts:
  Tooltips nennen das Buch, ein Klick auf einen Punkt zeigt es in
  calibre, Mausrad zoomt und Ziehen verschiebt, eine Zeitraum-Auswahl
  berechnet Median und Mittelwert für diesen Zeitraum neu, die Punkte
  nutzen die einstellbare Farbe von „Gelesen“, und das Chart lässt sich
  als PNG speichern oder in die Zwischenablage kopieren.
- **Setzt calibre 8.0 oder neuer voraus.** Das Plugin nutzt nur noch
  Qt 6; der Kompatibilitätscode für Qt 5 ist entfallen.
- **Klarere Fehlermeldungen:** Fehlt die Spalte „gelesen“ oder
  „zuletzt gelesen“ oder hat sie den falschen Typ, nennen die Charts
  die Spalte und wo man sie ändert, statt einer kurzen Meldung in der
  Statuszeile. Die Einstellungen warnen schon beim Speichern. Andere
  Lesefehler öffnen einen Dialog mit Details.
- Projekt von Codeberg zu GitHub umgezogen; CI und Releases laufen
  jetzt über GitHub Actions.
- Testsuite auf 110 Tests erweitert, mit Pflicht-Coverage von 100 % auf
  den Qt-freien Modulen; die CI läuft unter Python 3.10 und 3.12.
- Konfigurations-Standards und Migrationen von `__init__.py` nach
  `main.py` verschoben, damit der Build mit `calibre-customize -b` nicht
  mehr bricht, wenn ein neuer Helfer hinzukommt.

### Behoben

- Beim Hineinzoomen ins Burn-up-Chart ragen Linien nicht mehr in die
  Achsenränder.
- Die Beschriftung der Y-Achse stimmt wieder: Schritte wie 2,5 wurden zu
  „0, 2, 5, 7, 10, 12“ abgeschnitten, kleine Achsen zeigten „0, 0, 1,
  1“. Buchzahlen haben jetzt ganzzahlige Schritte.
- Die Achse des Verzögerungs-Charts in Jahren nutzt das
  Dezimaltrennzeichen der calibre-Sprache („1,5“ statt „1.5“).
- Eine leere Bibliothek oder eine ohne Aufnahmedaten zeigt jetzt „Keine
  Daten für diese Auswertung verfügbar.“ statt eines unübersetzten
  Fehlers.
- Ein Zieldatum in der Vergangenheit bleibt in den Einstellungen
  erhalten, statt beim Speichern auf heute zu springen.

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