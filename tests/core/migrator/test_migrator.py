"""
Copyright (c) Cutleast
"""

from core.migrator.migrator import Migrator

from ..base_test import BaseTest


class TestMigrator(BaseTest):
    """
    Tests `core.migrator.migrator.Migrator`.
    """

    def test_file_blacklist(self, qt_resources: None) -> None:
        """
        Tests `core.migrator.migrator.Migrator.FileBlacklist.get_files()`.
        """

        # when
        files: list[str] = Migrator.FileBlacklist.get_files()

        # then
        assert len(files) > 0
        assert ".gitignore" in files
