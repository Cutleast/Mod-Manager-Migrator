"""
Copyright (c) Cutleast
"""

import zipfile
from typing import override

from .archive import Archive


class ZIPARchive(Archive):
    """
    Class for ZIP Archives.
    """

    __files: list[str] | None = None

    @property
    @override
    def files(self) -> list[str]:
        if self.__files is None:
            self.__files = [
                file.filename
                for file in zipfile.ZipFile(self.path).filelist
                if not file.is_dir()
            ]

        return self.__files
