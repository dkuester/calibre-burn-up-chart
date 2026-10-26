# Roadmap

*[Deutsche Version](ROADMAP.de.md)*

This roadmap captures planned work and ideas for the plugin. It is a
living document – items move between sections as priorities change.

Priorities follow a simple rule: **maintenance and quality before new
features**. A feature that breaks existing code costs more than it is
worth.

## Done

### Next release

Merged into `main`, shipping with the next release:

- **PNG export and clipboard:** Both chart dialogs get "Save as PNG…"
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
- **Tests and CI:** 79 `pytest` tests with a 100% coverage gate on the
  Qt-free modules (`chart_common`, `config_helpers`,
  `export_reading_status`). CI runs `ruff` and `pytest` on Python 3.10
  and 3.12 for every push to `main` and every pull request. A `v*` tag
  publishes the release.
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

Nothing at the moment; the next candidates come from the ideas below.

## Ideas

Broader ideas, none of them committed.

### Additional analyses

- Reading rate per month / year (bar chart)
- Genre and category breakdown
- Page-count based analysis
- Author analysis
- Age distribution of the backlog
- Activity heatmap (GitHub-contributions style)

### UX improvements

- Parity for the reading-delay chart (tooltips, zoom/pan, configurable
  colors), which currently keeps fixed colors and no interaction
- Status bar widget showing current backlog permanently
- Context menu on selected books: "how long has this book been unread?"
- Automatic virtual shelf "long unread" (> 1000 days)

### Data quality

- Dialog listing books with missing `#last_read`
- Bulk edit helper for `#last_read` (backfill from "read" status changes)

### Sharing

- Markdown / HTML report of key metrics

## Not planned

Ideas that were considered and rejected. Listed here so they do not
keep coming up.

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