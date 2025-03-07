"""
Copyright (c) Cutleast
"""

from core.utilities.filesystem import get_documents_folder

from .enderalse import EnderalSE


class EnderalSEGOG(EnderalSE):
    """
    Class for Enderal Special Edition (GOG).
    """

    icon_name = ":/icons/Enderalse.ico"
    name = "Enderal Special Edition GOG"
    inidir = get_documents_folder() / "My Games" / name
    inifiles = [
        inidir / "Enderal.ini",
        inidir / "EnderalPrefs.ini",
        inidir / "EnderalCustom.ini",
    ]
