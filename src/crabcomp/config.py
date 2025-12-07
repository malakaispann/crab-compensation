import logging

from pathlib import Path
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    AnyUrl,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
)
from pydantic_core import PydanticCustomError

__all__ = ["Uri", "DataStoreConfig", "LoggingConfig"]

type Uri = AnyUrl | Path  # order is significant

_shared_model_config = ConfigDict(
    frozen=True,
    extra="ignore",
    serialize_by_alias=True,
    validate_by_alias=True,
    validate_by_name=False,
)


def _check_uri(uri: Uri) -> Uri:
    """Validates passed uri.

    If the URI is a local path, this method ensures it exists and points to
    a regular file. Other input types are not currently validated.

    Args:
        uri: the uri to check.

    Returns:
        The validated, unmodified uri.
    """
    if uri is None:
        return uri

    # Ensure file exists if it's a local path
    if isinstance(uri, Path) and (not uri.exists() or uri.is_file()):
        raise ValidationError.from_exception_data(
            title="Invalid Data Path",
            line_errors=[
                {
                    "type": PydanticCustomError(
                        "invalid_data_path",
                        "Data file could not be found or is not a file. Normalized path: {path}",
                        {"path": str(uri.absolute())},
                    ),
                    "input": str(uri),
                }
            ],
        )

    return uri


def _transform_log_string(level: Any) -> int:
    """Validates passed level against known levels.

    Args:
        level: the level to validate in string format.

    Returns:
        The integer representation of the passed log level, if available.
    """
    if level is None:
        return level

    # Get valid logging levels excluding NOTSET.
    level_mapping = logging.getLevelNamesMapping()
    level_mapping.pop("NOTSET")

    # Ensure passed level is valid.
    if isinstance(level, str) and (representation := level_mapping.get(level.upper())):
        return representation

    raise ValidationError.from_exception_data(
        title="Invalid Log Level",
        line_errors=[
            {
                "type": PydanticCustomError(
                    "invalid_log_level",
                    "Provided log level is not valid, Available options {options}",
                    {"options": list(level_mapping.keys())},
                ),
                "input": level,
            }
        ],
    )


class DataStoreConfig(BaseModel):
    """A configuration parser, validator, data storage construct used to
    define the location of data used by the application.
    """

    model_config = _shared_model_config

    data_uri: Annotated[Uri, AfterValidator(_check_uri), Field(alias="DATA_URI")]
    """The local path or web url to a file containing the expected data."""


class LoggingConfig(BaseModel):
    """
    A configuration parser, validator, data storage construct used to
    define logging behavior across the application
    """

    model_config = _shared_model_config

    level: Annotated[
        int, BeforeValidator(_transform_log_string), Field(alias="LOG_LEVEL")
    ] = logging.INFO
    """The minimum level to use when outputting logs. Defaults to INFO"""
