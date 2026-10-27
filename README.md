<div align="center">

# Reading Progress for calibre

**See how your library, your read books and your to-be-read pile grow over time, right inside calibre.**

[![Release](https://img.shields.io/github/v/release/dkuester/calibre-burn-up-chart?label=release)](https://github.com/dkuester/calibre-burn-up-chart/releases/latest)
[![CI](https://github.com/dkuester/calibre-burn-up-chart/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/dkuester/calibre-burn-up-chart/actions/workflows/ci.yml)
[![calibre](https://img.shields.io/badge/calibre-8.0%2B-informational)](#requirements)
[![License](https://img.shields.io/github/license/dkuester/calibre-burn-up-chart)](LICENSE)

[Installation](#installation) · [Features](#features) · [Configuration](#configuration) · [Development](#development) · [Changelog](CHANGELOG.md) · [Roadmap](ROADMAP.md) · [Deutsch](README.de.md)

</div>

Reading Progress is a calibre plugin that draws your reading progress as a
burn-up chart. It reconstructs the history from your library's metadata (the
date a book was added and two custom columns) and shows how the total library,
the books you have read and your backlog (TBR) developed month by month, back
to the oldest book in the library. Everything runs inside calibre; no extra
Python installation is needed.

---

## Features

| Feature | Description |
|---|---|
| **Burn-up chart** | Total library, cumulative books read and backlog over time, as monthly snapshots. |
| **Target date** | A goal line "TBR = 0 on …" with a date you choose. |
| **Gentle reduction** | A second, more realistic reference line, e.g. TBR halved by the target date (adjustable factor). |
| **Required pace** | Below the title: how many books per month to read, or at most to buy, to reach the goal (TBR = 0 and gentle reduction) by the target date, based on the same typical purchase and reading rates as the forecast. |
| **Forecast** | Continues today's TBR with the typical month (mean of the last 24 full months without the 20 % highest and lowest, so bulk imports barely count) as a dashed line, with a shaded band for 80 % of cases and the realistic month range for TBR = 0 – or how fast it grows. Needs 3 full months; marked as preliminary below 12. |
| **Yearly reading goal** | With the separately installed [Reading Goal](https://www.mobileread.com/forums/showthread.php?t=355769) plugin: list books read against the target over the year, projection, required pace, pages, monthly figures, previous-year comparison and all books read according to your own data. Reading Goal's data is only read. |
| **Purchase rate vs. reading rate** | Books added and books read per month as 12-month averages; the area between them shows whether the backlog shrinks or grows. |
| **Days in TBR column** | One click in the settings adds a calibre column with each book's days in the TBR, always up to date and sortable. |
| **Age of the TBR** | Unread books by whole years since they were added; click a bar to show those books in calibre. |
| **Started series** | Series begun but not finished, with progress, the next unread volume and when the series was last read, stalled ones first; shows the next volume in calibre. |
| **TBR by series** | The 20 series with the most unread books as bars, with their share of the TBR; click a bar to show the series' unread books in calibre. |
| **TBR in the status bar** | Permanently "TBR: 1652 ▲172" with the change against 12 months ago; tooltip with read/total and the required pace, click opens the burn-up chart. Can be turned off. |
| **Merge series names** | One series under several names, e.g. read partly in German and partly in English (`Die Nebelgeborenen = Mistborn`), counts as one in the series analyses; a volume read in one language counts as read. Groups from the data quality check can be taken over with one click. The series names in calibre stay unchanged. |
| **Report** | Saves the key figures as Markdown or as a single HTML page with the burn-up and rate charts, plus the yearly goal with Reading Goal. |
| **Data quality check** | Lists read books without a read date or read before being added, and series problems: one series under several names, duplicate volume numbers and gaps (an earlier volume unread although a later one is read), plus days that look like a bulk import (many books from many series and authors), whose date added is probably wrong. Shows the books in calibre's book list for fixing. |
| **Reading delay** | For each book marked as read: the time between adding it to calibre and reading it, as a scatter plot with median and mean; hover names the book, click shows it in calibre. |
| **Time range** | Show all time, or only the last 5 or 2 years up to today. |
| **Interactive** | Tooltips in every chart. In the burn-up and reading-delay charts, zoom with the mouse wheel, pan by dragging, double-click to reset. |
| **Export** | Save any chart as a PNG or copy it to the clipboard, exactly as shown (zoom, pan, theme). |
| **Your colors, your theme** | Every series and reference line can be recolored. Charts follow calibre's light or dark theme. |
| **Bilingual** | English and German interface, following calibre's language. More languages can be added in `translations/<lang>/`. |

## Requirements

- calibre 8.0 or newer
- Two custom columns in your library (names can be changed in the settings):

| Column | Type | Purpose |
|---|---|---|
| `#gelesen` | Yes/No | Marks a book as read |
| `#last_read` | Date | Date the book was last read |

## Installation

1. Download `ReadingProgress-<version>.zip` from the [latest release](https://github.com/dkuester/calibre-burn-up-chart/releases/latest).
2. In calibre: *Preferences → Advanced → Plugins → Load plugin from file*, select the zip.
3. Restart calibre.
4. Add the button to the toolbar: *Preferences → Interface → Toolbars & menus →
   The main toolbar*, then add **Burn-up Chart** from the available actions.

> [!TIP]
> Installing from a clone works too:
> `calibre-customize -b <path-to-clone>/readingprogress`.

## Usage

The toolbar button opens a menu with four charts (five with Reading Goal), a data check and a report:

- **Burn-up chart**: library size, books read and backlog over time.
- **Reading goal**: progress of the Reading Goal plugin's yearly list against the target. Shown only when the plugin has data for the current library.
- **Time between purchase and reading**: the reading delay per book.
- **Purchase rate vs. reading rate**: books added and read per month.
- **Age of the TBR**: unread books by years since they were added.
- **Started series**: series begun but not finished, with the next volume to read.
- **TBR by series**: the series with the most unread books.
- **Check data quality**: read books without a usable read date and series problems (several names, duplicate volume numbers, gaps) and bulk-import days, to fix them in calibre; series under several names can be merged from there.
- **Save report…**: the key figures as Markdown, or as an HTML page with charts.

The right of the status bar permanently shows the TBR, e.g. "TBR: 1652 ▲172"
(arrow: change against 12 months ago). The tooltip gives read/total and the
required pace; a click opens the burn-up chart.

## Configuration

*Preferences → Advanced → Plugins → Reading Progress → Customize plugin*:

| Setting | Meaning |
|---|---|
| Target date | The day the backlog (TBR) should reach 0. |
| Gentle reduction (factor) | Share of the TBR left on the target date. `0.50` means the TBR is halved by then. |
| Show forecast line | Draws the forecast line with its uncertainty band and note (on by default). |
| Show the TBR in the status bar | Shows the whole library's TBR on the right of calibre's status bar (on by default). |
| Colors | Color of each series and reference line. Empty means "follow the theme"; *Reset colors to theme defaults* clears all custom colors. |
| Custom column "read" / "last read" | Lookup names of the two columns, if yours are named differently. |
| Create column "Days in TBR" | Adds a column `#days_in_tbr` that calibre computes itself: days between adding and reading for read books, days since adding for unread ones. Sort by it to find the books you have owned longest without reading. Restart calibre afterwards. |
| Merge series | One series per line, its names in calibre separated by `=`, e.g. `Die Nebelgeborenen = Mistborn`. The first name is displayed. "Started series", "TBR by series", the series checks and the report count them as one series. |

The settings are stored in `plugins/readingprogress.json` in calibre's
configuration folder and persist across restarts.

## Development

```bash
git clone https://github.com/dkuester/calibre-burn-up-chart.git
cd calibre-burn-up-chart
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest      # tests, coverage threshold enforced
.venv/bin/ruff check .          # lint
```

CI runs ruff and pytest (Python 3.10 and 3.12) on every push to `main` and
every pull request.

<details>
<summary><strong>Project structure</strong></summary>

```
readingprogress/
├── __init__.py              # plugin metadata, version
├── main.py                  # GUI integration (toolbar action, menu)
├── config_dialog.py         # settings dialog
├── config_helpers.py        # Qt-free config/locale and migration helpers
├── chart_common.py          # Qt-free chart math and colors
├── age_dialog.py            # age-of-the-TBR dialog
├── chart_dialog.py          # burn-up chart dialog (QPainter)
├── goal_dialog.py           # yearly reading goal dialog
├── import_days.py           # Qt-free bulk-import day detection
├── quality_dialog.py        # data quality dialog
├── rates_dialog.py          # purchase rate vs. reading rate dialog
├── reading_goal.py          # Qt-free, read-only Reading Goal data
├── report.py                # Qt-free Markdown/HTML report
├── series.py                # Qt-free series data, merging, series checks, started series, TBR by series
├── series_backlog_dialog.py # TBR-by-series chart dialog
├── status_summary.py        # Qt-free text and tooltip of the status-bar TBR
├── started_dialog.py        # started-series dialog
├── delay_dialog.py          # reading-delay chart dialog
├── export_reading_status.py # reads the live calibre database
├── localization.py          # gettext setup
├── images/icon.png
└── translations/de/LC_MESSAGES/readingprogress.{po,mo}
tests/                       # pytest suite
```

`export_reading_status.py` runs inside the calibre process and uses the live
database (`self.gui.current_db.new_api`). Charts are drawn with Qt's QPainter.

</details>

<details>
<summary><strong>Releasing</strong></summary>

The plugin follows [Semantic Versioning](https://semver.org/). The version is the
`__version__` tuple in `readingprogress/__init__.py`.

1. Update `__version__` and add an entry to [CHANGELOG.md](CHANGELOG.md) and
   [CHANGELOG.de.md](CHANGELOG.de.md).
2. Merge to `main` via pull request.
3. Tag the merge commit: `git tag -a v1.7.0 -m "…" && git push origin v1.7.0`.
4. CI builds `ReadingProgress-<version>.zip` and publishes the release.

</details>

## Support

| | |
|---|---|
| Bug reports and ideas | [Issues](https://github.com/dkuester/calibre-burn-up-chart/issues). Please include your calibre version and operating system. |
| Downloads and changelog | [Releases](https://github.com/dkuester/calibre-burn-up-chart/releases) · [CHANGELOG.md](CHANGELOG.md) |
| Planned features | [ROADMAP.md](ROADMAP.md) |
| Earlier history | Pull requests up to v1.6.0 are in the [archived Codeberg repository](https://codeberg.org/hortizept/calibre-burn-up-chart). |
| Contributing | Pull requests against `main`; CI must pass. |

## AI assistance

This plugin is developed with the help of AI coding assistants. Design
decisions, review and testing in calibre are done by a human.

## License

[GNU General Public License v3.0](LICENSE)
