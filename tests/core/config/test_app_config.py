"""
Copyright (c) Cutleast
"""

import json
from pathlib import Path
from typing import Any

import pytest
from base_test import BaseTest
from pydantic_core import ValidationError
from pyfakefs.fake_filesystem import FakeFilesystem

from app import Language
from core.config.app_config import AppConfig
from core.utilities.logger import Logger


class TestAppConfig(BaseTest):
    """
    Tests `core.config.app_config.AppConfig`.
    """

    def test_load(self, test_fs: FakeFilesystem) -> None:
        """
        Tests `AppConfig.load()` with an empty user config.
        """

        # given
        user_config_path = Path("test_config")

        # when
        app_config: AppConfig = AppConfig.load(user_config_path)

        # then
        assert app_config.log_level == Logger.Level.DEBUG
        assert app_config.log_num_of_files == 5

    def test_load_user_config(self, test_fs: FakeFilesystem) -> None:
        """
        Tests `AppConfig.load()` with a user config file.
        """

        # given
        user_config_path = Path("test_config")
        user_config_path.mkdir(parents=True, exist_ok=True)
        user_config_file_path = user_config_path / AppConfig.get_config_name()
        user_config_data: dict[str, Any] = {
            "log.level": "CRITICAL",
            "language": "de_DE",
            "log.num_of_files": "10",
        }
        user_config_file_path.write_text(json.dumps(user_config_data), encoding="utf8")

        # when
        app_config: AppConfig = AppConfig.load(user_config_path)

        # then
        assert app_config.log_level == Logger.Level.CRITICAL
        assert app_config.language == Language.German
        assert app_config.log_num_of_files == 10

        # when
        user_config_data = {"log.num_of_files": -2}
        user_config_file_path.write_text(json.dumps(user_config_data), encoding="utf8")
        app_config = AppConfig.load(user_config_path)

        # then
        assert app_config.log_num_of_files == 5

    def test_save_user_config(self, test_fs: FakeFilesystem) -> None:
        """
        Tests `AppConfig.save()`.
        """

        # given
        user_config_path = Path("test_config")
        user_config_path.mkdir(parents=True, exist_ok=True)
        app_config: AppConfig = AppConfig.load(user_config_path)

        # when
        app_config.log_level = Logger.Level.CRITICAL
        app_config.language = Language.German
        app_config.save()

        # then
        app_config: AppConfig = AppConfig.load(user_config_path)
        assert app_config.log_level == Logger.Level.CRITICAL
        assert app_config.language == Language.German

        # when
        app_config.log_level = app_config.__pydantic_fields__["log_level"].default
        app_config.language = app_config.__pydantic_fields__["language"].default
        app_config.save()

        # then
        assert not (user_config_path / AppConfig.get_config_name()).exists()

    def test_log_num_validation(self) -> None:
        """
        Tests `AppConfig.log_num_of_files` validation.
        """

        # given
        app_config: AppConfig = AppConfig.load(Path("test_config"))

        # when/then
        app_config.log_num_of_files = -1
        with pytest.raises(ValidationError):
            app_config.log_num_of_files = -2

        app_config.log_num_of_files = 1
