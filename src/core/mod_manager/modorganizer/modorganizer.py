"""
Copyright (c) Cutleast
"""

import os
from pathlib import Path
from typing import Any, Optional

from core.archive.archive import Archive
from core.game.game import Game
from core.instance.instance import Instance
from core.instance.metadata import Metadata
from core.instance.mod import Mod
from core.instance.tool import Tool
from core.mod_manager.exceptions import InstanceNotFoundError
from core.mod_manager.modorganizer.exceptions import (
    CannotInstallGlobalMo2Error,
    GlobalInstanceDetectedError,
    InvalidGlobalInstancePathError,
)
from core.utilities.downloader import Downloader
from core.utilities.env_resolver import resolve
from core.utilities.exceptions import NotEnoughSpaceError
from core.utilities.filesystem import clean_fs_string, get_free_disk_space
from core.utilities.ini_file import INIFile
from core.utilities.progress_update import ProgressUpdate
from core.utilities.scale import scale_value
from core.utilities.unique import unique
from ui.widgets.loading_dialog import LoadingDialog

from ..mod_manager import ModManager
from .mo2_instance_info import MO2InstanceInfo


class ModOrganizer(ModManager):
    """
    Mod manager class for Mod Organizer 2.
    """

    display_name = "Mod Organizer 2"
    id = "modorganizer"
    icon_name = ":/icons/MO2_Label.svg"

    # TODO: Make this dynamic instead of a fixed url
    DOWNLOAD_URL: str = "https://github.com/ModOrganizer2/modorganizer/releases/download/v2.5.2/Mod.Organizer-2.5.2.7z"

    GAMES: dict[str, type[Game]] = {
        "SkyrimSE": Game.get_game_by_id("skyrimse"),
    }
    """
    Dict of game names in the meta.ini file to game classes.
    """

    appdata_path = resolve(Path("%LOCALAPPDATA%") / "ModOrganizer")

    def __repr__(self) -> str:
        return "ModOrganizer"

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

    def load_instance(
        self, instance_data: MO2InstanceInfo, ldialog: Optional[LoadingDialog] = None
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

        mods: list[Mod] = self._load_mods(instance_data, ldialog)

        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Processing mod conflicts..."),
                value1=0,
                max1=0,
                show2=False,
            )

        self.__process_conflicts(mods)

        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Loading tools from {0} > {1}...").format(
                    instance_name, profile_name
                ),
            )

        tools: list[Tool] = self._load_tools(instance_data, ldialog)

        instance = Instance(
            display_name=f"{instance_name} > {profile_name}",
            mods=mods,
            tools=tools,
            order_matters=True,
        )

        self.log.info(
            f"Loaded {instance_name} > {profile_name} with {len(mods)} mod(s) "
            f"and {len(instance.tools)} tool(s)."
        )

        return instance

    def _load_mods(
        self, instance_data: MO2InstanceInfo, ldialog: Optional[LoadingDialog] = None
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
            mods.append(mod)

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
            mod_id = int(general.get("modid") or 0) or None
            version = general.get("version") or ""
            if general.get("installationFile"):
                install_file = Path(general["installationFile"] or "").name

            while version.endswith(".0") and version.count(".") > 1:
                version = version.removesuffix(".0")

            if "gameName" in general and general["gameName"] in ModOrganizer.GAMES:
                game_id = ModOrganizer.GAMES[general["gameName"]].nexus_id
            elif "gameName" in general:
                self.log.warning(
                    f"Unknown game for mod {meta_ini_path.parent.name!r}: {general['gameName']}"
                )

            if "installedFiles" in meta_ini_data:
                file_id = (
                    int(meta_ini_data["installedFiles"].get("1\\fileid", 0)) or None
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
        lines: list[str] = [f"+{mod.display_name}\n" for mod in reversed(mods)]
        with open(modlist_txt_path, "w", encoding="utf8") as modlist_file:
            modlist_file.writelines(lines)

    @staticmethod
    def __process_conflicts(mods: list[Mod]) -> None:
        file_index: dict[str, list[Mod]] = ModOrganizer._index_modlist(mods)

        for mod_list in file_index.values():
            while len(mod_list) > 1:
                mod: Mod = mod_list.pop(0)
                mod.mod_conflicts.extend(mod_list)

        # Remove duplicate conflicts
        for mod in mods:
            mod.mod_conflicts = unique(mod.mod_conflicts)

    @staticmethod
    def _index_modlist(mods: list[Mod]) -> dict[str, list[Mod]]:
        """
        Indexes all mod files and maps each file to a list of mods that contain it.

        Args:
            mods (list[Mod]): The list of mods.

        Returns:
            dict[str, list[Mod]]: The indexed list of mods.
        """

        indexed_mods: dict[str, list[Mod]] = {}
        for mod in mods:
            for file in mod.files:
                indexed_mods.setdefault(str(file).lower(), []).append(mod)

        return indexed_mods

    def _load_tools(
        self, instance_data: MO2InstanceInfo, ldialog: Optional[LoadingDialog] = None
    ) -> list[Tool]:
        return []  # TODO: Implement this

    def create_instance(
        self, instance_data: MO2InstanceInfo, ldialog: Optional[LoadingDialog] = None
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
                "gameName": "Skyrim Special Edition",
                "selected_profile": "@ByteArray(Default)",
                "gamePath": str(game.get_install_dir()).replace("\\", "/"),
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

        if instance_data.install_mo2:
            self.__download_and_install_mo2(instance_data.base_folder, ldialog)

        self.log.info("Instance created successfully.")

        return Instance(
            display_name=instance_data.display_name,
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

    def install_mod(
        self,
        mod: Mod,
        instance: Instance,
        instance_data: MO2InstanceInfo,
        use_hardlinks: bool,
        replace: bool,
        blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        self.log.info(f"Installing mod {mod.display_name!r}...")

        game: Game = instance_data.game

        regular: bool = True
        mod_folder: Path = instance_data.mods_folder / clean_fs_string(mod.display_name)
        if mod.deploy_path is not None and mod.deploy_path == Path("."):
            if instance_data.use_root_builder:
                mod_folder /= "Root"
            else:
                mod_folder = game.get_install_dir()
                regular = False
        elif mod.deploy_path is not None:
            mod_folder /= mod.deploy_path

        if mod_folder.is_dir() and regular:
            self.log.warning(
                f"Mod {mod.display_name!r} is already exists! Merging files..."
            )
        mod_folder.mkdir(parents=True, exist_ok=True)

        # Create and write metadata to meta.ini
        # if the mod doesn't already have one
        if regular and Path("meta.ini") not in mod.files:
            meta_ini_path: Path = mod_folder / "meta.ini"
            meta_ini_file = INIFile(meta_ini_path)
            meta_ini_file.data = {
                "General": {
                    "game": game.display_name,
                    "modid": str(mod.metadata.mod_id),
                    "version": mod.metadata.version,
                    "installationFile": mod.metadata.file_name,
                },
                "installedFiles": {
                    "1\\modid": str(mod.metadata.mod_id),
                    "size": "1",
                    "1\\fileid": str(mod.metadata.file_id),
                },
            }
            meta_ini_file.save_file()
        elif Path("meta.ini") in mod.files:
            self.log.warning(f"Mod {mod.display_name!r} already has a meta.ini file.")

        self._migrate_mod_files(
            mod, mod_folder, use_hardlinks, replace, blacklist, ldialog
        )

        if regular:
            instance.mods.append(mod)

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
        # TODO: Implement this
        ...

    def get_instance_ini_dir(self, instance_data: MO2InstanceInfo) -> Path:
        return instance_data.profiles_folder / instance_data.profile

    def get_additional_files_folder(self, instance_data: MO2InstanceInfo) -> Path:
        return instance_data.profiles_folder / instance_data.profile

    def prepare_migration(self, instance_data: MO2InstanceInfo) -> None:
        if not instance_data.is_global and self.detect_global_instances():
            raise GlobalInstanceDetectedError

        elif instance_data.is_global:
            mo2_ini_path: Path = instance_data.base_folder / "ModOrganizer.ini"
            if not mo2_ini_path.is_relative_to(self.appdata_path):
                raise InvalidGlobalInstancePathError

            if instance_data.install_mo2:
                raise CannotInstallGlobalMo2Error

    def finalize_migration(
        self, migrated_instance: Instance, migrated_instance_data: MO2InstanceInfo
    ) -> None:
        modlist_txt_path: Path = (
            migrated_instance_data.profiles_folder
            / migrated_instance_data.profile
            / "modlist.txt"
        )
        self.__dump_modlist_txt(modlist_txt_path, migrated_instance.loadorder)
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

    def get_completed_message(self, migrated_instance_data: MO2InstanceInfo) -> str:
        text: str = super().get_completed_message(migrated_instance_data)

        if migrated_instance_data.use_root_builder:
            text += "\n\n" + self.tr(
                "The usage of root builder was enabled.\n"
                "In order to correctly deploy the root files, you have to download and "
                'extract the root builder plugin from Nexus Mods to the "plugins" '
                "folder of the new MO2 installation."
            )

        return text

    def check_destination_disk_space(
        self, dst_info: MO2InstanceInfo, src_size: int
    ) -> None:
        mods_folder: Path = dst_info.mods_folder
        free_space: int = get_free_disk_space(mods_folder.drive)

        if free_space < src_size:
            raise NotEnoughSpaceError(
                mods_folder.drive, scale_value(src_size), scale_value(free_space)
            )
