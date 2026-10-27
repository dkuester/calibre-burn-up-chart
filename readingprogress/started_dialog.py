"""
Dialog for the started series.

Lists series begun but not finished: progress, the next volume to read
(and, after a gap, the first volume above the highest read one) and
when something of the series was last read. Shows the next volume or
the whole series in calibre's book list on request. It never changes
book data.
"""

import csv

from calibre.gui2 import choose_save_file, error_dialog
from calibre_plugins.readingprogress.localization import _
from calibre_plugins.readingprogress.series import (
    format_index,
    started_csv_rows,
)
from qt.core import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class _SortItem(QTableWidgetItem):
    """Table cell that sorts by ``key`` instead of its display text."""

    def __init__(self, text, key, entry):
        super().__init__(text)
        self.key = key
        self.entry = entry

    def __lt__(self, other):
        return self.key < getattr(other, 'key', self.key)


def _volume(book):
    if book is None:
        return '', (0, -1.0, '')
    return ('{} – {}'.format(format_index(book['index']), book['title']),
            (1, book['index'], book['title'].lower()))


def _next_ids(entry):
    ids = [entry['next_book']['book_id']]
    if entry['after_book'] is not None:
        ids.append(entry['after_book']['book_id'])
    return ids


class StartedSeriesDialog(QDialog):
    """Table of started series with their next volume.

    ``on_show(book_ids)`` displays those books in calibre's book list;
    the dialog closes before it is called.
    """

    def __init__(self, started, date_format, parent=None, on_show=None):
        super().__init__(parent)
        self.started = started
        self.date_format = date_format
        self.on_show = on_show
        self.setWindowTitle(_("Started series"))
        self.resize(1150, 650)

        layout = QVBoxLayout(self)
        summary = QLabel(_(
            "<b>{count} started series:</b> at least two books, at least "
            "one of them read and one unread. The longest unread come "
            "first.").format(count=len(started)))
        summary.setWordWrap(True)
        layout.addWidget(summary)
        hint = QLabel(_(
            "\"After highest read\" appears when an earlier volume is "
            "still unread (a gap). A series under several names is listed "
            "once per name; \"Check data quality\" shows such names."))
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.table = self._build_table()
        layout.addWidget(self.table, 1)

        row = QHBoxLayout()
        self.show_next_btn = QPushButton(_("Show next volume in calibre"))
        self.show_next_btn.clicked.connect(
            lambda: self._show(self._selected_ids(_next_ids)))
        row.addWidget(self.show_next_btn)
        self.show_series_btn = QPushButton(_("Show whole series in calibre"))
        self.show_series_btn.clicked.connect(
            lambda: self._show(self._selected_ids(lambda e: e['book_ids'])))
        row.addWidget(self.show_series_btn)
        csv_btn = QPushButton(_("Save as CSV…"))
        csv_btn.clicked.connect(self._save_csv)
        row.addWidget(csv_btn)
        row.addStretch()
        close_btn = QPushButton(_("Close"))
        close_btn.clicked.connect(self.reject)
        row.addWidget(close_btn)
        layout.addLayout(row)
        self._update_buttons()

    def _build_table(self):
        headers = [_("Series"), _("Progress"), _("Next volume"),
                   _("After highest read"), _("Last read")]
        table = QTableWidget(len(self.started), len(headers), self)
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)

        for r, s in enumerate(self.started):
            last_read = s['last_read']
            cells = [
                (s['series'], s['series'].lower()),
                ('{}/{}'.format(s['read'], s['total']),
                 (s['read'] / s['total'], s['total'])),
                _volume(s['next_book']),
                _volume(s['after_book']),
                (last_read.strftime(self.date_format) if last_read else '–',
                 (last_read is not None,
                  last_read.toordinal() if last_read else 0,
                  s['series'].lower())),
            ]
            for c, (text, key) in enumerate(cells):
                item = _SortItem(text, key, s)
                if c == 1:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight
                        | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(r, c, item)

        # Start with the series read longest ago, so stalled ones show.
        table.setSortingEnabled(True)
        table.sortItems(4, Qt.SortOrder.AscendingOrder)
        # Size columns after sorting, so the sort arrow is accounted for;
        # the padding leaves room for it on the other columns too.
        table.resizeColumnsToContents()
        for column in range(table.columnCount()):
            table.setColumnWidth(column, table.columnWidth(column) + 20)
        for column, limit in ((0, 260), (2, 300), (3, 260)):
            table.setColumnWidth(column, min(table.columnWidth(column), limit))
        table.horizontalHeader().setStretchLastSection(True)
        table.itemSelectionChanged.connect(self._update_buttons)
        table.itemDoubleClicked.connect(
            lambda item: self._show(_next_ids(item.entry)))
        return table

    def _selected_entries(self):
        entries = []
        for item in self.table.selectedItems():
            if not any(e is item.entry for e in entries):
                entries.append(item.entry)
        return entries

    def _selected_ids(self, ids_of):
        ids = []
        for entry in self._selected_entries():
            ids += [i for i in ids_of(entry) if i not in ids]
        return ids

    def _update_buttons(self):
        selected = bool(self._selected_entries())
        self.show_next_btn.setEnabled(selected)
        self.show_series_btn.setEnabled(selected)

    def _show(self, book_ids):
        if not book_ids:
            return
        self.accept()
        if self.on_show is not None:
            self.on_show(book_ids)

    def _save_csv(self):
        path = choose_save_file(
            self, 'readingprogress-export-csv', _("Save list as CSV"),
            filters=[(_("CSV files"), ['csv'])], all_files=False,
            initial_filename='reading-progress-started-series.csv')
        if not path:
            return
        if not path.lower().endswith('.csv'):
            path += '.csv'
        header = [_("Series"), _("Read"), _("Books"),
                  _("Next volume"), _("Title"),
                  _("After highest read"), _("Title"), _("Last read")]
        try:
            # utf-8-sig and ';' so spreadsheet apps open it correctly
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(header)
                writer.writerows(started_csv_rows(self.started,
                                                  self.date_format))
        except OSError as e:
            error_dialog(self, _("Export failed"),
                         _("Could not write {path}.").format(path=path),
                         det_msg=str(e), show=True)
