"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Any

import pytest
from base_test import BaseTest
from cutleast_core_lib.test.utils import Utils
from setup.mock_plyvel import MockPlyvelDB

from core.utilities.leveldb import LevelDB


class TestLevelDB(BaseTest):
    """
    Tests `core.utilities.leveldb.LevelDB`.
    """

    DATA: tuple[str, type[dict[str, str]]] = "data", dict[str, str]
    """Identifier for accessing the private data field."""

    CHANGES_PENDING: tuple[str, type[bool]] = "changes_pending", bool
    """Identifier for accessing the private changes_pending field."""

    test_load_cases: list[tuple[str, dict[str, Any]]] = [
        (
            "settings###gameMode###discovered###skyrimse###environment###SteamAPPId",
            {
                "settings": {
                    "gameMode": {
                        "discovered": {
                            "skyrimse": {"environment": {"SteamAPPId": "489830"}}
                        }
                    }
                }
            },
        ),
        (
            "persistent###profiles###1a2b3c4d###features###local_game_settings",
            {
                "persistent": {
                    "profiles": {
                        "1a2b3c4d": {"features": {"local_game_settings": False}}
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
        full_vortex_db: MockPlyvelDB,
    ) -> None:
        """
        Tests `core.utilities.leveldb.LevelDB.load()`.
        """

        # given
        leveldb = LevelDB(Path(), use_symlink=False)

        # when/then
        real_output: dict[str, Any] = leveldb.load(prefix=prefix)
        assert real_output == expected_output

    def test_get_key_lazy_loads_missing_key(self, full_vortex_db: MockPlyvelDB) -> None:
        """
        Tests that get_key() loads missing keys on-demand from the database.
        """

        # given
        leveldb = LevelDB(Path(), use_symlink=False)

        # key exists only in DB, not in __data
        key = "settings###gameMode###discovered###skyrimse###environment###SteamAPPId"

        # when
        value = leveldb.get_key(key)

        # then
        assert isinstance(value, str) and value == "489830"

    def test_get_key_returns_in_memory_if_present(
        self, full_vortex_db: MockPlyvelDB
    ) -> None:
        """
        Tests that get_key() returns in-memory data without DB access.
        """

        # given
        leveldb = LevelDB(Path(), use_symlink=False)
        key = "persistent###profiles###custom_key"
        leveldb.set_key(key, "in-memory")

        # when
        result = leveldb.get_key(key)

        # then
        assert result == "in-memory"

    def test_set_key_marks_changes_pending(self, full_vortex_db: MockPlyvelDB) -> None:
        """
        Tests that set_key() updates in-memory data and marks changes pending.
        """

        # given
        leveldb = LevelDB(Path(), use_symlink=False)

        # when
        leveldb.set_key("abc", "123")

        # internal state check
        assert Utils.get_private_field(leveldb, *TestLevelDB.CHANGES_PENDING) is True
        assert Utils.get_private_field(leveldb, *TestLevelDB.DATA)["abc"] == '"123"'

    def test_get_section_loads_missing_keys_without_overwriting(
        self, full_vortex_db: MockPlyvelDB
    ) -> None:
        """
        Tests that get_section() loads missing keys from DB but does not overwrite
        existing in-memory values.
        """

        # given
        leveldb = LevelDB(Path(), use_symlink=False)

        prefix = "settings###"

        # simulate pending in-memory modification
        leveldb.set_key(
            "settings###gameMode###discovered###skyrimse###environment###SteamAPPId",
            "LOCAL_OVERRIDE",
        )

        # when
        section = leveldb.get_section(prefix)

        # then
        # override must remain intact
        assert (
            section["settings"]["gameMode"]["discovered"]["skyrimse"]["environment"][
                "SteamAPPId"
            ]
            == "LOCAL_OVERRIDE"
        )

    def test_save_writes_changes_and_clears_pending(
        self, full_vortex_db: MockPlyvelDB
    ) -> None:
        """
        Tests that save() writes in-memory keys to DB and resets pending state.
        """

        # given
        leveldb = LevelDB(Path(), use_symlink=False)
        key = "k1###sub"
        leveldb.set_key(key, "v1")

        # precondition
        assert Utils.get_private_field(leveldb, *TestLevelDB.CHANGES_PENDING) is True

        # when
        leveldb.save()

        # then
        assert full_vortex_db.get(key.encode()) == b'"v1"'
        assert Utils.get_private_field(leveldb, *TestLevelDB.CHANGES_PENDING) is False

    def test_get_section_parsing(self, full_vortex_db: MockPlyvelDB) -> None:
        """
        Tests that get_section() correctly parses nested data.
        """

        # given
        leveldb = LevelDB(Path(), use_symlink=False)

        # when
        section = leveldb.get_section(
            "settings###gameMode###discovered###skyrimse###environment"
        )

        # then
        assert section == {
            "settings": {
                "gameMode": {
                    "discovered": {
                        "skyrimse": {"environment": {"SteamAPPId": "489830"}}
                    }
                }
            }
        }

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

    def test_flatten_nested_dict_with_prefix(self) -> None:
        """
        Tests `core.utilities.leveldb.LevelDB.flatten_nested_dict()` with a prefix.
        """

        # given
        data: dict[str, Any] = {
            "key1": {"subkey1": {"subsubkey1": {"subsubsubkey1": "subsubsubvalue1"}}},
            "key2": "value2",
        }
        prefix = "prefix###"
        expected: dict[str, str] = {
            "prefix###key1###subkey1###subsubkey1###subsubsubkey1": '"subsubsubvalue1"',
            "prefix###key2": '"value2"',
        }

        # when
        result: dict[str, str] = LevelDB.flatten_nested_dict(data, prefix=prefix)

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
