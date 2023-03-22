"""
Part of MMM. Contains game classes.
"""

import os
import winreg

from main import MainApp


# Create class for Game instance #####################################
class GameInstance:
    """
    General class for game instances.
    """

    def __init__(self, app: MainApp):
        self.app = app
        self.name = ""
        self.installdir = ""
        self.inidir = ""
        self.inifiles = []
        self.steamid = 0
        self.gogid = 0
    
    def __repr__(self):
        return "GameInstance"
    
    def get_install_dir(self):
        """
        Gets game's install directory and returns it.

        If steamid is given, get the install location from there.

        If this fails, it tries to get the install location from GOG if that id is given.
        """

        installdir = self.installdir

        # Only search for installdir if not already done
        if not installdir:
            # Try to get Skyrim path from Steam if installed
            if self.steamid:
                try:
                    reg_path = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Steam App {self.steamid}"
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as hkey:
                        installdir = os.path.normpath(winreg.QueryValueEx(hkey, "installLocation")[0])
                        if os.path.isdir(installdir):
                            self.installdir = installdir
                            return self.installdir
                except Exception as ex:
                    self.app.log.error(f"Failed to get install path from Steam: {ex}")

            # Try to get Skyrim path from GOG if installed
            elif self.gogid:
                try:
                    reg_path = f"SOFTWARE\\WOW6432Node\\GOG.com\\Games\\{self.gogid}"
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as hkey:
                        installdir = os.path.normpath(winreg.QueryValueEx(hkey, "path")[0])
                        if os.path.isdir(installdir):
                            self.installdir = installdir
                            return self.installdir
                except Exception as ex:
                    self.app.log.error(f"Failed to get install path from Steam: {ex}")

        return self.installdir
    

# Create class for SkyrimSE instance #################################
class SkyrimSEInstance(GameInstance):
    """
    Class for SkyrimSE GameInstance. Inherited from GameInstance class.
    """

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Skyrim Special Edition"
        self.inidir = os.path.join(self.app.doc_path, 'My Games', 'Skyrim Special Edition')
        self.inifiles = ['Skyrim.ini', 'SkyrimPrefs.ini', 'SkyrimCustom.ini']
        self.steamid = 489830
        self.gogid = 1711230643

    def __repr__(self):
        return "SkyrimSEInstance"


# Create class for Skyrim ("Oldrim") instance ########################
class SkyrimInstance(GameInstance):
    """
    Class for Skyrim ("Oldrim") GameInstance. Inherited from GameInstance class.
    """

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Skyrim"
        self.inidir = os.path.join(self.app.doc_path, 'My Games', 'Skyrim')
        self.inifiles = ['Skyrim.ini', 'SkyrimPrefs.ini', 'SkyrimCustom.ini']
        self.steamid = 72850

    def __repr__(self):
        return "SkyrimInstance"


# Create class for Fallout4 instance #################################
class Fallout4Instance(GameInstance):
    """
    Class for Fallout 4 GameInstance. Inherited from GameInstance class.
    """

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Fallout 4"
        self.inidir = os.path.join(self.app.doc_path, 'My Games', 'Fallout 4')
        self.steamid = 377160

    def __repr__(self):
        return "Fallout4Instance"


# Create class for Enderal instance ##################################
class EnderalInstance(GameInstance):
    """
    Class for Enderal GameInstance. Inherited from GameInstance class.
    """

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Enderal"
        self.inidir = os.path.join(self.app.doc_path, 'My Games', 'Enderal')
        self.steamid = 933480

    def __repr__(self):
        return "EnderalInstance"


# Create class for EnderalSE instance ##################################
class EnderalSEInstance(GameInstance):
    """
    Class for EnderalSE GameInstance. Inherited from GameInstance class.
    """

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Enderal Special Edition"
        self.inidir = os.path.join(self.app.doc_path, 'My Games', 'Enderal Special Edition')
        self.steamid = 976620

    def __repr__(self):
        return "EnderalSEInstance"
