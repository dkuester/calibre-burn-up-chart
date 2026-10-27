# Roadmap

*[Deutsche Version](ROADMAP.de.md)*

This roadmap captures planned work and ideas for the plugin. It is a
living document – items move between sections as priorities change.

Priorities follow a simple rule: **maintenance and quality before new
features**. A feature that breaks existing code costs more than it is
worth.

## Next version

Done, not yet released:

- **Required pace to reach the goal:** two lines below the burn-up
  title and two rows in the report, e.g. "For TBR = 0 by 04.09.2050:
  read 26.4 books/month or buy at most 0.3 books/month." One line for
  TBR = 0, one for the gentle reduction, both at the purchase and
  reading rates of the last 12 months. Turns the goal into a monthly
  number to act on.
- **Yearly reading goal (with the Reading Goal plugin):** the "Reading
  Goal" plugin keeps a yearly list of books per library
  (`plugins/Reading_Goal_Data_<library id>.json`); its goal is that
  list, not a number of its own. Instead of a second goal setting, the
  plugin reads that data (read-only) and shows progress against the
  target as a chart and in the report, enriched with our figures (all
  books read, books added, TBR, reading delay). Shown only when Reading
  Goal has data for the current library.
- **Series checks in the data quality dialog:** a "Series" tab lists
  series under several names ("Expanse", "The Expanse-Serie", "The
  Expanse"), duplicate volume numbers within a series (editions in two
  languages, omnibus volumes, or no number kept) and gaps (an earlier
  volume unread while a later one is read). Names count as the same
  series when they differ only in case, punctuation, a leading article
  or a word like "Series"; a similarity match was tried and dropped
  because it mostly paired different volumes ("Black Panther
  (2005-2008)" and "(2008-2010)"). Cleaner series data makes the series
  analyses below more reliable.

## Done

### 1.7.0

Shipping with 1.7.0:

- **PNG export and clipboard:** All chart dialogs get "Save as PNG…"
  and "Copy to clipboard" buttons. They capture the chart as currently
  shown, including zoom, pan and the active theme.
- **Time range (burn-up chart):** "All time", "Last 5 years" or "Last 2
  years". The limited ranges end today instead of at the target date.
- **Purchase rate vs. reading rate:** a third chart with books added
  and read per month (12-month averages), shaded by whether the backlog
  shrinks or grows.
- **"Days in TBR" column:** a button in the settings creates a calibre
  column that calibre computes itself, so it is always up to date and
  no values are written into the library.
- **Data quality check:** lists read books without a read date or read
  before being added (the charts count them as read on the day added)
  and shows them in calibre's book list for fixing.
- **Age of the TBR:** a bar chart of the unread books by whole years
  since they were added; clicking a bar shows those books in calibre.
- **Reading-delay chart on par:** tooltips naming the book, click to
  show it in calibre, zoom and pan, time range with its own median and
  mean, the configurable read color, and PNG/clipboard export.
- **Report:** saves the key figures of all charts as Markdown or as a
  single HTML page with the burn-up and rate charts embedded.
- **Requires calibre 8.0:** the plugin uses Qt 6 only, so the Qt 5
  compatibility code is gone.
- **Tests and CI:** 110 `pytest` tests with a 100% coverage gate on the
  Qt-free modules (`chart_common`, `config_helpers`,
  `export_reading_status`, `report`). CI runs `ruff` and `pytest` on
  Python 3.10 and 3.12 for every push to `main` and every pull request.
  A `v*` tag publishes the release.
- **Moved to GitHub:** Until October 2026 the project lived on Codeberg
  and used Forgejo Actions. The Codeberg repository is archived.

### Released

Details in the [changelog](CHANGELOG.md).

- **1.6.0:** dark mode for both charts.
- **1.5.0:** forecast line, interactive tooltips, zoom and pan, and
  configurable colors (all for the burn-up chart). `ChartWidget` was
  split into renderer classes. First unit tests and CI.
- **1.4.0:** reading-delay analysis ("time between purchase and
  reading").
- **1.3.0:** charts drawn directly with QPainter; no matplotlib.

## Planned

Features we intend to build, but without a fixed target version.

### Started series with their next volume

A list of series that are started but not finished: series, progress
("60/76"), the next unread volume (number and title) and when something
from the series was last read, so stalled series stand out. Clicking
shows the next volume in calibre, as in the data quality check and the
age chart. Series with a single book in the library are left out. With
gaps, show both the lowest unread volume and the first one after the
highest read volume.

### TBR by series

Which series make up the largest part of the TBR, as bars. Helps decide
what to read down – or what no longer to read at all.

### Merge series names

Reading a series partly in German and partly in English leaves it under
two names ("Die Nebelgeborenen" and "Mistborn", "Das Lied von Eis und
Feuer" and "A Song of Ice and Fire"). A list in the settings merges such
names, e.g. `Die Nebelgeborenen = Mistborn`. The series names in calibre
stay unchanged; "Started series", "TBR by series" and the series checks
count the names as one series. Groups from "Several names" in the data
quality dialog can be taken over with one click. Automatic detection
(same author, other language) was tried on real data and dropped: 42
pairs, only about 5 of them real, because an author with several series
pairs with all of them.

### Series progress chart

One stacked bar (read/unread) per started series, sorted by progress.
Visually appealing, but close to "Started series" in content.

## Ideas

Broader ideas, none of them committed.

### Additional analyses

- Reading rate per month / year (bar chart)
- Genre and category breakdown
- Page-count based analysis
- Author analysis
- Activity heatmap (GitHub-contributions style)

### UX improvements

- Status bar widget showing current backlog permanently

## Not planned

Ideas that were considered and rejected. Listed here so they do not
keep coming up.

### "How long unread?" context menu and "long unread" shelf

Both are covered by the "Days in TBR" column: sort by it, or create a
virtual library with the search `#days_in_tbr:>1000 and #gelesen:false`
(using your read column).

### Bulk backfill of `#last_read` from status changes

calibre keeps no history of when a book was marked as read, so there is
nothing to backfill from. The data quality check lists the affected
books instead, so they can be fixed by hand.

### Stacked bar chart

An alternative chart design where books read and backlog are shown as
stacked yearly bars, with the total library as a line. Prototyped in
matplotlib during v1.3.0 development, but the pure line chart turned
out to be visually cleaner. The prototype is documented in the
development history but not implemented.

### External charting libraries

matplotlib was used in versions up to 1.2.0 to render the chart as a
PNG in a subprocess. Removed in 1.3.0 because it required an external
Python installation and introduced needless file-system round trips.
The current implementation draws directly in Calibre using QPainter.

### QtCharts

Considered as an alternative to QPainter. Not available in the official
Calibre distribution, so would not work without installing extra
packages. Rejected in favor of the QPainter approach, which has zero
external dependencies.