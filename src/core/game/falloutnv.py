"""
Copyright (c) Cutleast
"""

from core.utilities.filesystem import get_documents_folder

from .game import Game


class FalloutNV(Game):
    """
    Class for Fallout: New Vegas.
    """

    icon_name = ":/icons/FalloutNV.ico"
    name = "Fallout New Vegas"
    id = "FalloutNV"
    nexus_id = "newvegas"
    inidir = get_documents_folder() / "My Games" / id
    inifiles = [
        inidir / "Fallout.ini",
        inidir / "FalloutPrefs.ini",
    ]
    reg_paths = [
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Bethesda Softworks\\falloutnv\\installed path",
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\GOG.com\\Games\\1998527297\\path",
    ]
