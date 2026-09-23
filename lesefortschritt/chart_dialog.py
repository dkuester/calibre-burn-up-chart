import os

from qt.core import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, Qt, QPixmap
)

from calibre_plugins.lesefortschritt.localization import _


class ChartDialog(QDialog):

    def __init__(self, png_pfad, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_('Reading progress'))

        self._original_pixmap = None

        layout = QVBoxLayout(self)

        if not os.path.exists(png_pfad):
            layout.addWidget(QLabel(
                _('Chart not found:\n{}\n\n'
                  'Did zeichne_chart.py run successfully?').format(png_pfad)
            ))
            self._fuege_buttonzeile_hinzu(layout)
            self._setze_startgroesse()
            return

        pixmap = QPixmap(png_pfad)
        if pixmap.isNull():
            layout.addWidget(QLabel(
                _('Could not load PNG:\n{}').format(png_pfad)
            ))
            self._fuege_buttonzeile_hinzu(layout)
            self._setze_startgroesse()
            return

        self._original_pixmap = pixmap

        self.bild = QLabel()
        self.bild.setAlignment(Qt.AlignCenter)
        self.bild.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        layout.addWidget(self.bild, 1)

        self._fuege_buttonzeile_hinzu(layout)
        self._setze_startgroesse()
        self._zentriere()

    def _fuege_buttonzeile_hinzu(self, layout):
        zeile = QHBoxLayout()
        zeile.addStretch()
        btn = QPushButton(_('Close'))
        btn.clicked.connect(self.accept)
        zeile.addWidget(btn)
        layout.addLayout(zeile)

    def _setze_startgroesse(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(1200, 800)
            return
        verfuegbar = screen.availableGeometry()
        self.resize(
            int(verfuegbar.width()  * 0.90),
            int(verfuegbar.height() * 0.90),
        )

    def _zentriere(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        verfuegbar = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(verfuegbar.center())
        self.move(frame.topLeft())

    def _skaliere(self):
        if self._original_pixmap is None:
            return
        ziel = self.bild.size()
        if ziel.width() < 2 or ziel.height() < 2:
            return
        skaliert = self._original_pixmap.scaled(
            ziel, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.bild.setPixmap(skaliert)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._skaliere()

    def showEvent(self, event):
        super().showEvent(event)
        self._skaliere()