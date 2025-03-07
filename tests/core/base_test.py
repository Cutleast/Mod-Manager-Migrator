"""
Copyright (c) Cutleast
"""

import shutil
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import jstyleson as json
import pytest
from pytest_mock import MockerFixture

from src.core.instance.instance import Instance
from src.core.instance.metadata import Metadata
from src.core.instance.mod import Mod
from src.core.utilities.leveldb import LevelDB
from tests.core._setup.mock_plyvel import MockPlyvelDB


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
    def mock_plyvel(
        self, mocker: MockerFixture, state_v2_json: Path
    ) -> Generator[MockPlyvelDB, None, None]:
        """
        Pytest fixture to mock the plyvel.DB class and redirect it to use a sample JSON file.

        Yields:
            Generator[MockPlyvelDB]: The mocked plyvel.DB instance
        """

        flat_data: dict[str, str] = LevelDB.flatten_nested_dict(
            json.loads(state_v2_json.read_text())
        )
        mock_instance = MockPlyvelDB(flat_data)
        # mock_instance = MockPlyvelDB()

        magic: MagicMock = mocker.patch("plyvel.DB", return_value=mock_instance)

        # Does not work because plyvel.DB is immutable
        # with mocker.patch.context_manager(
        #     plyvel.DB, "__new__", return_value=mock_instance
        # ):
        #     yield mock_instance

        yield mock_instance

        mocker.stop(magic)

    @pytest.fixture
    def state_v2_json(self) -> Generator[Path, None, None]:
        """
        Fixture to return a path to a sample JSON file within a temp folder resembling
        a Vortex database.

        Yields:
            Generator[Path]: Path to sample JSON file
        """

        with tempfile.TemporaryDirectory(prefix="MMM_test_") as tmp_dir:
            src = Path("tests") / "data" / "state.v2.json"
            dst = Path(tmp_dir) / "state.v2.json"
            shutil.copyfile(src, dst)
            yield dst
