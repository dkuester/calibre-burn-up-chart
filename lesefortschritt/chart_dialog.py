"""
Chart-Dialog für das Lesefortschritt-Plugin.

Zeichnet das Burn-up-Chart direkt mit QPainter in einem QWidget.
Keine externen Abhängigkeiten außer Qt (in Calibre enthalten).
"""

import traceback

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
    Qt,
    QVBoxLayout,
    QWidget,
)

# Fehlerprotokoll für paintEvent (zum Debuggen)
LOG_FEHLER = '/tmp/lesefortschritt_paint_error.log'


def _qt_enum(*pfade):
    """Ermittelt einen Qt-Enum-Wert versionsunabhängig.

    Probiert nacheinander die angegebenen Attributpfade.
    Beispiel: _qt_enum(['PenStyle', 'DashLine'], ['DashLine'])
    → Qt.PenStyle.DashLine (modern) oder Qt.DashLine (alt).
    """
    for pfad in pfade:
        if isinstance(pfad, str):
            pfad = [pfad]
        obj = Qt
        ok = True
        for teil in pfad:
            obj = getattr(obj, teil, None)
            if obj is None:
                ok = False
                break
        if ok:
            return obj
    return None


def _render_hint(*pfade):
    """Ermittelt einen QPainter.RenderHint versionsunabhängig."""
    for pfad in pfade:
        if isinstance(pfad, str):
            pfad = [pfad]
        obj = QPainter
        ok = True
        for teil in pfad:
            obj = getattr(obj, teil, None)
            if obj is None:
                ok = False
                break
        if ok:
            return obj
    return None


# Robust ermittelte Enums (mit Fallback auf numerische Qt-Werte)
ALIGN_CENTER  = _qt_enum(['AlignmentFlag', 'AlignCenter'],
                         ['AlignCenter'])  or 0x0004
ALIGN_LEFT    = _qt_enum(['AlignmentFlag', 'AlignLeft'],
                         ['AlignLeft'])    or 0x0001
ALIGN_RIGHT   = _qt_enum(['AlignmentFlag', 'AlignRight'],
                         ['AlignRight'])   or 0x0002
ALIGN_VCENTER = _qt_enum(['AlignmentFlag', 'AlignVCenter'],
                         ['AlignVCenter']) or 0x0080

PEN_SOLID   = _qt_enum(['PenStyle', 'SolidLine'],
                       ['SolidLine'])   or 1
PEN_DASH    = _qt_enum(['PenStyle', 'DashLine'],
                       ['DashLine'])    or 2
PEN_DOT     = _qt_enum(['PenStyle', 'DotLine'],
                       ['DotLine'])     or 3
PEN_DASHDOT = _qt_enum(['PenStyle', 'DashDotLine'],
                       ['DashDotLine']) or 4
PEN_NOPEN   = _qt_enum(['PenStyle', 'NoPen'],
                       ['NoPen'])       or 0

CAP_ROUND  = _qt_enum(['PenCapStyle', 'RoundCap'],
                      ['RoundCap'])
JOIN_ROUND = _qt_enum(['PenJoinStyle', 'RoundJoin'],
                      ['RoundJoin'])

# Render-Hints (versionsunabhängig)
RENDER_ANTIALIASING = _render_hint(
    ['RenderHint', 'Antialiasing'],   # Qt 6
    ['Antialiasing'],                  # Qt 5
)
RENDER_TEXT_ANTIALIASING = _render_hint(
    ['RenderHint', 'TextAntialiasing'],
    ['TextAntialiasing'],
)

# Numerische Fallbacks (stabil über Qt-Versionen)
if RENDER_ANTIALIASING is None:
    RENDER_ANTIALIASING = 0x01
if RENDER_TEXT_ANTIALIASING is None:
    RENDER_TEXT_ANTIALIASING = 0x02


# Farben
FARBE_GESAMT  = QColor("#888888")
FARBE_GELESEN = QColor("#2a9d8f")
FARBE_BACKLOG = QColor("#e76f51")
FARBE_ZIEL    = QColor("#264653")
FARBE_STABIL  = QColor("#f4a261")
FARBE_SANFT   = QColor("#8ecae6")
FARBE_ACHSE   = QColor("#333333")
FARBE_RASTER  = QColor("#e0e0e0")
FARBE_TEXT    = QColor("#222222")

