"""
Copyright (c) Cutleast
"""

from PySide6.QtWidgets import QApplication

from ..exceptions import ModManagerError


class InvalidGlobalInstancePathError(ModManagerError):
    """
    Exception when the path for a global instance is outside of the
    `%LOCALAPPDATA%\ModOrganizer` folder.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Invalid global instance path! "
            "The path must not be outside of the %LOCALAPPDATA%\\ModOrganizer folder "
            "when choosing the global instance type!",
        )


class CannotInstallGlobalMo2Error(ModManagerError):
    """
    Exception when a global instance is selected as destination and
    the install MO2 checkbox is checked.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Cannot install MO2 when a global instance is selected as destination!",
        )


class GlobalInstanceDetectedError(ModManagerError):
    """
    Exception when at least one global instance was detected
    and it was tried to create a portable instance.

    Global instances cause issues with portable instances.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Cannot create a portable instance because at least one global instance was "
            "detected!\nGlobal instances cause issues with portable instances.",
        )
