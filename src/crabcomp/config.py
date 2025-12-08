import logging

from pathlib import Path
from typing import Annotated, Any, Mapping

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

from crabcomp.result import ErrorCode, Result

__all__ = ["Uri", "AppConfig", "AppConfigErrorCodes"]

_logger = logging.getLogger(__name__)

type Uri = AnyUrl | Path  # order is significant


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
        _logger.debug("Nullish URI detected during validation.")
        return uri

    # Ensure file exists if it's a local path.
    if isinstance(uri, Path) and (not uri.exists() or not uri.is_file()):
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
        _logger.debug("Nullish log level detected during validation.")
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


class AppConfigErrorCodes(ErrorCode):
    """
    Indicates an error was encountered while attempting to extract and validate
    the application configuration from an environment.
    """

    INVALID_CONFIGURATION = ErrorCode.auto()


class AppConfig(BaseModel):
    """
    A configuration parser, validator, data storage construct used to
    define the location of data used by the application, logging behavior, etc.
    across the application.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        serialize_by_alias=True,
        validate_by_alias=True,
        validate_by_name=False,
    )

    data_uri: Annotated[Uri, AfterValidator(_check_uri), Field(alias="DATA_URI")]
    """The local path or web url to a file containing the expected data."""

    log_level: Annotated[
        int, BeforeValidator(_transform_log_string), Field(alias="LOG_LEVEL")
    ] = logging.INFO
    """The minimum level to use when outputting logs. Defaults to INFO"""

    @staticmethod
    def extract(environ: Mapping[str, Any]) -> Result["AppConfig"]:
        """Extracts the application configuration.

        Args:
            environ: the environment extract the configuration from.

        Raises:
            AppConfigurationError if unable to extract the configuration information
            from the provided environment.

        Returns:
            The wrapped application configuration if provided environment contains valid definitions.
        """
        _logger.debug("Attempting to application extract configuration.")
        try:
            app_config = AppConfig.model_validate(environ)
        except ValidationError as err:
            _logger.error(
                f"Failed to extract configuration from provided environment. Errors: {err.json()}"
            )
            return Result.failure(AppConfigErrorCodes.INVALID_CONFIGURATION)

        return Result.success(app_config)