# Ränder des Zeichenbereichs (in Pixeln)
RAND_LINKS  = 85
RAND_RECHTS = 30
RAND_OBEN   = 60
RAND_UNTEN  = 60


class PlotScale:
    """Bündelt die Abbildung von Daten- in Pixelkoordinaten."""

    def __init__(self, plot, x_min, x_tage, y_max):
        self.plot = plot
        self.x_min = x_min
        self.x_tage = x_tage
        self.y_max = y_max

    def date_to_x(self, date):
        tage = (date - self.x_min).days
        return self.plot.left() + self.plot.width() * tage / self.x_tage

    def value_to_y(self, value):
        return self.plot.bottom() - self.plot.height() * value / self.y_max


class AxesRenderer:
    """Zeichnet Achsen, Raster, Tick-Beschriftungen und Achsentitel."""

    def draw(self, painter, scale, x_max, y_max, y_step):
        plot = scale.plot
        painter.setPen(QPen(FARBE_ACHSE, 1))
        painter.drawLine(QPointF(plot.left(),  plot.top()),
                         QPointF(plot.left(),  plot.bottom()))
        painter.drawLine(QPointF(plot.left(),  plot.bottom()),
                         QPointF(plot.right(), plot.bottom()))

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)

        # Y-Achse
        y_wert = 0
        while y_wert <= y_max + 0.01:
            y_pix = scale.value_to_y(y_wert)
            pen = QPen(FARBE_RASTER, 1)
            pen.setStyle(PEN_DOT)
            painter.setPen(pen)
            painter.drawLine(QPointF(plot.left(),  y_pix),
                             QPointF(plot.right(), y_pix))
            painter.setPen(FARBE_TEXT)
            text = str(int(y_wert))
            breite = fm.horizontalAdvance(text)
            painter.drawText(
                QRectF(plot.left() - 10 - breite, y_pix - 8, breite, 16),
                ALIGN_RIGHT | ALIGN_VCENTER, text,
            )
            y_wert += y_step

        # X-Achse: Jahresmarkierungen
        jahre_spanne = (x_max - scale.x_min).days / 365.25
        if jahre_spanne <= 5:
            schritt = 1
        elif jahre_spanne <= 15:
            schritt = 2
        elif jahre_spanne <= 40:
            schritt = 5
        else:
            schritt = 10

        from datetime import date as _date
        for jahr in range(scale.x_min.year + 1, x_max.year + 1):
            if jahr % schritt != 0:
                continue
            try:
                d = _date(jahr, 1, 1)
            except ValueError:
                continue
            x_pix = scale.date_to_x(d)
            if x_pix < plot.left() or x_pix > plot.right():
                continue
            painter.setPen(QPen(FARBE_ACHSE, 1))
            painter.drawLine(QPointF(x_pix, plot.bottom()),
                             QPointF(x_pix, plot.bottom() + 5))
            painter.setPen(FARBE_TEXT)
            text = str(jahr)
            breite = fm.horizontalAdvance(text)
            painter.drawText(
                QRectF(x_pix - breite / 2, plot.bottom() + 8, breite, 18),
                ALIGN_CENTER, text,
            )

        # Achsentitel
        font_titel = QFont()
        font_titel.setPointSize(11)
        painter.setFont(font_titel)
        painter.setPen(FARBE_TEXT)
        painter.drawText(
            QRectF(plot.left(), plot.bottom() + 28, plot.width(), 20),
            ALIGN_CENTER, _("Year"),
        )

        painter.save()
        painter.translate(20, plot.center().y())
        painter.rotate(-90)
        painter.drawText(
            QRectF(-plot.height() / 2, -10, plot.height(), 20),
            ALIGN_CENTER, _("Number of books"),
        )
        painter.restore()


class SeriesRenderer:
    """Zeichnet Datenreihen und Ziel-/Referenzgeraden."""

    def draw_series(self, painter, scale, rows, index, color, width):
        pen = QPen(color, width)
        if CAP_ROUND is not None:
            pen.setCapStyle(CAP_ROUND)
        if JOIN_ROUND is not None:
            pen.setJoinStyle(JOIN_ROUND)
        painter.setPen(pen)

        punkte = []
        for row in rows:
            x = scale.date_to_x(row[0])
            y = scale.value_to_y(row[index])
            punkte.append(QPointF(x, y))

        for i in range(len(punkte) - 1):
            painter.drawLine(punkte[i], punkte[i + 1])

    def draw_reference_line(self, painter, scale, start, end, color, style,
                            width):
        pen = QPen(color, width)
        pen.setStyle(style)
        if CAP_ROUND is not None:
            pen.setCapStyle(CAP_ROUND)
        painter.setPen(pen)

        x1 = scale.date_to_x(start[0])
        y1 = scale.value_to_y(start[1])
        x2 = scale.date_to_x(end[0])
        y2 = scale.value_to_y(end[1])

        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))


