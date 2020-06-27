from enum import Enum
from typing import Dict, Optional, Union, no_type_check

from pydantic import BaseSettings, validator

from waterloo.types import (
    LOG_LEVEL_LABELS,
    ImportCollisionPolicy,
    LogLevel,
    UnpathedTypePolicy,
)


class CoerceEnumSettings(BaseSettings):
    """
    Allow to set value via Enum member name rather than enum instance to fields
    having an Enum type, in conjunction with Config.validate_assignment = True
    """

    @no_type_check
    def __setattr__(self, name, value):
        field = self.__fields__[name]
        if issubclass(field.type_, Enum) and not isinstance(value, Enum):
            value = field.type_[value]
        return super().__setattr__(name, value)


class Settings(CoerceEnumSettings):
    class Config:
        validate_assignment = True
        env_prefix = "WATERLOO_"

    PYTHON_VERSION: str = "2.7"

    ALLOW_UNTYPED_ARGS: bool = False
    REQUIRE_RETURN_TYPE: bool = False

    IMPORT_COLLISION_POLICY: ImportCollisionPolicy = ImportCollisionPolicy.IMPORT
    UNPATHED_TYPE_POLICY: UnpathedTypePolicy = UnpathedTypePolicy.FAIL

    ECHO_STYLES: Optional[Dict[str, str]] = None

    VERBOSE_ECHO: bool = True
    LOG_LEVEL: LogLevel = LogLevel.INFO

    @validator("IMPORT_COLLISION_POLICY")
    def key_to_member(
        cls, value: Union[ImportCollisionPolicy, str]
    ) -> ImportCollisionPolicy:
        if isinstance(value, ImportCollisionPolicy):
            return value
        return ImportCollisionPolicy[value]

    @validator("ECHO_STYLES")
    def echo_styles_required_fields(
        cls, value: Optional[Dict[str, str]]
    ) -> Optional[Dict[str, str]]:
        if value is not None:
            assert all(
                key in value for key in LOG_LEVEL_LABELS.values()
            ), f"missing required keys from {LOG_LEVEL_LABELS.values()}"
        return value

    def indent(self) -> str:
        if isinstance(self.INDENT, int):
            return " " * self.INDENT
        else:
            return "\t"
