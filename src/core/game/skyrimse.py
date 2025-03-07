"""
Copyright (c) Cutleast
"""

from core.game.skyrim import Skyrim
from core.utilities.filesystem import get_documents_folder


class SkyrimSE(Skyrim):
    """
    Class for Skyrim Special Edition.
    """

    icon_name = ":/icons/Skyrimse.ico"
    name = "Skyrim Special Edition"
    id = "SkyrimSE"
    nexus_id = "skyrimspecialedition"
    inidir = get_documents_folder() / "My Games" / name
    inifiles = [
        inidir / "Skyrim.ini",
        inidir / "SkyrimPrefs.ini",
        inidir / "SkyrimCustom.ini",
    ]
    reg_paths = [
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Bethesda Softworks\\Skyrim Special Edition\\installed path",
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\GOG.com\\Games\\1711230643\\path",
    ]
