"""
Copyright (c) Cutleast
"""

from core.utilities.filesystem import get_documents_folder

from .game import Game


class Skyrim(Game):
    """
    Class for Skyrim ("Oldrim").
    """

    icon_name = ":/icons/Skyrim.ico"
    name = "Skyrim"
    id = "Skyrim"
    nexus_id = "skyrim"
    inidir = get_documents_folder() / "My Games" / name
    inifiles = [
        inidir / "Skyrim.ini",
        inidir / "SkyrimPrefs.ini",
        inidir / "SkyrimCustom.ini",
    ]
    additional_files = [
        "plugins.txt",
        "loadorder.txt",
    ]
    reg_paths = [
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Bethesda Softworks\\Skyrim\\installed path"
    ]
