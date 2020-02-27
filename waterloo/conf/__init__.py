from typing import Dict, Optional, Union

import toml
from pydantic import BaseSettings, validator

from waterloo.types import UnresolvedTypePolicy, ECHO_STYLES_REQUIRED_FIELDS


class ConfigModel(BaseSettings):
    class Config:
        validate_assignment = True

    INDENT: str = "    "
    MAX_INDENT_LEVEL: int = 10

    ALLOW_UNTYPED_ARGS: bool = False
    REQUIRE_RETURN_TYPE: bool = False

    UNRESOLVED_TYPE_POLICY: Union[UnresolvedTypePolicy, str] = (
        UnresolvedTypePolicy.AUTO
    )

    ECHO_STYLES: Optional[Dict[str, str]] = None

    @validator('UNRESOLVED_TYPE_POLICY')
    def key_to_member(cls, value):
        if isinstance(value, UnresolvedTypePolicy):
            return value
        return UnresolvedTypePolicy[value]

    @validator('ECHO_STYLES')
    def echo_styles_required_fields(cls, value):
        if value is not None:
            assert all(
                key in value for key in ECHO_STYLES_REQUIRED_FIELDS
            ), f"missing required keys from {ECHO_STYLES_REQUIRED_FIELDS!r}"
        return value


try:
    _config = toml.load('waterloo.toml')
except FileNotFoundError:
    _config = {}


settings = ConfigModel(
    **{key.upper(): val for key, val in _config.items()}
)
