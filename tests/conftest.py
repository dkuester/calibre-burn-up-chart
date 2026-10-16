"""Gemeinsame Fixtures und Import-Pfad für die Tests.

``export_lesestatus.py`` kommt ohne Calibre-Abhängigkeiten aus und wird hier
als flaches Modul importiert. ``readingprogress/__init__.py`` darf nicht als
Paket geladen werden, weil es ``calibre.customize`` importiert – deshalb wird
``readingprogress/`` als Verzeichnis (nicht als Paket) auf ``sys.path`` gelegt.
"""

import sys
from pathlib import Path

import pytest

_PLUGIN_DIR = Path(__file__).resolve().parent.parent / "readingprogress"
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))


class FakeDbApi:
    """Ersatz für Calibres ``new_api`` – nur die beiden genutzten Methoden."""

    def __init__(self, books):
        # books: {book_id: {feld: wert}}
        self.books = books

    def all_book_ids(self):
        return sorted(self.books)

    def all_field_for(self, field, ids):
        return {bid: self.books[bid].get(field)
                for bid in ids if bid in self.books}


@pytest.fixture
def make_db():
    """Fabrik: ``make_db({book_id: {feld: wert}})`` liefert eine FakeDbApi."""
    return FakeDbApi
