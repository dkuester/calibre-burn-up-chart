## [Unreleased]

### Added

- **PNG export and clipboard:** "Save as PNG…" and "Copy to clipboard"
  buttons in both chart dialogs. They capture the chart as currently
  shown, including zoom, pan and the active theme.
- **Age of the TBR:** A new chart shows the unread books by whole years
  since they were added (books of 10 years and more share one bar),
  with counts, shares and the median age. Clicking a bar shows its
  books in calibre's book list. PNG/clipboard export as in the other
  charts.
- **Data quality check:** A new menu entry lists read books whose read
  date the charts cannot use (no read date, or read before being added),
  sortable by date added to spot bulk imports. Selected or all of them
  can be shown in calibre's book list, or saved as CSV. Nothing in the
  library is changed.
- **"Days in TBR" column:** A button in the plugin settings creates a
  calibre column `#days_in_tbr` that calibre computes itself from the
  date added and the read columns: days between adding and reading for
  read books, days since adding for unread ones. It is always up to
  date, sorts numerically and changes no book data.
- **Purchase rate vs. reading rate:** A third chart, opened from the
  toolbar menu. It shows books added and books read per month as
  12-month averages and shades the area between them by whether the
  backlog shrinks or grows. A key-figures line sums up the last 12
  months, and the tooltip shows each month's counts. Time range
  selector and PNG/clipboard export as in the burn-up chart.
- **Time range (burn-up chart):** A "Time range" selector in the chart
  dialog: "All time", "Last 5 years", "Last 2 years". The limited
  ranges end today, so recent history fills the chart; the title then
  names the range and the legend lists only the data series. Zoom and pan stay within the range, and
  the choice is remembered.

### Changed

- Project moved from Codeberg to GitHub; CI and releases now run on
  GitHub Actions.
- Test suite extended to 91 tests with a 100% coverage gate on the
  Qt-free modules; CI runs on Python 3.10 and 3.12.
- Config defaults and migrations moved from `__init__.py` to
  `main.py`, so building with `calibre-customize -b` no longer breaks
  when a new helper is added.

### Fixed

- Lines no longer spill into the axis margins when the burn-up chart is
  zoomed in.

## [1.6.0] – 2026-10-16

### Added

- **Dark mode:** Both charts now follow Calibre's current theme. On a
  dark palette the chart chrome (background, axes, grid, text,
  legend/annotation boxes) switches to light-on-dark colors, and the
  configurable series colors fall back to higher-contrast dark-theme
  defaults unless the user explicitly picked a color. The reading-delay
  chart's fixed colors get dark variants too.

### Changed

- Series colors now default to "follow theme" (empty value) instead of
  fixed hex values; only explicitly picked colors are persisted. A new
  "Reset colors to theme defaults" button clears custom colors.
- One-time color migration: users who never customized a color (still on
  the old light defaults) are switched to "auto" so dark mode applies.

## [1.5.0] – 2026-10-16

### Added

- **Forecast line:** Linear regression over the last 12 months of the
  backlog (TBR), drawn as a dashed line and annotating the realistic
  date the TBR reaches 0, next to the desired target date. Toggleable
  via "Show forecast line" (on by default).
- **Interactive tooltips:** Hovering over a data point shows its date
  and the total/read/backlog values.
- **Zoom and pan:** Mouse wheel zooms around the cursor, dragging pans,
  and a double-click resets the view.
- **Configurable colors:** Every data series and reference line can be
  recolored in the plugin settings.
- Unit test suite (`pytest`, 34 tests) for the data-processing functions.
- Forgejo Actions CI workflow (`ruff` + `pytest` on every push and pull
  request).

### Changed

- Plugin renamed to **"Reading Progress"** (previously "Lesefortschritt").
  The configuration is migrated automatically from the legacy plugin.
- Interface fully internationalized: English identifiers, docstrings and
  comments; German and English UI labels.
- `ChartWidget` drawing split into renderer classes (`AxesRenderer`,
  `SeriesRenderer`, `LegendRenderer`, `AnnotationRenderer`).
- Version bumped to 1.5.0.

## [1.4.0] – 2026-10-02

### Added

- Second analysis option: "Time between purchase and reading". For each
  book marked as read, the plugin computes the delay between the date
  the book was added to Calibre and the date it was last read. The
  result is shown as a scatter plot with a median line, a mean line,
  and a header with summary statistics (median, mean, range, count).
- Dropdown menu on the toolbar button to choose between the burn-up
  chart and the reading-delay analysis.
- New helper `berechne_lesezeit()` in `export_lesestatus.py`.
- New module `delay_dialog.py` with the delay chart widget and dialog.

### Changed

- Version bumped to 1.4.0.

## [1.3.0] – 2026-09-25

### Changed

- The chart is now drawn directly in Calibre using Qt's QPainter API.
  The entire matplotlib subprocess has been removed, along with the
  intermediate CSV file and the PNG output. The plugin no longer
  requires an external Python installation.
- `main.py` has been substantially simplified: it only retrieves the
  data from the live library and opens the chart dialog.

### Removed

- `zeichne_chart.py` (replaced by an in-process QPainter implementation).
- The intermediate CSV file (`/tmp/burndown_log.csv`).
- The rendered PNG file (`/tmp/lesefortschritt.png`).
- The cached `zeichne_chart.py` copy in the temp directory.
- All `subprocess` calls and the Python interpreter search logic.
- The `--log-pfad` and `--ausgabe-pfad` parameters.