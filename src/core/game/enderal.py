"""
Copyright (c) Cutleast
"""

from core.utilities.filesystem import get_documents_folder

from .game import Game


class Enderal(Game):
    """
    Class for Enderal.
    """

    icon_name = ":/icons/Enderal.ico"
    name = "Enderal"
    id = "Enderal"
    nexus_id = "enderal"
    inidir = get_documents_folder() / "My Games" / name
    inifiles = [
        inidir / "Enderal.ini",
        inidir / "EnderalPrefs.ini",
        inidir / "EnderalCustom.ini",
    ]
    reg_paths = [
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\SureAI\\Enderal\\installed path",
    ]
