"""
Dialog for the data-quality check.

Two tabs: read books whose read date the charts cannot use as is (no
read date, or read before being added), and series problems (one series
under several names, duplicate volume numbers, gaps). Shows the affected
books in calibre's book list on request. It never changes book data.
"""

import csv

from calibre.gui2 import choose_save_file, error_dialog
from calibre_plugins.readingprogress.export_reading_status import (
    MISSING_LAST_READ,
    READ_BEFORE_ADDED,
    problem_csv_rows,
)
from calibre_plugins.readingprogress.localization import _
from calibre_plugins.readingprogress.series import (
    DUPLICATE_INDEX,
    GAP,
    NAME_VARIANTS,
    format_index,
    series_csv_rows,
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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# Volume numbers shown in the table before "…" (the CSV has all of them)
_MAX_NUMBERS = 8


class _SortItem(QTableWidgetItem):
    """Table cell that sorts by ``key`` instead of its display text."""

    def __init__(self, text, key, book_ids):
        super().__init__(text)
        self.key = key
        self.book_ids = book_ids

    def __lt__(self, other):
        return self.key < getattr(other, 'key', self.key)


def _numbers(indices, limit=None):
    shown = indices if limit is None else indices[:limit]
    text = ', '.join(format_index(i) for i in shown)
    return text + ', …' if len(shown) < len(indices) else text


def _new_table(parent, headers, rows):
    table = QTableWidget(len(rows), len(headers), parent)
    table.setHorizontalHeaderLabels(headers)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(
        QAbstractItemView.SelectionBehavior.SelectRows)
    table.verticalHeader().setVisible(False)
    for r, (cells, book_ids) in enumerate(rows):
        for c, (text, key) in enumerate(cells):
            table.setItem(r, c, _SortItem(text, key, book_ids))
    return table


def _size_columns(table, limits):
    # Size columns after sorting, so the sort arrow is accounted for;
    # the padding leaves room for it on the other columns too.
    table.resizeColumnsToContents()
    for column in range(table.columnCount()):
        table.setColumnWidth(column, table.columnWidth(column) + 20)
    for column, limit in limits.items():
        table.setColumnWidth(column, min(table.columnWidth(column), limit))
    table.horizontalHeader().setStretchLastSection(True)


class QualityDialog(QDialog):
    """Tables of books with questionable read dates and series problems.

    ``on_show(book_ids)`` displays those books in calibre's book list;
    the dialog closes before it is called. A tab without problems is
    left out.
    """

    def __init__(self, problems, read_total, date_format, parent=None,
                 on_show=None, series_problems=()):
        super().__init__(parent)
        self.problems = problems
        self.series_problems = list(series_problems)
        self.date_format = date_format
        self.on_show = on_show
        self.labels = {
            MISSING_LAST_READ: _("No read date"),
            READ_BEFORE_ADDED: _("Read before added"),
        }
        self.series_labels = {
            NAME_VARIANTS: _("Several names"),
            DUPLICATE_INDEX: _("Duplicate volume number"),
            GAP: _("Gap"),
        }
        self.setWindowTitle(_("Data quality"))
        self.resize(1150, 650)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        # one entry per tab: (table, all book ids, save_csv)
        self.pages = []
        if problems:
            self._add_date_tab(read_total)
        if self.series_problems:
            self._add_series_tab()
        layout.addWidget(self.tabs, 1)

        row = QHBoxLayout()
        self.show_selected_btn = QPushButton(_("Show selected in calibre"))
        self.show_selected_btn.setEnabled(False)
        self.show_selected_btn.clicked.connect(
            lambda: self._show(self._selected_ids()))
        row.addWidget(self.show_selected_btn)
        show_all_btn = QPushButton(_("Show all in calibre"))
        show_all_btn.clicked.connect(
            lambda: self._show(self._page()[1]))
        row.addWidget(show_all_btn)
        csv_btn = QPushButton(_("Save as CSV…"))
        csv_btn.clicked.connect(lambda: self._page()[2]())
        row.addWidget(csv_btn)
        row.addStretch()
        close_btn = QPushButton(_("Close"))
        close_btn.clicked.connect(self.reject)
        row.addWidget(close_btn)
        layout.addLayout(row)

        self.tabs.currentChanged.connect(lambda _index: self._update_buttons())

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------
    def _add_page(self, title, labels, table, book_ids, save_csv):
        page = QWidget(self)
        page_layout = QVBoxLayout(page)
        for text in labels:
            label = QLabel(text)
            label.setWordWrap(True)
            page_layout.addWidget(label)
        page_layout.addWidget(table, 1)
        table.itemSelectionChanged.connect(self._update_buttons)
        table.itemDoubleClicked.connect(
            lambda item: self._show(item.book_ids))
        self.pages.append((table, book_ids, save_csv))
        self.tabs.addTab(page, title)

    def _add_date_tab(self, read_total):
        problems = self.problems
        missing = sum(1 for p in problems if p['problem'] == MISSING_LAST_READ)
        summary = _(
            "<b>{count} of {read} read books have a questionable read "
            "date:</b> {missing} without a read date, {early} read before "
            "being added. The charts count all of them as read on the day "
            "they were added.").format(
                count=len(problems), read=read_total, missing=missing,
                early=len(problems) - missing)
        hint = _(
            "Tip: if many of them were added on the same day, the date "
            "added is probably wrong (a bulk import), not the read date. "
            "Sort by \"Added\" to spot such days.")

        headers = [_("Problem"), _("Title"), _("Author(s)"), _("Added"),
                   _("Last read"), _("Days before")]
        rows = []
        for p in problems:
            authors = ' & '.join(p['authors'])
            last_read = p['last_read']
            days = p['days_before']
            rows.append(([
                (self.labels[p['problem']], p['problem']),
                (p['title'], p['title'].lower()),
                (authors, authors.lower()),
                (p['added'].strftime(self.date_format),
                 (p['added'].toordinal(), p['title'].lower())),
                (last_read.strftime(self.date_format) if last_read else '',
                 last_read.toordinal() if last_read else -1),
                ('' if days is None else str(days),
                 -1 if days is None else days),
            ], [p['book_id']]))
        table = _new_table(self, headers, rows)
        # Start sorted by date added, so bulk-import days stand out.
        table.setSortingEnabled(True)
        table.sortItems(3, Qt.SortOrder.AscendingOrder)
        _size_columns(table, {1: 360, 2: 220})
        self._add_page(_("Read dates"), [summary, hint], table,
                       [p['book_id'] for p in problems], self._save_date_csv)

    def _add_series_tab(self):
        problems = self.series_problems
        counts = {kind: sum(1 for p in problems if p['kind'] == kind)
                  for kind in self.series_labels}
        summary = _(
            "<b>{count} series problems:</b> {names} series under several "
            "names, {duplicates} with duplicate volume numbers, {gaps} with "
            "gaps.").format(
                count=len(problems), names=counts[NAME_VARIANTS],
                duplicates=counts[DUPLICATE_INDEX], gaps=counts[GAP])
        hint = _(
            "Several names: the names differ only in case, punctuation, a "
            "leading article or a word like \"Series\". A volume number "
            "used twice is often 1, which calibre sets when a book has no "
            "number. Gap: an earlier volume is unread although a later one "
            "is read.")

        headers = [_("Problem"), _("Series"), _("Details"), _("Books")]
        order = list(self.series_labels)
        rows = []
        for p in problems:
            names = ' | '.join(p['series'])
            rows.append(([
                (self.series_labels[p['kind']],
                 (order.index(p['kind']), names.lower())),
                (names, names.lower()),
                (self._describe(p, _MAX_NUMBERS), self._describe(p)),
                (str(len(p['book_ids'])), len(p['book_ids'])),
            ], p['book_ids']))
        table = _new_table(self, headers, rows)
        table.setSortingEnabled(True)
        table.sortItems(0, Qt.SortOrder.AscendingOrder)
        _size_columns(table, {1: 420, 2: 360})
        book_ids = []
        for p in problems:
            book_ids += [i for i in p['book_ids'] if i not in book_ids]
        self._add_page(_("Series"), [summary, hint], table, book_ids,
                       self._save_series_csv)

    def _describe(self, problem, limit=None):
        if problem['kind'] == NAME_VARIANTS:
            return _("{count} names").format(count=len(problem['series']))
        numbers = _numbers(problem['indices'], limit)
        if problem['kind'] == DUPLICATE_INDEX:
            return _("Volume {numbers} more than once").format(
                numbers=numbers)
        return _("Volume {numbers} unread, read up to {last}").format(
            numbers=numbers, last=format_index(problem['max_read']))

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------
    def _page(self):
        return self.pages[self.tabs.currentIndex()]

    def _update_buttons(self):
        self.show_selected_btn.setEnabled(bool(self._selected_ids()))

    def _selected_ids(self):
        ids = []
        for item in self._page()[0].selectedItems():
            ids += [i for i in item.book_ids if i not in ids]
        return ids

    def _show(self, book_ids):
        if not book_ids:
            return
        self.accept()
        if self.on_show is not None:
            self.on_show(book_ids)

    def _save_date_csv(self):
        header = ['ID', _("Problem"), _("Title"), _("Author(s)"),
                  _("Added"), _("Last read"), _("Days before")]
        self._save_csv('reading-progress-data-quality.csv', header,
                       problem_csv_rows(self.problems, self.date_format,
                                        self.labels))

    def _save_series_csv(self):
        header = [_("Problem"), _("Series"), _("Details"), _("Books"),
                  _("Book IDs")]
        self._save_csv('reading-progress-series-quality.csv', header,
                       series_csv_rows(self.series_problems,
                                       self.series_labels, self._describe))

    def _save_csv(self, filename, header, rows):
        path = choose_save_file(
            self, 'readingprogress-export-csv', _("Save list as CSV"),
            filters=[(_("CSV files"), ['csv'])], all_files=False,
            initial_filename=filename)
        if not path:
            return
        if not path.lower().endswith('.csv'):
            path += '.csv'
        try:
            # utf-8-sig and ';' so spreadsheet apps open it correctly
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(header)
                writer.writerows(rows)
        except OSError as e:
            error_dialog(self, _("Export failed"),
                         _("Could not write {path}.").format(path=path),
                         det_msg=str(e), show=True)
