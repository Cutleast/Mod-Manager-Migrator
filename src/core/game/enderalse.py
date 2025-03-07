"""
Copyright (c) Cutleast
"""

from core.utilities.filesystem import get_documents_folder

from .game import Game


class EnderalSE(Game):
    """
    Class for Enderal Special Edition Game.
    """

    icon_name = ":/icons/Enderalse.ico"
    name = "Enderal Special Edition"
    id = "EnderalSpecialEdition"
    nexus_id = "enderalspecialedition"
    inidir = get_documents_folder() / "My Games" / name
    inifiles = [
        inidir / "Enderal.ini",
        inidir / "EnderalPrefs.ini",
        inidir / "EnderalCustom.ini",
    ]
    reg_paths = [
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\SureAI\\Enderal SE\\installed path",
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\GOG.com\\Games\\1708684988\\path",
    ]
