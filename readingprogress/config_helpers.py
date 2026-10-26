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


# Composite column "Days in TBR" created from the settings dialog
DAYS_IN_TBR_LABEL = "days_in_tbr"


def days_in_tbr_template(read_column, last_read_column):
    """Calibre template for the "Days in TBR" composite column.

    Read books: days between adding and ``last_read_column`` (0 if read
    before adding, empty without a read date). Unread books: days since
    adding, up to today. Uses raw field values (``$$``) because the
    displayed dates are localized ("30 Dez 2025") and days_between()
    cannot parse every language.
    """
    return (
        "program:\n"
        "if $${read} == 'true' then\n"
        "  d = days_between($${last_read}, $$timestamp);\n"
        "  if d then cmp(d, 0, '0', '0', format_number(d, '{{0:.0f}}'))"
        " else '' fi\n"
        "else\n"
        "  format_number(days_between(today(), $$timestamp), '{{0:.0f}}')\n"
        "fi"
    ).format(read=read_column, last_read=last_read_column)
