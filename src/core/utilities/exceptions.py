"""
Copyright (c) Cutleast
"""

import traceback
from abc import abstractmethod
from typing import Any

from PySide6.QtWidgets import QApplication


def format_exception(exception: Exception) -> str:
    """
    Formats an exception to a string.

    Args:
        exception (Exception): The exception to format.

    Returns:
        str: Formatted exception
    """

    return "".join(traceback.format_exception(exception))


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
