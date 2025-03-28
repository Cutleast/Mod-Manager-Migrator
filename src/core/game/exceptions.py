"""
Copyright (c) Cutleast
"""

from PySide6.QtWidgets import QApplication

from core.utilities.exceptions import ExceptionBase


class GameNotFoundError(ExceptionBase):
    """
    Exception when the installation folder for a game could not be found.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "The installation folder for the selected game could not be found!",
        )
