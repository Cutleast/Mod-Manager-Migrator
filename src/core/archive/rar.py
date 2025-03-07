"""
Copyright (c) Cutleast
"""

import rarfile

from .archive import Archive


class RARArchive(Archive):
    """
    Class for RAR Archives.
    """

    __files: list[str] | None = None

    @property
    def files(self) -> list[str]:
        if self.__files is None:
            self.__files = [
                file.filename
                for file in rarfile.RarFile(self.path).infolist()
                if file.is_file()
            ]

        return self.__files
