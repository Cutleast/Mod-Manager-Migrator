"""
Copyright (c) Cutleast
"""

import os
from pathlib import Path


class MockPath(Path):
    """
    Class for mocking filesystem-related methods like mkdir, rmdir, etc
    of pathlib.Path objects.
    """

    __is_dir: bool
    __is_file: bool

    def __init__(self, *args: os.PathLike) -> None:
        super().__init__(*args)

        self.__is_dir = super().is_dir()
        self.__is_file = super().is_file()

    def mkdir(
        self, mode: int = 511, parents: bool = False, exist_ok: bool = False
    ) -> None:
        self.__is_dir = True

    def is_dir(self) -> bool:
        return self.__is_dir

    def rmdir(self) -> None:
        if not self.is_dir():
            raise FileNotFoundError(self)

        self.__is_dir = False

    def is_file(self) -> bool:
        return self.__is_file

    def unlink(self, missing_ok: bool = False) -> None:
        if not self.is_file() and not missing_ok:
            raise FileNotFoundError(self)

        self.__is_file = False
