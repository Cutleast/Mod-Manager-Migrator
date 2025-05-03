"""
Copyright (c) Cutleast
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Generator, Optional, override
from unittest.mock import MagicMock

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture
from setup.mock_plyvel import MockPlyvelDB

import resources_rc  # type: ignore # noqa: F401
from core.config.app_config import AppConfig
from core.game.game import Game
from core.instance.instance import Instance
from core.instance.metadata import Metadata
from core.instance.mod import Mod
from core.instance.tool import Tool
from core.migrator.file_blacklist import FileBlacklist
from core.mod_manager.modorganizer.mo2_instance_info import MO2InstanceInfo
from core.mod_manager.modorganizer.modorganizer import ModOrganizer
from core.mod_manager.vortex.profile_info import ProfileInfo
from core.utilities.env_resolver import resolve
from core.utilities.leveldb import LevelDB


class BaseTest:
    """
    Base class for all tests.
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
    def app_config(self, data_folder: Path) -> AppConfig:
        """
        Returns the application config for the tests.

        Returns:
            AppConfig: The application config.
        """

        return AppConfig.load(data_folder / "config")

    @pytest.fixture
    def test_fs(self, data_folder: Path, fs: FakeFilesystem) -> FakeFilesystem:
        """
        Creates a fake filesystem for testing.

        Returns:
            FakeFilesystem: The fake filesystem.
        """

        fs.add_real_directory(data_folder)
        fs.add_real_directory(
            data_folder / "mod_instance",
            read_only=False,
            target_path="C:\\Modding\\Test Instance",
        )
        fs.add_real_directory(
            data_folder / "skyrimse",
            read_only=False,
            target_path=resolve(Path("%APPDATA%")) / "Vortex" / "skyrimse",
        )
        fs.add_real_directory(
            data_folder / "skyrimse_mods",
            read_only=False,
            target_path="E:\\Modding\\Vortex\\skyrimse",
        )

        # Set total disk sizes to 1 GB
        fs.set_disk_usage(total_size=1024**3, path="C:")
        fs.set_disk_usage(total_size=1024**3, path="E:")

        return fs

    @pytest.fixture
    def mo2_instance_info(self) -> MO2InstanceInfo:
        """
        Returns the MO2 instance info of the test mod instance.

        Returns:
            MO2InstanceInfo: The instance info of the test mod instance.
        """

        base_dir_path = Path("C:\\Modding\\Test Instance")

        return MO2InstanceInfo(
            display_name="Test Instance",
            game=Game.get_game_by_id("skyrimse"),
            profile="Default",
            is_global=False,
            base_folder=base_dir_path,
            mods_folder=base_dir_path / "mods",
            profiles_folder=base_dir_path / "profiles",
        )

    @pytest.fixture
    def vortex_profile_info(self) -> ProfileInfo:
        """
        Returns the Vortex profile info of the test mod instance.

        Returns:
            ProfileInfo: The profile info of the test mod instance.
        """

        return ProfileInfo(
            display_name="Test Instance (1a2b3c4d)",
            game=Game.get_game_by_id("skyrimse"),
            id="1a2b3c4d",
        )

    @pytest.fixture
    def instance(
        self,
        mo2_instance_info: MO2InstanceInfo,
        app_config: AppConfig,
        test_fs: FakeFilesystem,
    ) -> Instance:
        """
        Loads the test mod instance.

        Returns:
            Instance: The test mod instance.
        """

        return ModOrganizer().load_instance(
            mo2_instance_info, app_config.modname_limit, FileBlacklist.get_files()
        )

    @pytest.fixture
    def test_instance(self) -> Instance:
        """
        Creates a mocked mod instance with 10 mods.

        TODO: Check if this is still needed

        Returns:
            Instance: The mocked mod instance.
        """

        return Instance(
            display_name="Test Instance",
            game_folder=Path("E:\\SteamLibrary\\Skyrim Special Edition"),
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

    def get_mod_by_name(self, mod_name: str, mod_instance: Instance) -> Mod:
        """
        Gets a mod by its name from the specified mod instance.

        Args:
            mod_name (str): The name of the mod
            mod_instance (Instance): The mod instance

        Raises:
            ValueError: When no mod with the specified name is found

        Returns:
            Mod: The mod
        """

        try:
            mod: Mod = next(
                (mod for mod in mod_instance.mods if mod.display_name == mod_name)
            )
        except StopIteration:
            raise ValueError(f"No mod with name {mod_name} found in mod instance.")

        return mod

    def get_tool_by_name(self, tool_name: str, mod_instance: Instance) -> Tool:
        """
        Gets a tool by its name from the specified mod instance.

        Args:
            tool_name (str): The name of the tool
            mod_instance (Instance): The mod instance

        Raises:
            ValueError: When no tool with the specified name is found

        Returns:
            Tool: The tool
        """

        try:
            tool: Tool = next(
                (tool for tool in mod_instance.tools if tool.display_name == tool_name)
            )
        except StopIteration:
            raise ValueError(f"No tool with name {tool_name} found in mod instance.")

        return tool

    @pytest.fixture
    def ready_vortex_db(
        self, mocker: MockerFixture, ready_state_v2_json: Path
    ) -> Generator[MockPlyvelDB, None, None]:
        """
        Pytest fixture to mock the plyvel.DB classand redirect it to use a sample
        JSON file.

        Yields:
            Generator[MockPlyvelDB]: The mocked plyvel.DB instance
        """

        flat_data: dict[str, str] = LevelDB.flatten_nested_dict(
            json.loads(ready_state_v2_json.read_text())
        )
        mock_instance = MockPlyvelDB(
            {k.encode(): v.encode() for k, v in flat_data.items()}
        )

        magic: MagicMock = mocker.patch("plyvel.DB", return_value=mock_instance)

        yield mock_instance

        mocker.stop(magic)

    @pytest.fixture
    def empty_vortex_db(
        self, mocker: MockerFixture, empty_state_v2_json: Path
    ) -> Generator[MockPlyvelDB, None, None]:
        """
        Pytest fixture to mock the plyvel.DB class and redirect it to use an empty
        database.

        Yields:
            Generator[MockPlyvelDB]: The mocked plyvel.DB instance
        """

        flat_data: dict[str, str] = LevelDB.flatten_nested_dict(
            json.loads(empty_state_v2_json.read_text())
        )
        mock_instance = MockPlyvelDB(
            {k.encode(): v.encode() for k, v in flat_data.items()}
        )

        magic: MagicMock = mocker.patch("plyvel.DB", return_value=mock_instance)

        yield mock_instance

        mocker.stop(magic)

    @pytest.fixture
    def full_vortex_db(
        self, mocker: MockerFixture, full_state_v2_json: Path
    ) -> Generator[MockPlyvelDB, None, None]:
        """
        Pytest fixture to mock the plyvel.DB class and redirect it to use the
        database with the test instance.

        Yields:
            Generator[MockPlyvelDB]: The mocked plyvel.DB instance
        """

        flat_data: dict[str, str] = LevelDB.flatten_nested_dict(
            json.loads(full_state_v2_json.read_text())
        )
        mock_instance = MockPlyvelDB(
            {k.encode(): v.encode() for k, v in flat_data.items()}
        )

        magic: MagicMock = mocker.patch("plyvel.DB", return_value=mock_instance)

        yield mock_instance

        mocker.stop(magic)

    @pytest.fixture
    def ready_state_v2_json(self) -> Generator[Path, None, None]:
        """
        Fixture to return a path to a sample JSON file within a temp folder resembling
        a Vortex database ready for a migration.

        Yields:
            Generator[Path]: Path to sample JSON file
        """

        # TODO: Check if this is still needed
        with tempfile.TemporaryDirectory(prefix="MMM_test_") as tmp_dir:
            src = Path("tests") / "data" / "ready_state.v2.json"
            dst = Path(tmp_dir) / "ready_state.v2.json"
            shutil.copyfile(src, dst)
            yield dst

    @pytest.fixture
    def empty_state_v2_json(self) -> Generator[Path, None, None]:
        """
        Fixture to return a path to a sample JSON file within a temp folder resembling
        an empty Vortex database, right after its installation and first start up.

        Yields:
            Generator[Path]: Path to sample JSON file
        """

        with tempfile.TemporaryDirectory(prefix="MMM_test_") as tmp_dir:
            src = Path("tests") / "data" / "empty_state.v2.json"
            dst = Path(tmp_dir) / "empty_state.v2.json"
            shutil.copyfile(src, dst)
            yield dst

    @pytest.fixture
    def full_state_v2_json(self) -> Generator[Path, None, None]:
        """
        Fixture to return a path to a sample JSON file within a temp folder resembling
        the full Vortex database after migrating the test instance.

        Yields:
            Generator[Path]: Path to sample JSON file
        """

        with tempfile.TemporaryDirectory(prefix="MMM_test_") as tmp_dir:
            src = Path("tests") / "data" / "full_state.v2.json"
            dst = Path(tmp_dir) / "full_state.v2.json"
            shutil.copyfile(src, dst)
            yield dst

    @staticmethod
    def create_blank_mod(mod_name: str, files: Optional[list[Path]] = None) -> Mod:
        """
        Creates a blank mod with the specified name for usage in tests.

        Args:
            mod_name (str): The name of the mod
            files (Optional[list[Path]], optional):
                The files of the mod. Defaults to None.

        Returns:
            Mod: The blank mod
        """

        class MockMod(Mod):
            """
            Mod subclass for mocking the files property.
            """

            @property
            @override
            def files(self) -> list[Path]:
                return files or []

            @property
            @override
            def size(self) -> int:
                return len(self.files)

        return MockMod(
            display_name=mod_name,
            path=Path(mod_name),
            deploy_path=None,
            metadata=Metadata(
                mod_id=None,
                file_id=None,
                version="",
                file_name=None,
                game_id="skyrimspecialedition",
            ),
            installed=True,
            enabled=True,
        )