class AnnotationRenderer:
    """Zeichnet den Titel und die 'Heute'-Annotation."""

    def draw_title(self, painter, plot, rows, target_date, reduction_factor,
                   date_format):
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(FARBE_TEXT)

        heutiger_backlog = rows[-1][3]
        ziel_sanft_i = round(heutiger_backlog * reduction_factor)
        datum_str = target_date.strftime(date_format)
        titel = _("Reading progress for TBR = {tbr} on {date}").format(
            tbr=ziel_sanft_i, date=datum_str)
        painter.drawText(
            QRectF(plot.left(), 15, plot.width(), 30),
            ALIGN_CENTER, titel,
        )

    def draw_today(self, painter, scale, today, current_backlog):
        x = scale.date_to_x(today)
        y = scale.value_to_y(current_backlog)

        painter.setPen(QPen(FARBE_BACKLOG, 1))
        painter.setBrush(FARBE_BACKLOG)
        painter.drawEllipse(QPointF(x, y), 5, 5)

        text = _("Today: {count} unread").format(count=current_backlog)
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text) + 16
        th = fm.height() + 10

        plot = scale.plot
        if x + tw + 20 < plot.right():
            bx = x + 15
        else:
            bx = x - tw - 15
        by = y - th - 15
        if by < plot.top() + 5:
            by = y + 15

        box = QRectF(bx, by, tw, th)
        painter.setBrush(QColor(255, 255, 255, 235))
        painter.setPen(QPen(QColor("#cccccc"), 1))
        painter.drawRoundedRect(box, 5, 5)

        painter.setPen(FARBE_TEXT)
        painter.drawText(box, ALIGN_CENTER, text)

        painter.setPen(QPen(FARBE_ACHSE, 1))
        start = QPointF(box.left() + 5 if bx > x else box.right() - 5,
                        box.center().y())
        painter.drawLine(start, QPointF(x, y))


class LegendRenderer:
    """Zeichnet die Legende."""

    def draw(self, painter, plot, target_date, date_format, target_soft):
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = QFontMetrics(font)

        datum_str = target_date.strftime(date_format)
        jahr_str = target_date.strftime('%Y')
        ziel_sanft_i = round(target_soft)

        eintraege = [
            (_("Total library"), FARBE_GESAMT, PEN_SOLID),
            (_("Read (cumulative)"), FARBE_GELESEN, PEN_SOLID),
            (_("Backlog (TBR)"), FARBE_BACKLOG, PEN_SOLID),
            (_("Goal: TBR = 0 on {date}").format(date=datum_str),
             FARBE_ZIEL, PEN_DASH),
            (_("Constant library (buy rate = read rate)"),
             FARBE_STABIL, PEN_DOT),
            (_("Gentle reduction to TBR = {tbr} by {year}").format(
                tbr=ziel_sanft_i, year=jahr_str),
             FARBE_SANFT, PEN_DASHDOT),
        ]

        linien_breite = 30
        padding = 10
        zeilen_hoehe = fm.height() + 6
        max_text_breite = max(fm.horizontalAdvance(e[0]) for e in eintraege)
        box_breite = padding * 2 + linien_breite + 8 + max_text_breite
        box_hoehe = padding * 2 + zeilen_hoehe * len(eintraege)

        box_x = plot.right() - box_breite - 10
        box_y = plot.top() + 10

        painter.setPen(QPen(QColor("#cccccc"), 1))
        painter.setBrush(QColor(255, 255, 255, 230))
        painter.drawRoundedRect(
            QRectF(box_x, box_y, box_breite, box_hoehe), 5, 5)

        for i, (text, farbe, stil) in enumerate(eintraege):
            zeile_y = box_y + padding + i * zeilen_hoehe + zeilen_hoehe / 2
            pen = QPen(farbe, 2.5)
            pen.setStyle(stil)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(box_x + padding, zeile_y),
                QPointF(box_x + padding + linien_breite, zeile_y),
            )
            painter.setPen(FARBE_TEXT)
            painter.drawText(
                QRectF(box_x + padding + linien_breite + 8,
                       zeile_y - zeilen_hoehe / 2,
                       max_text_breite, zeilen_hoehe),
                ALIGN_LEFT | ALIGN_VCENTER, text,
            )


