from qt.core import (
    QWidget, QFormLayout, QDateEdit, QDoubleSpinBox, QLabel, QDate
)

from calibre_plugins.lesefortschritt import config
from calibre_plugins.lesefortschritt.localization import _


class ConfigWidget(QWidget):

    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)

        # --- Zieldatum ---
        ziel_str = config['ziel_datum']
        try:
            jahr, monat, tag = (int(x) for x in ziel_str.split('-'))
        except (ValueError, AttributeError):
            jahr, monat, tag = 2050, 9, 4

        self.datum_edit = QDateEdit()
        self.datum_edit.setCalendarPopup(True)
        self.datum_edit.setDisplayFormat('dd.MM.yyyy')
        self.datum_edit.setDate(QDate(jahr, monat, tag))
        self.datum_edit.setMinimumDate(QDate.currentDate())
        layout.addRow(_('Target date:'), self.datum_edit)

        # --- Abbau-Faktor ---
        self.faktor_edit = QDoubleSpinBox()
        self.faktor_edit.setRange(0.0, 1.0)
        self.faktor_edit.setSingleStep(0.05)
        self.faktor_edit.setDecimals(2)
        self.faktor_edit.setValue(float(config['abbau_faktor']))
        layout.addRow(_('Gentle reduction (factor):'), self.faktor_edit)

        # --- Erläuterung ---
        hinweis = QLabel(_(
            '<b>Target date:</b> Date by which the backlog (TBR) should '
            'reach 0.<br><br>'
            '<b>Gentle reduction:</b> Fraction of the TBR that remains at '
            'the target date. 0.50 means: TBR halved by the target date.'
        ))
        hinweis.setWordWrap(True)
        layout.addRow(hinweis)

    def save_settings(self):
        qdate = self.datum_edit.date()
        config['ziel_datum'] = (
            f'{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}'
        )
        config['abbau_faktor'] = float(self.faktor_edit.value())