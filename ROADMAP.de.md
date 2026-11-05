# Roadmap

*[English version](ROADMAP.md)*

Was für das Plugin geplant ist und welche Ideen offen sind, gruppiert
nach Aufwand und Nutzen: zuerst schnelle Gewinne, dann hohe Priorität,
dann optionale Extras. Nichts davon hat eine feste Version. Was schon
erschienen ist, steht im [Changelog](CHANGELOG.de.md).

Die Reihenfolge folgt einer einfachen Regel: **Pflege und Qualität vor
neuen Features.** Ein Feature, das bestehenden Code bricht, kostet mehr,
als es wert ist.

## Schnelle Gewinne

### Gelesene Bücher pro Jahr

Ein Balkendiagramm der gelesenen Bücher pro Jahr. Zeigt den
langfristigen Trend auf einen Blick, den die 12-Monats-Mittel in
„Kaufrate vs. Leserate“ glätten. Die Monatszahlen gibt es schon; es
fehlen nur die Jahressumme und ein Dialog. Aufwand: klein.

## Hohe Priorität

### Genre- und Kategorie-Auswertung

Gelesene und ungelesene Bücher nach calibre-Schlagwort. Zeigt, welche
Genres sich im SuB stapeln. Dafür müssen die Schlagwörter erst in den
Datenexport. Aufwand: mittel.

## Niedrige Priorität (optional)

### Seiten im SuB *(optional)*

Seiten im SuB, auf Basis einer einstellbaren Seitenzahl-Spalte (die
gelesenen Seiten pro Monat stehen bereits im Bericht unter
„Lesegeschwindigkeit“). calibre 9.3.1 bringt die Spalte „Pages“ mit;
stattdessen lässt sich eine benutzerdefinierte Spalte konfigurieren
(z. B. aus dem Plugin „Count Pages“). Aufwand: klein.

### Lesegeschwindigkeit im Chart *(optional)*

Die Lesegeschwindigkeit (Seiten pro Monat und pro Tag) im Burn-up-Chart
oder im Dialog „Kaufrate vs. Leserate“ zeigen, nicht nur im Bericht. Die
Zahlen gibt es schon (Bericht, „Lesegeschwindigkeit“). Aufwand: klein.
