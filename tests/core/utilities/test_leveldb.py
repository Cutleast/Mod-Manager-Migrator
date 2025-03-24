"""
Copyright (c) Cutleast
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from core.utilities.leveldb import LevelDB

from .._setup.mock_plyvel import MockPlyvelDB
from ..base_test import BaseTest


class TestLevelDB(BaseTest):
    """
    Tests `core.utilities.leveldb.LevelDB`.
    """

    test_load_cases: list[tuple[str, dict[str, Any]]] = [
        (
            "settings###gameMode###discovered###skyrimse###store",
            {
                "settings": {
                    "gameMode": {"discovered": {"skyrimse": {"store": "steam"}}}
                }
            },
        ),
        (
            "persistent###profiles###Kn463e8fe###features###local_game_settings",
            {
                "persistent": {
                    "profiles": {
                        "Kn463e8fe": {"features": {"local_game_settings": False}}
                    }
                }
            },
        ),
    ]

    @pytest.mark.parametrize("prefix, expected_output", test_load_cases)
    def test_load(
        self, prefix: str, expected_output: dict[str, Any], mock_plyvel: MockPlyvelDB
    ) -> None:
        """
        Tests `core.utilities.leveldb.LevelDB.load()`.
        """

        # given
        leveldb = LevelDB(Path(), use_symlink=False)

        # when/then
        real_output: dict[str, Any] = leveldb.load(prefix=prefix)
        assert real_output == expected_output

    def test_dump(self, mock_plyvel: MockPlyvelDB) -> None:
        """
        Tests `core.utilities.leveldb.LevelDB.dump()`.
        """

        # given
        leveldb = LevelDB(Path(), use_symlink=False)

        # when
        data: dict[str, Any] = leveldb.load("settings###")
        data["settings"]["gameMode"]["discovered"]["skyrimse"]["store"] = "gog"

        # then
        leveldb.dump(data)
        assert (
            leveldb.get_key("settings###gameMode###discovered###skyrimse###store")
            == "gog"
        )

    def test_flatten_nested_dict(self) -> None:
        """
        Tests `core.utilities.leveldb.LevelDB.flatten_nested_dict()`.
        """

        # given
        data: dict[str, Any] = {
            "key1": {"subkey1": {"subsubkey1": {"subsubsubkey1": "subsubsubvalue1"}}},
            "key2": "value2",
        }
        expected: dict[str, str] = {
            "key1###subkey1###subsubkey1###subsubsubkey1": '"subsubsubvalue1"',
            "key2": '"value2"',
        }

        # when
        result: dict[str, str] = LevelDB.flatten_nested_dict(data)

        # then
        assert result == expected

    def test_parse_flat_dict(self) -> None:
        """
        Tests `core.utilities.leveldb.LevelDB.parse_flat_dict()`.
        """

        # given
        data: dict[str, str] = {
            "key1###subkey1###subsubkey1###subsubsubkey1": '"subsubsubvalue1"',
            "key2": '"value2"',
        }
        expected: dict[str, Any] = {
            "key1": {"subkey1": {"subsubkey1": {"subsubsubkey1": "subsubsubvalue1"}}},
            "key2": "value2",
        }

        # when
        result: dict[str, Any] = LevelDB.parse_flat_dict(data)

        # then
        assert result == expected

    @pytest.fixture
    def mock_plyvel(
        self, mocker: MockerFixture, state_v2_json: Path
    ) -> Generator[MockPlyvelDB, None, None]:
        """
        Pytest fixture to mock the plyvel.DB classand redirect it to use a sample
        JSON file.

        Yields:
            Generator[MockPlyvelDB]: The mocked plyvel.DB instance
        """

        flat_data: dict[str, str] = LevelDB.flatten_nested_dict(
            json.loads(state_v2_json.read_text())
        )
        mock_instance = MockPlyvelDB(
            {k.encode(): v.encode() for k, v in flat_data.items()}
        )

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
