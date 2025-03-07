"""
Copyright (c) Cutleast
"""

from core.utilities.filesystem import get_documents_folder

from .game import Game


class Fallout4(Game):
    """
    Class for Fallout 4.
    """

    icon_name = ":/icons/Fallout4.ico"
    name = "Fallout 4"
    id = "Fallout4"
    nexus_id = "fallout4"
    inidir = get_documents_folder() / "My Games" / id
    inifiles = [
        inidir / "Fallout4.ini",
        inidir / "Fallout4Prefs.ini",
        inidir / "Fallout4Custom.ini",
    ]
    reg_paths = [
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Bethesda Softworks\\Fallout4\\installed path",
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\GOG.com\\Games\\1998527297\\path",
    ]
