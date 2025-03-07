"""
Copyright (c) Cutleast
"""

from core.utilities.filesystem import get_documents_folder

from .game import Game


class Fallout3(Game):
    """
    Class for Fallout 3.
    """

    icon_name = ":/icons/Fallout3.ico"
    name = "Fallout 3"
    id = "Fallout3"
    nexus_id = "fallout3"
    inidir = get_documents_folder() / "My Games" / id
    inifiles = [
        inidir / "Fallout.ini",
        inidir / "FalloutPrefs.ini",
    ]
    reg_paths = [
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Bethesda Softworks\\Fallout3\\installed path",
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\GOG.com\\Games\\1248282609\\path",
    ]
