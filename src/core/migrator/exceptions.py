"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.utilities.exceptions import LocalizedException
from PySide6.QtWidgets import QApplication


class NotEnoughSpaceError(LocalizedException):
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


class SameSourceDestinationError(LocalizedException):
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


class SameModsLocationDiffManagerError(LocalizedException):
    """
    Exception when the source and destination have the same mods location but different
    mod managers.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Source and destination have the same mods location but different mod "
            "managers!\nChoose another location for the mods folder and try again.",
        )
