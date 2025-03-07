"""
Copyright (c) Cutleast
"""

import os
from pathlib import Path
from unittest.mock import patch

from src.core.utilities.env_resolver import resolve

from .._setup.mock_path import MockPath


class TestMockPath:
    """
    Tests `tests.core._setup.mock_path.MockPath`.
    """

    @patch("pathlib.WindowsPath", new=MockPath)
    def test_mock_path(self) -> None:
        # when
        path = Path("temp")

        # then
        assert isinstance(path, MockPath)

    @patch("pathlib.WindowsPath", new=MockPath)
    def test_mock_path_resolve(self) -> None:
        # when
        path: Path = resolve(Path("%temp%"))

        # then
        assert isinstance(path, MockPath)

    @patch("pathlib.WindowsPath", new=MockPath)
    def test_mkdir(self) -> None:
        # given
        path = Path("temp")

        # when
        assert not os.path.exists(path)
        assert not path.is_dir()

        path.mkdir()

        # then
        assert not os.path.exists(path)
        assert path.is_dir()
