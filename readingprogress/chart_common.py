"""
Shared chart helpers with no Qt or Calibre dependency.

Kept free of Qt imports on purpose, so the pure math (axis scaling,
view/zoom windows) is unit-testable outside Calibre. Imported flatly by
the test suite (see ``tests/conftest.py``) and as a package module by the
plugin code.
"""

import math
from datetime import date, timedelta

# Configurable colors (hex strings); axis/grid/text are fixed chrome.
DEFAULT_COLORS = {
    "total":    "#888888",
    "read":     "#2a9d8f",
    "backlog":  "#e76f51",
    "goal":     "#264653",
    "stable":   "#f4a261",
    "soft":     "#8ecae6",
    "forecast": "#8338ec",
}


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
    return 10 * magnitude


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


def zoom_view(x_min, x_max, y_max, fit_x_min, fit_x_max, fit_y_max, fx,
              factor, min_window_days=30):
    """New (x_min, x_max, y_max) after zooming by ``factor`` around ``fx``.

    ``factor`` > 1 zooms in (narrower range); < 1 zooms out. ``fx`` is the
    cursor position as a fraction of the plot width (0 = left, 1 = right).
    The window is clamped to the fit range and never zooms out beyond it.
    """
    full_x_days = (fit_x_max - fit_x_min).days
    if full_x_days <= 0:
        return x_min, x_max, y_max

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

    return new_x_min, new_x_max, new_y_max


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

    return new_x_min, new_x_max, y_max
