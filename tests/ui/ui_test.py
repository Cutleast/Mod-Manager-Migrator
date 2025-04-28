"""
Copyright (c) Cutleast
"""

import pytest

from tests.base_test import BaseTest

from ._setup.clipboard import Clipboard


class UiTest(BaseTest):
    """
    Base class for all ui-related tests.
    """

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
