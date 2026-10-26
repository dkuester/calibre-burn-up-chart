"""
Dialog for the data-quality check.

Lists read books whose read date the charts cannot use as is (no read
date, or read before being added) and shows them in calibre's book list
on request. It never changes book data.
"""

import csv

from calibre.gui2 import choose_save_file, error_dialog
from calibre_plugins.readingprogress.export_reading_status import (
    MISSING_LAST_READ,
    READ_BEFORE_ADDED,
    problem_csv_rows,
)
from calibre_plugins.readingprogress.localization import _
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


def _enum(owner, scope, name):
    """Qt enum member, scoped (Qt 6) or flat (Qt 5)."""
    scoped = getattr(owner, scope, None)
    value = getattr(scoped, name, None) if scoped is not None else None
    return value if value is not None else getattr(owner, name)


class _SortItem(QTableWidgetItem):
    """Table cell that sorts by ``key`` instead of its display text."""

    def __init__(self, text, key, book_id):
        super().__init__(text)
        self.key = key
        self.book_id = book_id

    def __lt__(self, other):
        return self.key < getattr(other, 'key', self.key)


class QualityDialog(QDialog):
    """Table of books with questionable read dates.

    ``on_show(book_ids)`` displays those books in calibre's book list;
    the dialog closes before it is called.
    """

    def __init__(self, problems, read_total, date_format, parent=None,
                 on_show=None):
        super().__init__(parent)
        self.problems = problems
        self.date_format = date_format
        self.on_show = on_show
        self.labels = {
            MISSING_LAST_READ: _("No read date"),
            READ_BEFORE_ADDED: _("Read before added"),
        }
        self.setWindowTitle(_("Data quality"))
        self.resize(1150, 650)

        layout = QVBoxLayout(self)
        missing = sum(1 for p in problems if p['problem'] == MISSING_LAST_READ)
        summary = QLabel(_(
            "<b>{count} of {read} read books have a questionable read "
            "date:</b> {missing} without a read date, {early} read before "
            "being added. The charts count all of them as read on the day "
            "they were added.").format(
                count=len(problems), read=read_total, missing=missing,
                early=len(problems) - missing))
        summary.setWordWrap(True)
        layout.addWidget(summary)
        hint = QLabel(_(
            "Tip: if many of them were added on the same day, the date "
            "added is probably wrong (a bulk import), not the read date. "
            "Sort by \"Added\" to spot such days."))
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.table = self._build_table()
        layout.addWidget(self.table, 1)

        row = QHBoxLayout()
        self.show_selected_btn = QPushButton(_("Show selected in calibre"))
        self.show_selected_btn.setEnabled(False)
        self.show_selected_btn.clicked.connect(
            lambda: self._show(self._selected_ids()))
        row.addWidget(self.show_selected_btn)
        show_all_btn = QPushButton(_("Show all in calibre"))
        show_all_btn.clicked.connect(
            lambda: self._show([p['book_id'] for p in problems]))
        row.addWidget(show_all_btn)
        csv_btn = QPushButton(_("Save as CSV…"))
        csv_btn.clicked.connect(self._save_csv)
        row.addWidget(csv_btn)
        row.addStretch()
        close_btn = QPushButton(_("Close"))
        close_btn.clicked.connect(self.reject)
        row.addWidget(close_btn)
        layout.addLayout(row)

    def _build_table(self):
        headers = [_("Problem"), _("Title"), _("Author(s)"), _("Added"),
                   _("Last read"), _("Days before")]
        table = QTableWidget(len(self.problems), len(headers), self)
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(
            _enum(QAbstractItemView, 'EditTrigger', 'NoEditTriggers'))
        table.setSelectionBehavior(
            _enum(QAbstractItemView, 'SelectionBehavior', 'SelectRows'))
        table.verticalHeader().setVisible(False)

        for r, p in enumerate(self.problems):
            authors = ' & '.join(p['authors'])
            last_read = p['last_read']
            days = p['days_before']
            cells = [
                (self.labels[p['problem']], p['problem']),
                (p['title'], p['title'].lower()),
                (authors, authors.lower()),
                (p['added'].strftime(self.date_format),
                 (p['added'].toordinal(), p['title'].lower())),
                (last_read.strftime(self.date_format) if last_read else '',
                 last_read.toordinal() if last_read else -1),
                ('' if days is None else str(days),
                 -1 if days is None else days),
            ]
            for c, (text, key) in enumerate(cells):
                table.setItem(r, c, _SortItem(text, key, p['book_id']))

        # Start sorted by date added, so bulk-import days stand out.
        table.setSortingEnabled(True)
        table.sortItems(3, _enum(Qt, 'SortOrder', 'AscendingOrder'))
        # Size columns after sorting, so the sort arrow is accounted for;
        # the padding leaves room for it on the other columns too.
        table.resizeColumnsToContents()
        for column in range(table.columnCount()):
            table.setColumnWidth(column, table.columnWidth(column) + 20)
        table.setColumnWidth(1, min(table.columnWidth(1), 360))
        table.setColumnWidth(2, min(table.columnWidth(2), 220))
        table.horizontalHeader().setStretchLastSection(True)
        table.itemSelectionChanged.connect(
            lambda: self.show_selected_btn.setEnabled(
                bool(self._selected_ids())))
        table.itemDoubleClicked.connect(
            lambda item: self._show([item.book_id]))
        return table

    def _selected_ids(self):
        ids = []
        for item in self.table.selectedItems():
            if item.book_id not in ids:
                ids.append(item.book_id)
        return ids

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
            initial_filename='reading-progress-data-quality.csv')
        if not path:
            return
        if not path.lower().endswith('.csv'):
            path += '.csv'
        header = ['ID', _("Problem"), _("Title"), _("Author(s)"),
                  _("Added"), _("Last read"), _("Days before")]
        try:
            # utf-8-sig and ';' so spreadsheet apps open it correctly
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(header)
                writer.writerows(problem_csv_rows(
                    self.problems, self.date_format, self.labels))
        except OSError as e:
            error_dialog(self, _("Export failed"),
                         _("Could not write {path}.").format(path=path),
                         det_msg=str(e), show=True)
