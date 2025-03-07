"""
Copyright (c) Cutleast
"""

from pathlib import Path

from ._base_config import BaseConfig


class AppConfig(BaseConfig):
    """
    Class for managing application settings.
    """

    def __init__(self, config_folder: Path):
        super().__init__(config_folder / "app.json")

    @property
    def log_level(self) -> str:
        return self._settings["log.level"]

    @log_level.setter
    def log_level(self, log_level: str) -> None:
        AppConfig.validate_type(log_level, str)

        log_level = log_level.upper()  # Normalize value
        valid_values: set[str] = {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        AppConfig.validate_value(log_level, valid_values)

        self._settings["log.level"] = log_level

    @property
    def log_num_of_files(self) -> int:
        return self._settings["log.num_of_files"]

    @log_num_of_files.setter
    def log_num_of_files(self, value: int) -> None:
        AppConfig.validate_type(value, int)

        self._settings["log.num_of_files"] = value

    @property
    def log_format(self) -> str:
        return self._settings["log.format"]

    @log_format.setter
    def log_format(self, format: str) -> None:
        AppConfig.validate_type(format, str)

        self._settings["log.format"] = format

    @property
    def log_date_format(self) -> str:
        return self._settings["log.date_format"]

    @log_date_format.setter
    def log_date_format(self, date_format: str) -> None:
        AppConfig.validate_type(date_format, str)

        self._settings["log.date_format"] = date_format

    @property
    def log_file_name(self) -> str:
        return self._settings["log.file_name"]

    @log_file_name.setter
    def log_file_name(self, file_name: str) -> None:
        AppConfig.validate_type(file_name, str)

        if not file_name.endswith(".log"):
            raise ValueError('Log file name must end with ".log"!')

        self._settings["log.file_name"] = file_name

    @property
    def language(self) -> str:
        """
        App language.
        """

        return self._settings["language"]

    @language.setter
    def language(self, language: str) -> None:
        AppConfig.validate_type(language, str)

        self._settings["language"] = language

    @property
    def ui_mode(self) -> str:
        return self._settings["ui.mode"]

    @ui_mode.setter
    def ui_mode(self, value: str) -> None:
        AppConfig.validate_type(value, str)

        value = value.capitalize()  # Normalize value
        valid_values: set[str] = {"Dark", "Light", "System"}

        AppConfig.validate_value(value, valid_values)

        self._settings["ui.mode"] = value

    @property
    def use_hardlinks(self) -> bool:
        return self._settings["use_hardlinks"]

    @use_hardlinks.setter
    def use_hardlinks(self, value: bool) -> None:
        AppConfig.validate_type(value, bool)

        self._settings["use_hardlinks"] = value

    @property
    def replace_when_merge(self) -> bool:
        return self._settings["replace_when_merge"]

    @replace_when_merge.setter
    def replace_when_merge(self, value: bool) -> None:
        AppConfig.validate_type(value, bool)

        self._settings["replace_when_merge"] = value
