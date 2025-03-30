"""
Copyright (c) Cutleast
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from core.game.game import Game
from core.instance.instance import Instance
from core.instance.metadata import Metadata
from core.instance.mod import Mod
from core.migrator.file_blacklist import FileBlacklist
from core.mod_manager.modorganizer.mo2_instance_info import MO2InstanceInfo
from core.mod_manager.modorganizer.modorganizer import ModOrganizer


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
    def instance(self, data_folder: Path, qt_resources: None) -> Instance:
        """
        Loads the test mod instance.

        Returns:
            Instance: The test mod instance.
        """

        mo2 = ModOrganizer()
        instance_info = MO2InstanceInfo(
            display_name="Test Instance",
            game=Game.get_game_by_id("skyrimse"),
            profile="Default",
            is_global=False,
            base_folder=data_folder / "mod_instance",
            mods_folder=data_folder / "mod_instance" / "mods",
            profiles_folder=data_folder / "mod_instance" / "profiles",
        )
        return mo2.load_instance(instance_info, FileBlacklist.get_files())

    @pytest.fixture
    def test_instance(self) -> Instance:
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
