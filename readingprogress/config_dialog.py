import traceback

from calibre.gui2 import (
    error_dialog,
    info_dialog,
    question_dialog,
    warning_dialog,
)
from calibre_plugins.readingprogress import config
from calibre_plugins.readingprogress.chart_common import (
    DARK_DEFAULT_COLORS,
    DEFAULT_COLORS,
    is_dark_background,
)
from calibre_plugins.readingprogress.config_helpers import (
    DAYS_IN_TBR_LABEL,
    column_problems,
    custom_column_types,
    days_in_tbr_template,
    describe_column_problems,
)
from calibre_plugins.readingprogress.localization import _
from calibre_plugins.readingprogress.series import (
    format_series_groups,
    parse_series_groups,
    series_group_problems,
)
from qt.core import (
    QCheckBox,
    QColor,
    QColorDialog,
    QDate,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPalette,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)


class ConfigWidget(QWidget):

    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)

        # --- Target date ---
        target_str = config['target_date']
        try:
            year, month, day = (int(x) for x in target_str.split('-'))
        except (ValueError, AttributeError):
            year, month, day = 2050, 9, 4

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        stored = QDate(year, month, day)
        # A stored date in the past stays selectable instead of being
        # silently moved to today.
        self.date_edit.setMinimumDate(min(stored, QDate.currentDate()))
        self.date_edit.setDate(stored)
        layout.addRow(_('Target date:'), self.date_edit)

        # --- Reduction factor ---
        self.factor_edit = QDoubleSpinBox()
        self.factor_edit.setRange(0.0, 1.0)
        self.factor_edit.setSingleStep(0.05)
        self.factor_edit.setDecimals(2)
        self.factor_edit.setValue(float(config['reduction_factor']))
        layout.addRow(_('Gentle reduction (factor):'), self.factor_edit)

        # --- Forecast line ---
        self.forecast_check = QCheckBox(_('Show forecast line'))
        self.forecast_check.setChecked(bool(config['show_forecast']))
        layout.addRow(self.forecast_check)

        # --- TBR in the status bar ---
        self.status_tbr_check = QCheckBox(_('Show the TBR in the status bar'))
        self.status_tbr_check.setChecked(bool(config['show_status_tbr']))
        layout.addRow(self.status_tbr_check)

        # --- Colors (keys come from chart_common.DEFAULT_COLORS) ---
        self._color_buttons = {}
        self._color_modified = {key: False for key in DEFAULT_COLORS}
        color_labels = {
            'total': _('Total library color:'),
            'read': _('Read (cumulative) color:'),
            'backlog': _('Backlog (TBR) color:'),
            'goal': _('Goal line color:'),
            'stable': _('Constant library line color:'),
            'soft': _('Gentle reduction line color:'),
            'forecast': _('Forecast line color:'),
        }
        for key in DEFAULT_COLORS:
            btn = QPushButton()
            btn.setFixedWidth(90)
            self._update_color_button(
                btn, config[f'color_{key}'] or self._theme_default(key))
            btn.clicked.connect(
                lambda checked=False, k=key: self._pick_color(k))
            layout.addRow(color_labels[key], btn)
            self._color_buttons[key] = btn

        reset_btn = QPushButton(_('Reset colors to theme defaults'))
        reset_btn.clicked.connect(self._reset_colors)
        layout.addRow(reset_btn)

        # --- Custom columns ---
        self.read_column_edit = QLineEdit()
        self.read_column_edit.setText(config['read_column'])
        self.read_column_edit.setPlaceholderText('#gelesen')
        layout.addRow(_('Custom column "read":'), self.read_column_edit)

        self.last_read_column_edit = QLineEdit()
        self.last_read_column_edit.setText(config['last_read_column'])
        self.last_read_column_edit.setPlaceholderText('#last_read')
        layout.addRow(_('Custom column "last read":'),
                      self.last_read_column_edit)

        # --- "Days in TBR" composite column ---
        self.tbr_column_btn = QPushButton(_('Create column "Days in TBR"'))
        self.tbr_column_btn.clicked.connect(self._create_days_in_tbr_column)
        self.tbr_column_status = QLabel()
        self.tbr_column_status.setWordWrap(True)
        layout.addRow(self.tbr_column_btn)
        layout.addRow(self.tbr_column_status)
        self._refresh_tbr_column_state()

        # --- Merged series names ---
        self.series_merge_edit = QPlainTextEdit()
        self.series_merge_edit.setPlainText(
            format_series_groups(config['series_merge']))
        self.series_merge_edit.setPlaceholderText(
            'Die Nebelgeborenen = Mistborn')
        # One group per line, so lines do not wrap
        self.series_merge_edit.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.NoWrap)
        self.series_merge_edit.setFixedHeight(
            self.series_merge_edit.fontMetrics().lineSpacing() * 7)
        layout.addRow(QLabel(_('Merge series:')))
        layout.addRow(self.series_merge_edit)

        # --- Explanation ---
        hint = QLabel(_(
            '<b>Target date:</b> Date by which the backlog (TBR) should '
            'reach 0.<br><br>'
            '<b>Gentle reduction:</b> Fraction of the TBR that remains at '
            'the target date. 0.50 means: TBR halved by the target date.'
            '<br><br>'
            '<b>Custom columns:</b> Names of your Calibre columns (with '
            'leading #) used to mark books as read and to store the last '
            'read date.<br><br>'
            '<b>Days in TBR:</b> A column calibre computes itself: for '
            'read books the days between adding and reading, for unread '
            'books the days since adding. Sort by it to find the books '
            'you have owned longest without reading them.<br><br>'
            '<b>Merge series:</b> One series per line, its names in '
            'calibre separated by "=", for example a series you read '
            'partly in German and partly in English. The first name is '
            'displayed. "Started series", "TBR by series" and the data '
            'quality check count them as one series; a volume read in '
            'one language counts as read. The series names in calibre '
            'stay unchanged.'
        ))
        hint.setWordWrap(True)
        layout.addRow(hint)

    def save_settings(self):
        qdate = self.date_edit.date()
        config['target_date'] = (
            f'{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}'
        )
        config['reduction_factor'] = float(self.factor_edit.value())
        config['show_forecast'] = bool(self.forecast_check.isChecked())
        config['show_status_tbr'] = bool(self.status_tbr_check.isChecked())
        for key, btn in self._color_buttons.items():
            config[f'color_{key}'] = (
                btn.text() if self._color_modified[key] else ''
            )
        config['read_column'] = (
            self.read_column_edit.text().strip() or '#gelesen'
        )
        config['last_read_column'] = (
            self.last_read_column_edit.text().strip() or '#last_read'
        )
        groups = parse_series_groups(self.series_merge_edit.toPlainText())
        config['series_merge'] = groups
        self._warn_about_columns()
        self._refresh_status_tbr()
        self._warn_about_series_groups(groups)

    @staticmethod
    def _refresh_status_tbr():
        """Applies the new settings to the TBR in the status bar."""
        from calibre.gui2.ui import get_gui
        gui = get_gui()
        action = gui.iactions.get('Reading Progress') if gui else None
        if action is not None:
            action.refresh_status_tbr()

    def _warn_about_series_groups(self, groups):
        """Warns (after saving) about merge lines without effect."""
        problems = series_group_problems(groups)
        lines = []
        if problems['single']:
            lines.append(_('Lines with only one name are ignored: '
                           '{names}').format(
                names=', '.join(problems['single'])))
        if problems['repeated']:
            lines.append(_('Names in more than one line only count for '
                           'the first: {names}').format(
                names=', '.join(problems['repeated'])))
        if lines:
            warning_dialog(self, _('Merge series'), '\n'.join(lines),
                           show=True)

    def _warn_about_columns(self):
        """Warns (after saving) if the charts cannot use the columns."""
        db = self._library()
        if db is None:
            return
        try:
            problems = column_problems(custom_column_types(db),
                                       config['read_column'],
                                       config['last_read_column'])
        except Exception:
            return
        if problems:
            warning_dialog(
                self, _('Column not usable'),
                '\n'.join(describe_column_problems(problems, _)),
                show=True)

    def _update_color_button(self, btn, hex_value):
        color = QColor(hex_value)
        if not color.isValid():
            color = QColor('#888888')
        btn.setStyleSheet(
            f'background-color: {color.name()};'
            ' border: 1px solid #999999;'
        )
        btn.setText(color.name())

    def _theme_default(self, key):
        bg = self.palette().color(QPalette.ColorRole.Window)
        dark = is_dark_background((bg.red(), bg.green(), bg.blue()))
        return DARK_DEFAULT_COLORS[key] if dark else DEFAULT_COLORS[key]

    def _pick_color(self, key):
        current = QColor(self._color_buttons[key].text())
        color = QColorDialog.getColor(current, self)
        if color.isValid():
            self._update_color_button(self._color_buttons[key], color.name())
            self._color_modified[key] = True

    def _reset_colors(self):
        for key, btn in self._color_buttons.items():
            self._update_color_button(btn, self._theme_default(key))
            self._color_modified[key] = False

    # ------------------------------------------------------------------
    # "Days in TBR" column
    # ------------------------------------------------------------------
    @staticmethod
    def _library():
        """new_api of the open library, or None outside the GUI."""
        from calibre.gui2.ui import get_gui
        gui = get_gui()
        return gui.current_db.new_api if gui is not None else None

    def _refresh_tbr_column_state(self):
        db = self._library()
        key = '#' + DAYS_IN_TBR_LABEL
        if db is None:
            self.tbr_column_btn.setEnabled(False)
            self.tbr_column_status.setText(
                _('Only available while a library is open.'))
        elif key in db.field_metadata.custom_field_keys():
            self.tbr_column_btn.setEnabled(False)
            self.tbr_column_status.setText(
                _('Column {key} exists in this library.').format(key=key))
        elif self._column_pending(db):
            self.tbr_column_btn.setEnabled(False)
            self.tbr_column_status.setText(
                _('Column {key} created. Restart calibre to see it.').format(
                    key=key))
        else:
            self.tbr_column_status.setText('')

    @staticmethod
    def _column_pending(db):
        """True if the column was created but calibre not restarted yet
        (it is in the database, but not loaded)."""
        try:
            labels = {row[0] for row in db.backend.execute(
                'SELECT label FROM custom_columns')}
        except Exception:
            return False
        return DAYS_IN_TBR_LABEL in labels

    def _create_days_in_tbr_column(self):
        db = self._library()
        if db is None:
            return
        read_column = self.read_column_edit.text().strip() or '#gelesen'
        last_read_column = (
            self.last_read_column_edit.text().strip() or '#last_read'
        )
        problems = column_problems(custom_column_types(db), read_column,
                                   last_read_column)
        if problems:
            error_dialog(
                self, _('Column not usable'),
                '\n'.join(describe_column_problems(problems, _)), show=True)
            return

        key = '#' + DAYS_IN_TBR_LABEL
        if not question_dialog(
                self, _('Create column?'),
                _('This adds the column {key} ("Days in TBR") to the '
                  'current library. calibre computes its values from '
                  '{read} and {last_read}; no book data is changed. '
                  'calibre has to be restarted afterwards.').format(
                    key=key, read=read_column,
                    last_read=last_read_column)):
            return
        try:
            db.create_custom_column(
                DAYS_IN_TBR_LABEL, _('Days in TBR'), 'composite', False,
                display={
                    'composite_template': days_in_tbr_template(
                        read_column, last_read_column),
                    'composite_sort': 'number',
                    'make_category': False,
                    'contains_html': False,
                    'use_decorations': False,
                })
        except Exception as e:
            error_dialog(
                self, _('Could not create the column'), str(e),
                det_msg=traceback.format_exc(), show=True)
            return

        self.tbr_column_btn.setEnabled(False)
        self.tbr_column_status.setText(
            _('Column {key} created. Restart calibre to see it.').format(
                key=key))
        info_dialog(
            self, _('Column created'),
            _('Restart calibre to see the column "Days in TBR".'),
            show=True)
