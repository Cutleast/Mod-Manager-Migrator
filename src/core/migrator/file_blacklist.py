"""
Copyright (c) Cutleast
"""

from typing import Optional

from core.utilities.qt_res_provider import read_resource


class FileBlacklist:
    """
    Class that holds a list of files that should not be migrated.
    """

    _files: Optional[list[str]] = None

    @classmethod
    def get_files(cls) -> list[str]:
        """
        Gets the list of files that should not be migrated. Reads the blacklist
        resource if not already done.

        Returns:
            list[str]: The list of files that should not be migrated.
        """

        if cls._files is None:
            cls._files = read_resource(":/blacklist").splitlines()

        return cls._files
