"""
gettext-Setup für das Plugin.

Lädt die Übersetzung für die von Calibre gewählte Sprache. Da Calibre
Plugins immer aus einem ZIP lädt, kann gettext die .mo-Datei nicht
direkt aus dem Archiv lesen – sie wird daher nach /tmp extrahiert.
"""

import gettext
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


def _mo_aus_zip(zip_pfad, codes):
    """Extrahiert die passende .mo aus dem ZIP nach /tmp und gibt den Pfad zurück."""
    with zipfile.ZipFile(zip_pfad) as z:
        for code in codes:
            rel = f'translations/{code}/LC_MESSAGES/lesefortschritt.mo'
            try:
                daten = z.read(rel)
            except KeyError:
                continue
            ziel = os.path.join(tempfile.gettempdir(),
                                f'lesefortschritt_{code}.mo')
            with open(ziel, 'wb') as f:
                f.write(daten)
            return ziel
    return None


def _mo_aus_ordner(ordner, codes):
    """Sucht die .mo im Dateisystem (Entwicklungsbetrieb)."""
    for code in codes:
        pfad = os.path.join(ordner, 'translations', code,
                            'LC_MESSAGES', 'lesefortschritt.mo')
        if os.path.exists(pfad):
            return pfad
    return None


def finde_mo(lang):
    """Liefert einen Dateisystempfad zur passenden .mo-Datei oder None.

    Öffentliche Funktion, damit main.py denselben Pfad für den
    zeichne_chart.py-Subprozess wiederverwenden kann.
    """
    codes = _sprachcodes(lang)
    pdir = _plugin_dir()

    if pdir.endswith('.zip'):
        return _mo_aus_zip(pdir, codes)

    return _mo_aus_ordner(pdir, codes)


def _install():
    try:
        mo_pfad = finde_mo(get_lang())
        if mo_pfad is None:
            return gettext.NullTranslations().gettext
        with open(mo_pfad, 'rb') as f:
            return gettext.GNUTranslations(f).gettext
    except Exception as e:
        print(f'Lesefortschritt: localization error: {e}')
        return gettext.NullTranslations().gettext


_ = _install()