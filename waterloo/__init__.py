import inject

from waterloo.conf import _settings
from waterloo.utils import StylePrinter


def configuration_factory(settings):
    def configure(binder):
        binder.bind("settings", settings)
        binder.bind(
            "echo",
            StylePrinter(
                style=getattr(settings, "ECHO_STYLES", None),
                log_level=settings.LOG_LEVEL,
            ),
        )

    return configure


inject.configure(configuration_factory(_settings))
