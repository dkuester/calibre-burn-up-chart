"""
Shared chart helpers with no Qt or Calibre dependency.

Kept free of Qt imports on purpose, so the pure math (axis scaling,
view/zoom windows) is unit-testable outside Calibre. Imported flatly by
the test suite (see ``tests/conftest.py``) and as a package module by the
plugin code.
"""

import math
from collections import namedtuple
from datetime import date, timedelta

# Configurable series colors, light-theme defaults (hex strings).
DEFAULT_COLORS = {
    "total":    "#888888",
    "read":     "#2a9d8f",
    "backlog":  "#e76f51",
    "goal":     "#264653",
    "stable":   "#f4a261",
    "soft":     "#8ecae6",
    "forecast": "#8338ec",
}

# Series colors tuned for a dark theme (higher luminance for contrast).
DARK_DEFAULT_COLORS = {
    "total":    "#b8b8b8",
    "read":     "#3fd0b0",
    "backlog":  "#ff8a75",
    "goal":     "#8fc3d9",
    "stable":   "#ffb066",
    "soft":     "#a5d8f0",
    "forecast": "#b18cf0",
}

# Non-configurable "chrome" (axis/grid/text/boxes) per theme. Values are
# hex strings except ``box_bg`` (an RGB tuple; alpha is applied at the
# QColor call site).
CHROME = {
    False: {
        "axis":   "#333333",
        "grid":   "#e0e0e0",
        "text":   "#222222",
        "border": "#cccccc",
        "muted":  "#555555",
        "error":  "#cc0000",
        "box_bg": (255, 255, 255),
    },
    True: {
        "axis":   "#b5b5b5",
        "grid":   "#404040",
        "text":   "#dddddd",
        "border": "#555555",
        "muted":  "#a0a0a0",
        "error":  "#ff6b6b",
        "box_bg": (58, 58, 58),
    },
}

# Fixed series colors for the reading-delay scatter chart (not user
# configurable), per theme.
DELAY_COLORS = {
    False: {
        "points": "#2a9d8f",
        "median": "#264653",
        "mean":   "#f4a261",
    },
    True: {
        "points": "#3fd0b0",
        "median": "#8fc3d9",
        "mean":   "#ffb066",
    },
}


def is_dark_background(rgb):
    """True if the (r, g, b) background is dark (needs light chrome)."""
    r, g, b = rgb
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return luminance < 0.5


def chrome_colors(rgb):
    """Chrome palette (axis/grid/text/boxes) for a background color."""
    return CHROME[is_dark_background(rgb)]


def delay_colors(rgb):
    """Fixed series colors for the delay chart, for a background color."""
    return DELAY_COLORS[is_dark_background(rgb)]


def resolve_series_colors(dark, overrides):
    """Series colors as hex, from theme defaults plus explicit overrides.

    ``overrides`` maps key -> hex, or '' (empty = follow theme).
    """
    defaults = DARK_DEFAULT_COLORS if dark else DEFAULT_COLORS
    resolved = {}
    for key, default_hex in defaults.items():
        hex_val = (overrides or {}).get(key) or default_hex
        resolved[key] = hex_val
    return resolved


def all_colors_are_light_defaults(stored):
    """True if every stored series color equals the light-theme default.

    ``stored`` maps color key -> resolved value (after config defaults),
    so ``''`` means "follow theme, not yet set". True only when the user
    never customized a color (all values still the old light defaults).
    """
    return all(stored.get(k) == DEFAULT_COLORS[k] for k in DEFAULT_COLORS)


def nice_step(max_value):
    """A "nice" tick step (1/2/2.5/5 x 10^n) for a value axis."""
    if max_value <= 0:
        return 1
    raw = max_value / 5.0
    magnitude = 10 ** math.floor(math.log10(raw))
    for factor in (1, 2, 2.5, 5, 10):
        step = factor * magnitude
        if step >= raw:
            return step
    return 10 * magnitude  # pragma: no cover  (factor=10 always returns)


def compute_y_axis(max_value):
    """(tick step, rounded-up axis maximum) for a value axis."""
    if max_value <= 0:
        return 1, 1
    step = nice_step(max_value)
    y_max = math.ceil(max_value / step) * step
    return step, y_max


def year_tick_step(year_span):
    """Year-marker interval for an x-axis spanning ``year_span`` years."""
    if year_span <= 5:
        return 1
    if year_span <= 15:
        return 2
    if year_span <= 40:
        return 5
    return 10


