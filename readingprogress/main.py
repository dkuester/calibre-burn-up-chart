import os
import traceback
import zipfile

from calibre.gui2 import error_dialog, info_dialog
from calibre.gui2.actions import InterfaceAction
from calibre.utils.config import JSONConfig
from calibre.utils.localization import get_lang
from calibre_plugins.readingprogress import config
from calibre_plugins.readingprogress.chart_common import (
    DEFAULT_COLORS,
    all_colors_are_light_defaults,
)
from calibre_plugins.readingprogress.config_helpers import (
    column_problems,
    custom_column_types,
    date_format,
    decimal_separator,
    describe_column_problems,
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


def _target_settings():
    """(target_date, reduction_factor) from the settings."""
    from datetime import datetime
    try:
        target_date = datetime.fromisoformat(config['target_date']).date()
    except ValueError:
        target_date = datetime(2050, 9, 4).date()
    return target_date, float(config['reduction_factor'])


def _chart_png_base64(widget, width=1200, height=700):
    """Renders ``widget`` off screen and returns it as base64 PNG."""
    import base64
    import tempfile
    widget.resize(width, height)
    fd, path = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    try:
        if not widget.grab().save(path, 'PNG'):
            return None
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('ascii')
    finally:
        os.remove(path)


def _date_format():
    """Locale date format for the current Calibre UI language."""
    return date_format(get_lang().split('_')[0])


def _decimal_separator():
    """Decimal separator for the current Calibre UI language."""
    return decimal_separator(get_lang().split('_')[0])


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
        menu.addAction(_('Purchase rate vs. reading rate'),
                       self.show_rates)
        menu.addAction(_('Age of the TBR'), self.show_age)
        menu.addSeparator()
        menu.addAction(_('Check data quality'), self.show_quality)
        menu.addAction(_('Save report…'), self.save_report)
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
                    tb.setPopupMode(
                        QToolButton.ToolButtonPopupMode.MenuButtonPopup)
                    return
        except Exception as e:
            print(f'ReadingProgress: PopupMode error: {e}')

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def _read_library(self, fetch):
        """``fetch(db_api, read_column, last_read_column)`` after checking
        the configured columns.

        :return: its result, or ``None`` if the columns are unusable, the
            library has no data or reading failed – the user has then
            been told why.
        """
        from calibre_plugins.readingprogress.export_reading_status import (
            NoDataError,
        )

        db_api = self.gui.current_db.new_api
        read_column = config['read_column']
        last_read_column = config['last_read_column']
        try:
            problems = column_problems(custom_column_types(db_api),
                                       read_column, last_read_column)
            if not problems:
                return fetch(db_api, read_column, last_read_column)
        except NoDataError:
            self.gui.status_bar.show_message(
                _('No data available for this analysis.'), 8000)
            return None
        except Exception:
            error_dialog(self.gui, _('Export failed'),
                         _('Could not read the library.'),
                         det_msg=traceback.format_exc(), show=True)
            return None
        error_dialog(
            self.gui, _('Column not usable'),
            '\n'.join(describe_column_problems(problems, _)) + '\n\n'
            + _('You can change the column names in the plugin settings.'),
            show=True)
        return None

    @staticmethod
    def _colors():
        return {key: config[f'color_{key}'] for key in DEFAULT_COLORS}

    @staticmethod
    def _save_time_range(key):
        config['time_range'] = key

    def _show_in_library(self, book_ids):
        from calibre_plugins.readingprogress.export_reading_status import (
            id_search,
        )
        self.gui.search.set_search_string(id_search(book_ids))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def show_chart(self):
        from calibre_plugins.readingprogress.chart_dialog import ChartDialog
        from calibre_plugins.readingprogress.export_reading_status import (
            export_snapshots,
            forecast_backlog,
        )

        info = self._read_library(export_snapshots)
        if info is None:
            return

        target_date, reduction_factor = _target_settings()
        self.gui.status_bar.show_message(
            _('Reading status: {read}/{total} read, backlog {backlog}').format(
                read=info['read'], total=info['total'],
                backlog=info['backlog']), 5000)

        show_forecast = bool(config['show_forecast'])
        forecast = forecast_backlog(info['rows']) if show_forecast else None
        ChartDialog(info['rows'], target_date, reduction_factor,
                    _date_format(), self.gui,
                    show_forecast=show_forecast, forecast=forecast,
                    colors=self._colors(), time_range=config['time_range'],
                    on_time_range_changed=self._save_time_range).exec()

    def show_delay(self):
        from calibre_plugins.readingprogress.delay_dialog import DelayChartDialog
        from calibre_plugins.readingprogress.export_reading_status import (
            compute_reading_time,
        )

        def fetch(db_api, read_column, last_read_column):
            info = compute_reading_time(db_api, read_column, last_read_column)
            ids = [p[2] for p in info['points']]
            titles = db_api.all_field_for('title', ids)
            authors = db_api.all_field_for('authors', ids)
            books = {i: (titles.get(i) or '',
                         ' & '.join(authors.get(i) or ()))
                     for i in ids}
            return info['points'], books

        result = self._read_library(fetch)
        if result is None:
            return
        points, books = result
        if not points:
            self.gui.status_bar.show_message(
                _('No data available for this analysis.'), 8000)
            return

        # Median and mean are in the chart header, computed for the
        # selected time range.
        DelayChartDialog(
            points, _date_format(), _decimal_separator(), self.gui,
            books=books, colors=self._colors(),
            time_range=config['time_range'],
            on_time_range_changed=self._save_time_range,
            on_show=self._show_in_library).exec()

    def show_rates(self):
        from calibre_plugins.readingprogress.export_reading_status import (
            compute_rates,
            export_snapshots,
        )
        from calibre_plugins.readingprogress.rates_dialog import (
            RatesChartDialog,
        )

        info = self._read_library(export_snapshots)
        if info is None:
            return
        RatesChartDialog(
            compute_rates(info['rows']), _decimal_separator(), self.gui,
            colors=self._colors(), time_range=config['time_range'],
            on_time_range_changed=self._save_time_range).exec()

    def show_quality(self):
        from calibre_plugins.readingprogress.export_reading_status import (
            find_date_problems,
        )
        from calibre_plugins.readingprogress.quality_dialog import (
            QualityDialog,
        )

        def fetch(db_api, read_column, last_read_column):
            problems = find_date_problems(db_api, read_column,
                                          last_read_column)
            read_flags = db_api.all_field_for(read_column,
                                              db_api.all_book_ids())
            return problems, sum(1 for v in read_flags.values() if v is True)

        result = self._read_library(fetch)
        if result is None:
            return
        problems, read_total = result
        if not problems:
            info_dialog(
                self.gui, _('Data quality'),
                _('All read books have a usable read date.'), show=True)
            return

        QualityDialog(problems, read_total, _date_format(), self.gui,
                      on_show=self._show_in_library).exec()

    def show_age(self):
        from calibre_plugins.readingprogress.age_dialog import AgeChartDialog
        from calibre_plugins.readingprogress.export_reading_status import (
            MAX_AGE_YEARS,
            age_buckets,
            backlog_ages,
            median_age_years,
        )

        ages = self._read_library(
            lambda db_api, read_column, _last_read: backlog_ages(
                db_api, read_column))
        if ages is None:
            return
        if not ages:
            self.gui.status_bar.show_message(
                _('No data available for this analysis.'), 8000)
            return

        summary = {
            'median_years': median_age_years(ages),
            'oldest_year': min(a[1] for a in ages).year,
        }
        AgeChartDialog(age_buckets(ages), MAX_AGE_YEARS, summary,
                       _decimal_separator(), self.gui, colors=self._colors(),
                       on_show=self._show_in_library).exec()

    def save_report(self):
        from datetime import date

        from calibre.gui2 import choose_save_file
        from calibre_plugins.readingprogress.chart_dialog import ChartWidget
        from calibre_plugins.readingprogress.export_reading_status import (
            collect_report_data,
        )
        from calibre_plugins.readingprogress.rates_dialog import (
            RatesChartWidget,
        )
        from calibre_plugins.readingprogress.report import (
            HTML,
            build_report,
            report_format,
        )

        target_date, reduction_factor = _target_settings()
        data = self._read_library(
            lambda db_api, read_column, last_read_column: collect_report_data(
                db_api, read_column, last_read_column, target_date,
                reduction_factor))
        if data is None:
            return

        today = date.today()
        path = choose_save_file(
            self.gui, 'readingprogress-report', _('Save report'),
            filters=[(_('HTML page'), ['html']), (_('Markdown'), ['md'])],
            all_files=False,
            initial_filename='reading-progress-{}.html'.format(
                today.isoformat()))
        if not path:
            return
        fmt = report_format(path)
        if fmt == HTML and not path.lower().endswith(('.html', '.htm')):
            path += '.html'

        images = []
        if fmt == HTML:
            colors = self._colors()
            charts = [
                (_('Burn-up chart'), ChartWidget(
                    data['rows'], target_date, reduction_factor,
                    _date_format(), show_forecast=bool(
                        config['show_forecast']),
                    forecast=data['forecast'], colors=colors)),
                (_('Purchase rate vs. reading rate'), RatesChartWidget(
                    data['rates'], _decimal_separator(), colors=colors)),
            ]
            for caption, widget in charts:
                png = _chart_png_base64(widget)
                widget.deleteLater()
                if png:
                    images.append((caption, png))

        text = build_report(
            data, fmt, _, _date_format(), _decimal_separator(),
            title=_('Reading progress report – {date}').format(
                date=today.strftime(_date_format())),
            images=images)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
        except OSError as e:
            error_dialog(self.gui, _('Export failed'),
                         _('Could not write {path}.').format(path=path),
                         det_msg=str(e), show=True)
            return
        self.gui.status_bar.show_message(
            _('Report saved: {path}').format(path=path), 8000)
