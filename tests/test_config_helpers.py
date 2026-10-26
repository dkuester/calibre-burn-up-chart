"""Tests for the Qt-free config/locale helpers."""

import chart_common as cc
import config_helpers as ch


def test_date_format_german():
    assert ch.date_format('de') == '%d.%m.%Y'


def test_date_format_english():
    assert ch.date_format('en') == '%Y-%m-%d'


def test_date_format_other_language():
    assert ch.date_format('fr') == '%Y-%m-%d'


def test_migrate_legacy_keys_falls_back_to_legacy():
    current = {}
    legacy = {
        'ziel_datum': '2050-09-04',
        'abbau_faktor': 0.5,
        'spalte_gelesen': '#gelesen',
        'spalte_last_read': '#last_read',
    }
    assert ch.migrate_legacy_keys(current, legacy) == {
        'target_date': '2050-09-04',
        'reduction_factor': 0.5,
        'read_column': '#gelesen',
        'last_read_column': '#last_read',
    }


def test_migrate_legacy_keys_prefers_current():
    current = {'ziel_datum': '2030-01-01'}
    legacy = {
        'ziel_datum': '2050-09-04',
        'abbau_faktor': 0.5,
        'spalte_gelesen': '#gelesen',
        'spalte_last_read': '#last_read',
    }
    result = ch.migrate_legacy_keys(current, legacy)
    assert result['target_date'] == '2030-01-01'
    assert result['reduction_factor'] == 0.5


def test_all_colors_are_light_defaults_yes():
    assert cc.all_colors_are_light_defaults(dict(cc.DEFAULT_COLORS)) is True


def test_all_colors_are_light_defaults_customized():
    stored = dict(cc.DEFAULT_COLORS)
    stored['goal'] = '#123456'
    assert cc.all_colors_are_light_defaults(stored) is False


def test_all_colors_are_light_defaults_auto():
    assert cc.all_colors_are_light_defaults(
        {k: '' for k in cc.DEFAULT_COLORS}) is False


def test_decimal_separator():
    assert ch.decimal_separator('de') == ','
    assert ch.decimal_separator('en') == '.'


def test_days_in_tbr_template_uses_configured_columns():
    t = ch.days_in_tbr_template('#read', '#lastread')
    assert t.startswith('program:\n')
    assert "$$#read == 'true'" in t
    assert 'days_between($$#lastread, $$timestamp)' in t
    assert 'days_between(today(), $$timestamp)' in t
    assert "'{0:.0f}'" in t
    assert '#gelesen' not in t


class _FieldMetadata(dict):
    def custom_field_keys(self):
        return [k for k in self if k.startswith('#')]


class _Db:
    def __init__(self, types):
        self.field_metadata = _FieldMetadata(
            {k: {'datatype': v} for k, v in types.items()})


def test_custom_column_types():
    db = _Db({'title': 'text', '#gelesen': 'bool', '#last_read': 'datetime'})
    assert ch.custom_column_types(db) == {'#gelesen': 'bool',
                                          '#last_read': 'datetime'}


def test_column_problems_none_when_types_match():
    types = {'#gelesen': 'bool', '#last_read': 'datetime'}
    assert ch.column_problems(types, '#gelesen', '#last_read') == []


def test_column_problems_missing_and_wrong_type():
    types = {'#read': 'text'}
    assert ch.column_problems(types, '#read', '#last_read') == [
        ('#read', 'Yes/No', 'text'),
        ('#last_read', 'Date', None),
    ]


def test_describe_column_problems_translates():
    lines = ch.describe_column_problems(
        [('#read', 'Yes/No', 'text'), ('#last_read', 'Date', None)],
        lambda text: '>' + text)
    assert lines == [
        '>The column #read is not of type ">Yes/No".',
        '>The column #last_read does not exist in this library.',
    ]
