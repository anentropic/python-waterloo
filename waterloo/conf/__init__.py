import toml

from waterloo.conf.types import Settings

try:
    _config = toml.load("waterloo.toml")
except FileNotFoundError:
    _config = {}


_settings = Settings(**{key.upper(): val for key, val in _config.items()})
