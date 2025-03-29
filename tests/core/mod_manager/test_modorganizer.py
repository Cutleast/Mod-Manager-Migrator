"""
Copyright (c) Cutleast
"""

from pathlib import Path

from core.game.game import Game
from core.instance.metadata import Metadata
from core.mod_manager.modorganizer.modorganizer import ModOrganizer
from tests.utils import Utils

from ..base_test import BaseTest


class TestModOrganizer(BaseTest):
    """
    Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer`.
    """

    @staticmethod
    def parse_meta_ini_stub(meta_ini_path: Path, default_game: Game) -> Metadata:
        """
        Stub for `core.mod_manager.modorganizer.modorganizer.ModOrganizer.__parse_meta_ini()`.
        """

        raise NotImplementedError

    def test_parse_meta_ini(self, data_folder: Path, qt_resources: None) -> None:
        """
        Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer.__parse_meta_ini()`.
        """

        # given
        mo2 = ModOrganizer()
        test_meta_ini_path: Path = (
            data_folder / "mods" / "Metadata Test Mod" / "meta.ini"
        )

        # when
        metadata: Metadata = Utils.get_private_method(
            mo2, "parse_meta_ini", TestModOrganizer.parse_meta_ini_stub
        )(
            meta_ini_path=test_meta_ini_path,
            default_game=Game.get_game_by_id("skyrimse"),
        )

        # then
        assert metadata.mod_id == -1
        assert metadata.file_id is None
        assert metadata.version == ""
        assert metadata.file_name is None
