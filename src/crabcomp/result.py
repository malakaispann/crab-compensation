import enum

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar


__all__ = ["ErrorCode", "GenericCode", "Result", "ResultCode"]

T = TypeVar("T")


class ResultCode(enum.IntEnum):
    """Base class for result codes representing success or failure states."""

    def __str__(self) -> str:
        return self.name.replace("_", " ").title()


class GenericCode(ResultCode):
    """Nondescript result codes to use for generic successes and failures."""

    SUCCESS = 0
    FAILURE = 1


class ErrorCode(ResultCode):
    """Represents a failure of an operation.

    These codes should have values >= 2. Prefer using `ErrorCode.auto` method
    over manual definition.
    """

    def auto() -> int:
        # pylint: disable=no-method-argument
        """Iterates on the last defined value."""
        return enum.auto()

    @staticmethod
    def _generate_next_value_(name: str, _: int, count: int, last_values: list[int]):
        """
        Ensures all codes generated with a value of >= 2/

        See https://docs.python.org/3/library/enum.html#enum.Enum._generate_next_value_ for a
        full list of parameter definitions.
        """
        retval = ResultCode._generate_next_value_(
            name=name, start=2, count=count, last_values=last_values
        )

        assert isinstance(retval, int)
        return retval


@dataclass(frozen=True, init=True)
class Result(Generic[T]):
    """

    Always check is_success and the value for nullishness.

    """

    code: ResultCode
    """The result code associated with the operation."""

    value: Optional[T]
    """The value returned by the operation."""

    @property
    def is_success(self) -> bool:
        """Returns whether the result can be considered a success."""
        return self.code.value is GenericCode.SUCCESS.value

    @property
    def is_failure(self) -> bool:
        """Returns whether the result can be considered a failure."""
        return not self.is_success

    @staticmethod
    def success(value: T) -> "Result[T]":
        """Factory method for generating 'successful' Results.

        Args:
            value: The value to give the result.
        """
        return Result(GenericCode.SUCCESS, value)

    @staticmethod
    def failure(
        code: ResultCode = GenericCode.FAILURE, value: Optional[T] = None
    ) -> "Result[T]":
        """Factory method for generating 'failure' Results.

        Args:
            code: The failure code to give the result. Defaults to GenericCode.FAILURE.
            value: The value to give the result. Defaults to None.
        """
        return Result(code, value)

    def __str__(self) -> str:
        return f"({str(self.code.__class__.__name__)}){str(self.code)}"
