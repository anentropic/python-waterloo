from enum import Enum
from typing import Dict, no_type_check, Optional, Union

import toml
from pydantic import BaseSettings, validator

from waterloo.types import (
    AmbiguousTypePolicy,
    ECHO_STYLES_REQUIRED_FIELDS,
)


class CoerceEnumSettings(BaseSettings):
    """
    Allow to set value via Enum member name rather than enum instance to fields
    having an Enum type, in conjunction with Config.validate_assignment = True
    """
    @no_type_check
    def __setattr__(self, name, value):
        field = self.__fields__[name]
        if (
            issubclass(field.type_, Enum)
            and not isinstance(value, Enum)
        ):
            value = field.type_[value]
        return super().__setattr__(name, value)


class ConfigModel(CoerceEnumSettings):
    class Config:
        validate_assignment = True
        env_prefix = 'WATERLOO_'

    PYTHON_VERSION: str = "2.7"

    ALLOW_UNTYPED_ARGS: bool = False
    REQUIRE_RETURN_TYPE: bool = False

    AMBIGUOUS_TYPE_POLICY: AmbiguousTypePolicy = AmbiguousTypePolicy.AUTO

    ECHO_STYLES: Optional[Dict[str, str]] = None

    @validator('AMBIGUOUS_TYPE_POLICY')
    def key_to_member(
        cls, value: Union[AmbiguousTypePolicy, str]
    ) -> AmbiguousTypePolicy:
        if isinstance(value, AmbiguousTypePolicy):
            return value
        return AmbiguousTypePolicy[value]

    @validator('ECHO_STYLES')
    def echo_styles_required_fields(
        cls, value: Optional[Dict[str, str]]
    ) -> Optional[Dict[str, str]]:
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
