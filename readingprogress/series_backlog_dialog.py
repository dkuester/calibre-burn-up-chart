"""
Dialog for the TBR by series.

One horizontal bar per series with the most unread books. Clicking a
bar shows the unread books of that series in calibre's book list.
"""

from calibre_plugins.readingprogress.chart_common import (
    axis_ticks,
    compute_y_axis,
    is_dark_background,
)
from calibre_plugins.readingprogress.chart_dialog import (
    ALIGN_CENTER,
    ALIGN_LEFT,
    ALIGN_RIGHT,
    ALIGN_VCENTER,
    LEFT_BUTTON,
    MARGIN_RIGHT,
    PEN_DOT,
    PEN_NOPEN,
    RENDER_ANTIALIASING,
    RENDER_TEXT_ANTIALIASING,
    _cursor_pos,
    _global_pos,
    add_export_buttons,
    build_series_colors,
    chrome_for,
    show_paint_error,
)
from calibre_plugins.readingprogress.localization import _
from qt.core import (
    QDialog,
    QFont,
    QFontMetrics,
    QHBoxLayout,
    QLabel,
    QPainter,
    QPen,
    QPointF,
    QPushButton,
    QRectF,
    Qt,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

# Room for title and key-figures line above, axis labels below the plot
MARGIN_TOP    = 95
MARGIN_BOTTOM = 60

# Series names on the left: at most this wide (longer ones are elided)
LABEL_MAX_WIDTH = 340
LABEL_GAP       = 10

# Room right of the longest bar for its count
COUNT_WIDTH = 40

# Bar height as a share of its slot
BAR_SHARE = 0.7

CURSOR_HAND  = Qt.CursorShape.PointingHandCursor
CURSOR_ARROW = Qt.CursorShape.ArrowCursor
ELIDE_RIGHT  = Qt.TextElideMode.ElideRight


def _percent(part, whole, decimal_sep):
    if not whole:
        return '–'
    return '{:.0f}'.format(100 * part / whole).replace('.', decimal_sep)


class SeriesBacklogWidget(QWidget):
    """Draws the series with the most unread books as horizontal bars.

    ``data`` is the dict from ``series.backlog_by_series()``, ``backlog``
    the number of unread books in the library;
    ``on_bar_clicked(book_ids)`` is called for a click on a bar.
    """

    def __init__(self, data, backlog, decimal_sep='.', parent=None,
                 colors=None, on_bar_clicked=None):
        super().__init__(parent)
        self.data = data
        self.top = data['top']
        self.backlog = backlog
        self.decimal_sep = decimal_sep
        self.on_bar_clicked = on_bar_clicked
        self.chrome = chrome_for(self)
        bg = self.chrome['background']
        series = build_series_colors(
            is_dark_background((bg.red(), bg.green(), bg.blue())), colors)
        self.color_bar = series['backlog']
        self.color_hover = series['backlog'].lighter(125)
        self._hover = None
        self.setMinimumSize(700, 450)
        self.setMouseTracking(True)

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------
    def _label_font(self):
        font = QFont()
        font.setPointSize(10)
        return font

    def _label_width(self):
        fm = QFontMetrics(self._label_font())
        widest = max(fm.horizontalAdvance(e['series']) for e in self.top)
        return min(widest, LABEL_MAX_WIDTH)

    def _plot_rect(self):
        left = 20 + self._label_width() + LABEL_GAP
        return QRectF(
            left,
            MARGIN_TOP,
            max(50, self.width() - left - MARGIN_RIGHT - COUNT_WIDTH),
            max(50, self.height() - MARGIN_TOP - MARGIN_BOTTOM),
        )

    def _x_axis(self):
        return compute_y_axis(self.top[0]['unread'], integer=True)

    def _slot(self, plot):
        return plot.height() / len(self.top)

    def _bar_rect(self, plot, index, x_max):
        slot = self._slot(plot)
        height = slot * BAR_SHARE
        width = plot.width() * self.top[index]['unread'] / x_max
        return QRectF(plot.left(), plot.top() + index * slot
                      + (slot - height) / 2, width, height)

    def _bar_at(self, pos):
        """Index of the bar row under ``pos``, or None."""
        plot = self._plot_rect()
        if not self.top or not (plot.top() <= pos.y() < plot.bottom()):
            return None
        if not (20 <= pos.x() <= plot.right() + COUNT_WIDTH):
            return None
        index = int((pos.y() - plot.top()) / self._slot(plot))
        return index if 0 <= index < len(self.top) else None

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        try:
            self._do_paint()
        except Exception as e:
            show_paint_error(self, e)

    def _do_paint(self):
        painter = QPainter(self)
        painter.setRenderHint(RENDER_ANTIALIASING, True)
        painter.setRenderHint(RENDER_TEXT_ANTIALIASING, True)
        painter.fillRect(self.rect(), self.chrome['background'])

        if not self.top:
            painter.setPen(self.chrome['text'])
            painter.drawText(self.rect(), ALIGN_CENTER, _("No data"))
            painter.end()
            return

        plot = self._plot_rect()
        x_step, x_max = self._x_axis()
        self._draw_header(painter)
        self._draw_axes(painter, plot, x_step, x_max)
        self._draw_bars(painter, plot, x_max)
        painter.end()

    def _draw_header(self, painter):
        width = self.width() - 40
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(self.chrome['text'])
        painter.drawText(QRectF(20, 15, width, 30), ALIGN_CENTER,
                         _("TBR by series"))

        d = self.data
        top_books = d['books'] - d['rest_books']
        text = _("{backlog} unread books · {books} of them in {series} "
                 "series ({share} %) · the {top} largest: {top_share} %"
                 ).format(
            backlog=self.backlog, books=d['books'], series=d['series_count'],
            share=_percent(d['books'], self.backlog, self.decimal_sep),
            top=len(self.top),
            top_share=_percent(top_books, self.backlog, self.decimal_sep))
        font = QFont()
        font.setPointSize(11)
        painter.setFont(font)
        painter.setPen(self.chrome['muted'])
        painter.drawText(QRectF(20, 50, width, 22), ALIGN_CENTER, text)

    def _draw_axes(self, painter, plot, x_step, x_max):
        painter.setPen(QPen(self.chrome['axis'], 1))
        painter.drawLine(QPointF(plot.left(), plot.top()),
                         QPointF(plot.left(), plot.bottom()))
        painter.drawLine(QPointF(plot.left(), plot.bottom()),
                         QPointF(plot.right(), plot.bottom()))

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        for value in axis_ticks(x_max, x_step):
            x = plot.left() + plot.width() * value / x_max
            if value:
                pen = QPen(self.chrome['grid'], 1)
                pen.setStyle(PEN_DOT)
                painter.setPen(pen)
                painter.drawLine(QPointF(x, plot.top()),
                                 QPointF(x, plot.bottom()))
            painter.setPen(self.chrome['text'])
            painter.drawText(QRectF(x - 30, plot.bottom() + 6, 60, 18),
                             ALIGN_CENTER, str(int(value)))

        font = QFont()
        font.setPointSize(11)
        painter.setFont(font)
        painter.drawText(QRectF(plot.left(), plot.bottom() + 30,
                                plot.width(), 20),
                         ALIGN_CENTER, _("Unread books"))

    def _draw_bars(self, painter, plot, x_max):
        font = self._label_font()
        painter.setFont(font)
        fm = QFontMetrics(font)
        label_width = self._label_width()
        slot = self._slot(plot)
        for index, entry in enumerate(self.top):
            rect = self._bar_rect(plot, index, x_max)
            painter.setPen(QPen(PEN_NOPEN))
            painter.setBrush(self.color_hover if index == self._hover
                             else self.color_bar)
            painter.drawRect(rect)

            painter.setPen(self.chrome['text'])
            row_top = plot.top() + index * slot
            name = fm.elidedText(entry['series'], ELIDE_RIGHT, label_width)
            painter.drawText(QRectF(20, row_top, label_width, slot),
                             ALIGN_RIGHT | ALIGN_VCENTER, name)
            painter.drawText(QRectF(rect.right() + 6, row_top,
                                    COUNT_WIDTH, slot),
                             ALIGN_LEFT | ALIGN_VCENTER, str(entry['unread']))

    # ------------------------------------------------------------------
    # Interaction: hover tooltip, click shows the books
    # ------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        index = self._bar_at(_cursor_pos(event))
        if index != self._hover:
            self._hover = index
            self.setCursor(CURSOR_HAND if index is not None
                           else CURSOR_ARROW)
            self.update()
        if index is None:
            QToolTip.hideText()
            return
        entry = self.top[index]
        text = _("{series}\n{unread} unread · {read} of {total} read\n"
                 "{share} % of the TBR\n"
                 "Click to show the unread books in calibre").format(
            series=entry['series'], unread=entry['unread'],
            read=entry['read'], total=entry['total'],
            share=_percent(entry['unread'], self.backlog, self.decimal_sep))
        QToolTip.showText(_global_pos(event), text, self)

    def leaveEvent(self, event):
        if self._hover is not None:
            self._hover = None
            self.update()

    def mousePressEvent(self, event):
        if event.button() != LEFT_BUTTON:
            return
        index = self._bar_at(_cursor_pos(event))
        if index is not None and self.on_bar_clicked is not None:
            self.on_bar_clicked(self.top[index]['book_ids'])


class SeriesBacklogDialog(QDialog):
    """Dialog with the TBR-by-series chart, export buttons and Close.

    ``on_show(book_ids)`` displays books in calibre's book list; the
    dialog closes before it is called.
    """

    def __init__(self, data, backlog, decimal_sep='.', parent=None,
                 colors=None, on_show=None):
        super().__init__(parent)
        self.on_show = on_show
        self.setWindowTitle(_("TBR by series"))
        self.resize(1200, 750)

        layout = QVBoxLayout(self)
        self.chart = SeriesBacklogWidget(data, backlog, decimal_sep, self,
                                         colors=colors,
                                         on_bar_clicked=self._show)
        layout.addWidget(self.chart, 1)

        row = QHBoxLayout()
        row.addWidget(QLabel(
            _("Click a bar to show the unread books of that series in "
              "calibre."), self))
        row.addStretch()
        add_export_buttons(row, self.chart, 'tbr-by-series')
        btn = QPushButton(_("Close"))
        btn.clicked.connect(self.reject)
        row.addWidget(btn)
        layout.addLayout(row)

    def _show(self, book_ids):
        self.accept()
        if self.on_show is not None:
            self.on_show(book_ids)
