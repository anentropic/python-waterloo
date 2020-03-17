import inject

from waterloo.conf import _settings
from waterloo.utils import StylePrinter


def configuration_factory(settings):
    def configure(binder):
        binder.bind('settings', settings)
        binder.bind(
            'echo',
            StylePrinter(getattr(settings, 'ECHO_STYLES', None))
        )
    return configure


inject.configure(configuration_factory(_settings))
