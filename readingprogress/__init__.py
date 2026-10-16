from calibre.customize import InterfaceActionBase
from calibre.utils.config import JSONConfig
from calibre_plugins.readingprogress.chart_common import DEFAULT_COLORS

__version__ = (1, 6, 0)
__version_str__ = '.'.join(str(x) for x in __version__)


config = JSONConfig('plugins/readingprogress')
config.defaults['target_date'] = '2050-09-04'
config.defaults['reduction_factor'] = 0.5
config.defaults['read_column'] = '#gelesen'
config.defaults['last_read_column'] = '#last_read'
config.defaults['show_forecast'] = True
for color_key in DEFAULT_COLORS:
    config.defaults[f'color_{color_key}'] = ''   # '' = follow theme
config.defaults['_migrated_keys'] = False
config.defaults['_migrated_colors_auto'] = False

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

# One-time migration: colors previously defaulted to the light-theme hexes.
# If none were customized, reset them to '' (auto) so dark mode applies.
if not config['_migrated_colors_auto']:
    if all(config[f'color_{k}'] == DEFAULT_COLORS[k] for k in DEFAULT_COLORS):
        for k in DEFAULT_COLORS:
            config[f'color_{k}'] = ''
    config['_migrated_colors_auto'] = True


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
