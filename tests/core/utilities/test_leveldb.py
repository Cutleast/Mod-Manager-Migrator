"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Any

import pytest

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
        self,
        prefix: str,
        expected_output: dict[str, Any],
        ready_vortex_db: MockPlyvelDB,
    ) -> None:
        """
        Tests `core.utilities.leveldb.LevelDB.load()`.
        """

        # given
        leveldb = LevelDB(Path(), use_symlink=False)

        # when/then
        real_output: dict[str, Any] = leveldb.load(prefix=prefix)
        assert real_output == expected_output

    def test_dump(self, ready_vortex_db: MockPlyvelDB) -> None:
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
