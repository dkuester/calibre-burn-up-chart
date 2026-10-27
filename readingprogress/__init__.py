from calibre.customize import InterfaceActionBase
from calibre.utils.config import JSONConfig

__version__ = (1, 7, 0)
__version_str__ = '.'.join(str(x) for x in __version__)


config = JSONConfig('plugins/readingprogress')
# Defaults and one-time migrations live in main._setup_config(), not here:
# calibre-customize -b executes this module in a context where sibling
# imports (chart_common, config_helpers) resolve to the installed plugin.


class ReadingProgressPlugin(InterfaceActionBase):
    name = 'Reading Progress'
    description = 'Displays reading progress as a burn-up chart'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Daniel'
    version = __version__
    minimum_calibre_version = (9, 3, 1)

    actual_plugin = 'calibre_plugins.readingprogress.main:ReadingProgressAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.readingprogress.config_dialog import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()
