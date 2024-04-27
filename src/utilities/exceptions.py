"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""


class UiException(Exception):
    """
    Subclass of Exception used for translated error messages.

    Usage:
        raise UiException("[<error id>] <raw error message>")
    """


class LevelDBError(Exception):
    """
    General exceptions for level db.
    """


class DBAlreadyInUse(LevelDBError):
    """
    Exception when database is already used
    (when Vortex is running).
    """
