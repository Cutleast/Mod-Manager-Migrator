"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import datetime
import os
import random
import shutil
import string
import time
from pathlib import Path

import utilities as utils
from main import MainApp
from widgets import LoadingDialog

from .instance import ModInstance


class VortexInstance(ModInstance):
    """
    Class for Vortex ModInstance. Inherited from ModInstance class.
    """

    icon_name = "Vortex_Label.svg"

    def __init__(self, app: MainApp):
        super().__init__(app)

        # Initialize Vortex specific attributes
        try:
            self.db = utils.VortexDatabase(app)
            self.database = self.db.load_db()
        except utils.DBAlreadyInUse:
            raise utils.UiException(
                "[vortex_running] Failed to access Vortex database: \
Vortex is running!"
            )
        self.profiles: dict[str, str] = {}

        # Files and overwrites
        self.overwrites: dict[utils.Mod, list[utils.Mod]] = (
            {}
        )  # mod: [overwriting mod, overwriting mod, etc...]

        # Current profile
        self.profname: str = None
        self.profid: str = None

        # Get settings from database
        settings = self.database["settings"]

        game = self.app.game.lower()

        # Get paths from settings
        apppath = Path(os.getenv("APPDATA")) / "Vortex"
        installpaths: dict[str, str] = settings["mods"].get("installPath", {})
        modspath: str = installpaths.get(game, str(apppath / game / "mods"))
        modspath = Path(modspath.replace("{game}", self.app.game.lower()))
        dlpath: str = settings["downloads"]["path"]
        dlpath = Path(dlpath.replace("{USERDATA}", str(apppath)))

        self.mods_path = modspath
        self.paths["download_dir"] = dlpath

    def __repr__(self):
        return "VortexInstance"

    def setup_instance(self):
        game = self.app.game.lower()
        profname = self.instance_data["name"]

        self.log.info(f"Setting up Vortex profile with name '{profname}'...")

        # Generate unique profile id
        self.load_instances()
        profids = list(self.profiles.values())
        while (
            profid := "".join(
                [random.choice(string.ascii_letters + string.digits) for n in range(9)]
            )
        ) in profids:
            pass
        self.profid = profid
        self.profiles[profname] = profid

        # Configure profile data
        ini_files = [
            file.name.lower()
            for file in self.app.src_modinstance.additional_files
            if file.suffix.lower() == ".ini"
        ]
        local_game_settings = str(bool(ini_files)).lower()
        profile = {
            "features": {
                "local_game_settings": local_game_settings,
                "local_saves": "false",
            },
            "gameId": game,
            "modState": {},
            "id": profid,
            "lastActivated": time.time(),
            "name": profname,
        }

        # Add profile to database
        self.database["persistent"]["profiles"][profid] = profile

        # Create profile folder
        apppath = Path(os.getenv("APPDATA")) / "Vortex"
        profpath = apppath / game / "profiles" / profid
        os.mkdir(profpath)

        self.log.info(f"Created Vortex profile '{profname}' with id '{profid}'.")

    def load_instances(self):
        if not self.profiles:
            self.log.debug("Loading profiles from database...")

            persistent: dict[str, dict] = self.database["persistent"]
            profiles: dict[str, dict] = persistent["profiles"]
            for profid, profdata in profiles.items():
                # Check if profile is from selected game
                if (
                    (profdata["gameId"] == self.app.game.lower())
                    # And if it has mods installed
                    and ("modState" in profdata.keys())
                ):
                    profname = profdata["name"]
                    self.profiles[profname] = profid

            self.log.debug(f"Loaded {len(self.profiles)} profile(s) from database.")

        return list(self.profiles.keys())

    def load_instance(self, profile_name: str, ldialog: LoadingDialog = None):
        self.log.info(f"Loading profile '{profile_name}'...")

        self.mods = []
        self._loadorder = []

        # Update progress bar
        if ldialog:
            ldialog.updateProgress(text1=self.app.lang["loading_instance"])

        # Raise exception if profile is not found
        if profile_name not in self.profiles:
            raise ValueError(f"Profile '{profile_name}' not found in database!")

        # Load profile
        game = self.app.game.lower()
        profid = self.profiles[profile_name]
        profile = self.database["persistent"]["profiles"][profid]
        apppath = Path(os.getenv("APPDATA")) / "Vortex"

        # Load mods from profile and their data from database
        profmods: dict = profile["modState"]
        persistent: dict = self.database["persistent"]
        modsdata: dict = persistent["mods"][game]
        for modindex, (modname, modstate) in enumerate(profmods.items()):
            if modname not in modsdata:
                continue

            # Update progress bar
            if ldialog:
                ldialog.updateProgress(
                    text1=f"{self.app.lang['loading_instance']} ({modindex}/{len(profmods)})",
                    value1=modindex,
                    max1=len(profmods),
                )

            moddata = modsdata[modname]
            attributes: dict[str, str] = moddata["attributes"]
            filename = modname
            if not (name := attributes.get("customFileName")):
                name = attributes.get("logicalFileName", modname)
            modname = name

            # Update progress bar
            if ldialog:
                ldialog.updateProgress(show2=True, text2=modname)

            modpath = self.mods_path / filename
            modid = attributes.get("modId", None)
            fileid = attributes.get("fileId", None)
            version = attributes.get("version", None)
            enabled = modstate["enabled"]
            if "modSize" in attributes:
                modsize = attributes["modSize"]
            else:
                modsize = utils.get_folder_size(modpath)
            modfiles = utils.create_folder_list(modpath, lower=False)

            mod = utils.Mod(
                name=modname,
                path=modpath,
                metadata={
                    "name": modname,
                    "modid": modid,
                    "fileid": fileid,
                    "version": version,
                    "filename": filename,
                },
                files=modfiles,
                size=modsize,
                enabled=enabled,
                installed=False,
            )
            self.mods.append(mod)

            # Add modfiles to modfiles
            for file in modfiles:
                if file in self.modfiles:
                    self.modfiles[file].append(mod)
                else:
                    self.modfiles[file] = [mod]

        # Get additional files
        profpath = apppath / game / "profiles" / profid
        self.additional_files = [
            profpath / file for file in profpath.iterdir() if file.is_file()
        ]
        userlist_path = apppath / game / "userlist.yaml"
        self.additional_files.append(userlist_path)

        self.name = profile_name

        self.log.info(f"Loaded profile '{profile_name}' with id '{profid}'.")

    def copy_mods(self, ldialog: LoadingDialog = None):
        self.log.info("Migrating mods to instance...")

        game = self.app.game.lower()
        if "mods" in self.database["persistent"].keys():
            if game in self.database["persistent"]["mods"].keys():
                installed_mods: dict = self.database["persistent"]["mods"][game]
            else:
                installed_mods: dict = {}
                self.database["persistent"]["mods"][game] = installed_mods
        else:
            installed_mods: dict = {}
            self.database["persistent"] = {"mods": {game: installed_mods}}

        # Check installed mods
        for mod in self.mods:
            mod.installed = mod.metadata["filename"] in installed_mods

        maximum = len(self.mods)
        for modindex, mod in enumerate(self.mods):
            self.log.debug(f"Migrating mod '{mod.name}' ({modindex}/{maximum})...")

            # Skip mod if it is not selected in source box
            if not mod.selected:
                self.log.debug("Skipped mod: Mod is not selected.")
                continue

            # Update progress bars
            if ldialog:
                ldialog.updateProgress(
                    # Update first progress bar
                    text1=f"{self.app.lang['migrating_instance']} ({modindex}/{maximum})",
                    value1=modindex,
                    max1=maximum,
                    # Display and update second progress bar
                    show2=True,
                    text2=mod.metadata["name"],
                    value2=0,
                    max2=0,
                )

            # Merge rules if mod is already installed
            if mod.installed:
                moddata = installed_mods[mod.metadata["filename"]]
                rules: list = moddata.get("rules", [])
                # Check for rules
                for overwriting_mod in mod.overwriting_mods:
                    overwriting_mod_filename = overwriting_mod.metadata["filename"]

                    # Skip mod if both mods already exist in database
                    # since rule is very likely to exist, too
                    # if overwriting_mod_filename in installed_mods:
                    if overwriting_mod.installed:
                        continue

                    # Merge rules
                    rule = {
                        "reference": {
                            "id": overwriting_mod_filename,
                            "idHint": overwriting_mod_filename,
                            "versionMatch": "*",
                        },
                        "type": "before",
                    }
                    rules.append(rule)

                installed_mods[mod.metadata["filename"]]["rules"] = rules

                # Add file conflicts
                if mod.overwriting_files:
                    overrides: list[str] = installed_mods[mod.metadata["filename"]].get(
                        "fileOverrides", []
                    )
                    overrides.extend(
                        [
                            str(file)
                            for file in mod.overwriting_files
                            if str(file) not in overrides
                        ]
                    )

                    installed_mods[mod.metadata["filename"]][
                        "fileOverrides"
                    ] = overrides

            # Add mod to database otherwise
            else:
                source = "nexus" if mod.metadata["modid"] else "other"
                moddata = {
                    "attributes": {
                        "customFileName": mod.metadata["name"],
                        "downloadGame": game,
                        "installTime": datetime.datetime.utcfromtimestamp(
                            time.time()
                        ).isoformat()
                        + "Z",
                        "fileId": mod.metadata["fileid"],
                        "modId": mod.metadata["modid"],
                        "logicalFileName": mod.metadata["filename"],
                        "version": mod.metadata["version"],
                        "source": source,
                    },
                    "id": mod.metadata["filename"],
                    "installationPath": mod.metadata["filename"],
                    "state": "installed",
                    "type": None,
                }

                # Add rules
                rules = []
                for overwriting_mod in mod.overwriting_mods:
                    overwriting_mod_filename = overwriting_mod.metadata["filename"]

                    rule = {
                        "reference": {
                            "id": overwriting_mod_filename,
                            "idHint": overwriting_mod_filename,
                            "versionMatch": "*",
                        },
                        "type": "before",
                    }
                    if rule not in rules:
                        rules.append(rule)

                moddata["rules"] = rules

                # Add file conflicts
                if mod.overwriting_files:
                    overrides = [str(file) for file in mod.overwriting_files]

                    moddata["fileOverrides"] = overrides

                installed_mods[mod.metadata["filename"]] = moddata

            # Add mod to profile
            profiles = self.database["persistent"]["profiles"]
            profile_mods = profiles[self.profid]["modState"]
            modstate = {
                "enabled": True,
                "enabledTime": int(time.time()),
            }
            profile_mods[mod.metadata["filename"]] = modstate

            # Skip mod if it is already installed
            modpath: Path = self.mods_path / mod.metadata["filename"]
            modpath = utils.clean_filepath(modpath)
            if modpath.is_dir():
                if list(modpath.iterdir()):
                    mod.installed = True
            if mod.installed:
                self.log.debug("Skipped mod: Mod is already installed.")
                continue

            # Link or copy mod to destination
            for fileindex, file in enumerate(mod.files):
                src_path = mod.path / file
                dst_path = modpath / file
                dst_dirs = dst_path.parent

                # Fix too long paths (> 260 characters)
                dst_dirs = f"\\\\?\\{dst_dirs}".replace(".mohidden", "")
                src_path = f"\\\\?\\{src_path}"
                dst_path = f"\\\\?\\{dst_path}".replace(".mohidden", "")

                # Update progress bars
                if ldialog:
                    ldialog.updateProgress(
                        text2=f"{mod.metadata['name']} ({fileindex}/{len(mod.files)})",
                        value2=fileindex,
                        max2=len(mod.files),
                        show3=True,
                        text3=f"{file.name} ({utils.scale_value(os.path.getsize(src_path))})",
                    )

                # Create directory structure and hardlink file
                os.makedirs(dst_dirs, exist_ok=True)

                # Copy file
                if self.app.mode == "copy":
                    shutil.copyfile(src_path, dst_path)
                # Link file
                else:
                    os.link(src_path, dst_path)

        self.log.debug("Saving database...")
        self.database["persistent"]["mods"][game] = installed_mods
        # Update progress bars
        if ldialog:
            ldialog.updateProgress(
                # Update first progress bar
                text1=self.app.lang["saving_database"],
                value1=0,
                max1=0,
                # Hide second progress bar
                show2=False,
                # Hide third progress bar
                show3=False,
            )
        self.db.save_db()

        self.log.info("Mod migration complete.")

    def copy_files(self, ldialog: LoadingDialog = None):
        # Copy additional files like inis
        additional_files = self.app.src_modinstance.additional_files
        if additional_files:
            self.log.info("Copying additional files from source to destination...")

            # Get paths
            game = self.app.game.lower()
            app_dir = Path(os.getenv("APPDATA")) / "Vortex" / game
            dst_dir = app_dir / "profiles" / self.profid

            # Copy files
            maximum = len(additional_files)
            for fileindex, file in enumerate(additional_files):
                # Skip file if it does not exist
                if not file.is_file():
                    self.log.error(
                        f"Failed to copy '{file.name}': File does not exist!"
                    )
                    continue

                # Update progress bars
                if ldialog:
                    ldialog.updateProgress(
                        # Update first progress bar
                        text1=f"{self.app.lang['copying_files']} ({fileindex}/{maximum})",
                        value1=fileindex,
                        max1=maximum,
                        # Display and update second progress bar
                        show2=True,
                        text2=file.name,
                        value2=0,
                        max2=0,
                    )

                filename = file.name
                if filename == "userlist.yaml":
                    dst_path = app_dir / filename

                    # Skip if source and destination file are the same
                    if file == dst_path:
                        continue

                    # Create 'userlist.yaml' backup if it already exists
                    userlists = list(app_dir.glob("userlist.yaml.mmm_*"))
                    c = len(userlists) + 1
                    if dst_path.is_file():
                        old_name = dst_path
                        new_name = app_dir / f"userlist.yaml.mmm_{c}"
                        os.rename(old_name, new_name)

                        self.log.debug("Created backup of Vortex's userlist.yaml.")

                    # Copy userlist.yaml from source to destination
                    os.makedirs(app_dir, exist_ok=True)
                    shutil.copyfile(file, dst_path)
                else:
                    # Copy additional files like ini files to profile folder
                    dst_path = dst_dir / filename.lower()
                    os.makedirs(dst_dir, exist_ok=True)
                    shutil.copyfile(file, dst_path)

                self.log.debug(f"Copied '{filename}' to destination.")

    def get_file_conflicts(self):
        game = self.app.game.lower()
        installed_mods: dict[str, dict] = self.database["persistent"]["mods"][game]

        for mod in self.mods:
            if "fileOverrides" in installed_mods[mod.metadata["filename"]]:
                mod.overwriting_files = [
                    Path(file)
                    for file in installed_mods[mod.metadata["filename"]][
                        "fileOverrides"
                    ]
                ]

    def set_file_conflicts(self):
        """
        Converts Mod.overwritten_files to Mod.overwriting_files.
        """

        for file, mods in self.modfiles.items():
            # Skip file if it has no conflicts
            if len(mods) == 1:
                continue

            # Scan for file conflicts
            for mod in mods:
                if file in mod.overwritten_files:
                    # Add file conflict to every mod that is load before
                    overwriting_mods = [
                        _mod
                        for _mod in mods
                        if self.loadorder.index(_mod) < self.loadorder.index(mod)
                    ]

                    for overwriting_mod in overwriting_mods:
                        overwriting_mod.overwriting_files.append(file)

    @property
    def loadorder(self, ldialog: LoadingDialog = None):
        if not self._loadorder:
            self.log.info("Creating loadorder from conflict rules...")

            new_loadorder = self.mods.copy()
            new_loadorder.sort(key=lambda mod: mod.name)

            game = self.app.game.lower()
            installed_mods: dict[str, dict] = self.database["persistent"]["mods"][game]
            for mod in self.mods.copy():
                modtype = installed_mods[mod.metadata["filename"]]["type"]

                # Skip mod if it is a root mod
                if modtype and modtype != "collection":
                    print(f"{mod}: {modtype}")
                    self.root_mods.append(mod)
                    self.mods.remove(mod)
                    new_loadorder.remove(mod)
                    continue
                # Ignore collection bundle
                elif modtype == "collection":
                    self.mods.remove(mod)
                    new_loadorder.remove(mod)
                    continue

                # Get rules of mod
                rules = installed_mods[mod.metadata["filename"]].get("rules", [])
                for rule in rules:
                    reference = rule["reference"]
                    if "id" in reference:
                        ref_mod = reference["id"].strip()
                    elif "fileExpression" in reference:
                        ref_mod = reference["fileExpression"].strip()
                    # Skip mod if reference mod does not exist
                    else:
                        continue

                    # Get referenced mod from mod list if available
                    if ref_mods := list(
                        filter(
                            lambda _mod: _mod.metadata["filename"] == ref_mod, self.mods
                        )
                    ):
                        ref_mod: utils.Mod = ref_mods[0]
                    else:
                        ref_mod = None
                    # Check if mod is in migrated mods
                    if ref_mod in self.mods:
                        ruletype = rule["type"]
                        # Before
                        if ruletype == "before":
                            mod.overwriting_mods.append(ref_mod)
                        # After
                        elif ruletype == "after":
                            ref_mod.overwriting_mods.append(mod)
                        # Ignore if it is a dependency
                        elif ruletype == "requires":
                            continue
                        # Ignore but warn if a mod conflict is detected
                        # for eg. when two mods are incompatible
                        elif ruletype == "conflicts":
                            self.log.warning(f"Detected incompatible mod conflict!")
                            self.log.debug(f"Mod: {mod}")
                            self.log.debug(f"Conflicting mod: {ref_mod}")
                            if version_match := reference.get("versionMatch", None):
                                self.log.debug(f"Version match: {version_match}")
                            continue
                        # Raise error if rule type is unknown
                        else:
                            self.log.debug(f"Mod: {mod}")
                            self.log.debug(f"Ref mod: {ref_mod}")
                            self.log.debug(f"Rule type: {rule['type']}")
                            self.log.debug(f"Rule reference: {reference}")
                            raise ValueError(f"Unknown rule type '{rule['type']}'!")

                # Sort mod
                if mod.overwriting_mods:
                    # self.log.debug(f"Sorting mod '{mod}'...")

                    old_index = index = new_loadorder.index(mod)

                    # Get smallest index of all overwriting mods
                    overwriting_mods = [
                        new_loadorder.index(overwriting_mod)
                        for overwriting_mod in mod.overwriting_mods
                    ]
                    index = min(overwriting_mods)
                    # self.log.debug(
                    #    f"Current index: {old_index} | Minimal index of overwriting_mods: {index}"
                    # )

                    if old_index > index:
                        new_loadorder.insert(index, new_loadorder.pop(old_index))
                        # self.log.debug(f"Moved mod '{mod}' from index {old_index} to {index}.")

            # Replace Vortex's full mod names displayed name
            final_loadorder = []
            for mod in new_loadorder:
                modname = mod.metadata["name"]
                final_loadorder.append(modname)

            self._loadorder = new_loadorder
            self.log.info("Created loadorder from conflicts.")

        return self._loadorder

    @loadorder.setter
    def loadorder(self, loadorder: list[utils.Mod], ldialog: LoadingDialog = None):
        self.log.info("Creating conflict rules from loadorder...")

        self.log.debug("Scanning mods for file conflicts...")
        for mod in self.mods:
            for file in mod.files:
                # Make all files lowercase
                file = Path(str(file).lower())
                if file in self.modfiles:
                    self.modfiles[file].append(mod)
                else:
                    self.modfiles[file] = [mod]

        self.log.debug("Creating conflict rules...")
        for file, mods in self.modfiles.items():
            # Skip file if it comes from a single mod
            if len(mods) == 1:
                continue

            # Get indices of overwriting mods
            overwriting_mods = mods.copy()

            # Sort overwriting mods after loadorder index
            overwriting_mods.sort(key=loadorder.index)

            # Create rules for all mods
            while len(overwriting_mods) > 1:
                # Process and remove first mod from list
                mod = overwriting_mods.pop(0)

                # Add rest of the mods to its overwriting list
                mod.overwriting_mods.extend(overwriting_mods)

                # Remove mod from its own list
                if mod in mod.overwriting_mods:
                    mod.overwriting_mods.remove(mod)

            # Remove duplicates
            mod.overwriting_mods = list(set(mod.overwriting_mods))

        self._loadorder = loadorder

        self.log.info("Created conflict rules.")
