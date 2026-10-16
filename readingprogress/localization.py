"""
gettext-Setup für das Plugin.

Lädt die Übersetzung für die von Calibre gewählte Sprache. Da Calibre
Plugins immer aus einem ZIP lädt, kann gettext die .mo-Datei nicht
direkt aus dem Archiv lesen – sie wird daher in ein temporäres
Verzeichnis extrahiert.
"""

import gettext
import hashlib
import os
import tempfile
import zipfile

from calibre.utils.localization import get_lang


def _plugin_dir():
    return os.path.dirname(os.path.abspath(__file__))


def _sprachcodes(lang):
    """'de_DE' → ['de_DE', 'de']; 'de' → ['de']."""
    codes = [lang]
    if '_' in lang:
        codes.append(lang.split('_')[0])
    return codes


def _cache_name(zip_pfad, code):
    kurz = hashlib.md5(zip_pfad.encode('utf-8')).hexdigest()[:8]
    return f'readingprogress_{code}_{kurz}.mo'


def _mo_aus_zip(zip_pfad, codes):
    with zipfile.ZipFile(zip_pfad) as z:
        for code in codes:
            rel = f'translations/{code}/LC_MESSAGES/readingprogress.mo'
            try:
                daten = z.read(rel)
            except KeyError:
                continue
            ziel = os.path.join(tempfile.gettempdir(),
                                _cache_name(zip_pfad, code))
            with open(ziel, 'wb') as f:
                f.write(daten)
            return ziel
    return None


def _mo_aus_ordner(ordner, codes):
    for code in codes:
        pfad = os.path.join(ordner, 'translations', code,
                            'LC_MESSAGES', 'readingprogress.mo')
        if os.path.exists(pfad):
            return pfad
    return None


def _finde_mo(lang):
    codes = _sprachcodes(lang)
    pdir = _plugin_dir()

    if pdir.endswith('.zip'):
        return _mo_aus_zip(pdir, codes)

    return _mo_aus_ordner(pdir, codes)


def _install():
    try:
        mo_pfad = _finde_mo(get_lang())
        if mo_pfad is None:
            return gettext.NullTranslations().gettext
        with open(mo_pfad, 'rb') as f:
            return gettext.GNUTranslations(f).gettext
    except Exception as e:
        print(f'ReadingProgress: localization error: {e}')
        return gettext.NullTranslations().gettext


_ = _install()