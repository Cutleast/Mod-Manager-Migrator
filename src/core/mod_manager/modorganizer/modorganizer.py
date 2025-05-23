"""
Copyright (c) Cutleast
"""

import os
import re
from copy import copy
from pathlib import Path
from typing import Any, Optional, override

from core.archive.archive import Archive
from core.game.exceptions import GameNotFoundError
from core.game.game import Game
from core.instance.instance import Instance
from core.instance.metadata import Metadata
from core.instance.mod import Mod
from core.instance.tool import Tool
from core.mod_manager.exceptions import InstanceNotFoundError
from core.mod_manager.modorganizer.exceptions import (
    CannotInstallGlobalMo2Error,
    InvalidGlobalInstancePathError,
)
from core.utilities.downloader import Downloader
from core.utilities.env_resolver import resolve
from core.utilities.filesystem import clean_fs_string
from core.utilities.ini_file import INIFile
from core.utilities.progress_update import ProgressUpdate
from core.utilities.scale import scale_value
from core.utilities.unique import unique
from ui.widgets.loading_dialog import LoadingDialog

from ..mod_manager import ModManager
from .mo2_instance_info import MO2InstanceInfo


class ModOrganizer(ModManager[MO2InstanceInfo]):
    """
    Mod manager class for Mod Organizer 2.
    """

    # TODO: Make this dynamic instead of a fixed url
    DOWNLOAD_URL: str = "https://github.com/ModOrganizer2/modorganizer/releases/download/v2.5.2/Mod.Organizer-2.5.2.7z"

    BYTE_ARRAY_PATTERN: re.Pattern[str] = re.compile(r"^@ByteArray\((.*)\)$")
    INI_ARG_PATTERN: re.Pattern[str] = re.compile(r'(?:[^ "]+|"[^"]+")+')
    INI_ARG_QUOTED_PATTERN: re.Pattern[str] = re.compile(r'^"?(([^"]|\\")+)"?$')
    INI_QUOTE_PATTERN: re.Pattern[str] = re.compile(r'^"([^"]+)"$')
    EXE_BLACKLIST: list[str] = ["Explorer++.exe"]
    """List of executable names to ignore when loading tools."""

    appdata_path = resolve(Path("%LOCALAPPDATA%") / "ModOrganizer")

    def __init__(self) -> None:
        super().__init__()

    @override
    def __repr__(self) -> str:
        return "ModOrganizer"

    @override
    @staticmethod
    def get_id() -> str:
        return "modorganizer"

    @override
    @staticmethod
    def get_display_name() -> str:
        return "Mod Organizer 2"

    @override
    @staticmethod
    def get_icon_name() -> str:
        return ":/icons/mo2.png"

    @override
    def get_instance_names(self, game: Game) -> list[str]:
        self.log.info(f"Getting global MO2 instances for {game.id}...")

        instances: list[str] = []

        if self.appdata_path.is_dir():
            for instance_ini in self.appdata_path.glob("**/ModOrganizer.ini"):
                ini_file = INIFile(instance_ini)
                instance_data: dict[str, Any] = ini_file.load_file()

                if "General" not in instance_data:
                    continue

                instance_game: str = instance_data["General"].get("gameName", "")
                if instance_game.lower() == game.display_name.lower():
                    instances.append(instance_ini.parent.name)

        self.log.info(f"Got {len(instances)} instances.")

        return instances

    @override
    def load_instance(
        self,
        instance_data: MO2InstanceInfo,
        modname_limit: int,
        file_blacklist: list[str] = [],
        game_folder: Optional[Path] = None,
        ldialog: Optional[LoadingDialog] = None,
    ) -> Instance:
        instance_name: str = instance_data.display_name
        profile_name: str = instance_data.profile
        game: Game = instance_data.game

        if instance_data.is_global and instance_name not in self.get_instance_names(
            game
        ):
            raise InstanceNotFoundError(f"{instance_name} > {profile_name}")

        instance_path: Path = instance_data.base_folder
        mo2_ini_path: Path = instance_path / "ModOrganizer.ini"

        if not mo2_ini_path.is_file():
            raise InstanceNotFoundError(f"{instance_name} > {profile_name}")

        mo2_ini_data: dict[str, dict[str, Any]] = INIFile(mo2_ini_path).load_file()
        raw_game_folder: Optional[str] = mo2_ini_data.get("General", {}).get("gamePath")
        if raw_game_folder is not None:
            raw_game_folder = ModOrganizer.BYTE_ARRAY_PATTERN.sub(
                r"\1", raw_game_folder
            )
            raw_game_folder = raw_game_folder.replace("\\\\", "\\")
            game_folder = Path(raw_game_folder)
        elif game_folder is None:
            raise GameNotFoundError

        self.log.info(
            f"Loading profile {profile_name!r} from instance "
            f"{instance_name!r} at '{instance_path}'..."
        )
        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Loading mods from {0} > {1}...").format(
                    instance_name, profile_name
                ),
            )

        mods: list[Mod] = self._load_mods(
            instance_data, modname_limit, game_folder, file_blacklist, ldialog
        )

        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Loading tools from {0} > {1}...").format(
                    instance_name, profile_name
                ),
            )

        tools: list[Tool] = self._load_tools(
            instance_data, mods, game_folder, file_blacklist, ldialog
        )

        instance = Instance(
            display_name=f"{instance_name} > {profile_name}",
            game_folder=game_folder,
            mods=mods,
            tools=tools,
            order_matters=True,
        )

        self.log.info(
            f"Loaded {instance_name} > {profile_name} with {len(mods)} mod(s) "
            f"and {len(instance.tools)} tool(s)."
        )

        return instance

    @override
    def _load_mods(
        self,
        instance_data: MO2InstanceInfo,
        modname_limit: int,
        game_folder: Path,
        file_blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> list[Mod]:
        instance_name: str = instance_data.display_name
        profile_name: str = instance_data.profile

        self.log.info(f"Loading mods from {instance_name} > {profile_name}...")
        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Loading mods from {0} > {1}...").format(
                    instance_name, profile_name
                ),
            )

        mo2_ini_path: Path = instance_data.base_folder / "ModOrganizer.ini"
        mods_dir: Path = ModOrganizer.get_mods_folder(mo2_ini_path)
        prof_dir: Path = ModOrganizer.get_profiles_folder(mo2_ini_path)
        modlist_txt_path: Path = prof_dir / instance_data.profile / "modlist.txt"

        if not (mods_dir.is_dir() and prof_dir.is_dir() and modlist_txt_path.is_file()):
            raise InstanceNotFoundError(f"{instance_name} > {profile_name}")

        modnames: list[tuple[str, bool]] = self.__parse_modlist_txt(modlist_txt_path)
        unmanaged_modnames: list[str] = [
            f.name
            for f in mods_dir.iterdir()
            if f.is_dir() and not any(f.name.lower() in m[0].lower() for m in modnames)
        ]
        if unmanaged_modnames:
            self.log.warning(f"Found {len(unmanaged_modnames)} unmanaged mod(s):")
            for modname in unmanaged_modnames:
                self.log.warning(f" - {modname}")
        modnames += [(m, False) for m in unmanaged_modnames]
        mods: list[Mod] = []

        for m, (modname, enabled) in enumerate(modnames):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Loading mods from {0} > {1}...").format(
                        instance_name, profile_name
                    )
                    + f" ({m}/{len(modnames)})",
                    value1=m,
                    max1=len(modnames),
                    show2=True,
                    text2=modname,
                )

            mod_path: Path = mods_dir / modname
            mod_meta_path: Path = mod_path / "meta.ini"
            metadata: Metadata
            if mod_meta_path.is_file():
                metadata = self.__parse_meta_ini(mod_meta_path, instance_data.game)
            else:
                metadata = Metadata(
                    mod_id=None, file_id=None, version="", file_name="", game_id=""
                )
                self.log.warning(f"No Metadata available for {modname!r}!")

            deploy_path: Optional[Path] = None
            if (mod_path / "Root").is_dir():
                deploy_path = Path(".")
                mod_path /= "Root"

                self.log.debug(f"Detected mod using Root Builder plugin: {modname}")

            mod = Mod(
                display_name=modname.removesuffix("_separator"),
                path=mod_path,
                deploy_path=deploy_path,
                metadata=metadata,
                installed=True,
                enabled=enabled,
                mod_type=(
                    Mod.Type.Separator
                    if modname.endswith("_separator")
                    else Mod.Type.Regular
                ),
            )
            mod.files  # build cache for mod files
            mods.append(mod)

        # Load overwrite folder as mod
        overwrite_folder: Path = ModOrganizer.get_overwrite_folder(mo2_ini_path)
        if overwrite_folder.is_dir() and os.listdir(overwrite_folder):
            overwrite_mod = Mod(
                display_name="Overwrite",
                path=overwrite_folder,
                deploy_path=None,
                metadata=Metadata(
                    mod_id=None, file_id=None, version="", file_name=None, game_id=""
                ),
                installed=True,
                enabled=True,
                mod_type=Mod.Type.Overwrite,
            )
            overwrite_mod.files  # build cache for mod files
            mods.append(overwrite_mod)

        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Processing mod conflicts..."),
                value1=0,
                max1=0,
                show2=False,
            )

        self.__process_conflicts(mods, file_blacklist, ldialog)

        self.log.info(
            f"Loaded {len(mods)} mod(s) from {instance_name} > {profile_name}."
        )

        return mods

    def __parse_meta_ini(self, meta_ini_path: Path, default_game: Game) -> Metadata:
        ini_file = INIFile(meta_ini_path)
        meta_ini_data: dict[str, Any] = ini_file.load_file()

        general: Optional[dict[str, Any]] = meta_ini_data.get("General")
        mod_id: Optional[int] = None
        file_id: Optional[int] = None
        version: str = ""
        game_id: str = default_game.nexus_id
        install_file: Optional[str] = None
        if general is not None:
            try:
                mod_id = int(general.get("modid") or 0) or None
                version = general.get("version") or ""
                if general.get("installationFile"):
                    install_file = Path(general["installationFile"] or "").name

                while version.endswith(".0") and version.count(".") > 1:
                    version = version.removesuffix(".0")

                try:
                    game_id = Game.get_game_by_short_name(general["gameName"]).nexus_id
                except KeyError:
                    self.log.warning(
                        f"No game specified for {meta_ini_path.parent.name!r}!"
                    )
                except ValueError:
                    self.log.warning(
                        f"Unknown game for mod {meta_ini_path.parent.name!r}: {general.get('gameName')}"
                    )

                if "installedFiles" in meta_ini_data:
                    file_id = (
                        int(meta_ini_data["installedFiles"].get("1\\fileid") or 0)
                        or None
                    )
            except Exception as ex:
                self.log.error(
                    f"Failed to parse meta.ini in {str(meta_ini_path.parent)!r}: {ex}"
                )
        else:
            self.log.warning(f"Incomplete meta.ini in {str(meta_ini_path.parent)!r}!")

        return Metadata(
            mod_id=mod_id,
            file_id=file_id,
            version=version,
            file_name=install_file,
            game_id=game_id,
        )

    @staticmethod
    def __parse_modlist_txt(modlist_txt_path: Path) -> list[tuple[str, bool]]:
        with open(modlist_txt_path, "r", encoding="utf8") as modlist_file:
            lines: list[str] = modlist_file.readlines()

        mods: list[tuple[str, bool]] = [
            (line[1:].removesuffix("\n"), line.startswith("+"))
            for line in reversed(lines)
            if line.strip() and line[0] in ("+", "-")
        ]

        return mods

    @staticmethod
    def __dump_modlist_txt(modlist_txt_path: Path, mods: list[Mod]) -> None:
        lines: list[str] = [
            (
                ("+" if mod.enabled and not mod.mod_type == Mod.Type.Separator else "-")
                + clean_fs_string(mod.display_name)
                + ("_separator" if mod.mod_type == Mod.Type.Separator else "")
                + "\n"
            )
            for mod in reversed(mods)
            if mod.mod_type != Mod.Type.Overwrite
        ]
        with open(modlist_txt_path, "w", encoding="utf8") as modlist_file:
            modlist_file.writelines(lines)

    def __process_conflicts(
        self,
        mods: list[Mod],
        file_blacklist: list[str],
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        file_index: dict[str, list[Mod]] = ModOrganizer._index_modlist(
            mods, file_blacklist
        )
        self.log.debug(f"Modlist has {len(file_index)} file(s) in {len(mods)} mod(s).")

        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Processing mod conflicts..."),
                value1=0,
                max1=0,
            )

        for mod_list in file_index.values():
            for m, mod in enumerate(mod_list):
                mod.mod_conflicts.extend(mod_list[m + 1 :])

        # Remove duplicate conflicts
        for mod in mods:
            mod.mod_conflicts = unique(mod.mod_conflicts)

        # Process single file conflicts (.mohidden files)
        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Processing single file conflicts..."))

        hidden_files: dict[str, list[Mod]] = {
            f: m
            for f, m in file_index.items()
            if f.endswith(".mohidden") and f.removesuffix(".mohidden") in file_index
        }
        self.log.debug(f"Found {len(hidden_files)} hidden file(s) with conflicts.")

        for hidden_file, mod_list in hidden_files.items():
            real_file: str = hidden_file.removesuffix(".mohidden")
            overwriting_mod: Mod = file_index[real_file][-1]
            for mod in mod_list:
                mod.file_conflicts[real_file] = overwriting_mod

    @override
    def _load_tools(
        self,
        instance_data: MO2InstanceInfo,
        mods: list[Mod],
        game_folder: Path,
        file_blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> list[Tool]:
        instance_name: str = instance_data.display_name
        profile_name: str = instance_data.profile
        mods_by_folders: dict[Path, Mod] = {m.path: m for m in mods}

        self.log.info(f"Loading tools from {instance_name} > {profile_name}...")
        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Loading tools from {0} > {1}...").format(
                    instance_name, profile_name
                ),
            )

        mo2_ini_path: Path = instance_data.base_folder / "ModOrganizer.ini"
        mo2_ini_data: dict[str, dict[str, Any]] = INIFile(mo2_ini_path).load_file()
        custom_executables: dict[str, Any] = mo2_ini_data.get("customExecutables", {})
        custom_executables_size = int(custom_executables.get("size", 0))
        tools: list[Tool] = []

        for i in range(1, custom_executables_size + 1):
            try:
                raw_exe_path: str = custom_executables[f"{i}\\binary"]
                raw_args: str = custom_executables[f"{i}\\arguments"] or ""
                name: str = custom_executables[f"{i}\\title"]
                raw_working_dir: Optional[str] = custom_executables[
                    f"{i}\\workingDirectory"
                ]
            except Exception as ex:
                self.log.error(f"Failed to load tool with index {i}: {ex}", exc_info=ex)
                continue

            exe_path = Path(raw_exe_path)
            if exe_path.name in ModOrganizer.EXE_BLACKLIST:
                self.log.debug(
                    f"Skipped tool '{exe_path.name}' due to mod manager blacklist."
                )
                continue

            working_dir: Optional[Path] = (
                Path(raw_working_dir) if raw_working_dir is not None else None
            )
            if working_dir == game_folder:
                working_dir = None

            mod: Optional[Mod] = ModOrganizer._get_mod_for_path(
                exe_path, mods_by_folders
            )
            is_in_game_dir: bool = False
            if mod is not None:
                exe_path = exe_path.relative_to(mod.path)
            elif exe_path.is_relative_to(game_folder):
                exe_path = exe_path.relative_to(game_folder)
                is_in_game_dir = True

            tool = Tool(
                display_name=name,
                mod=mod,
                executable=exe_path,
                commandline_args=ModOrganizer.process_ini_arguments(raw_args),
                working_dir=working_dir,
                is_in_game_dir=is_in_game_dir,
            )
            tools.append(tool)

        self.log.info(
            f"Loaded {len(tools)} tool(s) from {instance_name} > {profile_name}."
        )

        return tools

    @staticmethod
    def process_ini_arguments(raw_args: str) -> list[str]:
        """
        Processes a raw string of commandline arguments for an executable by splitting
        it into a list of separate arguments.

        Examples:
            `-D:\\"C:\\\\Games\\\\Nolvus Ascension\\\\STOCK GAME\\\\Data\\" -c:\\"C:\\\\Games\\\\Nolvus Ascension\\\\TOOLS\\\\SSE Edit\\\\Cache\\\\\\"`

            => `[r'-D:"C:\\Games\\Nolvus Ascension\\STOCK GAME\\Data"', r'-c:"C:\\Games\\Nolvus Ascension\\TOOLS\\SSE Edit\\Cache\\"']`

        Args:
            raw_args (str): Raw string of commandline arguments.

        Returns:
            list[str]: List of commandline arguments.
        """

        if raw_args.startswith('"') and raw_args.endswith('"'):
            raw_args = ModOrganizer.INI_ARG_QUOTED_PATTERN.sub(r"\1", raw_args)
        raw_args = raw_args.replace('\\"', '"').replace("\\\\", "\\")

        raw_matches: list[str] = ModOrganizer.INI_ARG_PATTERN.findall(raw_args)
        args: list[str] = [
            ModOrganizer.INI_QUOTE_PATTERN.sub(r"\1", arg) for arg in raw_matches
        ]
        return args

    @override
    @staticmethod
    def get_actual_files(mod: Mod) -> dict[Path, Path]:
        return {
            Path(file): Path(file).with_suffix(file.suffix.removesuffix(".mohidden"))
            for file in mod.files
            if file.suffix.endswith(".mohidden")
            and str(file).lower().removesuffix(".mohidden") in mod.file_conflicts
        }

    @override
    def create_instance(
        self,
        instance_data: MO2InstanceInfo,
        game_folder: Path,
        ldialog: Optional[LoadingDialog] = None,
    ) -> Instance:
        self.log.info(f"Creating instance {instance_data.display_name!r}...")

        mo2_ini_path: Path = instance_data.base_folder / "ModOrganizer.ini"
        game: Game = instance_data.game

        mods_dir: str
        if instance_data.mods_folder.is_relative_to(instance_data.base_folder):
            mods_dir = "%BASE_DIR%/" + str(
                instance_data.mods_folder.relative_to(instance_data.base_folder)
            ).replace("\\", "/")
        else:
            mods_dir = str(instance_data.mods_folder).replace("\\", "/")

        prof_dir: str
        if instance_data.profiles_folder.is_relative_to(instance_data.base_folder):
            prof_dir = "%BASE_DIR%/" + str(
                instance_data.profiles_folder.relative_to(instance_data.base_folder)
            ).replace("\\", "/")
        else:
            prof_dir = str(instance_data.profiles_folder).replace("\\", "/")

        mo2_ini_path.parent.mkdir(parents=True, exist_ok=True)
        mo2_ini_file = INIFile(mo2_ini_path)
        mo2_ini_file.data = {
            "General": {
                "gameName": game.display_name,
                "selected_profile": "@ByteArray(Default)",
                "gamePath": str(game_folder).replace("\\", "/"),
                "first_start": "true",
            },
            "Settings": {
                "base_directory": str(instance_data.base_folder).replace("\\", "/"),
                "download_directory": "%BASE_DIR%/downloads",  # TODO: Make this configurable
                "mod_directory": mods_dir,
                "profiles_directory": prof_dir,
                "overwrite_directory": "%BASE_DIR%/overwrite",
                "language": "en",
                "style": "Paper Dark.qss",
            },
        }
        mo2_ini_file.save_file()

        instance_data.mods_folder.mkdir(parents=True, exist_ok=True)
        instance_data.profiles_folder.mkdir(parents=True, exist_ok=True)
        os.makedirs(
            instance_data.profiles_folder / instance_data.profile, exist_ok=True
        )
        os.makedirs(instance_data.base_folder / "downloads", exist_ok=True)
        os.makedirs(instance_data.base_folder / "overwrite", exist_ok=True)
        (instance_data.profiles_folder / instance_data.profile / "modlist.txt").touch()

        if instance_data.install_mo2:
            self.__download_and_install_mo2(instance_data.base_folder, ldialog)

        self.log.info("Instance created successfully.")

        return Instance(
            display_name=instance_data.display_name,
            game_folder=game_folder,
            mods=[],
            tools=[],
            order_matters=True,
        )

    def __download_and_install_mo2(
        self, dest: Path, ldialog: Optional[LoadingDialog] = None
    ) -> None:
        self.log.info(f"Downloading and installing ModOrganizer to {str(dest)!r}...")

        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Downloading and installing ModOrganizer...")
            )

        downloaded_archive: Path = self.__download_mo2(dest, ldialog)
        self.__install_mo2(downloaded_archive, dest, ldialog)

        downloaded_archive.unlink()
        self.log.debug(f"Deleted downloaded {str(downloaded_archive)!r}.")

        self.log.info("ModOrganizer downloaded and installed successfully.")

    def __download_mo2(
        self, dest: Path, ldialog: Optional[LoadingDialog] = None
    ) -> Path:
        self.log.info("Downloading ModOrganizer...")

        def update(progress_update: ProgressUpdate) -> None:
            if ldialog is not None:
                ldialog.updateProgress(
                    show2=True,
                    text2=self.tr("Downloading ModOrganizer...")
                    + f" ({scale_value(progress_update.current)} / "
                    f"{scale_value(progress_update.maximum)})",
                    value2=progress_update.current,
                    max2=progress_update.maximum,
                )

        return Downloader.single_download(
            url=ModOrganizer.DOWNLOAD_URL,
            dest_folder=dest,
            progress_callback=update,
        )

    def __install_mo2(
        self,
        downloaded_archive: Path,
        dest: Path,
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        self.log.info("Installing ModOrganizer...")

        if ldialog is not None:
            ldialog.updateProgress(
                text2=self.tr("Extracting archive..."), value2=0, max2=0
            )

        archive: Archive = Archive.load_archive(downloaded_archive)
        archive.extract_all(dest, full_paths=True)

    @override
    def install_mod(
        self,
        mod: Mod,
        instance: Instance,
        instance_data: MO2InstanceInfo,
        file_redirects: dict[Path, Path],
        use_hardlinks: bool,
        replace: bool,
        blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        self.log.info(f"Installing mod {mod.display_name!r}...")

        game: Game = instance_data.game

        mod_folder: Path
        regular_deployment: bool = True

        if mod.mod_type in [Mod.Type.Regular, Mod.Type.Separator]:
            mod_name: str = mod.display_name
            if mod.mod_type == Mod.Type.Separator:
                mod_name += "_separator"
            mod_folder = instance_data.mods_folder / clean_fs_string(mod_name)
            meta_ini_path: Path = mod_folder / "meta.ini"
            if mod.deploy_path is not None and mod.deploy_path == Path("."):
                if instance_data.use_root_builder:
                    mod_folder /= "Root"
                else:
                    mod_folder = instance.game_folder
                    regular_deployment = False
            elif mod.deploy_path is not None:
                mod_folder /= mod.deploy_path

            self.log.debug(f"Deploy path: {mod.deploy_path}")
            self.log.debug(f"Mod folder: {mod_folder}")

            if mod_folder.is_dir() and regular_deployment:
                self.log.warning(
                    f"Mod {mod.display_name!r} already exists! Merging files..."
                )
            mod_folder.mkdir(parents=True, exist_ok=True)

            # Create and write metadata to meta.ini
            # if the mod doesn't already have one
            if regular_deployment and Path("meta.ini") not in mod.files:
                meta_ini_file = INIFile(meta_ini_path)
                meta_ini_file.data = {
                    "General": {
                        "game": game.short_name,
                        "modid": mod.metadata.mod_id,
                        "version": mod.metadata.version,
                        "installationFile": mod.metadata.file_name,
                    },
                    "installedFiles": {
                        "1\\modid": mod.metadata.mod_id,
                        "size": "1",
                        "1\\fileid": mod.metadata.file_id,
                    },
                }
                meta_ini_file.save_file()
            elif regular_deployment and Path("meta.ini") in mod.files:
                meta_ini_path.write_bytes((mod.path / "meta.ini").read_bytes())
                self.log.info("Copied original meta.ini from mod.")

        # Process overwrite folder
        elif mod.mod_type == Mod.Type.Overwrite:
            mo2_ini_path: Path = instance_data.base_folder / "ModOrganizer.ini"
            mod_folder: Path = ModOrganizer.get_overwrite_folder(mo2_ini_path)

        else:
            self.log.error(f"Unknown mod type: {mod.mod_type}")
            return

        self._migrate_mod_files(
            mod, mod_folder, file_redirects, use_hardlinks, replace, blacklist, ldialog
        )

        # Append .mohidden suffix to files in mod.file_conflicts
        for file in mod.file_conflicts.keys():
            src: Path = mod_folder / file
            dst: Path = src.with_suffix(src.suffix + ".mohidden")
            os.rename(src, dst)
            self.log.debug(
                f"Renamed '{file}' to '{dst}' due to configured file conflict."
            )

        # Merge conflicts with already installed mods
        if instance.is_mod_installed(mod):
            existing_mod: Mod = instance.get_installed_mod(mod)
            existing_mod.mod_conflicts = unique(
                existing_mod.mod_conflicts + mod.mod_conflicts
            )
            existing_mod.file_conflicts.update(mod.file_conflicts)

        elif regular_deployment:
            new_mod: Mod = Mod.copy(mod)
            new_mod.path = mod_folder
            instance.mods.append(new_mod)

    @override
    def add_tool(
        self,
        tool: Tool,
        instance: Instance,
        instance_data: MO2InstanceInfo,
        use_hardlinks: bool,
        replace: bool,
        blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        if tool in instance.tools:
            return

        self.log.info(f"Adding tool {tool.display_name!r}...")

        mo2_ini_path: Path = instance_data.base_folder / "ModOrganizer.ini"
        mo2_ini_file = INIFile(mo2_ini_path)
        custom_executables: dict[str, Any] = mo2_ini_file.data.setdefault(
            "customExecutables", {"size": 0}
        )
        new_index = int(custom_executables["size"]) + 1

        new_tool: Tool = copy(tool)
        if new_tool.mod is not None and instance.is_mod_installed(new_tool.mod):
            # Map tool to the installed mod
            new_tool.mod = instance.get_installed_mod(new_tool.mod)

        custom_executables.update(
            ModOrganizer._tool_to_ini_data(new_tool, new_index, instance.game_folder)
        )
        custom_executables["size"] = new_index

        mo2_ini_file.save_file()

    @staticmethod
    def _tool_to_ini_data(tool: Tool, index: int, game_folder: Path) -> dict[str, Any]:
        """
        Creates a INI data section for the specified tool to be written to an
        instance's ModOrganizer.ini file.

        Args:
            tool (Tool): Tool to add to the instance
            index (int): New index for the tool
            game_folder (Path): Path to the game folder

        Returns:
            dict[str, Any]: INI data
        """

        return {
            f"{index}\\arguments": ModOrganizer.prepare_ini_arguments(
                tool.commandline_args
            ),
            f"{index}\\binary": str(tool.get_full_executable_path(game_folder)).replace(
                "\\", "/"
            ),
            f"{index}\\hide": False,
            f"{index}\\ownicon": False,
            f"{index}\\steamAppID": None,
            f"{index}\\title": tool.display_name,
            f"{index}\\toolbar": False,
            f"{index}\\workingDirectory": str(tool.working_dir or ""),
        }

    @staticmethod
    def prepare_ini_arguments(args: list[str]) -> str:
        """
        Prepares a list of arguments for writing to a ModOrganizer.ini file.

        Args:
            args (list[str]): List of arguments

        Returns:
            str: Concatenated and escaped list of arguments
        """

        return repr(" ".join(args))[1:-1]

    @override
    def get_instance_ini_dir(self, instance_data: MO2InstanceInfo) -> Path:
        return instance_data.profiles_folder / instance_data.profile

    @override
    def get_additional_files_folder(self, instance_data: MO2InstanceInfo) -> Path:
        return instance_data.profiles_folder / instance_data.profile

    @override
    def prepare_migration(self, instance_data: MO2InstanceInfo) -> None:
        if instance_data.is_global:
            mo2_ini_path: Path = instance_data.base_folder / "ModOrganizer.ini"
            if not mo2_ini_path.is_relative_to(self.appdata_path):
                raise InvalidGlobalInstancePathError

            if instance_data.install_mo2:
                raise CannotInstallGlobalMo2Error

    @override
    def finalize_migration(
        self,
        migrated_instance: Instance,
        migrated_instance_data: MO2InstanceInfo,
        order_matters: bool,
        activate_new_instance: bool,
    ) -> None:
        modlist_txt_path: Path = (
            migrated_instance_data.profiles_folder
            / migrated_instance_data.profile
            / "modlist.txt"
        )
        self.__dump_modlist_txt(
            modlist_txt_path, migrated_instance.get_loadorder(order_matters)
        )
        self.log.debug(f"Dumped modlist to {str(modlist_txt_path)!r}.")

        settings_ini_path: Path = (
            migrated_instance_data.profiles_folder
            / migrated_instance_data.profile
            / "settings.ini"
        )
        settings_ini = INIFile(settings_ini_path)
        settings_ini.data = {
            "General": {
                "LocalSaves": str(migrated_instance.separate_save_games).lower(),
                "LocalSettings": str(migrated_instance.separate_ini_files).lower(),
            }
        }
        settings_ini.save_file()
        self.log.debug(f"Dumped settings to {str(settings_ini_path)!r}.")

    @staticmethod
    def get_mods_folder(mo2_ini_path: Path) -> Path:
        """
        Gets the path to the mods folder of the specified MO2 instance.

        Args:
            mo2_ini_path (Path): Path to the ModOrganizer.ini file of the instance.

        Returns:
            Path: Path to the mods folder.
        """

        ini_file = INIFile(mo2_ini_path)
        ini_data: dict[str, Any] = ini_file.load_file()

        settings: dict[str, Any] = ini_data["Settings"]
        base_dir = Path(settings.get("base_directory", mo2_ini_path.parent))

        mods_dir: Path
        if "mod_directory" in settings:
            mods_dir = resolve(Path(settings["mod_directory"]), base_dir=str(base_dir))
        else:
            mods_dir = base_dir / "mods"

        return mods_dir

    @staticmethod
    def get_profiles_folder(mo2_ini_path: Path) -> Path:
        """
        Gets the path to the profiles folder of the specified MO2 instance.

        Args:
            mo2_ini_path (Path): Path to the ModOrganizer.ini file of the instance.

        Returns:
            Path: Path to the profiles folder.
        """

        ini_file = INIFile(mo2_ini_path)
        ini_data: dict[str, Any] = ini_file.load_file()

        settings: dict[str, Any] = ini_data["Settings"]
        base_dir = Path(settings.get("base_directory", mo2_ini_path.parent))

        prof_dir: Path
        if "profiles_directory" in settings:
            prof_dir = resolve(
                Path(settings["profiles_directory"]), base_dir=str(base_dir)
            )
        else:
            prof_dir = base_dir / "profiles"

        return prof_dir

    @staticmethod
    def get_overwrite_folder(mo2_ini_path: Path) -> Path:
        """
        Gets the path to the overwrite folder of the specified MO2 instance.

        Args:
            mo2_ini_path (Path): Path to the ModOrganizer.ini file of the instance.

        Returns:
            Path: Path to the overwrite folder.
        """

        ini_file = INIFile(mo2_ini_path)
        ini_data: dict[str, Any] = ini_file.load_file()

        settings: dict[str, Any] = ini_data["Settings"]
        base_dir = Path(settings.get("base_directory", mo2_ini_path.parent))

        overwrite_dir: Path
        if "overwrite_directory" in settings:
            overwrite_dir = resolve(
                Path(settings["overwrite_directory"]), base_dir=str(base_dir)
            )
        else:
            overwrite_dir = base_dir / "overwrite"

        return overwrite_dir

    @staticmethod
    def get_profile_names(mo2_ini_path: Path) -> list[str]:
        """
        Gets the names of all profiles in the specified MO2 instance.

        Args:
            mo2_ini_path (Path): Path to the ModOrganizer.ini file of the instance.

        Returns:
            list[str]: List of profile names.
        """

        ini_file = INIFile(mo2_ini_path)
        ini_data: dict[str, Any] = ini_file.load_file()

        settings: dict[str, Any] = ini_data["Settings"]
        base_dir = Path(settings.get("base_directory", mo2_ini_path.parent))

        prof_dir: Path
        if "profiles_directory" in settings:
            prof_dir = resolve(
                Path(settings["profiles_directory"]), base_dir=str(base_dir)
            )
        else:
            prof_dir = base_dir / "profiles"

        return [prof.name for prof in prof_dir.iterdir() if prof.is_dir()]

    def detect_global_instances(self) -> bool:
        """
        Checks for global instances at AppData\\Local\\ModOrganizer.

        Returns:
            bool: Whether there are global MO2 instances.
        """

        self.log.info("Checking for global instances...")

        instances_found: bool = False

        global_instance_path: Path = resolve(Path("%LOCALAPPDATA%")) / "ModOrganizer"
        if global_instance_path.is_dir():
            instances_found = (
                len(list(global_instance_path.glob("*/ModOrganizer.ini"))) > 0
            )

        self.log.info(f"Global instances found: {instances_found}")

        return instances_found

    @override
    def get_completed_message(self, migrated_instance_data: MO2InstanceInfo) -> str:
        text: str = ""

        if migrated_instance_data.use_root_builder:
            if migrated_instance_data.is_global:
                text = (
                    self.tr(
                        "The usage of root builder was enabled.\n"
                        "In order to correctly deploy the root files, you have to "
                        "download and extract the root builder plugin from Nexus Mods "
                        'to the "plugins" folder of your MO2 installation if not '
                        "already installed."
                    )
                    + "\n\n"
                )
            else:
                text = (
                    self.tr(
                        "The usage of root builder was enabled.\n"
                        "In order to correctly deploy the root files, you have to "
                        "download and extract the root builder plugin from Nexus Mods "
                        'to the "plugins" folder of the new MO2 installation.'
                    )
                    + "\n\n"
                )

        if not migrated_instance_data.is_global and self.detect_global_instances():
            text += self.tr(
                "At least one global instance was detected.\n"
                "Global instances cause issues with portable instances and it is "
                "recommended to delete (or rename) the following folder:\n{0}"
            ).format(str(self.appdata_path))

        return text

    @override
    def get_mods_path(self, instance_data: MO2InstanceInfo) -> Path:
        return instance_data.mods_folder

    @override
    def is_instance_existing(self, instance_data: MO2InstanceInfo) -> bool:
        instance_name: str = instance_data.display_name
        profile_name: str = instance_data.profile
        game: Game = instance_data.game

        if instance_data.is_global and instance_name in self.get_instance_names(game):
            return True

        instance_path: Path = instance_data.base_folder
        mo2_ini_path: Path = instance_path / "ModOrganizer.ini"
        if mo2_ini_path.is_file():
            profile_path: Path = (
                ModOrganizer.get_profiles_folder(mo2_ini_path) / profile_name
            )
            return profile_path.is_dir()

        return False
