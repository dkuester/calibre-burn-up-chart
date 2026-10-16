from calibre.customize import InterfaceActionBase
from calibre.utils.config import JSONConfig

__version__ = (1, 5, 0)
__version_str__ = '.'.join(str(x) for x in __version__)


config = JSONConfig('plugins/readingprogress')
config.defaults['target_date'] = '2050-09-04'
config.defaults['reduction_factor'] = 0.5
config.defaults['read_column'] = '#gelesen'
config.defaults['last_read_column'] = '#last_read'
config.defaults['show_forecast'] = True
config.defaults['color_total'] = '#888888'
config.defaults['color_read'] = '#2a9d8f'
config.defaults['color_backlog'] = '#e76f51'
config.defaults['color_goal'] = '#264653'
config.defaults['color_stable'] = '#f4a261'
config.defaults['color_soft'] = '#8ecae6'
config.defaults['color_forecast'] = '#8338ec'
config.defaults['_migrated_keys'] = False

# One-time migration from the legacy German config keys to English ones:
# reads the interim German keys from this config, falling back to the
# pre-rename 'plugins/lesefortschritt' config for a direct upgrade.
if not config['_migrated_keys']:
    legacy = JSONConfig('plugins/lesefortschritt')
    legacy.defaults.update({
        'ziel_datum': '2050-09-04',
        'abbau_faktor': 0.5,
        'spalte_gelesen': '#gelesen',
        'spalte_last_read': '#last_read',
    })
    for new_key, old_key in (('target_date', 'ziel_datum'),
                             ('reduction_factor', 'abbau_faktor'),
                             ('read_column', 'spalte_gelesen'),
                             ('last_read_column', 'spalte_last_read')):
        try:
            value = config[old_key]
        except KeyError:
            value = legacy[old_key]
        config[new_key] = value
    config['_migrated_keys'] = True


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
