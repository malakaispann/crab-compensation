import logging

from pytest import mark, raises
from pydantic import ValidationError

from crabcomp.config import AppConfig


MINIMUM_VALID_CONFIG = {"DATA_URI": "https://foo.com/bar.tar.gz"}


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
                {self.CONFIG_ID: level} | MINIMUM_VALID_CONFIG
            ).level
            == representation
        )

    def test_Returns_info_representation_When_level_not_provided(self):
        assert AppConfig.model_validate(MINIMUM_VALID_CONFIG | {}).level == logging.INFO

    def test_Raises_validation_error_When_notset_level_provided(self):
        with raises(ValidationError):
            AppConfig.model_validate(MINIMUM_VALID_CONFIG | {self.CONFIG_ID: "NOTSET"})

    def test_Raises_validation_error_When_invalid_level_provided(self):
        with raises(ValidationError):
            AppConfig.model_validate(MINIMUM_VALID_CONFIG | {self.CONFIG_ID: "foo"})


class TestDataStoreConfig:

    CONFIG_ID = "DATA_URI"

    def test_Returns_unmodified_value_When_provided_url(self):
        url = "s3://foo/bar/baz.tar.gz"
        assert (
            str(
                AppConfig.model_validate(
                    MINIMUM_VALID_CONFIG | {self.CONFIG_ID: url}
                ).data_uri
            )
            == url
        )

    @mark.skip("Implement mock for exist and file check")
    def test_Returns_unmodified_path_When_provided_local_path_that_exists_And_is_regular_file(
        self,
    ): ...

    @mark.skip("Implement mock for exist and file check")
    def test_Raises_validation_error_When_provided_local_path_that_does_not_exist(
        self,
    ): ...

    @mark.skip("Implement mock for exist and file check")
    def test_Raises_validation_error_When_provided_local_path_that_exists_And_is_not_regular_file(
        self,
    ): ...
