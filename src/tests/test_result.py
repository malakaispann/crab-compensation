from pytest import mark

from crabcomp.result import ErrorCode, GenericCode, Result, ResultCode


class TestResultCode:

    def test_str_Returns_title_case_With_underscores_converted_to_spaces(self):
        class TestCode(ResultCode):
            CUSTOM_ERROR_CODE = 42

        assert str(TestCode.CUSTOM_ERROR_CODE) == "Custom Error Code"


class TestErrorCode:

    def test_auto_Generates_values_starting_from_2_When_auto_used(self):
        class TestErrorCode(ErrorCode):
            FIRST_ERROR = ErrorCode.auto()
            SECOND_ERROR = ErrorCode.auto()
            THIRD_ERROR = ErrorCode.auto()

        assert TestErrorCode.FIRST_ERROR.value >= 2
        assert TestErrorCode.SECOND_ERROR.value > TestErrorCode.FIRST_ERROR.value
        assert TestErrorCode.THIRD_ERROR.value > TestErrorCode.SECOND_ERROR.value


class TestResult:

    @mark.parametrize("value", [None, "test_string", 42, {"key": "value"}])
    def test_success_Creates_successful_result(self, value):
        result = Result.success(value)
        assert result.is_success
        assert result.code == GenericCode.SUCCESS
        assert result.value == value

    def test_failure_Creates_failed_result_With_default_code_When_failure_called_Without_args(
        self,
    ):
        result = Result.failure()
        assert result.is_failure
        assert result.code == GenericCode.FAILURE
        assert result.value is None

    def test_failure_Creates_failed_result_With_provided_code_and_value(
        self,
    ):
        class CustomErrorCode(ErrorCode):
            CUSTOM_ERROR = ErrorCode.auto()

        value = "foo"

        result = Result.failure(CustomErrorCode.CUSTOM_ERROR, value)
        assert result.is_failure
        assert result.code == CustomErrorCode.CUSTOM_ERROR
        assert result.value is value

    def test_is_success_Returns_true_When_success_code_used(self):
        assert Result(GenericCode.SUCCESS, None).is_success

    def test_is_failure_Returns_true_When_non_success_code_used(self):
        assert Result(GenericCode.FAILURE, None).is_failure

    def test_str_Returns_formatted_representation(
        self,
    ):
        class CustomErrorCode(ErrorCode):
            NETWORK_ERROR = ErrorCode.auto()

        result = Result.failure(CustomErrorCode.NETWORK_ERROR)
        assert str(result) == "(CustomErrorCode)Network Error"
