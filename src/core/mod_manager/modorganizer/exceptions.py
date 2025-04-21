"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtWidgets import QApplication

from ..exceptions import PreMigrationCheckFailedError


class InvalidGlobalInstancePathError(PreMigrationCheckFailedError):
    """
    Exception when the path for a global instance is outside of the
    `%LOCALAPPDATA%\\ModOrganizer` folder.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Invalid global instance path! "
            "The path must not be outside of the %LOCALAPPDATA%\\ModOrganizer folder "
            "when choosing the global instance type!",
        )


class CannotInstallGlobalMo2Error(PreMigrationCheckFailedError):
    """
    Exception when a global instance is selected as destination and
    the install MO2 checkbox is checked.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Cannot install MO2 when a global instance is selected as destination!",
        )
