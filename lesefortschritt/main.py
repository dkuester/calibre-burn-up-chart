import os
import subprocess
import zipfile

from qt.core import QIcon, QPixmap

from calibre.gui2.actions import InterfaceAction

from calibre_plugins.lesefortschritt import config


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
    action_spec = ('Burn-up Chart', None,
                   'Lesefortschritt als Burn-up-Chart anzeigen', None)
    action_type = 'current'

    def genesis(self):
        # ZUERST die Verbindung — damit der Klick immer funktioniert
        self.qaction.triggered.connect(self.show_chart)

        # DANN das Icon — Fehler hier dürfen den Button nicht lahmlegen
        try:
            icon = _lade_icon()
            if icon is not None:
                self.qaction.setIcon(icon)
            else:
                print('Lesefortschritt: Icon nicht gefunden '
                      '(images/icon.png fehlt oder ist ungültig).')
        except Exception as e:
            print(f'Lesefortschritt: Icon konnte nicht geladen werden: {e}')

    def show_chart(self):
        from calibre_plugins.lesefortschritt.export_lesestatus import exportiere
        from calibre_plugins.lesefortschritt.chart_dialog import ChartDialog

        # 1. CSV schreiben — direkt aus der laufenden Bibliothek
        try:
            info = exportiere(db_api=self.gui.current_db.new_api,
                              log_pfad=CSV_PFAD)
        except Exception as e:
            self.gui.status_bar.show_message(
                f'Export fehlgeschlagen: {e}', 5000)
            return

        # 2. Zeichen-Skript lokalisieren
        try:
            skript = _hole_zeichne_skript()
        except Exception as e:
            self.gui.status_bar.show_message(
                f'Zeichen-Skript konnte nicht extrahiert werden: {e}', 8000)
            return

        if not skript or not os.path.exists(skript):
            self.gui.status_bar.show_message(
                'zeichne_chart.py nicht gefunden.', 8000)
            return

        # 3. Chart zeichnen — Config-Werte und Pfade als Argumente
        ziel_datum   = config['ziel_datum']
        abbau_faktor = config['abbau_faktor']

        try:
            subprocess.run(
                [PYTHON3, skript,
                 '--log-pfad', CSV_PFAD,
                 '--ziel-datum', ziel_datum,
                 '--abbau-faktor', str(abbau_faktor),
                 '--ausgabe-pfad', CHART_PNG],
                check=True, capture_output=True, text=True,
                cwd=PROJEKT_DIR,
            )
        except FileNotFoundError:
            self.gui.status_bar.show_message(
                f'Python nicht gefunden: {PYTHON3}', 5000)
            return
        except subprocess.CalledProcessError as e:
            msg = (e.stderr or e.stdout or '').strip().splitlines()
            kurz = msg[-1] if msg else 'unbekannter Fehler'
            self.gui.status_bar.show_message(
                f'Chart-Zeichnen fehlgeschlagen: {kurz}', 8000)
            return

        # 4. Kurze Statusmeldung
        self.gui.status_bar.show_message(
            f"Lesestatus: {info['gelesen']}/{info['gesamt']} gelesen, "
            f"Backlog {info['backlog']}", 5000)

        # 5. Dialog mit dem fertigen PNG
        dlg = ChartDialog(CHART_PNG, self.gui)
        dlg.exec_()