class ChartWidget(QWidget):
    """Zeichnet das Burn-up-Chart; hält nur die Orchestrierung."""

    def __init__(self, rows, ziel_datum, abbau_faktor, datum_format,
                 parent=None):
        super().__init__(parent)
        self.rows = rows
        self.ziel_datum = ziel_datum
        self.abbau_faktor = abbau_faktor
        self.datum_format = datum_format
        self._achsen = AxesRenderer()
        self._reihen = SeriesRenderer()
        self._legende = LegendRenderer()
        self._annotation = AnnotationRenderer()
        self.setMinimumSize(700, 450)

    # ------------------------------------------------------------------
    # Zeichnen (mit Fehlerfang, damit ein Fehler nicht Calibre killt)
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

        if not self.rows or len(self.rows) < 2:
            painter.setPen(FARBE_TEXT)
            painter.drawText(self.rect(), ALIGN_CENTER, _("No data"))
            painter.end()
            return

        plot = QRectF(
            RAND_LINKS,
            RAND_OBEN,
            max(50, self.width()  - RAND_LINKS - RAND_RECHTS),
            max(50, self.height() - RAND_OBEN  - RAND_UNTEN),
        )

        x_min = self.rows[0][0]
        x_max = self.ziel_datum
        x_tage = (x_max - x_min).days
        if x_tage <= 0:
            painter.end()
            return

        y_max_daten = max(
            max(r[1] for r in self.rows),
            max(r[2] for r in self.rows),
            max(r[3] for r in self.rows),
        )
        y_step, y_max = self._berechne_y_achse(y_max_daten)

        scale = PlotScale(plot, x_min, x_tage, y_max)

        self._achsen.draw(painter, scale, x_max, y_max, y_step)
        self._annotation.draw_title(painter, plot, self.rows,
                                    self.ziel_datum, self.abbau_faktor,
                                    self.datum_format)

        heutiger_backlog = self.rows[-1][3]
        heute = self.rows[-1][0]
        ziel_sanft = heutiger_backlog * self.abbau_faktor

        self._reihen.draw_reference_line(
            painter, scale, start=(heute, heutiger_backlog),
            end=(self.ziel_datum, 0),
            color=FARBE_ZIEL, style=PEN_DASH, width=2,
        )
        self._reihen.draw_reference_line(
            painter, scale, start=(heute, heutiger_backlog),
            end=(self.ziel_datum, ziel_sanft),
            color=FARBE_SANFT, style=PEN_DASHDOT, width=2,
        )
        self._reihen.draw_reference_line(
            painter, scale, start=(heute, heutiger_backlog),
            end=(self.ziel_datum, heutiger_backlog),
            color=FARBE_STABIL, style=PEN_DOT, width=2,
        )

        self._reihen.draw_series(painter, scale, self.rows,
                                 index=1, color=FARBE_GESAMT, width=2)
        self._reihen.draw_series(painter, scale, self.rows,
                                 index=2, color=FARBE_GELESEN, width=2.5)
        self._reihen.draw_series(painter, scale, self.rows,
                                 index=3, color=FARBE_BACKLOG, width=3)

        self._annotation.draw_today(painter, scale, heute, heutiger_backlog)
        self._legende.draw(painter, plot, self.ziel_datum, self.datum_format,
                           ziel_sanft)

        painter.end()

    # ------------------------------------------------------------------
    # Skalierung
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


class ChartDialog(QDialog):
    """Dialog, der das Chart-Widget und einen Schließen-Button enthält."""

    def __init__(self, rows, ziel_datum, abbau_faktor, datum_format,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Reading progress"))
        self.resize(1200, 750)

        layout = QVBoxLayout(self)
        self.chart = ChartWidget(rows, ziel_datum, abbau_faktor,
                                 datum_format, self)
        layout.addWidget(self.chart, 1)

        zeile = QHBoxLayout()
        zeile.addStretch()
        btn = QPushButton(_("Close"))
        btn.clicked.connect(self.accept)
        zeile.addWidget(btn)
        layout.addLayout(zeile)
