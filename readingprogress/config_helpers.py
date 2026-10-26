"""Qt-/Calibre-free config and locale helpers.

Extracted from ``__init__.py``/``main.py`` so the migration and locale
logic is unit-testable outside Calibre. This module must not import
``calibre`` or ``qt`` – tests import it flat (see ``tests/conftest.py``).
"""

# Old German config keys from before the plugin was renamed (English).
LEGACY_KEY_MAP = {
    "target_date": "ziel_datum",
    "reduction_factor": "abbau_faktor",
    "read_column": "spalte_gelesen",
    "last_read_column": "spalte_last_read",
}


def date_format(language):
    """Locale date format for a Calibre UI language code ('de', 'en', …)."""
    return "%d.%m.%Y" if language == "de" else "%Y-%m-%d"


def decimal_separator(language):
    """Decimal separator for a Calibre UI language code."""
    return "," if language == "de" else "."


def migrate_legacy_keys(current, legacy):
    """Resolves each new key from its legacy German key.

    Prefers ``current``'s old key, falling back to ``legacy``. Both are
    dict-likes whose ``__getitem__`` raises ``KeyError`` for a missing
    key (plain ``dict`` and Calibre's ``JSONConfig`` both do).
    """
    result = {}
    for new_key, old_key in LEGACY_KEY_MAP.items():
        try:
            value = current[old_key]
        except KeyError:
            value = legacy[old_key]
        result[new_key] = value
    return result
