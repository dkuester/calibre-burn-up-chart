import os
import subprocess
import zipfile

from qt.core import QIcon, QPixmap

from calibre.gui2.actions import InterfaceAction
from calibre.utils.localization import get_lang

from calibre_plugins.lesefortschritt import config
from calibre_plugins.lesefortschritt.localization import _, finde_mo


PROJEKT_DIR  = '/Users/daniel/GitHub/calibre-burn-up-chart'
PYTHON3      = '/opt/homebrew/bin/python3'
CACHE_SKRIPT = os.path.join(PROJEKT_DIR, '.zeichne_chart_cache.py')

# Feste, für beide Prozesse sichtbare Pfade
CSV_PFAD  = '/tmp/burndown_log.csv'
CHART_PNG = '/tmp/lesefortschritt.png'


def _hole_zeichne_skript():
    """Liefert den Dateisystempfad zu zeichne_chart.py."""
    plugin_dir = os.path.dirname(os.path.abspath(__file__))

    if plugin_dir.endswith('.zip'):
        with zipfile.ZipFile(plugin_dir) as z:
            quelle = z.read('zeichne_chart.py')
        with open(CACHE_SKRIPT, 'wb') as f:
            f.write(quelle)
        return CACHE_SKRIPT

    direkt = os.path.join(plugin_dir, 'zeichne_chart.py')
    if os.path.exists(direkt):
        return direkt

    return None


def _lade_icon():
    """Lädt das Plugin-Icon aus images/icon.png – Ordner oder ZIP."""
    plugin_dir = os.path.dirname(os.path.abspath(__file__))

    if plugin_dir.endswith('.zip'):
        with zipfile.ZipFile(plugin_dir) as z:
            try:
                daten = z.read('images/icon.png')
            except KeyError:
                return None
        pixmap = QPixmap()
        if not pixmap.loadFromData(daten):
            return None
        return QIcon(pixmap)

    pfad = os.path.join(plugin_dir, 'images', 'icon.png')
    if not os.path.exists(pfad):
        return None
    pixmap = QPixmap(pfad)
    if pixmap.isNull():
        return None
    return QIcon(pixmap)


class LesefortschrittAction(InterfaceAction):

    name = 'Lesefortschritt'
    action_spec = (_('Burn-up Chart'), None,
                   _('Display reading progress as a burn-up chart'), None)
    action_type = 'current'

    def genesis(self):
        self.qaction.triggered.connect(self.show_chart)

        try:
            icon = _lade_icon()
            if icon is not None:
                self.qaction.setIcon(icon)
        except Exception as e:
            print(f'Lesefortschritt: icon error: {e}')

    def show_chart(self):
        from calibre_plugins.lesefortschritt.export_lesestatus import exportiere
        from calibre_plugins.lesefortschritt.chart_dialog import ChartDialog

        try:
            info = exportiere(db_api=self.gui.current_db.new_api,
                              log_pfad=CSV_PFAD)
        except Exception as e:
            self.gui.status_bar.show_message(
                _('Export failed: {}').format(e), 5000)
            return

        try:
            skript = _hole_zeichne_skript()
        except Exception as e:
            self.gui.status_bar.show_message(
                _('Could not extract drawing script: {}').format(e), 8000)
            return

        if not skript or not os.path.exists(skript):
            self.gui.status_bar.show_message(
                _('zeichne_chart.py not found.'), 8000)
            return

        ziel_datum   = config['ziel_datum']
        abbau_faktor = config['abbau_faktor']

        # Sprachdatei für den Subprozess – dieselbe Quelle wie für den Dialog
        try:
            mo_pfad = finde_mo(get_lang())
        except Exception:
            mo_pfad = None

        cmd = [PYTHON3, skript,
               '--log-pfad', CSV_PFAD,
               '--ziel-datum', ziel_datum,
               '--abbau-faktor', str(abbau_faktor),
               '--ausgabe-pfad', CHART_PNG]
        if mo_pfad:
            cmd += ['--translation-mo', mo_pfad]

        try:
            subprocess.run(cmd, check=True, capture_output=True,
                           text=True, cwd=PROJEKT_DIR)
        except FileNotFoundError:
            self.gui.status_bar.show_message(
                _('Python not found: {}').format(PYTHON3), 5000)
            return
        except subprocess.CalledProcessError as e:
            msg = (e.stderr or e.stdout or '').strip().splitlines()
            kurz = msg[-1] if msg else 'unknown error'
            self.gui.status_bar.show_message(
                _('Chart rendering failed: {}').format(kurz), 8000)
            return

        self.gui.status_bar.show_message(
            _('Reading status: {read}/{total} read, backlog {backlog}').format(
                read=info['gelesen'], total=info['gesamt'],
                backlog=info['backlog']), 5000)

        dlg = ChartDialog(CHART_PNG, self.gui)
        dlg.exec_()