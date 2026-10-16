"""
Dialog für die Lese-Verzögerungs-Analyse.

Zeigt ein Streudiagramm: x-Achse = wann wurde gelesen, y-Achse = wie
viele Tage lag das Buch ungelesen im Regal. Horizontale Linien markieren
Median und Mittelwert.
"""

import traceback

from calibre_plugins.lesefortschritt.chart_dialog import (
    ALIGN_CENTER,
    ALIGN_RIGHT,
    ALIGN_VCENTER,
    CAP_ROUND,
    LOG_FEHLER,
    PEN_DASH,
    PEN_DOT,
    RENDER_ANTIALIASING,
    RENDER_TEXT_ANTIALIASING,
)
from calibre_plugins.lesefortschritt.localization import _
from qt.core import (
    QColor,
    QDialog,
    QFont,
    QFontMetrics,
    QHBoxLayout,
    QPainter,
    QPen,
    QPointF,
    QPushButton,
    QRectF,
    QVBoxLayout,
    QWidget,
)


class DelayChartWidget(QWidget):
    """Streudiagramm mit Median- und Mittelwertlinie."""

    FARBE_PUNKTE  = QColor("#2a9d8f")
    FARBE_MEDIAN  = QColor("#264653")
    FARBE_MITTEL  = QColor("#f4a261")
    FARBE_ACHSE   = QColor("#333333")
    FARBE_RASTER  = QColor("#e0e0e0")
    FARBE_TEXT    = QColor("#222222")

    RAND_LINKS  = 95
    RAND_RECHTS = 30
    RAND_OBEN   = 95
    RAND_UNTEN  = 65

    def __init__(self, punkte, statistik, datum_format, sprache,
                 parent=None):
        super().__init__(parent)
        self.punkte = punkte
        self.statistik = statistik
        self.datum_format = datum_format
        self.sprache = sprache
        self.setMinimumSize(700, 450)

        # Y-Einheit an die Größenordnung anpassen
        max_tage = statistik["max"]
        if max_tage <= 90:
            self.y_einheit = "tage"
            self.y_faktor = 1.0
            self.y_dezimal = 0
        elif max_tage <= 730:
            self.y_einheit = "monate"
            self.y_faktor = 1.0 / 30.44
            self.y_dezimal = 0
        else:
            self.y_einheit = "jahre"
            self.y_faktor = 1.0 / 365.25
            self.y_dezimal = 1

    # ------------------------------------------------------------------
    def paintEvent(self, event):
        try:
            self._do_paint()
        except Exception as e:
            fehler = traceback.format_exc()
            try:
                with open(LOG_FEHLER, 'w', encoding='utf-8') as f:
                    f.write(fehler)
            except Exception:
                pass
            try:
                painter = QPainter(self)
                painter.fillRect(self.rect(), QColor("#ffffff"))
                painter.setPen(QPen(QColor("#cc0000"), 1))
                painter.drawText(
                    self.rect(), ALIGN_CENTER,
                    f"Fehler beim Zeichnen:\n{type(e).__name__}: {e}\n\n"
                    f"Details: {LOG_FEHLER}",
                )
                painter.end()
            except Exception:
                pass

    def _do_paint(self):
        painter = QPainter(self)
        painter.setRenderHint(RENDER_ANTIALIASING, True)
        painter.setRenderHint(RENDER_TEXT_ANTIALIASING, True)
        painter.fillRect(self.rect(), QColor("#ffffff"))

        if not self.punkte:
            painter.setPen(self.FARBE_TEXT)
            painter.drawText(self.rect(), ALIGN_CENTER,
                             _("No data available for this analysis."))
            painter.end()
            return

        plot = QRectF(
            self.RAND_LINKS,
            self.RAND_OBEN,
            max(50, self.width()  - self.RAND_LINKS - self.RAND_RECHTS),
            max(50, self.height() - self.RAND_OBEN  - self.RAND_UNTEN),
        )

        # X-Bereich: frühestes bis spätestes Lesedatum + kleiner Rand
        x_min_d = self.punkte[0][0]
        x_max_d = self.punkte[-1][0]
        spanne = (x_max_d - x_min_d).days
        if spanne <= 0:
            spanne = 1
        rand = max(1, int(spanne * 0.02))
        from datetime import timedelta
        x_min_d = x_min_d - timedelta(days=rand)
        x_max_d = x_max_d + timedelta(days=rand)
        x_span = (x_max_d - x_min_d).days

        # Y-Bereich in Tagen; dann in die gewählte Einheit umrechnen
        y_max_tage = max(self.statistik["max"], 1)
        y_max_einheit = y_max_tage * self.y_faktor
        y_step, y_max = self._berechne_y_achse(y_max_einheit)

        # Titel und Kennzahlen
        self._zeichne_kopf(painter, plot)

        # Achsen und Raster
        self._zeichne_achsen(painter, plot, x_min_d, x_max_d, x_span,
                             y_max, y_step)

        # Statistiklinien
        self._zeichne_statistiklinien(painter, plot, y_max)

        # Datenpunkte (vorne)
        self._zeichne_punkte(painter, plot, x_min_d, x_span,
                             y_max)

        painter.end()

    # ------------------------------------------------------------------
    def _berechne_y_achse(self, max_wert):
        import math
        if max_wert <= 0:
            return 1, 1
        roh = max_wert / 5.0
        magnitude = 10 ** math.floor(math.log10(roh))
        step = magnitude
        for faktor in (1, 2, 2.5, 5, 10):
            step = faktor * magnitude
            if step >= roh:
                break
        y_max = math.ceil(max_wert / step) * step
        return step, y_max

    def _datum_zu_x(self, datum, x_min, x_span, plot):
        tage = (datum - x_min).days
        return plot.left() + plot.width() * tage / x_span

    def _wert_zu_y(self, wert, y_max, plot):
        return plot.bottom() - plot.height() * wert / y_max

    # ------------------------------------------------------------------
    def _zeichne_kopf(self, painter, plot):
        # Titel
        font_titel = QFont()
        font_titel.setPointSize(14)
        font_titel.setBold(True)
        painter.setFont(font_titel)
        painter.setPen(self.FARBE_TEXT)
        painter.drawText(
            QRectF(plot.left(), 15, plot.width(), 30),
            ALIGN_CENTER, _("Time between purchase and reading"),
        )

        # Kennzahlen-Zeile
        s = self.statistik
        text = _(
            "Median: {med} days · Mean: {mean} days · "
            "Range: {min}–{max} days · n = {n}"
        ).format(
            med=int(round(s["median"])),
            mean=int(round(s["mittel"])),
            min=s["min"],
            max=s["max"],
            n=s["anzahl"],
        )
        font_stats = QFont()
        font_stats.setPointSize(11)
        painter.setFont(font_stats)
        painter.setPen(QColor("#555555"))
        painter.drawText(
            QRectF(plot.left(), 50, plot.width(), 22),
            ALIGN_CENTER, text,
        )

    # ------------------------------------------------------------------
    def _zeichne_achsen(self, painter, plot, x_min_d, x_max_d, x_span,
                        y_max, y_step):
        painter.setPen(QPen(self.FARBE_ACHSE, 1))
        painter.drawLine(QPointF(plot.left(),  plot.top()),
                         QPointF(plot.left(),  plot.bottom()))
        painter.drawLine(QPointF(plot.left(),  plot.bottom()),
                         QPointF(plot.right(), plot.bottom()))

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)

        # Y-Achse
        y_wert = 0.0
        while y_wert <= y_max + 0.001:
            y_pix = self._wert_zu_y(y_wert, y_max, plot)
            pen = QPen(self.FARBE_RASTER, 1)
            pen.setStyle(PEN_DOT)
            painter.setPen(pen)
            painter.drawLine(QPointF(plot.left(),  y_pix),
                             QPointF(plot.right(), y_pix))

            painter.setPen(self.FARBE_TEXT)
            text = f"{y_wert:.{self.y_dezimal}f}"
            breite = fm.horizontalAdvance(text)
            painter.drawText(
                QRectF(plot.left() - 10 - breite, y_pix - 8, breite, 16),
                ALIGN_RIGHT | ALIGN_VCENTER, text,
            )
            y_wert += y_step

        # X-Achse: Jahre
        jahre_spanne = (x_max_d - x_min_d).days / 365.25
        if jahre_spanne <= 5:
            schritt = 1
        elif jahre_spanne <= 15:
            schritt = 2
        elif jahre_spanne <= 40:
            schritt = 5
        else:
            schritt = 10

        from datetime import date as _date
        for jahr in range(x_min_d.year, x_max_d.year + 1):
            if jahr % schritt != 0:
                continue
            try:
                d = _date(jahr, 1, 1)
            except ValueError:
                continue
            x_pix = self._datum_zu_x(d, x_min_d, x_span, plot)
            if x_pix < plot.left() or x_pix > plot.right():
                continue
            painter.setPen(QPen(self.FARBE_ACHSE, 1))
            painter.drawLine(QPointF(x_pix, plot.bottom()),
                             QPointF(x_pix, plot.bottom() + 5))
            painter.setPen(self.FARBE_TEXT)
            t = str(jahr)
            b = fm.horizontalAdvance(t)
            painter.drawText(
                QRectF(x_pix - b / 2, plot.bottom() + 8, b, 18),
                ALIGN_CENTER, t,
            )

        # Achsentitel
        font_titel = QFont()
        font_titel.setPointSize(11)
        painter.setFont(font_titel)
        painter.setPen(self.FARBE_TEXT)

        # X-Achsentitel
        painter.drawText(
            QRectF(plot.left(), plot.bottom() + 28, plot.width(), 20),
            ALIGN_CENTER, _("Read on"),
        )

        # Y-Achsentitel (gedreht)
        y_label_map = {
            "tage":   _("Days until read"),
            "monate": _("Months until read"),
            "jahre":  _("Years until read"),
        }
        y_label = y_label_map[self.y_einheit]
        painter.save()
        painter.translate(22, plot.center().y())
        painter.rotate(-90)
        painter.drawText(
            QRectF(-plot.height() / 2, -10, plot.height(), 20),
            ALIGN_CENTER, y_label,
        )
        painter.restore()

    # ------------------------------------------------------------------
    def _zeichne_statistiklinien(self, painter, plot, y_max):
        # Median
        med_einheit = self.statistik["median"] * self.y_faktor
        y_med = self._wert_zu_y(med_einheit, y_max, plot)
        pen = QPen(self.FARBE_MEDIAN, 2)
        pen.setStyle(PEN_DASH)
        if CAP_ROUND is not None:
            pen.setCapStyle(CAP_ROUND)
        painter.setPen(pen)
        painter.drawLine(QPointF(plot.left(), y_med),
                         QPointF(plot.right(), y_med))

        # Mittelwert
        mit_einheit = self.statistik["mittel"] * self.y_faktor
        y_mit = self._wert_zu_y(mit_einheit, y_max, plot)
        pen = QPen(self.FARBE_MITTEL, 2)
        pen.setStyle(PEN_DOT)
        if CAP_ROUND is not None:
            pen.setCapStyle(CAP_ROUND)
        painter.setPen(pen)
        painter.drawLine(QPointF(plot.left(), y_mit),
                         QPointF(plot.right(), y_mit))

        # Labels an der rechten Seite
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)

        self._zeichne_linien_label(
            painter, plot, y_med, _("Median"),
            self.FARBE_MEDIAN, fm)
        self._zeichne_linien_label(
            painter, plot, y_mit, _("Mean"),
            self.FARBE_MITTEL, fm)

    def _zeichne_linien_label(self, painter, plot, y, text, farbe, fm):
        tw = fm.horizontalAdvance(text) + 12
        th = fm.height() + 4
        box = QRectF(plot.left() + 8, y - th / 2, tw, th)
        painter.setPen(QPen(farbe, 1))
        painter.setBrush(QColor(255, 255, 255, 235))
        painter.drawRoundedRect(box, 4, 4)
        painter.setPen(farbe)
        painter.drawText(box, ALIGN_CENTER, text)

    # ------------------------------------------------------------------
    def _zeichne_punkte(self, painter, plot, x_min, x_span, y_max):
        farbe = QColor(self.FARBE_PUNKTE)
        farbe.setAlpha(150)
        painter.setPen(QPen(farbe, 1))
        painter.setBrush(farbe)
        for lese_datum, tage, _id in self.punkte:
            x = self._datum_zu_x(lese_datum, x_min, x_span, plot)
            y_einheit = tage * self.y_faktor
            y = self._wert_zu_y(y_einheit, y_max, plot)
            if y < plot.top() - 2 or y > plot.bottom() + 2:
                continue
            painter.drawEllipse(QPointF(x, y), 3.5, 3.5)


class DelayChartDialog(QDialog):
    """Dialog, der das Verzögerungs-Chart und einen Schließen-Button zeigt."""

    def __init__(self, punkte, statistik, datum_format, sprache,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Time between purchase and reading"))
        self.resize(1200, 750)

        layout = QVBoxLayout(self)
        self.chart = DelayChartWidget(punkte, statistik, datum_format,
                                      sprache, self)
        layout.addWidget(self.chart, 1)

        zeile = QHBoxLayout()
        zeile.addStretch()
        btn = QPushButton(_("Close"))
        btn.clicked.connect(self.accept)
        zeile.addWidget(btn)
        layout.addLayout(zeile)