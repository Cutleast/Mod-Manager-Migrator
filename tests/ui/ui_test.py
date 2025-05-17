"""
Copyright (c) Cutleast
"""

import os
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from tests.base_test import BaseTest

from ._setup.clipboard import Clipboard

os.environ["QT_QPA_PLATFORM"] = "offscreen"  # render widgets off-screen


class UiTest(BaseTest):
    """
    Base class for all ui-related tests.
    """

    @pytest.fixture
    def ui_test_fs(self, real_cwd: Path, test_fs: FakeFilesystem) -> FakeFilesystem:
        """
        Extends fake filesystem with data folders for qtawesome and other ui-related
        dependencies.

        Returns:
            FakeFilesystem: Extended fake filesystem for tests
        """

        test_fs.add_real_directory(
            real_cwd / ".venv" / "lib" / "site-packages" / "qtawesome" / "fonts"
        )

        return test_fs

    @pytest.fixture
    def clipboard(self, monkeypatch: pytest.MonkeyPatch) -> Clipboard:
        """
        Fixture to mock the clipboard using `_setup.clipboard.Clipboard`.
        Patches `pyperclip.copy` and `pyperclip.paste`.

        Args:
            monkeypatch (pytest.MonkeyPatch): The MonkeyPatch fixture.

        Returns:
            Clipboard: The mocked clipboard.
        """

        clipboard = Clipboard()

        monkeypatch.setattr("PySide6.QtGui.QClipboard.setText", clipboard.copy)
        monkeypatch.setattr("PySide6.QtGui.QClipboard.text", clipboard.paste)

        return clipboard
