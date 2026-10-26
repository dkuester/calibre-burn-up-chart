"""Tests for the Qt-free chart helpers in chart_common."""

import re
from datetime import date

import chart_common as cc
import pytest


def test_nice_step():
    assert cc.nice_step(0) == 1
    assert cc.nice_step(50) == 10
    assert cc.nice_step(100) == 20


def test_compute_y_axis():
    assert cc.compute_y_axis(0) == (1, 1)
    assert cc.compute_y_axis(50) == (10, 50)
    assert cc.compute_y_axis(96) == (20, 100)
    assert cc.compute_y_axis(210) == (50, 250)
    assert cc.compute_y_axis(1000) == (200, 1000)


def test_compute_y_axis_small_value():
    step, y_max = cc.compute_y_axis(1)
    assert step == pytest.approx(0.2)
    assert y_max == pytest.approx(1.0)


def test_year_tick_step():
    assert cc.year_tick_step(3) == 1
    assert cc.year_tick_step(5) == 1
    assert cc.year_tick_step(5.5) == 2
    assert cc.year_tick_step(15) == 2
    assert cc.year_tick_step(15.5) == 5
    assert cc.year_tick_step(40) == 5
    assert cc.year_tick_step(41) == 10


def test_zoom_view_in_narrows_and_scales_y():
    fit_x_min = date(2024, 1, 1)
    fit_x_max = date(2025, 1, 1)  # 366 days
    nx_min, nx_max, ny_max = cc.zoom_view(
        fit_x_min, fit_x_max, 100.0,
        fit_x_min, fit_x_max, 100.0, fx=0.5, factor=1.25)
    assert nx_min >= fit_x_min
    assert nx_max <= fit_x_max
    assert (nx_max - nx_min).days < 366
    assert ny_max == pytest.approx(80.0)


def test_zoom_view_out_clamps_to_fit():
    fit_x_min = date(2024, 1, 1)
    fit_x_max = date(2025, 1, 1)
    result = cc.zoom_view(
        fit_x_min, fit_x_max, 100.0,
        fit_x_min, fit_x_max, 100.0, fx=0.5, factor=0.8)
    assert result == (fit_x_min, fit_x_max, 100.0)


def test_zoom_view_left_and_right_anchor():
    fit_x_min = date(2024, 1, 1)
    fit_x_max = date(2025, 1, 1)
    nx_min, _, _ = cc.zoom_view(
        fit_x_min, fit_x_max, 100.0,
        fit_x_min, fit_x_max, 100.0, fx=0.0, factor=1.25)
    assert nx_min == fit_x_min
    _, nx_max, _ = cc.zoom_view(
        fit_x_min, fit_x_max, 100.0,
        fit_x_min, fit_x_max, 100.0, fx=1.0, factor=1.25)
    assert nx_max == fit_x_max


def test_pan_view_clamps_to_fit():
    fit_x_min = date(2024, 1, 1)
    fit_x_max = date(2024, 4, 1)   # 91 days (leap-year Feb)
    view_min = date(2024, 2, 1)
    view_max = date(2024, 3, 1)    # 29-day window
    # pan far right -> pinned to the right edge
    nx_min, nx_max, ny_max = cc.pan_view(
        view_min, view_max, 50.0, fit_x_min, fit_x_max, shift_days=1000)
    assert nx_max == fit_x_max
    assert (nx_max - nx_min).days == (view_max - view_min).days
    assert ny_max == 50.0
    # pan far left -> pinned to the left edge
    nx_min, nx_max, _ = cc.pan_view(
        view_min, view_max, 50.0, fit_x_min, fit_x_max, shift_days=-1000)
    assert nx_min == fit_x_min
    assert (nx_max - nx_min).days == (view_max - view_min).days


def test_zoom_view_empty_fit_range():
    fit = date(2024, 1, 1)
    result = cc.zoom_view(fit, fit, 100.0, fit, fit, 100.0, fx=0.5, factor=0.8)
    assert result == (fit, fit, 100.0)


