import toml
import typesystem as t


class Config(t.Schema):
    INDENT = t.String(default="    ")
    MAX_INDENT_LEVEL = t.Integer(default=10)

    ALLOW_UNTYPED_ARGS = t.Boolean(default=False)
    REQUIRE_RETURN_TYPE = t.Boolean(default=False)

    ECHO_STYLES = t.Object(
        properties=t.String(),
        required=['debug', 'info', 'warning', 'error']
    )


try:
    _config = toml.load('waterloo.toml')
except FileNotFoundError:
    _config = {}


settings = Config(**{key.upper(): val for key, val in _config.items()})
