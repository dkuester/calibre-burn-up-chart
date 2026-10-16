import os
import zipfile

from calibre.gui2.actions import InterfaceAction
from calibre.utils.localization import get_lang
from calibre_plugins.lesefortschritt import config
from calibre_plugins.lesefortschritt.localization import _
from qt.core import QIcon, QMenu, QPixmap, QTimer, QToolButton


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
                   _('Reading statistics for your library'), None)
    action_type = 'current'

    def genesis(self):
        # Icon setzen (Fehler dürfen nichts lahmlegen)
        try:
            icon = _lade_icon()
            if icon is not None:
                self.qaction.setIcon(icon)
        except Exception as e:
            print(f'Lesefortschritt: icon error: {e}')

        # Standardaktion bei Klick auf den Hauptbereich des Buttons
        self.qaction.triggered.connect(self.show_chart)

        # Menü mit beiden Optionen – erscheint beim Klick auf den Pfeil
        menu = QMenu(self.gui)
        menu.addAction(_('Burn-up chart'), self.show_chart)
        menu.addAction(_('Time between purchase and reading'),
                       self.show_delay)
        self.qaction.setMenu(menu)

        # Nach der Toolbar-Erstellung den QToolButton umkonfigurieren:
        # MenuButtonPopup = Klick auf Hauptbereich = Standardaktion,
        # kleiner Pfeil rechts = Menü
        QTimer.singleShot(0, self._aktiviere_popup_modus)

    def _aktiviere_popup_modus(self):
        """Setzt den QToolButton auf MenuButtonPopup."""
        try:
            for tb in self.gui.findChildren(QToolButton):
                if tb.defaultAction() is self.qaction:
                    tb.setPopupMode(QToolButton.MenuButtonPopup)
                    return
        except Exception as e:
            print(f'Lesefortschritt: PopupMode error: {e}')

    # ------------------------------------------------------------------
    # Aktionen
    # ------------------------------------------------------------------
    def show_chart(self):
        from datetime import datetime

        from calibre_plugins.lesefortschritt.chart_dialog import ChartDialog
        from calibre_plugins.lesefortschritt.export_lesestatus import exportiere

        try:
            info = exportiere(
                db_api=self.gui.current_db.new_api,
                spalte_gelesen=config['spalte_gelesen'],
                spalte_last_read=config['spalte_last_read'],
            )
        except Exception as e:
            self.gui.status_bar.show_message(
                _('Export failed: {}').format(e), 5000)
            return

        try:
            ziel_datum = datetime.fromisoformat(config['ziel_datum']).date()
        except ValueError:
            ziel_datum = datetime(2050, 9, 4).date()
        abbau_faktor = float(config['abbau_faktor'])

        sprache = get_lang().split('_')[0]
        datum_format = '%d.%m.%Y' if sprache == 'de' else '%Y-%m-%d'

        self.gui.status_bar.show_message(
            _('Reading status: {read}/{total} read, backlog {backlog}').format(
                read=info['gelesen'], total=info['gesamt'],
                backlog=info['backlog']), 5000)

        dlg = ChartDialog(info['rows'], ziel_datum, abbau_faktor,
                          datum_format, self.gui)
        dlg.exec_()

    def show_delay(self):
        from calibre_plugins.lesefortschritt.delay_dialog import DelayChartDialog
        from calibre_plugins.lesefortschritt.export_lesestatus import berechne_lesezeit

        try:
            info = berechne_lesezeit(
                db_api=self.gui.current_db.new_api,
                spalte_gelesen=config['spalte_gelesen'],
                spalte_last_read=config['spalte_last_read'],
            )
        except Exception as e:
            self.gui.status_bar.show_message(
                _('Export failed: {}').format(e), 5000)
            return

        if not info['punkte']:
            self.gui.status_bar.show_message(
                _('No data available for this analysis.'), 8000)
            return

        sprache = get_lang().split('_')[0]
        datum_format = '%d.%m.%Y' if sprache == 'de' else '%Y-%m-%d'

        s = info['statistik']
        self.gui.status_bar.show_message(
            _('Median: {med} days, mean: {mean} days (n={n})').format(
                med=int(round(s['median'])),
                mean=int(round(s['mittel'])),
                n=s['anzahl']), 5000)

        dlg = DelayChartDialog(
            info['punkte'], info['statistik'],
            datum_format, sprache, self.gui)
        dlg.exec_()