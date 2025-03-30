"""
Copyright (c) Cutleast
"""

from core.migrator.file_blacklist import FileBlacklist

from ..base_test import BaseTest


class TestFileBlacklist(BaseTest):
    """
    Tests `core.migrator.file_blacklist.FileBlacklist`.
    """

    def test_file_blacklist(self, qt_resources: None) -> None:
        """
        Tests `core.migrator.file_blacklist.FileBlacklist.get_files()`.
        """

        # when
        files: list[str] = FileBlacklist.get_files()

        # then
        assert len(files) > 0
        assert ".gitignore" in files
