import logging
import sys
from threading import local

import inject
import structlog
from structlog.processors import KeyValueRenderer
from structlog.stdlib import LoggerFactory
from structlog.threadlocal import merge_threadlocal

from waterloo.conf import _settings
from waterloo.printer import StylePrinter


def configuration_factory(settings):
    def get_logger():
        logging.basicConfig(
            stream=sys.stderr, level=settings.LOG_LEVEL.value,
        )
        structlog.configure(
            logger_factory=LoggerFactory(),
            processors=[merge_threadlocal, KeyValueRenderer()],
        )
        logger = structlog.get_logger("waterloo")
        return logger.bind()

    def configure(binder):
        binder.bind("settings", settings)
        binder.bind_to_constructor("log", get_logger)
        binder.bind(
            "echo",
            StylePrinter(
                style=getattr(settings, "ECHO_STYLES", None),
                verbose_echo=settings.VERBOSE_ECHO,
            ),
        )
        # for use in bowler subprocesses
        # for passing data between individual steps processing same source file
        binder.bind_to_constructor("threadlocals", local)

    return configure


inject.configure(configuration_factory(_settings))
