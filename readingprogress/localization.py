"""
gettext setup for the plugin.

Loads the translation for the language Calibre selected. Since Calibre
always loads plugins from a ZIP, gettext cannot read the .mo file
directly from the archive – it is therefore extracted to a temporary
directory.
"""

import gettext
import hashlib
import os
import tempfile
import zipfile

from calibre.utils.localization import get_lang


def _plugin_dir():
    return os.path.dirname(os.path.abspath(__file__))


def _language_codes(lang):
    """'de_DE' → ['de_DE', 'de']; 'de' → ['de']."""
    codes = [lang]
    if '_' in lang:
        codes.append(lang.split('_')[0])
    return codes


def _cache_name(zip_path, code):
    short = hashlib.md5(zip_path.encode('utf-8')).hexdigest()[:8]
    return f'readingprogress_{code}_{short}.mo'


def _mo_from_zip(zip_path, codes):
    with zipfile.ZipFile(zip_path) as z:
        for code in codes:
            rel = f'translations/{code}/LC_MESSAGES/readingprogress.mo'
            try:
                data = z.read(rel)
            except KeyError:
                continue
            target = os.path.join(tempfile.gettempdir(),
                                  _cache_name(zip_path, code))
            with open(target, 'wb') as f:
                f.write(data)
            return target
    return None


def _mo_from_folder(folder, codes):
    for code in codes:
        path = os.path.join(folder, 'translations', code,
                            'LC_MESSAGES', 'readingprogress.mo')
        if os.path.exists(path):
            return path
    return None


def _find_mo(lang):
    codes = _language_codes(lang)
    plugin_dir = _plugin_dir()

    if plugin_dir.endswith('.zip'):
        return _mo_from_zip(plugin_dir, codes)

    return _mo_from_folder(plugin_dir, codes)


def _install():
    try:
        mo_path = _find_mo(get_lang())
        if mo_path is None:
            return gettext.NullTranslations().gettext
        with open(mo_path, 'rb') as f:
            return gettext.GNUTranslations(f).gettext
    except Exception as e:
        print(f'ReadingProgress: localization error: {e}')
        return gettext.NullTranslations().gettext


_ = _install()
