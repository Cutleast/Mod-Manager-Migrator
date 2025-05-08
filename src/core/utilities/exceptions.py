"""
Copyright (c) Cutleast
"""

import traceback
from abc import abstractmethod
from typing import Any, override

from PySide6.QtWidgets import QApplication


def format_exception(
    exception: BaseException, only_message_when_localized: bool = True
) -> str:
    """
    Formats an exception to a string.

    Args:
        exception (BaseException): The exception to format.
        only_message_when_localized (bool):
            Whether to only return the message when localized.

    Returns:
        str: Formatted exception
    """

    if isinstance(exception, ExceptionBase) and only_message_when_localized:
        return exception.getLocalizedMessage()

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

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Not enough space ({2}) on the destination disk ({0})!\nRequired space: {1}",
        )


class SameSourceDestinationError(ExceptionBase):
    """
    Exception when the source and destination are the same.
    """

    def __init__(self) -> None:
        super().__init__()

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "Source and destination must not be the same!"
        )
