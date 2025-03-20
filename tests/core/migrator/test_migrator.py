"""
Copyright (c) Cutleast
"""

import os
import sys

from ..base_test import BaseTest

sys.path.append(os.path.join(os.getcwd(), "src"))

from src.core.migrator.migrator import Migrator


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
