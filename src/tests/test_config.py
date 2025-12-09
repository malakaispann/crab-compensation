import logging
import tempfile
from pathlib import Path

from pytest import mark, raises
from pydantic import ValidationError

from crabcomp.config import AppConfig, AppConfigErrorCodes

MINIMUM_VALID_CONFIG = {
    "DATA_URI": "https://foo.com/bar.tar.gz",
    "OUTPUT_URI": "https://foo.com/output.json",
}


class TestLogLevel:

    CONFIG_ID = "LOG_LEVEL"

    @mark.parametrize(
        "level, representation",
        [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ],
    )
    def test_Returns_expected_representation_When_valid_value_provided(
        self, level: str, representation: int
    ):
        assert (
            AppConfig.model_validate(
                {**{self.CONFIG_ID: level}, **MINIMUM_VALID_CONFIG}
            ).log_level
            == representation
        )

    def test_Returns_info_representation_When_level_not_provided(self):
        assert (
            AppConfig.model_validate({**MINIMUM_VALID_CONFIG, **{}}).log_level
            == logging.INFO
        )

    def test_Raises_validation_error_When_notset_level_provided(self):
        with raises(ValidationError) as err:
            AppConfig.model_validate(
                {**MINIMUM_VALID_CONFIG, **{self.CONFIG_ID: "NOTSET"}}
            )
        assert "invalid_log_level" in str(err.value)

    def test_Raises_validation_error_When_invalid_level_provided(self):
        with raises(ValidationError) as err:
            AppConfig.model_validate(
                {**MINIMUM_VALID_CONFIG, **{self.CONFIG_ID: "foo"}}
            )
        assert "invalid_log_level" in str(err.value)


class TestDataUri:

    CONFIG_ID = "DATA_URI"

    def test_Returns_unmodified_value_When_provided_url(self):
        url = "s3://foo/bar/baz.tar.gz"
        assert (
            str(
                AppConfig.model_validate(
                    {**MINIMUM_VALID_CONFIG, **{self.CONFIG_ID: url}}
                ).data_uri
            )
            == url
        )

    def test_Returns_unmodified_path_When_provided_local_path_that_exists_And_is_regular_file(
        self,
    ):
        with tempfile.NamedTemporaryFile() as temp_file:
            path = Path(temp_file.name)
            config = AppConfig.model_validate(
                {**MINIMUM_VALID_CONFIG, **{self.CONFIG_ID: str(path)}}
            )
            assert config.data_uri == path

    def test_Raises_validation_error_When_provided_local_path_that_does_not_exist(
        self,
    ):
        non_existent_path = "/tmp/this_file_definitely_does_not_exist_1234567890.tar.gz"
        with raises(ValidationError) as err:
            AppConfig.model_validate(
                {**MINIMUM_VALID_CONFIG, **{self.CONFIG_ID: non_existent_path}}
            )
        assert "invalid_data_path" in str(err.value)

    def test_Raises_validation_error_When_provided_local_path_that_exists_And_is_not_regular_file(
        self,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            with raises(ValidationError) as err:
                AppConfig.model_validate(
                    {**MINIMUM_VALID_CONFIG, **{self.CONFIG_ID: temp_dir}}
                )
            assert "invalid_data_path" in str(err.value)


class TestOutputUri:

    CONFIG_ID = "OUTPUT_URI"

    def test_Returns_unmodified_value_When_provided_url(self):
        url = "s3://foo/bar/output.json"
        assert (
            str(
                AppConfig.model_validate(
                    {**MINIMUM_VALID_CONFIG, **{self.CONFIG_ID: url}}
                ).output_uri
            )
            == url
        )

    def test_Returns_path_When_provided_local_path(self):
        path = "/tmp/output.json"
        config = AppConfig.model_validate(
            {**MINIMUM_VALID_CONFIG, **{self.CONFIG_ID: path}}
        )
        assert config.output_uri == Path(path)


class TestExtract:

    def test_Returns_success_result_With_config_When_valid_environment_provided(self):
        result = AppConfig.extract(
            {
                "DATA_URI": "https://example.com/data.tar.gz",
                "OUTPUT_URI": "https://example.com/output.json",
                "LOG_LEVEL": "INFO",
            }
        )

        assert result.is_success
        assert result.value is not None
        assert str(result.value.data_uri) == "https://example.com/data.tar.gz"
        assert str(result.value.output_uri) == "https://example.com/output.json"
        assert result.value.log_level == logging.INFO

    def test_Returns_failure_result_When_invalid_environment_provided(self):
        result = AppConfig.extract({"LOG_LEVEL": "INVALID"})

        assert result.is_failure
        assert result.code == AppConfigErrorCodes.INVALID_CONFIGURATION
        assert result.value is None
