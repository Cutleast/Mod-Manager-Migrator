"""
Copyright (c) Cutleast
"""

from PySide6.QtWidgets import QApplication

from ..exceptions import ModManagerError, PreMigrationCheckFailedError


class VortexIsRunningError(ModManagerError):
    """
    Exception that occurs when Vortex is running and locking its database.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Vortex is running and blocking its database. Close Vortex and try again!",
        )


class VortexIsDeployedError(ModManagerError):
    """
    Exception that occurs when user starts migration while Vortex is still deployed
    to the game folder.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Migration cannot continue while Vortex is deployed!\n"
            "Open Vortex and purge the game directory.\n"
            "Then click 'Continue' to complete the migration process.",
        )


class VortexNotFullySetupError(PreMigrationCheckFailedError):
    """
    Exception that occurs when Vortex is not installed or ready for a migration.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Vortex is not installed or fully setup.\nFollow these steps and try again:\n"
            "1. Install Vortex\n2. Start Vortex and enable the mod management for the "
            "game.\n3. Enable profile management in Vortex' settings.",
        )
