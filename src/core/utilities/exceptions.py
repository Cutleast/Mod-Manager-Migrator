"""
Copyright (c) Cutleast
"""

from abc import abstractmethod
from typing import Any

from PySide6.QtWidgets import QApplication


class ExceptionBase(Exception):
    """
    Base Exception class for localized exceptions.
    """

    def __init__(self, *values: Any) -> None:
        super().__init__(self.getLocalizedMessage().format(*values))

    @abstractmethod
    def getLocalizedMessage(self) -> str:
        """
        Returns localized message

        Returns:
            str: Localized message
        """


class MigrationError(ExceptionBase):
    """
    General exception for migration errors.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "A migration error occured!")


class NotEnoughSpaceError(ExceptionBase):
    """
    Exception when the destination disk has not enough space.
    """

    def __init__(self, disk: str, required_space: str, available_space: str) -> None:
        super().__init__(disk, required_space, available_space)

    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Not enough space ({2}) on the destination disk ({0})!\nRequired space: {1}",
        )


class GameNotFoundError(ExceptionBase):
    """
    Exception when the installation folder for a game could not be found.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "The installation folder for the selected game could not be found!",
        )
