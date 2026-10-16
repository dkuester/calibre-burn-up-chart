from calibre.customize import InterfaceActionBase
from calibre.utils.config import JSONConfig

__version__ = (1, 4, 0)
__version_str__ = '.'.join(str(x) for x in __version__)


config = JSONConfig('plugins/readingprogress')
config.defaults['ziel_datum'] = '2050-09-04'
config.defaults['abbau_faktor'] = 0.5
config.defaults['spalte_gelesen'] = '#gelesen'
config.defaults['spalte_last_read'] = '#last_read'
config.defaults['_migrated_from_legacy'] = False

# One-time migration from the old config key ('plugins/lesefortschritt'),
# so existing users keep their settings after the rename.
if not config['_migrated_from_legacy']:
    _legacy = JSONConfig('plugins/lesefortschritt')
    _legacy.defaults.update({
        'ziel_datum': '2050-09-04',
        'abbau_faktor': 0.5,
        'spalte_gelesen': '#gelesen',
        'spalte_last_read': '#last_read',
    })
    config['ziel_datum'] = _legacy['ziel_datum']
    config['abbau_faktor'] = _legacy['abbau_faktor']
    config['spalte_gelesen'] = _legacy['spalte_gelesen']
    config['spalte_last_read'] = _legacy['spalte_last_read']
    config['_migrated_from_legacy'] = True


class ReadingProgressPlugin(InterfaceActionBase):
    name = 'Reading Progress'
    description = 'Displays reading progress as a burn-up chart'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Daniel'
    version = __version__
    minimum_calibre_version = (5, 0, 0)

    actual_plugin = 'calibre_plugins.readingprogress.main:ReadingProgressAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.readingprogress.config_dialog import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()