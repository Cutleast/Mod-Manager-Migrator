"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from main import MainApp

from .game import GameInstance


class EnderalInstance(GameInstance):
    """
    Class for Enderal GameInstance.
    Inherited from GameInstance class.
    """

    icon_name = "Enderal.ico"

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Enderal"
        self.id = "Enderal"
        self.inidir = self.app.doc_path / "My Games" / self.name
        self.inifiles = [
            self.inidir / "Enderal.ini",
            self.inidir / "EnderalPrefs.ini",
            self.inidir / "EnderalCustom.ini",
        ]
        self.steamid = 933480

    def __repr__(self):
        return "EnderalInstance"
