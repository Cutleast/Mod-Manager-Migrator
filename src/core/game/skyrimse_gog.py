"""
Copyright (c) Cutleast
"""

from core.utilities.filesystem import get_documents_folder

from .skyrimse import SkyrimSE


class SkyrimSEGOG(SkyrimSE):
    """
    Class for Skyrim Special Edition (GOG).
    """

    name = "Skyrim Special Edition GOG"
    inidir = get_documents_folder() / "My Games" / name
    inifiles = [
        inidir / "Skyrim.ini",
        inidir / "SkyrimPrefs.ini",
        inidir / "SkyrimCustom.ini",
    ]
