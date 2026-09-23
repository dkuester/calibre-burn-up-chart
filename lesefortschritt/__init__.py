from calibre.customize import InterfaceActionBase
from calibre.utils.config import JSONConfig


# Einzige Quelle der Wahrheit für die Plugin-Version
__version__ = (1, 0, 0)
__version_str__ = '.'.join(str(x) for x in __version__)


config = JSONConfig('plugins/lesefortschritt')
config.defaults['ziel_datum'] = '2050-09-04'
config.defaults['abbau_faktor'] = 0.5


class LesefortschrittPlugin(InterfaceActionBase):
    name = 'Lesefortschritt'
    description = 'Zeigt den Lesefortschritt als Burn-up-Chart an'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Daniel'
    version = __version__
    minimum_calibre_version = (5, 0, 0)

    actual_plugin = 'calibre_plugins.lesefortschritt.main:LesefortschrittAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.lesefortschritt.config_dialog import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()