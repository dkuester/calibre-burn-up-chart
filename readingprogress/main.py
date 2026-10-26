import os
import zipfile

from calibre.gui2.actions import InterfaceAction
from calibre.utils.config import JSONConfig
from calibre.utils.localization import get_lang
from calibre_plugins.readingprogress import config
from calibre_plugins.readingprogress.chart_common import (
    DEFAULT_COLORS,
    all_colors_are_light_defaults,
)
from calibre_plugins.readingprogress.config_helpers import (
    date_format,
    migrate_legacy_keys,
)
from calibre_plugins.readingprogress.localization import _
from qt.core import QIcon, QMenu, QPixmap, QTimer, QToolButton


def _setup_config():
    """Config defaults + one-time migrations.

    Runs at this module's import (plugin activation), NOT from
    ``__init__.py``: ``calibre-customize -b`` executes ``__init__.py`` in
    a context where sibling imports resolve to the *installed* plugin, so
    the color defaults and migrations must live where those imports are
    resolved normally.
    """
    config.defaults['target_date'] = '2050-09-04'
    config.defaults['reduction_factor'] = 0.5
    config.defaults['read_column'] = '#gelesen'
    config.defaults['last_read_column'] = '#last_read'
    config.defaults['show_forecast'] = True
    config.defaults['time_range'] = 'all'
    for color_key in DEFAULT_COLORS:
        config.defaults[f'color_{color_key}'] = ''   # '' = follow theme
    config.defaults['_migrated_keys'] = False
    config.defaults['_migrated_colors_auto'] = False

    # One-time migration from the legacy German config keys.
    if not config['_migrated_keys']:
        legacy = JSONConfig('plugins/lesefortschritt')
        legacy.defaults.update({
            'ziel_datum': '2050-09-04',
            'abbau_faktor': 0.5,
            'spalte_gelesen': '#gelesen',
            'spalte_last_read': '#last_read',
        })
        for new_key, value in migrate_legacy_keys(config, legacy).items():
            config[new_key] = value
        config['_migrated_keys'] = True

    # One-time: reset colors to auto if none were ever customized.
    if not config['_migrated_colors_auto']:
        stored = {k: config[f'color_{k}'] for k in DEFAULT_COLORS}
        if all_colors_are_light_defaults(stored):
            for k in DEFAULT_COLORS:
                config[f'color_{k}'] = ''
        config['_migrated_colors_auto'] = True


_setup_config()


def _load_icon():
    """Loads the plugin icon from images/icon.png – folder or ZIP."""
    plugin_dir = os.path.dirname(os.path.abspath(__file__))

    if plugin_dir.endswith('.zip'):
        with zipfile.ZipFile(plugin_dir) as z:
            try:
                data = z.read('images/icon.png')
            except KeyError:
                return None
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return None
        return QIcon(pixmap)

    path = os.path.join(plugin_dir, 'images', 'icon.png')
    if not os.path.exists(path):
        return None
    pixmap = QPixmap(path)
    if pixmap.isNull():
        return None
    return QIcon(pixmap)


def _date_format():
    """Locale date format for the current Calibre UI language."""
    return date_format(get_lang().split('_')[0])


class ReadingProgressAction(InterfaceAction):

    name = 'Reading Progress'
    action_spec = (_('Burn-up Chart'), None,
                   _('Reading statistics for your library'), None)
    action_type = 'current'

    def genesis(self):
        # Set the icon (errors must not break anything)
        try:
            icon = _load_icon()
            if icon is not None:
                self.qaction.setIcon(icon)
        except Exception as e:
            print(f'ReadingProgress: icon error: {e}')

        # Default action when clicking the button's main area
        self.qaction.triggered.connect(self.show_chart)

        # Menu with both options – appears when clicking the arrow
        menu = QMenu(self.gui)
        menu.addAction(_('Burn-up chart'), self.show_chart)
        menu.addAction(_('Time between purchase and reading'),
                       self.show_delay)
        self.qaction.setMenu(menu)

        # Reconfigure the QToolButton after the toolbar is created:
        # MenuButtonPopup = click on main area = default action,
        # small arrow on the right = menu
        QTimer.singleShot(0, self._activate_popup_mode)

    def _activate_popup_mode(self):
        """Sets the QToolButton to MenuButtonPopup."""
        try:
            for tb in self.gui.findChildren(QToolButton):
                if tb.defaultAction() is self.qaction:
                    tb.setPopupMode(QToolButton.MenuButtonPopup)
                    return
        except Exception as e:
            print(f'ReadingProgress: PopupMode error: {e}')

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def show_chart(self):
        from datetime import datetime

        from calibre_plugins.readingprogress.chart_dialog import ChartDialog
        from calibre_plugins.readingprogress.export_reading_status import (
            export_snapshots,
            forecast_backlog,
        )

        try:
            info = export_snapshots(
                db_api=self.gui.current_db.new_api,
                read_column=config['read_column'],
                last_read_column=config['last_read_column'],
            )
        except Exception as e:
            self.gui.status_bar.show_message(
                _('Export failed: {}').format(e), 5000)
            return

        try:
            target_date = datetime.fromisoformat(config['target_date']).date()
        except ValueError:
            target_date = datetime(2050, 9, 4).date()
        reduction_factor = float(config['reduction_factor'])

        date_format = _date_format()

        self.gui.status_bar.show_message(
            _('Reading status: {read}/{total} read, backlog {backlog}').format(
                read=info['read'], total=info['total'],
                backlog=info['backlog']), 5000)

        show_forecast = bool(config['show_forecast'])
        forecast = forecast_backlog(info['rows']) if show_forecast else None
        colors = {key: config[f'color_{key}'] for key in DEFAULT_COLORS}

        dlg = ChartDialog(info['rows'], target_date, reduction_factor,
                          date_format, self.gui,
                          show_forecast=show_forecast, forecast=forecast,
                          colors=colors, time_range=config['time_range'],
                          on_time_range_changed=self._save_time_range)
        dlg.exec_()

    @staticmethod
    def _save_time_range(key):
        config['time_range'] = key

    def show_delay(self):
        from calibre_plugins.readingprogress.delay_dialog import DelayChartDialog
        from calibre_plugins.readingprogress.export_reading_status import (
            compute_reading_time,
        )

        try:
            info = compute_reading_time(
                db_api=self.gui.current_db.new_api,
                read_column=config['read_column'],
                last_read_column=config['last_read_column'],
            )
        except Exception as e:
            self.gui.status_bar.show_message(
                _('Export failed: {}').format(e), 5000)
            return

        if not info['points']:
            self.gui.status_bar.show_message(
                _('No data available for this analysis.'), 8000)
            return

        s = info['statistics']
        self.gui.status_bar.show_message(
            _('Median: {med} days, mean: {mean} days (n={n})').format(
                med=int(round(s['median'])),
                mean=int(round(s['mean'])),
                n=s['count']), 5000)

        dlg = DelayChartDialog(
            info['points'], info['statistics'], self.gui)
        dlg.exec_()
