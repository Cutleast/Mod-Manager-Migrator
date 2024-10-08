"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
import shutil
from pathlib import Path

import utilities as utils
from widgets import LoadingDialog

from .instance import ModInstance


class MO2Instance(ModInstance):
    """
    Class for ModOrganizer ModInstance. Inherited from ModInstance class.
    """

    icon_name = "MO2_Label.svg"

    def __repr__(self):
        return "MO2Instance"

    def setup_instance(self):
        game_path = self.app.game_instance.get_install_dir()
        name: str = self.instance_data["name"]

        self.log.info(f"Setting up MO2 instance '{name}'...")

        # Get paths from instance data
        appdata_path = Path(os.getenv("LOCALAPPDATA")) / "ModOrganizer" / name
        base_dir = Path(self.instance_data["paths"]["base_dir"])
        dl_dir = Path(self.instance_data["paths"]["download_dir"])
        mods_dir = Path(self.instance_data["paths"]["mods_dir"])
        profs_dir = Path(self.instance_data["paths"]["profiles_dir"])
        prof_dir = Path(os.path.join(profs_dir, "Default"))
        overw_dir = Path(self.instance_data["paths"]["overwrite_dir"])
        self.paths = {
            "base_dir": base_dir,
            "dl_dir": dl_dir,
            "mods_dir": mods_dir,
            "profs_dir": profs_dir,
            "prof_dir": prof_dir,
            "overw_dir": overw_dir,
        }

        # Create directories
        os.makedirs(appdata_path)
        os.makedirs(base_dir, exist_ok=True)
        os.makedirs(dl_dir, exist_ok=True)
        os.makedirs(mods_dir, exist_ok=True)
        os.makedirs(prof_dir, exist_ok=True)
        os.makedirs(overw_dir, exist_ok=True)
        self.log.debug("Created instance folders.")

        # Create ini file with instance configuration
        inipath = appdata_path / "ModOrganizer.ini"
        iniparser = utils.IniParser(inipath)
        iniparser.data = {
            "General": {
                "gameName": self.app.game_instance.name,
                "selected_profile": "@ByteArray(Default)",
                "gamePath": str(game_path).replace("\\", "/"),
                "first_start": "true",
            },
            "Settings": {
                "base_directory": str(base_dir).replace("\\", "/"),
                "download_directory": str(dl_dir).replace("\\", "/"),
                "mod_directory": str(mods_dir).replace("\\", "/"),
                "profiles_directory": str(profs_dir).replace("\\", "/"),
                "overwrite_directory": str(overw_dir).replace("\\", "/"),
                "style": "Paper Dark.qss",
            },
        }
        iniparser.save_file()
        self.log.debug("Created 'ModOrganizer.ini'.")

        # Create profile files
        # Create initweaks.ini
        inipath = prof_dir / "initweaks.ini"
        iniparser = utils.IniParser(inipath)
        iniparser.data = {"Archive": {"InvalidateOlderFiles": 1}}
        iniparser.save_file()
        self.log.debug("Created 'initweaks.ini'.")

        # Create modlist.txt
        modlist_path = prof_dir / "modlist.txt"
        loadorder = self.loadorder.copy()
        loadorder.reverse()
        with modlist_path.open("w", encoding="utf8") as file:
            mods = "# This file was automatically generated by Mod Organizer"
            for mod in loadorder:
                # Skip mod if it is not selected in source box
                if not mod.selected:
                    continue

                modname = utils.clean_string(mod.metadata["name"])
                modname = modname.strip(". ")
                # Enable mod in destination
                if mod.enabled:
                    mods += "\n+" + modname

                # Disable mod in destination
                else:
                    mods += "\n-" + modname
            mods = mods.strip()
            file.write(mods)
        self.log.debug("Created 'modlist.txt'.")

        self.log.info("Created MO2 instance.")

    def load_instances(self):
        if not self.instances:
            instances_path = Path(os.getenv("LOCALAPPDATA")) / "ModOrganizer"
            # Check if there are any instances
            if instances_path.is_dir():
                # Get all instance folders
                instances = [
                    obj
                    for obj in os.listdir(instances_path)
                    if (instances_path / obj / "ModOrganizer.ini").is_file()
                ]

                # Remove instances from other games
                for instance in instances.copy():
                    instance_ini = utils.IniParser(
                        instances_path / instance / "ModOrganizer.ini"
                    )
                    instance_data = instance_ini.load_file()
                    if (
                        instance_data["General"]["gameName"]
                        != self.app.game_instance.name
                    ):
                        instances.remove(instance)

                self.instances = instances
                self.log.debug(f"Found {len(instances)} instance(s).")
            # Show error message otherwise
            else:
                raise ValueError("Found no instances!")

        return self.instances

    def load_instance(self, name: str, ldialog: LoadingDialog = None):
        self.log.info(f"Loading instance '{name}'...")

        self._loadorder = []
        self.mods = []

        # Update progress bar
        if ldialog:
            ldialog.updateProgress(text1=self.loc.main.loading_instance)

        # Raise exception if instance is not found
        app_path = Path(os.getenv("LOCALAPPDATA")) / "ModOrganizer"
        instance_path = app_path / name
        if (name not in self.instances) or (not instance_path.is_dir()):
            raise ValueError(f"Instance '{name}' not found!")

        # Load settings from ini
        inifile = instance_path / "ModOrganizer.ini"
        iniparser = utils.IniParser(inifile)
        data = iniparser.load_file()
        settings: dict[str, str] = data["Settings"]

        # Get instance paths from ini
        base_dir = Path(settings.get("base_directory", instance_path))
        dl_dir = settings.get("download_directory", None)
        dl_dir = Path(
            (base_dir / "downloads")
            if dl_dir is None
            else dl_dir.replace("%BASE_DIR", str(base_dir))
        )
        mods_dir = settings.get("mod_directory", None)
        mods_dir = Path(
            (base_dir / "mods")
            if mods_dir is None
            else mods_dir.replace("%BASE_DIR", str(base_dir))
        )
        profs_dir = settings.get("profiles_directory", None)
        profs_dir = Path(
            (base_dir / "profiles")
            if profs_dir is None
            else profs_dir.replace("%BASE_DIR", str(base_dir))
        )
        prof_dir = profs_dir / "Default"
        overw_dir = settings.get("overwrite_directory", None)
        overw_dir = Path(
            (base_dir / "overwrite")
            if overw_dir is None
            else overw_dir.replace("%BASE_DIR", str(base_dir))
        )

        self.mods_path = mods_dir
        self.paths = {
            "base_dir": base_dir,
            "dl_dir": dl_dir,
            "mods_dir": mods_dir,
            "profs_dir": profs_dir,
            "prof_dir": prof_dir,
            "overw_dir": overw_dir,
        }

        # Load mods from modlist.txt and their data from meta.ini
        mods = []
        modlist = prof_dir / "modlist.txt"
        if not modlist.is_file():
            raise utils.UiException(f"[no_mods] Instance '{name}' has no mods!")
        with open(modlist, "r", encoding="utf8") as modlist:
            lines = modlist.readlines()

        for modindex, line in enumerate(lines):
            line = line.strip()
            if (line.startswith("+") or line.startswith("-")) and (
                not line.endswith("_separator")
            ):
                modname = line[1:]
                modpath = self.mods_path / modname

                # Update progress bar
                if ldialog:
                    ldialog.updateProgress(
                        text1=f"{self.loc.main.loading_instance} ({modindex}/{len(lines)})",
                        value1=modindex,
                        max1=len(lines),
                        show2=True,
                        text2=modname,
                    )

                # Load mod metadata from meta.ini
                metaini = modpath / "meta.ini"
                if metaini.is_file():
                    iniparser = utils.IniParser(metaini)
                    data = iniparser.load_file()

                    general = data["General"]
                    modid = general.get("modid", 0)
                    fileid = 0
                    version = general.get("version", "1.0")
                    _ver = "-".join(version.split("."))
                    installedfiles = data.get("installedFiles")
                    if not installedfiles:
                        filename = f"{modname}-{_ver}"
                    else:
                        fileid = installedfiles.get("1\\fileid", 0)
                        filename = general.get(
                            "installationFile", f"{modname}-{modid}-{_ver}-{fileid}.7z"
                        )
                        filename = filename.rsplit(".", 1)[0]  # remove file type

                # Create metadata if 'meta.ini' does not exist
                else:
                    self.log.warning(f"Found no 'meta.ini' for mod '{modname}'!")
                    self.log.debug("Creating empty metadata...")

                    modid = 0
                    fileid = 0
                    version = "1.0"
                    filename = f"{modname}-1-0"

                modfiles = utils.create_folder_list(modpath, lower=False)
                modsize = utils.get_folder_size(modpath)
                enabled = line.startswith("+")

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
                    installed=True,
                )
                mods.append(mod)

                # Add modfiles to modfiles
                for file in modfiles:
                    if file in self.modfiles:
                        self.modfiles[file].append(mod)
                    else:
                        self.modfiles[file] = [mod]
        self.mods = mods
        self._loadorder = self.mods.copy()
        self._loadorder.reverse()

        # Get additional files
        self.additional_files = [
            (prof_dir / file)
            for file in prof_dir.iterdir()
            if (
                file.name != "initweaks.ini"
                and file.name != "modlist.txt"
                and file.name != "archives.txt"
                and file.name != "settings.ini"
            )
        ]
        userlist_path = Path(os.getenv("LOCALAPPDATA")) / "LOOT" / "games"
        userlist_path = userlist_path / self.app.game_instance.name
        userlist_path = userlist_path / "userlist.yaml"
        self.additional_files.append(userlist_path)

        self.name = name

        self.log.info("Loaded instance.")

    def copy_mods(self, ldialog: LoadingDialog = None):
        self.log.info("Migrating mods to instance...")

        maximum = len(self.mods)
        for modindex, mod in enumerate(self.mods):
            self.log.debug(
                f"Migrating mod '{mod.name}' ({modindex}/{len(self.mods)})..."
            )

            # Skip mod if it is not selected in source box
            if not mod.selected:
                self.log.debug("Skipped mod: Mod is not selected.")
                continue

            # Update progress bars
            if ldialog:
                ldialog.updateProgress(
                    # Update first progress bar
                    text1=f"{self.loc.main.migrating_instance} ({modindex}/{maximum})",
                    value1=modindex,
                    max1=maximum,
                    # Display and update second progress bar
                    show2=True,
                    text2=mod.metadata["name"],
                    value2=0,
                    max2=0,
                )

            # Copy mod to mod path
            modpath: Path = self.mods_path / mod.metadata["name"]
            modpath = utils.clean_filepath(modpath)
            for fileindex, file in enumerate(mod.files):
                src_path = mod.path / file
                dst_path = modpath / file
                dst_dirs = dst_path.parent

                # Skip if destination file already exists
                if dst_path.is_file():
                    continue

                # Fix too long paths (> 260 characters)
                dst_dirs = f"\\\\?\\{dst_dirs}"
                src_path = f"\\\\?\\{src_path}"
                dst_path = f"\\\\?\\{dst_path}"

                # Update progress bars
                if ldialog:
                    ldialog.updateProgress(
                        text2=f"{mod.metadata['name']} ({fileindex}/{len(mod.files)})",
                        value2=fileindex,
                        max2=len(mod.files),
                        show3=True,
                        text3=f"{file.name} ({utils.scale_value(os.path.getsize(src_path))})",
                    )

                # Add .mohidden to path if file is overwritten
                if file in mod.overwritten_files:
                    dst_path += ".mohidden"

                # Create directory structure
                os.makedirs(dst_dirs, exist_ok=True)

                # Copy file
                if self.app.mode == "copy":
                    shutil.copyfile(src_path, dst_path)
                # Link file
                else:
                    os.link(src_path, dst_path)

            # Write metadata to 'meta.ini' in destination mod
            metaini = utils.IniParser(modpath / "meta.ini")
            metaini.data = {
                "General": {
                    "gameName": self.app.game,
                    "modid": mod.metadata["modid"],
                    "version": mod.metadata["version"],
                    "installationFile": f"{mod.metadata['filename']}.7z",
                    "repository": "Nexus",
                    "validated": "true",
                },
                "installedFiles": {
                    "1\\modid": mod.metadata["modid"],
                    "1\\fileid": mod.metadata["fileid"],
                },
            }
            metaini.save_file()

        self.log.info("Mod migration complete.")

    def copy_files(self, ldialog: LoadingDialog = None):
        # Copy additional files like inis
        additional_files = self.app.src_modinstance.additional_files
        if additional_files:
            self.log.info("Copying additional files from source to destination...")

            game = self.app.game_instance.name
            paths = self.paths
            app_dir = Path(os.getenv("LOCALAPPDATA")) / "LOOT" / game
            dst_dir = paths["prof_dir"]

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
                        text1=f"{self.loc.main.copying_files} ({fileindex}/{maximum})",
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

                    # Create userlist.yaml backup if it already exists
                    userlists = list(app_dir.glob("userlist.yaml.mmm_*"))
                    c = len(userlists) + 1
                    if dst_path.is_file():
                        old_name = app_dir / "userlist.yaml"
                        new_name = app_dir / f"userlist.yaml.mmm_{c}"
                        os.rename(old_name, new_name)

                        self.log.debug(
                            "Created backup of installed LOOT's 'userlist.yaml'."
                        )

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
        self.log.debug("Scanning mods for file conflicts...")

        for mod in self.mods:
            # Get list of overwritten files
            overwritten_files = [
                Path(str(file).replace(".mohidden", ""))
                for file in mod.files
                if ".mohidden" in str(file)
            ]
            # Add file to overwritten files list of mod
            mod.overwritten_files = overwritten_files

            # Get list of conflicting mods
            for file in overwritten_files:
                # Skip file if it has no conflicts
                if file not in self.modfiles:
                    continue

                overwriting_mods = self.modfiles[file]
                overwriting_indices = [
                    self.loadorder.index(overwriting_mod)
                    for overwriting_mod in overwriting_mods
                ]

                # Get last overwriting mod
                overwriting_index = max(overwriting_indices)
                overwriting_mod = self.loadorder[overwriting_index]

                # Add file to overwriting files list of overwriting mod
                overwriting_mod.overwriting_files.append(file)

    def set_file_conflicts(self):
        """
        Converts Mod.overwriting_files to Mod.overwritten_files.
        """

        for mod in self.mods:
            # Skip mod if it has no file overrides
            if not mod.overwriting_files:
                continue

            for file in mod.overwriting_files:
                if file not in self.modfiles:
                    self.log.warning(
                        f"Failed to migrate conflicting file '{file}': File was not found!"
                    )
                    continue

                # Check for mods that are loaded before
                overwritten_mods = [
                    overwritten_mod
                    for overwritten_mod in self.modfiles[file]
                    if self.loadorder.index(overwritten_mod) > self.loadorder.index(mod)
                ]

                for overwritten_mod in overwritten_mods:
                    overwritten_mod.overwritten_files.append(file)
