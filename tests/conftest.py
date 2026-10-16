"""Shared fixtures and the import path for the tests.

``export_reading_status.py`` has no Calibre dependencies and is imported
here as a flat module. ``readingprogress/__init__.py`` must not be loaded
as a package because it imports ``calibre.customize`` – so
``readingprogress/`` is placed on ``sys.path`` as a directory (not a
package).
"""

import sys
from pathlib import Path

import pytest

_PLUGIN_DIR = Path(__file__).resolve().parent.parent / "readingprogress"
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))


class FakeDbApi:
    """Stand-in for Calibre's ``new_api`` – only the two used methods."""

    def __init__(self, books):
        # books: {book_id: {field: value}}
        self.books = books

    def all_book_ids(self):
        return sorted(self.books)

    def all_field_for(self, field, ids):
        return {bid: self.books[bid].get(field)
                for bid in ids if bid in self.books}


@pytest.fixture
def make_db():
    """Factory: ``make_db({book_id: {field: value}})`` returns a FakeDbApi."""
    return FakeDbApi
