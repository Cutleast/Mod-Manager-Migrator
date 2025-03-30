"""
Copyright (c) Cutleast
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture

from core.game.game import Game
from core.instance.instance import Instance
from core.mod_manager.vortex.exceptions import VortexNotFullySetupError
from core.mod_manager.vortex.profile_info import ProfileInfo
from core.mod_manager.vortex.vortex import Vortex
from core.utilities.leveldb import LevelDB
from tests.utils import Utils

from .._setup.mock_path import MockPath
from .._setup.mock_plyvel import MockPlyvelDB
from ..base_test import BaseTest


class TestVortex(BaseTest):
    """
    Tests `core.mod_manager.vortex.Vortex`.
    """

    DATABASE: tuple[str, type[LevelDB]] = ("level_db", LevelDB)
    RAW_DATA: tuple[str, type[dict[bytes, bytes]]] = ("data", dict)

    @patch("pathlib.WindowsPath", new=MockPath)
    def test_create_instance(
        self, ready_vortex_db: MockPlyvelDB, qt_resources: None
    ) -> None:
        """
        Tests `core.mod_manager.vortex.Vortex.create_instance()`
        """

        # given
        vortex = Vortex()
        database: LevelDB = Utils.get_private_field(vortex, *TestVortex.DATABASE)
        database.use_symlink = False
        profile_info = ProfileInfo(
            display_name="Test profile",
            game=Game.get_game_by_id("skyrimse"),
            id="1a2b3c4d",
        )
        prefix: str = f"persistent###profiles###{profile_info.id}###"
        expected_profile_data: dict[str, Any] = {
            "features": {
                "local_game_settings": False,
                "local_saves": False,
            },
            "gameId": "skyrimse",
            "id": profile_info.id,
            "name": profile_info.display_name,
        }

        # when
        vortex.create_instance(profile_info)
        profile_data: dict[str, Any] = database.load(prefix)["persistent"]["profiles"][
            profile_info.id
        ]
        profile_data.pop("lastActivated")  # remove unique timestamp

        # then
        assert profile_data == expected_profile_data

        # when
        raw_data: dict[bytes, bytes] = Utils.get_private_field(
            ready_vortex_db, *TestVortex.RAW_DATA
        )
        profile_prefix: bytes = prefix.encode()

        # then
        assert (
            raw_data[profile_prefix + b"features###local_game_settings"]
            == json.dumps(False).encode()
        )
        assert (
            raw_data[profile_prefix + b"features###local_saves"]
            == json.dumps(False).encode()
        )
        assert raw_data[profile_prefix + b"gameId"] == json.dumps("skyrimse").encode()
        assert raw_data[profile_prefix + b"id"] == json.dumps(profile_info.id).encode()
        assert (
            raw_data[profile_prefix + b"name"]
            == json.dumps(profile_info.display_name).encode()
        )

    def test_vortex_not_installed(
        self, empty_vortex_db: MockPlyvelDB, qt_resources: None
    ) -> None:
        """
        Tests if `core.mod_manager.vortex.Vortex` raises a `VortexNotInstalledError`
        when running a pre-migration check on an empty Vortex database.
        """

        # given
        vortex = Vortex()
        Utils.get_private_field(vortex, *TestVortex.DATABASE).use_symlink = False
        profile_info = ProfileInfo(
            display_name="Test profile",
            game=Game.get_game_by_id("skyrimse"),
            id=ProfileInfo.generate_id(),
        )

        # then
        with pytest.raises(VortexNotFullySetupError):
            vortex.prepare_migration(profile_info)

    logical_file_name_data: list[tuple[str, int, str]] = [
        (
            "(Part 1) SSE Engine Fixes for 1.5.39 - 1.5.97-17230-5-9-1-1664974289.7z",
            17230,
            "(Part 1) SSE Engine Fixes for 1.5.39 - 1.5.97",
        ),
        (
            "(Part 2) Engine Fixes - skse64 Preloader and TBB Lib-17230-2020-3-1611367474.7z",
            17230,
            "(Part 2) Engine Fixes - skse64 Preloader and TBB Lib",
        ),
        (
            "Constructible Object Custom Keyword System NG-81731-1-1-1-1713893656.zip",
            81731,
            "Constructible Object Custom Keyword System NG",
        ),
        (
            "RaceMenu Anniversary Edition v0-4-19-16-19080-0-4-19-16-1706297897.7z",
            19080,
            "RaceMenu Anniversary Edition v0-4-19-16",
        ),
        ("Test Mod Name.7z", 0, "Test Mod Name"),
    ]

    @pytest.mark.parametrize(
        "file_name, mod_id, expected_logical_name", logical_file_name_data
    )
    def test_get_logical_file_name(
        self, file_name: str, mod_id: int, expected_logical_name: str
    ) -> None:
        """
        Tests `core.mod_manager.vortex.Vortex.get_logical_file_name()`
        """

        # when
        logical_file_name: str = Vortex.get_logical_file_name(file_name, mod_id)

        # then
        assert logical_file_name == expected_logical_name

    def test_install_mod(
        self,
        ready_vortex_db: MockPlyvelDB,
        instance: Instance,
        data_folder: Path,
        fs: FakeFilesystem,
        qt_resources: None,
    ) -> None:
        """
        Tests `core.mod_manager.vortex.Vortex.install_mod()`.
        """

        self.test_create_instance(ready_vortex_db, qt_resources)
        fs.add_real_directory(data_folder)

        # given
        vortex = Vortex()
        database: LevelDB = Utils.get_private_field(vortex, *TestVortex.DATABASE)
        database.use_symlink = False
        database.path.mkdir(parents=True)
        profile_info = ProfileInfo(
            display_name="Test profile (1a2b3c4d)",
            game=Game.get_game_by_id("skyrimse"),
            id="1a2b3c4d",
        )
        dst_profile: Instance = vortex.load_instance(profile_info)
        mod = instance.mods[1]

        # when
        vortex.install_mod(
            mod, dst_profile, profile_info, use_hardlinks=True, replace=True
        )

        # then
        dst_profile = vortex.load_instance(profile_info)
        assert dst_profile.mods[-1].metadata == mod.metadata

    def test_format_utc_timestamp(self) -> None:
        """
        Tests `core.mod_manager.vortex.Vortex.format_utc_timestamp()`.
        """

        # given
        timestamp: float = 1743321182.5131004
        expected_result: str = "2025-03-30T07:53:02.513100Z"

        # when
        actual_result: str = Vortex.format_utc_timestamp(timestamp)

        # then
        assert actual_result == expected_result

    def test_format_unix_timestamp(self) -> None:
        """
        Tests `core.mod_manager.vortex.Vortex.format_unix_timestamp()`.
        """

        # given
        timestamp: float = 1743321182.5131004
        expected_result: int = 1743321182513

        # when
        actual_result: int = Vortex.format_unix_timestamp(timestamp)

        # then
        assert actual_result == expected_result

    @pytest.fixture
    def ready_vortex_db(
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
    def empty_vortex_db(
        self, mocker: MockerFixture
    ) -> Generator[MockPlyvelDB, None, None]:
        """
        Pytest fixture to mock the plyvel.DB class and redirect it to use an empty
        database.

        Yields:
            Generator[MockPlyvelDB]: The mocked plyvel.DB instance
        """

        mock_instance = MockPlyvelDB()
        magic: MagicMock = mocker.patch("plyvel.DB", return_value=mock_instance)

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
