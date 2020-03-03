from typing import Dict, Optional, Union

import toml
from pydantic import BaseSettings, validator

from waterloo.types import (
    AmbiguousTypePolicy,
    ECHO_STYLES_REQUIRED_FIELDS,
)


class ConfigModel(BaseSettings):
    class Config:
        validate_assignment = True
        env_prefix = 'WATERLOO_'

    PYTHON_VERSION: str = "2.7"

    ALLOW_UNTYPED_ARGS: bool = False
    REQUIRE_RETURN_TYPE: bool = False

    AMBIGUOUS_TYPE_POLICY: Union[AmbiguousTypePolicy, str] = (
        AmbiguousTypePolicy.AUTO
    )

    ECHO_STYLES: Optional[Dict[str, str]] = None

    @validator('AMBIGUOUS_TYPE_POLICY')
    def key_to_member(cls, value):
        if isinstance(value, AmbiguousTypePolicy):
            return value
        return AmbiguousTypePolicy[value]

    @validator('ECHO_STYLES')
    def echo_styles_required_fields(cls, value):
        if value is not None:
            assert all(
                key in value for key in ECHO_STYLES_REQUIRED_FIELDS
            ), f"missing required keys from {ECHO_STYLES_REQUIRED_FIELDS!r}"
        return value

    def indent(self) -> str:
        if isinstance(self.INDENT, int):
            return " " * self.INDENT
        else:
            return "\t"


try:
    _config = toml.load('waterloo.toml')
except FileNotFoundError:
    _config = {}


settings = ConfigModel(
    **{key.upper(): val for key, val in _config.items()}
)