# A zoom/pan window: [x_min, x_max] date range plus the y-axis maximum.
View = namedtuple('View', ['x_min', 'x_max', 'y_max'])


def zoom_view(x_min, x_max, y_max, fit_x_min, fit_x_max, fit_y_max, fx,
              factor, min_window_days=30):
    """New (x_min, x_max, y_max) after zooming by ``factor`` around ``fx``.

    ``factor`` > 1 zooms in (narrower range); < 1 zooms out. ``fx`` is the
    cursor position as a fraction of the plot width (0 = left, 1 = right).
    The window is clamped to the fit range and never zooms out beyond it.
    """
    full_x_days = (fit_x_max - fit_x_min).days
    if full_x_days <= 0:
        return View(x_min, x_max, y_max)

    fx = min(max(fx, 0.0), 1.0)
    x_days = (x_max - x_min).days
    new_x_days = x_days / factor
    min_x_days = min(min_window_days, full_x_days)
    new_x_days = max(min(new_x_days, full_x_days), min_x_days)

    if new_x_days >= full_x_days:
        new_x_min, new_x_max = fit_x_min, fit_x_max
    else:
        anchor_ord = x_min.toordinal() + fx * x_days
        new_x_min_ord = round(anchor_ord - fx * new_x_days)
        new_x_min = date.fromordinal(new_x_min_ord)
        new_x_max = date.fromordinal(new_x_min_ord + round(new_x_days))
        if new_x_min < fit_x_min:
            new_x_min = fit_x_min
            new_x_max = date.fromordinal(new_x_min.toordinal()
                                         + round(new_x_days))
        if new_x_max > fit_x_max:
            new_x_max = fit_x_max
            new_x_min = date.fromordinal(new_x_max.toordinal()
                                         - round(new_x_days))

    new_y_max = max(y_max / factor, 1.0)
    if new_y_max > fit_y_max:
        new_y_max = fit_y_max

    return View(new_x_min, new_x_max, new_y_max)


def pan_view(x_min, x_max, y_max, fit_x_min, fit_x_max, shift_days):
    """(x_min, x_max, y_max) shifted horizontally by ``shift_days``,
    clamped to the fit range. The window width and y_max are unchanged."""
    new_x_min = x_min + timedelta(days=shift_days)
    new_x_max = x_max + timedelta(days=shift_days)

    if new_x_min < fit_x_min:
        drift = (fit_x_min - new_x_min).days
        new_x_min = fit_x_min
        new_x_max = new_x_max + timedelta(days=drift)
    if new_x_max > fit_x_max:
        drift = (new_x_max - fit_x_max).days
        new_x_max = fit_x_max
        new_x_min = new_x_min - timedelta(days=drift)

    return View(new_x_min, new_x_max, y_max)


def export_filename(kind, today=None):
    """Suggested file name for a PNG export, e.g.
    ``reading-progress-burn-up-2026-10-26.png``."""
    if today is None:
        today = date.today()
    return 'reading-progress-{}-{}.png'.format(kind, today.isoformat())


def ensure_png_suffix(path):
    """``path`` with a ``.png`` suffix (kept if already present, any case)."""
    if path.lower().endswith('.png'):
        return path
    return path + '.png'


# Selectable time ranges of the burn-up chart: (config key, years).
# None = everything from the first snapshot up to the target date.
TIME_RANGES = (('all', None), ('5y', 5), ('2y', 2))


def years_before(day, years):
    """``day`` shifted back by ``years``; Feb 29 becomes Feb 28."""
    try:
        return day.replace(year=day.year - years)
    except ValueError:
        return day.replace(year=day.year - years, day=28)


def fit_x_range(first, today, target, range_key):
    """(x_min, x_max) of the unzoomed burn-up chart for ``range_key``.

    'all' (and any unknown key) spans ``first`` … ``target``. A limited
    range covers the last N years up to ``today``, but never starts
    before ``first``.
    """
    years = dict(TIME_RANGES).get(range_key)
    if years is None:
        return first, target
    return max(first, years_before(today, years)), today


def visible_y_max(rows, x_min, x_max):
    """Largest total/read/backlog value of the rows within
    [x_min, x_max]; all rows count if none fall inside."""
    visible = [r for r in rows if x_min <= r[0] <= x_max] or rows
    return max(max(r[1], r[2], r[3]) for r in visible)
