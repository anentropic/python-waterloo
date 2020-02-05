import sys

from loguru import logger


# https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.add
LOG_FORMAT = '<level>{message}</level>'

logger.configure(
    handlers=[
        {'format': LOG_FORMAT, 'sink': sys.stderr},
    ],
)
logger.level(name='ERROR', color='<red>')
logger.level(name='WARNING', color='<yellow>')
logger.level(name='INFO', color='<white>')
