# Calibre Burn-up Chart Plugin

*[Deutsche Version](README.de.md)*

A Calibre plugin that displays reading progress as a burn-up chart.
It reconstructs the historical time series from the Calibre metadata
(`timestamp` and custom columns) and draws the progression of total
library size, books read, and backlog (TBR).

## Features

- **Historical time series:** Monthly snapshots derived from book metadata,
  going back to the oldest book in the library.
- **Burn-up chart:** Total library, cumulative books read, and backlog
  over time.
- **Configurable target date:** Goal line "TBR = 0 on …" with a freely
  selectable date via the plugin settings.
- **Gentle reduction:** Additional reference line for a more realistic
  scenario (TBR halved by the target date, adjustable factor).
- **Forecast line:** Extrapolates the backlog trend (linear regression
  over the last 12 months) as a dashed line, marking the realistic date
  the TBR reaches 0. Toggleable in the settings, on by default.
- **Interactive tooltips:** Hover over a data point to see its date and
  values.
- **Zoom and pan:** Mouse wheel zooms, drag to pan, double-click resets.
- **Configurable colors:** Recolor every series and reference line in the
  settings.
- **In-GUI display:** The chart opens as a dialog inside Calibre, with
  automatic scaling to screen size.
- **Bilingual:** German and English interface, depending on Calibre's
  language setting. Additional languages can be added via
  `translations/<lang>/`.
- **Reading delay analysis:** For each book marked as read, the time
  between adding it to Calibre and reading it is computed. The result
  is shown as a scatter plot with median and mean lines.

## Requirements

- Calibre 5.0 or newer
- No external Python installation required. Everything runs inside Calibre.
- Two custom columns in Calibre:
  - `#gelesen` (Yes/No) – marks books as read
  - `#last_read` (Date) – date of the last reading

## Installation

1. Clone the repository:

   ```bash
   git clone <repo-url> ~/GitHub/calibre-burn-up-chart
   ```

2. Install the plugin in Calibre:

   ```bash
   calibre-customize -b ~/GitHub/calibre-burn-up-chart/readingprogress
   ```

3. Restart Calibre.

4. Add the action to the toolbar:
   *Preferences → Interface → Toolbars & menus → The main toolbar*
   → add "Burn-up Chart" from the list of available actions.

## Usage

Clicking the toolbar button opens a dropdown menu with two options:

- **Burn-up chart** – the historical progression of library size,
  books read, and backlog.
- **Time between purchase and reading** – delay statistics per book.

### Configuration

Under *Preferences → Advanced → Plugins → Reading Progress → Customize*
you can adjust:

- **Target date:** The day on which the backlog (TBR) should reach 0.
- **Gentle reduction (factor):** Fraction of the TBR that remains at
  the target date. `0.50` means: TBR halved by the target date.
- **Show forecast line:** Whether the forecast line is drawn (on by
  default).
- **Colors:** The color of each data series and reference line (total,
  read, backlog, goal, constant, gentle, forecast).

The values are stored in
`~/Library/Preferences/calibre/plugins/readingprogress.json` and persist
across Calibre restarts.

## Versioning

This plugin follows [Semantic Versioning](https://semver.org/).
The current version is maintained as a `__version__` tuple in
`readingprogress/__init__.py` and is displayed by Calibre in the plugins
list. All changes are documented in [CHANGELOG.md](CHANGELOG.md)
([German version](CHANGELOG.de.md)).

Releases are marked in Git as annotated tags with a `v` prefix
(e.g. `v1.0.0`). To bump the version:

1. Update `__version__` in `readingprogress/__init__.py`.
2. Add an entry to `CHANGELOG.md`.
3. Rebuild and test the plugin.
4. Commit and tag:

   ```bash
   git commit -am "Release v1.0.1"
   git tag -a v1.0.1 -m "Short description"
   ```

Planned features and ideas are tracked in [ROADMAP.md](ROADMAP.md).

## Project structure

```
calibre-burn-up-chart/
├── .forgejo/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── README.md
├── README.de.md
├── LICENSE
├── AGENTS.md
├── CHANGELOG.md
├── CHANGELOG.de.md
├── ROADMAP.md
├── ROADMAP.de.md
├── make_icon.py
├── pyproject.toml
├── requirements-dev.txt
├── tests/
│   ├── conftest.py
│   ├── test_helpers.py
│   ├── test_chart_common.py
│   ├── test_compute_reading_time.py
│   ├── test_export_snapshots.py
│   └── test_forecast.py
└── readingprogress/
    ├── __init__.py                          # Plugin metadata, version
    ├── plugin-import-name-readingprogress.txt
    ├── localization.py                      # gettext setup
    ├── main.py                              # GUI integration
    ├── config_dialog.py                     # Settings dialog
    ├── chart_common.py                      # Shared Qt-free chart math + colors
    ├── chart_dialog.py                      # Chart display dialog
    ├── delay_dialog.py                      # Reading-delay chart dialog
    ├── export_reading_status.py             # Data retrieval from Calibre
    ├── images/
    │   └── icon.png                         # Plugin icon
    └── translations/
        └── de/LC_MESSAGES/
            ├── readingprogress.po
            └── readingprogress.mo
```

## Technical notes

- `export_reading_status.py` runs **inside** the Calibre process and uses
  the live database (`self.gui.current_db.new_api`).
- All processing runs inside Calibre's embedded Python. The chart is 
  drawn directly using Qt's QPainter API.

## Development

Run the test suite and linter in a virtualenv:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
.venv/bin/ruff check .
```

A Forgejo Actions workflow (`.forgejo/workflows/ci.yml`) runs the same
checks on every push and pull request.

## License

GNU General Public License v3.0 – see [LICENSE](LICENSE).