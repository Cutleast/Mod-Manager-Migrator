"""
Copyright (c) Cutleast
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from core.instance.instance import Instance
from core.instance.metadata import Metadata
from core.instance.mod import Mod


class BaseTest:
    """
    Base class for all core-related tests.
    """

    @pytest.fixture
    def tmp_folder(self) -> Generator[Path, None, None]:
        """
        Creates and returns a temporary folder.

        Returns:
            Path: The temporary folder path.

        Yields:
            Generator[Path]: The temporary folder path.
        """

        with tempfile.TemporaryDirectory(prefix="MMM_test_") as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def data_folder(self) -> Path:
        """
        Returns the path to the test data folder.

        Returns:
            Path: The path to the test data folder.
        """

        return Path("tests") / "data"

    @pytest.fixture
    def instance(self) -> Instance:
        """
        Creates a mocked mod instance with 10 mods.

        Returns:
            Instance: The mocked mod instance.
        """

        return Instance(
            display_name="Test Instance",
            mods=[
                Mod(
                    display_name=f"Test Mod {i}",
                    path=Path(),
                    deploy_path=None,
                    metadata=Metadata(
                        mod_id=i**2,
                        file_id=i**3,
                        version="1.0",
                        file_name=f"test_mod_{i}",
                        game_id="skyrimspecialedition",
                    ),
                    installed=True,
                    enabled=True,
                )
                for i in range(10)
            ],
            tools=[],
            order_matters=False,
        )

    @pytest.fixture
    def qt_resources(self) -> None:
        """
        Provides the compiled Qt resources by importing them.
        """

        import src.resources_rc  # noqa: F401