def test_zoom_view_left_clamp():
    # zooming out with the cursor right of the left edge pulls the window
    # past fit_x_min -> the left edge is clamped back to the fit range.
    fit_x_min = date(2024, 1, 1)
    fit_x_max = date(2025, 1, 1)          # 366 days
    view_min = date(2024, 1, 1)           # == fit_x_min
    view_max = date(2024, 7, 1)           # 182 days
    result = cc.zoom_view(
        view_min, view_max, 100.0,
        fit_x_min, fit_x_max, 100.0, fx=0.3, factor=0.8)
    assert result.x_min == fit_x_min            # clamped
    assert result.x_max < fit_x_max             # not a full fit
    assert (result.x_max - result.x_min).days == round(182 / 0.8)


def test_zoom_view_right_clamp():
    # zooming out with the cursor left of the right edge pulls the window
    # past fit_x_max -> the right edge is clamped back to the fit range.
    fit_x_min = date(2024, 1, 1)
    fit_x_max = date(2025, 1, 1)          # 366 days
    view_min = date(2024, 7, 1)
    view_max = date(2025, 1, 1)           # == fit_x_max, 184 days
    result = cc.zoom_view(
        view_min, view_max, 100.0,
        fit_x_min, fit_x_max, 100.0, fx=0.7, factor=0.8)
    assert result.x_max == fit_x_max            # clamped
    assert result.x_min > fit_x_min             # not a full fit
    assert (result.x_max - result.x_min).days == round(184 / 0.8)


def test_default_colors_keys_and_format():
    assert list(cc.DEFAULT_COLORS) == ['total', 'read', 'backlog', 'goal',
                                       'stable', 'soft', 'forecast']
    for value in cc.DEFAULT_COLORS.values():
        assert re.match(r'^#[0-9a-fA-F]{6}$', value)


def test_view_is_namedtuple():
    fit_x_min = date(2024, 1, 1)
    fit_x_max = date(2025, 1, 1)
    result = cc.zoom_view(
        fit_x_min, fit_x_max, 100.0,
        fit_x_min, fit_x_max, 100.0, fx=0.5, factor=0.8)
    assert result == (fit_x_min, fit_x_max, 100.0)   # tuple-compatible
    assert result.x_min == fit_x_min                   # named fields
    assert result.x_max == fit_x_max
    assert result.y_max == 100.0


def test_is_dark_background():
    assert cc.is_dark_background((255, 255, 255)) is False
    assert cc.is_dark_background((200, 200, 200)) is False
    assert cc.is_dark_background((0, 0, 0)) is True
    assert cc.is_dark_background((40, 40, 40)) is True


def test_chrome_colors():
    light = cc.chrome_colors((255, 255, 255))
    dark = cc.chrome_colors((20, 20, 20))
    assert light['text'] == '#222222'
    assert light['box_bg'] == (255, 255, 255)
    assert dark['text'] == '#dddddd'
    assert dark['box_bg'] == (58, 58, 58)
    assert dark['grid'] == '#404040'


def test_delay_colors():
    light = cc.delay_colors((255, 255, 255))
    dark = cc.delay_colors((20, 20, 20))
    assert light['median'] == '#264653'
    assert dark['median'] == '#8fc3d9'


def test_resolve_series_colors():
    # no overrides -> theme defaults
    assert cc.resolve_series_colors(False, {})['goal'] == '#264653'
    assert cc.resolve_series_colors(True, {})['goal'] == '#8fc3d9'
    # empty-string override = follow theme
    assert cc.resolve_series_colors(True, {'goal': ''})['goal'] == '#8fc3d9'
    # explicit override wins
    assert cc.resolve_series_colors(True, {'goal': '#123456'})['goal'] == '#123456'
    # missing override key -> theme default
    assert cc.resolve_series_colors(True, {'goal': '#123456'})['total'] == '#b8b8b8'
    # light theme, explicit override
    assert cc.resolve_series_colors(False, {'total': '#000000'})['total'] == '#000000'


def test_export_filename():
    assert cc.export_filename('burn-up', date(2026, 10, 26)) == \
        'reading-progress-burn-up-2026-10-26.png'


def test_export_filename_defaults_to_today():
    name = cc.export_filename('delay')
    assert name == 'reading-progress-delay-{}.png'.format(
        date.today().isoformat())


def test_ensure_png_suffix():
    assert cc.ensure_png_suffix('/tmp/chart') == '/tmp/chart.png'
    assert cc.ensure_png_suffix('/tmp/chart.png') == '/tmp/chart.png'
    assert cc.ensure_png_suffix('/tmp/chart.PNG') == '/tmp/chart.PNG'
