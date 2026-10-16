from calibre_plugins.readingprogress import config
from calibre_plugins.readingprogress.localization import _
from qt.core import (
    QCheckBox,
    QDate,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
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
        config['read_column'] = (
            self.read_column_edit.text().strip() or '#gelesen'
        )
        config['last_read_column'] = (
            self.last_read_column_edit.text().strip() or '#last_read'
        )
