"""
Copyright (c) Cutleast
"""

import logging
import os
from pathlib import Path
from typing import Any, Iterable

import jstyleson as json

from core.utilities.qt_res_provider import read_resource


class BaseConfig:
    """
    Base class for app configurations.
    """

    log: logging.Logger = logging.getLogger("BaseConfig")

    _config_path: Path
    _default_settings: dict[str, Any]
    _settings: dict[str, Any]

    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path

        # Load default config values from resources
        config_name: str = f":/default_configs/{config_path.name}"
        self._default_settings = json.loads(read_resource(config_name))

        self.load()

    def load(self) -> None:
        """
        Loads configuration from JSON File, if existing.
        """

        if self._config_path.is_file():
            with self._config_path.open("r", encoding="utf8") as file:
                self._settings = self._default_settings | json.load(file)

            for key in self._settings:
                if key not in self._default_settings:
                    self.log.warning(
                        f"Unknown setting detected in {self._config_path.name}: {key!r}"
                    )
        else:
            self._settings = self._default_settings.copy()

    def save(self) -> None:
        """
        Saves non-default configuration values to JSON File, creating it if not existing.
        """

        changed_values: dict[str, Any] = {
            key: item
            for key, item in self._settings.items()
            if item != self._default_settings.get(key)
        }

        # Create config folder if it doesn't exist
        os.makedirs(self._config_path.parent, exist_ok=True)

        with self._config_path.open("w", encoding="utf8") as file:
            json.dump(changed_values, file, indent=4, ensure_ascii=False)

    @staticmethod
    def validate_value(value: Any, valid_values: Iterable[Any]) -> None:
        """
        Validates a value by checking it against an iterable of valid values.

        Args:
            value (Any): Value to validate.
            valid_values (Iterable[Any]): Iterable containing valid values.

        Raises:
            ValueError: When the value is not a valid value.
        """

        if value not in list(valid_values):
            raise ValueError(f"{value!r} is not a valid value!")

    @staticmethod
    def validate_type(value: Any, type: type) -> None:
        """
        Validates if value is of a certain type.

        Args:
            value (Any): Value to validate.
            type (type): Type the value should have.

        Raises:
            TypeError: When the value is not of the specified type.
        """

        if not isinstance(value, type):
            raise TypeError(f"Value must be of type {type}!")

    def print_settings_to_log(self) -> None:
        """
        Prints current settings to log.
        """

        self.log.info("Current Configuration:")
        for key, item in self._settings.items():
            self.log.info(f"{key:>25} = {item!r}")
