"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from main import MainApp

from .skyrimse import SkyrimSEInstance


class SkyrimSEGOGInstance(SkyrimSEInstance):
    """
    Class for SkyrimSE GOG GameInstance.
    Inherited from SkyrimSEInstance class.
    """

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Skyrim Special Edition GOG"
        self.inidir = self.app.doc_path / "My Games" / self.name
        self.inifiles = [
            self.inidir / "Skyrim.ini",
            self.inidir / "SkyrimPrefs.ini",
            self.inidir / "SkyrimCustom.ini",
        ]

    def __repr__(self):
        return "SkyrimSEGOGInstance"
