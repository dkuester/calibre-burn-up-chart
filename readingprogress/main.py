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
from qt.core import QIcon, QMenu, QPixmap, QTimer, QToolButton, pyqtSignal


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
    config.defaults['show_status_tbr'] = True
    # Series names counted as one series: list of lists, first displayed
    config.defaults['series_merge'] = []
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


# Milliseconds to wait after the last library change before the TBR in
# the status bar is recounted, so bulk edits trigger one count
STATUS_REFRESH_DELAY = 1000


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

    # Emitted from calibre's listener thread; the queued connection
    # brings it to the GUI thread.
    _library_edited = pyqtSignal()

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
        # Only shown while Reading Goal has data for the current library
        self.goal_action = menu.addAction(_('Reading goal'),
                                          self.show_goal)
        menu.addAction(_('Time between purchase and reading'),
                       self.show_delay)
        menu.addAction(_('Purchase rate vs. reading rate'),
                       self.show_rates)
        menu.addAction(_('Age of the TBR'), self.show_age)
        menu.addAction(_('Started series'), self.show_started)
        menu.addAction(_('TBR by series'), self.show_series_backlog)
        menu.addSeparator()
        menu.addAction(_('Check data quality'), self.show_quality)
        menu.addAction(_('Save report…'), self.save_report)
        menu.aboutToShow.connect(self._update_goal_action)
        self.qaction.setMenu(menu)

        # Reconfigure the QToolButton after the toolbar is created:
        # MenuButtonPopup = click on main area = default action,
        # small arrow on the right = menu
        QTimer.singleShot(0, self._activate_popup_mode)

        self._status_button = None
        self._listening_db = None
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.setInterval(STATUS_REFRESH_DELAY)
        self._status_timer.timeout.connect(self.refresh_status_tbr)
        self._library_edited.connect(self._status_timer.start)
        # calibre keeps only a weak reference to its listeners
        self._db_listener = self._on_db_event

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
    # TBR in the status bar
    # ------------------------------------------------------------------
    def initialization_complete(self):
        try:
            button = QToolButton(self.gui.status_bar)
            button.setAutoRaise(True)
            button.clicked.connect(self.show_chart)
            self.gui.status_bar.addPermanentWidget(button)
            self._status_button = button
            self._listen_to(self.gui.current_db)
            self.refresh_status_tbr()
        except Exception as e:
            print(f'ReadingProgress: status bar error: {e}')

    def library_about_to_change(self, olddb, db):
        self._listen_to(None)

    def library_changed(self, db):
        self._listen_to(db)
        self.refresh_status_tbr()

    def shutting_down(self):
        self._listen_to(None)
        return True

    def _listen_to(self, db):
        """Moves the change listener to ``db`` (``None``: no library)."""
        if self._listening_db is not None:
            try:
                self._listening_db.new_api.remove_listener(self._db_listener)
            except Exception:
                pass
        self._listening_db = db
        if db is not None:
            db.new_api.add_listener(self._db_listener)

    def _on_db_event(self, event_type, library_id, event_data):
        """Runs in calibre's listener thread: only flags relevant
        changes, the count runs bundled in the GUI thread."""
        from calibre.db.listeners import EventType
        if event_type == EventType.metadata_changed:
            if event_data[0] not in (config['read_column'],
                                     config['last_read_column'],
                                     'timestamp'):
                return
        elif event_type not in (EventType.book_created,
                                EventType.books_removed):
            return
        self._library_edited.emit()

    def refresh_status_tbr(self):
        """Recounts the TBR in the status bar (or hides it)."""
        button = self._status_button
        if button is None:
            return
        visible = bool(config['show_status_tbr'])
        button.setVisible(visible)
        if not visible:
            return
        text, tooltip = self._status_summary()
        button.setText(text)
        button.setToolTip(tooltip)

    def _status_summary(self):
        """``(text, tooltip)`` for the status bar; never shows a dialog."""
        from calibre_plugins.readingprogress.chart_dialog import pace_lines
        from calibre_plugins.readingprogress.export_reading_status import (
            NoDataError,
            export_snapshots,
        )
        from calibre_plugins.readingprogress.status_summary import (
            empty_summary,
            error_summary,
            problem_summary,
            status_summary,
        )

        try:
            db_api = self.gui.current_db.new_api
            read_column = config['read_column']
            last_read_column = config['last_read_column']
            problems = column_problems(custom_column_types(db_api),
                                       read_column, last_read_column)
            if problems:
                return problem_summary(
                    describe_column_problems(problems, _), _)
            rows = export_snapshots(db_api, read_column,
                                    last_read_column)['rows']
            target_date, reduction_factor = _target_settings()
            return status_summary(rows, _, pace_lines(
                rows, target_date, reduction_factor, _date_format(),
                _decimal_separator()))
        except NoDataError:
            return empty_summary(_)
        except Exception:
            traceback.print_exc()
            return error_summary(_)

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

    def _goal_years(self):
        """Goal years of the Reading Goal plugin for the current library
        (see ``reading_goal.parse_goal_data()``), or ``None``. Its file is
        only read, never written."""
        from calibre.utils.config import config_dir
        from calibre_plugins.readingprogress.reading_goal import (
            goal_data_path,
            load_goal_data,
        )
        try:
            library_id = self.gui.current_db.library_id
        except Exception:
            return None
        return load_goal_data(goal_data_path(config_dir, library_id))

    def _update_goal_action(self):
        try:
            visible = self._goal_years() is not None
        except Exception as e:
            print(f'ReadingProgress: Reading Goal data error: {e}')
            visible = False
        self.goal_action.setVisible(visible)

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
                    on_time_range_changed=self._save_time_range,
                    decimal_sep=_decimal_separator()).exec()

    def show_goal(self):
        from datetime import date

        from calibre_plugins.readingprogress.goal_dialog import YearGoalDialog
        from calibre_plugins.readingprogress.reading_goal import (
            library_events,
        )

        years = self._goal_years()
        if years is None:
            self.gui.status_bar.show_message(
                _('The Reading Goal plugin has no data for this library.'),
                8000)
            return
        events = self._read_library(library_events)
        if events is None:
            return
        YearGoalDialog(years, events, date.today(), _date_format(),
                       _decimal_separator(), self.gui, colors=self._colors(),
                       on_show=self._show_in_library).exec()

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
        from calibre_plugins.readingprogress.import_days import (
            find_import_days,
        )
        from calibre_plugins.readingprogress.quality_dialog import (
            QualityDialog,
        )
        from calibre_plugins.readingprogress.series import (
            collect_series,
            find_series_problems,
        )

        def fetch(db_api, read_column, last_read_column):
            problems = find_date_problems(db_api, read_column,
                                          last_read_column)
            read_flags = db_api.all_field_for(read_column,
                                              db_api.all_book_ids())
            series_problems = find_series_problems(
                collect_series(db_api, read_column), config['series_merge'])
            return (problems,
                    sum(1 for v in read_flags.values() if v is True),
                    series_problems,
                    find_import_days(db_api, read_column, last_read_column))

        result = self._read_library(fetch)
        if result is None:
            return
        problems, read_total, series_problems, import_days = result
        if not problems and not series_problems and not import_days:
            info_dialog(
                self.gui, _('Data quality'),
                _('All read books have a usable read date, and no series '
                  'problems or bulk imports were found.'), show=True)
            return

        QualityDialog(problems, read_total, _date_format(), self.gui,
                      on_show=self._show_in_library,
                      series_problems=series_problems,
                      import_days=import_days,
                      on_merge=self._merge_series_names).exec()

    @staticmethod
    def _merge_series_names(names):
        """Adds a group from "Several names" to the merge list."""
        from calibre_plugins.readingprogress.series import add_series_group
        config['series_merge'] = add_series_group(config['series_merge'],
                                                  names)

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

    def show_started(self):
        from calibre_plugins.readingprogress.series import (
            collect_series,
            merge_series,
            started_series,
        )
        from calibre_plugins.readingprogress.started_dialog import (
            StartedSeriesDialog,
        )

        started = self._read_library(
            lambda db_api, read_column, last_read_column: started_series(
                merge_series(collect_series(db_api, read_column,
                                            last_read_column),
                             config['series_merge'])))
        if started is None:
            return
        if not started:
            info_dialog(
                self.gui, _('Started series'),
                _('No started series: every series with at least two books '
                  'is either unread or read completely.'), show=True)
            return

        StartedSeriesDialog(started, _date_format(), self.gui,
                            on_show=self._show_in_library).exec()

    def show_series_backlog(self):
        from calibre_plugins.readingprogress.export_reading_status import (
            backlog_ages,
        )
        from calibre_plugins.readingprogress.series import (
            backlog_by_series,
            collect_series,
            merge_series,
        )
        from calibre_plugins.readingprogress.series_backlog_dialog import (
            SeriesBacklogDialog,
        )

        def fetch(db_api, read_column, _last_read):
            # TBR as in the age chart, so the shares match the charts
            return (backlog_by_series(merge_series(
                        collect_series(db_api, read_column),
                        config['series_merge'])),
                    len(backlog_ages(db_api, read_column)))

        result = self._read_library(fetch)
        if result is None:
            return
        data, backlog = result
        if not data['top']:
            self.gui.status_bar.show_message(
                _('No data available for this analysis.'), 8000)
            return

        SeriesBacklogDialog(data, backlog, _decimal_separator(), self.gui,
                            colors=self._colors(),
                            on_show=self._show_in_library).exec()

    def save_report(self):
        from datetime import date

        from calibre.gui2 import choose_save_file
        from calibre_plugins.readingprogress.chart_dialog import ChartWidget
        from calibre_plugins.readingprogress.export_reading_status import (
            collect_report_data,
        )
        from calibre_plugins.readingprogress.goal_dialog import (
            YearGoalChartWidget,
        )
        from calibre_plugins.readingprogress.rates_dialog import (
            RatesChartWidget,
        )
        from calibre_plugins.readingprogress.reading_goal import (
            library_events,
            report_data,
        )
        from calibre_plugins.readingprogress.report import (
            HTML,
            build_report,
            report_format,
        )
        from calibre_plugins.readingprogress.series import (
            collect_series,
            find_series_problems,
            problem_counts,
        )

        target_date, reduction_factor = _target_settings()
        today = date.today()
        years = self._goal_years()

        def fetch(db_api, read_column, last_read_column):
            data = collect_report_data(db_api, read_column,
                                       last_read_column, target_date,
                                       reduction_factor)
            data['quality'].update(problem_counts(find_series_problems(
                collect_series(db_api, read_column),
                config['series_merge'])))
            events = (library_events(db_api, read_column, last_read_column)
                      if years else None)
            data['goal'] = (report_data(years, events, today)
                            if years else None)
            return data, events

        result = self._read_library(fetch)
        if result is None:
            return
        data, events = result

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
                    forecast=data['forecast'], colors=colors,
                    decimal_sep=_decimal_separator())),
                (_('Purchase rate vs. reading rate'), RatesChartWidget(
                    data['rates'], _decimal_separator(), colors=colors)),
            ]
            if years:
                charts.append((_('Reading goal'), YearGoalChartWidget(
                    years, events, today, _date_format(),
                    _decimal_separator(), colors=colors,
                    year=data['goal']['summary']['year'])))
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
