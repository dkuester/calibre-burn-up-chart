# Roadmap

*[Deutsche Version](ROADMAP.de.md)*

This roadmap captures planned work and ideas for the plugin. It is a
living document – items move between sections as priorities change.

Priorities follow a simple rule: **maintenance and quality before new
features**. A feature that breaks existing code costs more than it is
worth.

## Done

Completed in the current development cycle, shipping with the next
release:

### Unit tests

A `pytest` suite (28 tests) covers the two data-processing entry points:

- `compute_reading_time()` – median, mean, empty input, edge cases
- `export_snapshots()` – snapshot generation, month boundaries, edge cases

It runs against synthetic Calibre-style dictionaries, no real database.

### CI on Codeberg

A Forgejo Actions workflow (`.forgejo/workflows/ci.yml`) runs `ruff` and
`pytest` on every push and pull request.

### Refactoring `ChartWidget`

`ChartWidget` in `chart_dialog.py` is now split into renderer classes:
`AxesRenderer` (axes, grid, tick labels), `SeriesRenderer` (data series
lines), `LegendRenderer` (the legend box) and `AnnotationRenderer`
("Today: X unread" and similar). `ChartWidget` keeps only the
orchestration.

### Forecast line

A dashed forecast line extrapolates the backlog trend (linear regression
over the last 12 months) to show where the TBR is heading if the current
reading rate continues. It is configurable ("Show forecast line", on by
default) and annotates the realistic date the backlog reaches 0, next to
the desired target date.

### Interactive tooltips

Hovering over a data point shows its date and the total/read/backlog
values at that point.

### Zoom and pan

Mouse wheel zooms in and out around the cursor, dragging pans, and a
double-click resets the view to fit.

### Configurable colors

The colors of all data series and reference lines can be changed in the
plugin settings (with sensible defaults).

## Planned

Features we intend to build, but without a fixed target version.

### Purchase rate vs. reading rate

Two lines showing how many books are added per month and how many are
read per month. Complements the burn-up chart by showing the underlying
dynamics.

### Dark mode support

Adapt the chart colors to Calibre's current theme using
`palette().color(QPalette.Window)` and friends. Currently the chart
assumes a light theme.

### PNG export

A button in the chart dialog: "Save as PNG". Uses `widget.render(QPixmap)`
to write the current chart to a file. Useful for reports or sharing.

### Configurable time range

Options for "Last 2 years", "Last 5 years", "All time". Especially
useful as the library grows and early years become a flat line.

### Export to Calibre column

Write computed values into a custom column, e.g. "days until read" per
book. Then the Calibre interface itself can sort and filter by that
value – e.g. "show me the books I have owned longest without reading".

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

- Status bar widget showing current backlog permanently
- Context menu on selected books: "how long has this book been unread?"
- Automatic virtual shelf "long unread" (> 1000 days)

### Data quality

- Dialog listing books with missing `#last_read`
- Bulk edit helper for `#last_read` (backfill from "read" status changes)

### Sharing

- Copy chart to clipboard
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