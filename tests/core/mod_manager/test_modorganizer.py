"""
Copyright (c) Cutleast
"""

import os
import sys
from pathlib import Path

from ..base_test import BaseTest

sys.path.append(os.path.join(os.getcwd(), "src"))

from src.core.game.skyrimse import SkyrimSE
from src.core.instance.metadata import Metadata
from src.core.mod_manager.modorganizer.modorganizer import ModOrganizer


class TestModOrganizer(BaseTest):
    """
    Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer`.
    """

    def test_parse_meta_ini(self, data_folder: Path) -> None:
        """
        Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer.__parse_meta_ini()`.
        """

        # given
        mo2 = ModOrganizer()
        test_meta_ini_path: Path = (
            data_folder / "mods" / "Metadata Test Mod" / "meta.ini"
        )

        # when
        metadata: Metadata = mo2._ModOrganizer__parse_meta_ini(
            meta_ini_path=test_meta_ini_path, default_game=SkyrimSE()
        )

        # then
        assert metadata.mod_id == -1
        assert metadata.file_id is None
        assert metadata.version == ""
        assert metadata.file_name is None
