"""
Copyright (c) Cutleast
"""

from core.utilities.filesystem import get_documents_folder

from .game import Game


class Oblivion(Game):
    """
    Class for Oblivion.
    """

    icon_name = ":/icons/Oblivion.ico"
    name = "Oblivion"
    id = "Oblivion"
    nexus_id = "oblivion"
    inidir = get_documents_folder() / "My Games" / name
    inifiles = [
        inidir / "Oblivion.ini",
        inidir / "OblivionPrefs.ini",
        inidir / "BlendSettings.ini",
    ]
    reg_paths = [
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Bethesda Softworks\\Oblivion\\installed path"
    ]
