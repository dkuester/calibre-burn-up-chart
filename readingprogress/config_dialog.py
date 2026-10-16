from calibre_plugins.readingprogress import config
from calibre_plugins.readingprogress.chart_common import (
    DARK_DEFAULT_COLORS,
    DEFAULT_COLORS,
    is_dark_background,
)
from calibre_plugins.readingprogress.localization import _
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
        self.date_edit.setDate(QDate(year, month, day))
        self.date_edit.setMinimumDate(QDate.currentDate())
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

        # --- Explanation ---
        hint = QLabel(_(
            '<b>Target date:</b> Date by which the backlog (TBR) should '
            'reach 0.<br><br>'
            '<b>Gentle reduction:</b> Fraction of the TBR that remains at '
            'the target date. 0.50 means: TBR halved by the target date.'
            '<br><br>'
            '<b>Custom columns:</b> Names of your Calibre columns (with '
            'leading #) used to mark books as read and to store the last '
            'read date.'
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
        bg = self.palette().color(QPalette.Window)
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
