# Changelog

*[Deutsche Version](CHANGELOG.de.md)*

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.3.0] – 2026-09-25

### Changed

- The intermediate CSV file has been removed. `export_lesestatus.py`
  now returns the monthly snapshots directly, and `main.py` passes them
  to `zeichne_chart.py` as JSON via stdin. This eliminates the last
  write-and-read round trip through the filesystem.

### Removed

- `--log-pfad` parameter of `zeichne_chart.py` (replaced by JSON input
  via stdin).
- CSV output is no longer written by default. `exportiere()` only
  writes a CSV if `log_pfad` is explicitly passed (used by the
  standalone `calibre-debug -e` mode for debugging).

## [1.2.0] – 2026-09-23

### Added

- Custom column names (`#gelesen`, `#last_read`) are now configurable
  through the settings dialog. This allows the plugin to work for users
  whose Calibre columns have different names.
- Automatic detection of a Python 3 interpreter with matplotlib.
  Supports Homebrew (Apple Silicon and Intel), system Python, and `PATH`.
- Clearer error message when matplotlib is missing.

### Changed

- All temporary files (CSV, PNG, cache) now live in
  `tempfile.gettempdir()`. The plugin therefore also works on Windows.
- Date format in chart and settings dialog adapts to the language:
  `DD.MM.YYYY` for German, `YYYY-MM-DD` otherwise.
- `.mo` cache filenames include a hash of the source ZIP to avoid
  collisions when multiple versions are installed side by side.
- `SyntaxWarning` filter now only targets the Kobo plugin instead of
  applying process-wide.

### Removed

- Hardcoded paths (`/Users/daniel/...`, `/opt/homebrew/bin/python3`)
  have been removed from `main.py`.

## [1.1.0] – 2026-09-23

### Added

- Multilingual support via gettext. English is the source language,
  German is included as the first translation.
- Translation file `translations/de/LC_MESSAGES/lesefortschritt.po`
  with the German strings for plugin UI, dialogs, and chart.

### Changed

- All user-visible strings in `main.py`, `config_dialog.py`,
  `chart_dialog.py`, and `zeichne_chart.py` are now translatable via `_()`.
- `zeichne_chart.py` optionally accepts `--translation-mo` so that
  chart labels appear in the language selected in Calibre.

## [1.0.0] – 2026-09-23

### Added

- Historical time series of reading status derived from the Calibre
  library, with monthly snapshots going back to the oldest book.
- Burn-up chart with total library, cumulative books read, and backlog.
- Configurable target date and reduction factor via plugin settings.
- Chart dialog with automatic scaling to screen size.
- Custom plugin icon (burn-up motif).
- Toolbar integration via Calibre's InterfaceAction API.