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
- **In-GUI display:** The chart opens as a dialog inside Calibre, with
  automatic scaling to screen size.
- **Bilingual:** German and English interface, depending on Calibre's
  language setting. Additional languages can be added via
  `translations/<lang>/`.

## Requirements

- Calibre 5.0 or newer
- Homebrew Python 3 with matplotlib (`brew install python-matplotlib`)
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
   calibre-customize -b ~/GitHub/calibre-burn-up-chart/lesefortschritt
   ```

3. Restart Calibre.

4. Add the action to the toolbar:
   *Preferences → Interface → Toolbars & menus → The main toolbar*
   → add "Burn-up Chart" from the list of available actions.

## Usage

After clicking the **"Burn-up Chart"** button in the main toolbar, the
following happens:

1. The CSV with monthly snapshots is written (`/tmp/burndown_log.csv`).
2. The chart is rendered (`/tmp/lesefortschritt.png`).
3. A dialog opens showing the finished chart.

### Configuration

Under *Preferences → Advanced → Plugins → Lesefortschritt → Customize*
you can adjust:

- **Target date:** The day on which the backlog (TBR) should reach 0.
- **Gentle reduction (factor):** Fraction of the TBR that remains at
  the target date. `0.50` means: TBR halved by the target date.

The values are stored in
`~/Library/Preferences/calibre/plugins/lesefortschritt.json` and persist
across Calibre restarts.

## Versioning

This plugin follows [Semantic Versioning](https://semver.org/).
The current version is maintained as a `__version__` tuple in
`lesefortschritt/__init__.py` and is displayed by Calibre in the plugins
list. All changes are documented in [CHANGELOG.md](CHANGELOG.md)
([German version](CHANGELOG.de.md)).

Releases are marked in Git as annotated tags with a `v` prefix
(e.g. `v1.0.0`). To bump the version:

1. Update `__version__` in `lesefortschritt/__init__.py`.
2. Add an entry to `CHANGELOG.md`.
3. Rebuild and test the plugin.
4. Commit and tag:

   ```bash
   git commit -am "Release v1.0.1"
   git tag -a v1.0.1 -m "Short description"
   ```

## Project structure

```
calibre-burn-up-chart/
├── .gitignore
├── README.md
├── README.de.md
├── LICENSE
├── AGENTS.md
├── CHANGELOG.md
├── CHANGELOG.de.md
├── make_icon.py
└── lesefortschritt/
    ├── __init__.py                          # Plugin metadata, version
    ├── plugin-import-name-lesefortschritt.txt
    ├── localization.py                      # gettext setup
    ├── main.py                              # GUI integration
    ├── config_dialog.py                     # Settings dialog
    ├── chart_dialog.py                      # Chart display dialog
    ├── export_lesestatus.py                 # Data retrieval from Calibre
    ├── zeichne_chart.py                     # Chart rendering (matplotlib)
    ├── images/
    │   └── icon.png                         # Plugin icon
    └── translations/
        └── de/LC_MESSAGES/
            ├── lesefortschritt.po
            └── lesefortschritt.mo
```

## Technical notes

- `export_lesestatus.py` runs **inside** the Calibre process and uses
  the live database (`self.gui.current_db.new_api`).
- `zeichne_chart.py` runs **outside** as a subprocess under Homebrew
  Python, because Calibre's embedded Python does not include matplotlib.
- Communication between the two runs via `/tmp` files:
  `/tmp/burndown_log.csv` (data) and `/tmp/lesefortschritt.png` (chart).

## License

GNU General Public License v3.0 – see [LICENSE](LICENSE).