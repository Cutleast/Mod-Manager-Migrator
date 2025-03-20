"""
Copyright (c) Cutleast
"""

import datetime
import time
from pathlib import Path
from typing import Any, Optional

import plyvel

from core.game.game import Game
from core.game.skyrimse import SkyrimSE
from core.instance.instance import Instance
from core.instance.metadata import Metadata
from core.instance.mod import Mod
from core.instance.tool import Tool
from core.mod_manager.exceptions import InstanceNotFoundError
from core.mod_manager.vortex.exceptions import (
    VortexIsRunningError,
    VortexNotInstalledError,
)
from core.utilities.env_resolver import resolve
from core.utilities.exceptions import NotEnoughSpaceError
from core.utilities.filesystem import clean_fs_string, get_free_disk_space
from core.utilities.leveldb import LevelDB
from core.utilities.scale import scale_value
from ui.widgets.loading_dialog import LoadingDialog

from ..mod_manager import ModManager
from .profile_info import ProfileInfo


class Vortex(ModManager):
    """
    Mod manager class for Vortex.
    """

    display_name = "Vortex"
    id = "vortex"
    icon_name = ":/icons/Vortex_Label.svg"

    GAMES: dict[str, type[Game]] = {
        "skyrimse": SkyrimSE,
    }
    """
    Dict of game names in the meta.ini file to game classes.
    """

    db_path: Path = resolve(Path("%APPDATA%") / "Vortex" / "state.v2")
    __level_db: LevelDB

    __conflict_rules: Optional[dict[Mod, list[dict]]] = None

    def __init__(self) -> None:
        super().__init__()

        self.__level_db = LevelDB(self.db_path)

    def __repr__(self) -> str:
        return "Vortex"

    def get_instance_names(self, game: Game) -> list[str]:
        self.log.info(f"Getting profiles for {game.id} from database...")

        if not self.db_path.is_dir():
            self.log.debug("Found no Vortex database.")
            return []

        try:
            data = self.__level_db.load("persistent###profiles###")
        except plyvel.IOError as ex:
            self.log.debug(ex, exc_info=ex)
            raise VortexIsRunningError

        profile_data_items: dict[str, dict] = data.get("persistent", {}).get(
            "profiles", {}
        )

        profiles: list[str] = []
        for profile_id, profile_data in profile_data_items.items():
            profile_name: str = profile_data["name"]
            game_id: str = profile_data["gameId"]

            if game_id.lower() == game.id.lower():
                profiles.append(f"{profile_name} ({profile_id})")

        self.log.info(f"Got {len(profiles)} profile(s) from database.")

        return profiles

    def load_instance(
        self, instance_data: ProfileInfo, ldialog: Optional[LoadingDialog] = None
    ) -> Instance:
        instance_name: str = instance_data.display_name
        game: Game = instance_data.game

        if instance_name not in self.get_instance_names(game):
            raise InstanceNotFoundError(instance_name)

        self.log.info(f"Loading profile {instance_name!r}...")
        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Loading profile {0}...").format(instance_name),
            )

        mods: list[Mod] = self._load_mods(instance_data, ldialog)
        self.__process_conflict_rules(
            mods,
            self.__conflict_rules,  # type: ignore[arg-type]
        )

        # Clean up to avoid clash when loading another profile
        self.__conflict_rules = None

        instance = Instance(display_name=instance_name, mods=mods, tools=[])

        self.log.info(
            f"Loaded profile {instance_name!r} with {len(mods)} mod(s) "
            f"and {len(instance.tools)} tool(s)."
        )

        return instance

    def _load_mods(
        self, instance_data: ProfileInfo, ldialog: Optional[LoadingDialog] = None
    ) -> list[Mod]:
        instance_name: str = instance_data.display_name
        profile_id: str = instance_data.id
        game: Game = instance_data.game

        self.log.debug(f"Loading mods from instance {instance_name!r}...")
        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Loading mods from profile {0}...").format(instance_name),
            )

        appdata_path: Path = resolve(Path("%APPDATA%") / "Vortex")

        game_id: str = game.id.lower()

        profiles_data: dict = self.__level_db.load("persistent###profiles###")
        mod_state_data: dict[str, dict] = profiles_data["persistent"]["profiles"][
            profile_id
        ].get("modState", {})

        moddata: dict[str, Any]
        # for modname, moddata in mod_state_data.items():
        #     if moddata["enabled"]:
        #         modnames.append(modname)
        modnames: list[str] = [m for m in mod_state_data]

        mods_data: dict = self.__level_db.load(f"persistent###mods###{game_id}###")
        installed_mods: dict[str, dict] = mods_data["persistent"]["mods"][game_id]

        staging_folder_value: Optional[str] = self.__level_db.get_key(
            f"settings###mods###installPath###{game_id}"
        )

        staging_folder: Path
        if staging_folder_value is None:
            staging_folder = appdata_path / game_id / "mods"
        else:
            staging_folder = resolve(
                Path(staging_folder_value),
                sep=("{", "}"),
                game=game_id,
                userdata=str(appdata_path),
            )

        mods: list[Mod] = []
        conflict_rules: dict[Mod, list[dict]] = {}
        for m, modname in enumerate(modnames):
            if modname not in installed_mods:
                self.log.warning(
                    f"Failed to load mod {modname!r}: Mod is not installed!"
                )
                continue

            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Loading mods from profile {0}...").format(
                        instance_name
                    )
                    + f" ({m}/{len(modnames)})",
                    value1=m,
                    max1=len(modnames),
                    show2=True,
                    text2=modname,
                )

            moddata = installed_mods[modname]
            mod_meta_data: dict[str, Any] = moddata["attributes"]
            display_name: str = (
                mod_meta_data.get("customFileName")
                or mod_meta_data.get("logicalFileName")
                or mod_meta_data.get("modName")
                or modname
            )
            mod_path: Path = staging_folder / moddata.get("installationPath", modname)
            file_name: str = mod_meta_data.get("fileName", mod_path.name)

            deploy_path: Optional[Path] = None
            modtype: Optional[str] = mod_meta_data.get("type")

            # Set deploy path to game's root folder
            if modtype is not None and modtype != "collection":
                deploy_path = Path(".")

            # Ignore collection bundles
            elif modtype == "collection":
                continue

            if not mod_path.is_dir():
                self.log.warning(
                    f"Failed to load mod files for mod {display_name!r}: "
                    f"{str(mod_path)!r} does not exist!"
                )
                continue

            mod_id: int = int(mod_meta_data.get("modId", 0))
            file_id: int = int(mod_meta_data.get("fileId", 0))
            version: str = mod_meta_data.get("version", "")

            # Remove trailing .0 if any
            while version.endswith(".0") and version.count(".") > 1:
                version = version.removesuffix(".0")

            dl_game_id: str = instance_data.game.nexus_id
            if (
                "downloadGame" in mod_meta_data
                and mod_meta_data["downloadGame"] in Vortex.GAMES
            ):
                dl_game_id = Vortex.GAMES[mod_meta_data["downloadGame"]].nexus_id
            elif "downloadGame" in mod_meta_data:
                self.log.warning(
                    f"Unknown game for mod {display_name!r}: {mod_meta_data['downloadGame']}"
                )

            mod = Mod(
                display_name=display_name,
                path=mod_path,
                deploy_path=deploy_path,
                metadata=Metadata(
                    mod_id=mod_id,
                    file_id=file_id,
                    version=version,
                    file_name=file_name,
                    game_id=dl_game_id,
                ),
                installed=True,
                enabled=mod_state_data.get(modname, {}).get("enabled", False),
            )
            mods.append(mod)
            rules: list[dict] = moddata.get("rules", [])
            if rules:
                conflict_rules[mod] = rules

        self.__conflict_rules = conflict_rules

        self.log.debug(f"Loaded {len(mods)} mod(s) from instance {instance_name!r}.")

        return mods

    def __process_conflict_rules(
        self, mods: list[Mod], conflict_rules: dict[Mod, list[dict]]
    ) -> None:
        mods_by_file_name: dict[str, Mod] = {
            self.__get_unique_file_name(mod): mod for mod in mods
        }
        mod_overwrites: dict[Mod, list[Mod]] = {}

        for mod in mods:
            rules: list[dict[str, dict | str]] = conflict_rules.get(mod, [])

            for rule in rules:
                reference: dict[str, str] = rule["reference"]  # type: ignore[assignment]
                ref_modname: Optional[str] = reference.get("id") or reference.get(
                    "fileExpression"
                )

                if ref_modname is None:
                    self.log.warning(
                        "Failed to process mod conflict rule for mod "
                        f"{mod.display_name!r}: Reference mod name is empty!"
                    )
                    continue

                ref_mod: Optional[Mod] = mods_by_file_name.get(ref_modname)

                # Ignore conflicts with mods that aren't relevant to us
                if ref_mod is None:
                    continue

                ruletype: str = rule["type"]  # type: ignore[assignment]

                if ruletype == "before":
                    mod_overwrites.setdefault(mod, []).append(ref_mod)

                elif ruletype == "after":
                    mod_overwrites.setdefault(ref_mod, []).append(mod)

                else:
                    self.log.warning(
                        "Failed to process mod conflict rule for mod "
                        f"{mod.display_name!r}: Unknown rule type {ruletype!r}!"
                    )

        for mod, overwriting_mods in mod_overwrites.items():
            mod.mod_conflicts = overwriting_mods

    def _load_tools(
        self, instance_data: ProfileInfo, ldialog: Optional[LoadingDialog] = None
    ) -> list[Tool]:
        return []  # TODO: Implement this

    def create_instance(
        self, instance_data: ProfileInfo, ldialog: Optional[LoadingDialog] = None
    ) -> Instance:
        self.log.info(
            f"Creating profile {instance_data.display_name!r} "
            f"with id {instance_data.id!r}..."
        )

        game_id: str = instance_data.game.id.lower()
        profile_name: str = instance_data.display_name
        profile_id: str = instance_data.id

        profile_data: dict[str, Any] = {
            "features": {  # TODO: Make these customizable
                "local_game_settings": False,
                "local_saves": False,
            },
            "gameId": game_id,
            "modState": {},
            "id": profile_id,
            "lastActivated": int(time.time()),
            "name": profile_name,
        }

        profiles_data: dict = self.__level_db.load("persistent###profiles###")
        profiles_data.setdefault("persistent", {}).setdefault("profiles", {})[
            profile_id
        ] = profile_data
        self.__level_db.dump(profiles_data)

        # Create profile folder
        app_path: Path = resolve(Path("%APPDATA%") / "Vortex")
        prof_path: Path = app_path / game_id / "profiles" / profile_id
        prof_path.mkdir(parents=True)

        self.log.info("Created Vortex profile.")

        return Instance(display_name=instance_data.display_name, mods=[], tools=[])

    def install_mod(
        self,
        mod: Mod,
        instance: Instance,
        instance_data: ProfileInfo,
        use_hardlinks: bool,
        replace: bool,
        blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        self.log.info(f"Installing mod {mod.display_name!r}...")

        if mod.mod_type == Mod.Type.Separator:
            self.log.info("Skipped mod because separators are not supported by Vortex.")
            return

        game_id: str = instance_data.game.id.lower()
        mods_data: dict[str, Any] = (
            self.__level_db.load(f"persistent###mods###{game_id}###")
            .setdefault("persistence", {})
            .setdefault("mods", {})
            .setdefault(game_id, {})
        )

        file_name: str = self.__get_unique_file_name(mod).rsplit(".", 1)[0]
        if file_name not in mods_data:
            install_time: str = datetime.datetime.fromtimestamp(
                time.time(), datetime.timezone.utc
            ).isoformat()
            logical_file_name: str = Vortex.get_logical_file_name(
                self.__get_unique_file_name(mod), mod.metadata.mod_id or 0
            )
            source: str = "nexus" if mod.metadata.mod_id else "other"

            moddata: dict[str, Any] = {
                "attributes": {
                    "customFileName": mod.display_name,
                    "downloadGame": game_id,
                    "installTime": install_time + "Z",
                    "fileName": self.__get_unique_file_name(mod),
                    "fileId": mod.metadata.file_id,
                    "modId": mod.metadata.mod_id,
                    "logicalFileName": logical_file_name,
                    "version": mod.metadata.version,
                    "source": source,
                },
                "id": file_name,
                "installationPath": file_name,
                "state": "installed",
                "type": None,
            }
            mods_data[file_name] = moddata

            staging_folder: Path = self.__get_staging_folder(instance_data.game)

            self._migrate_mod_files(
                mod,
                staging_folder / file_name,
                use_hardlinks,
                replace,
                blacklist,
                ldialog,
            )
        else:
            self.log.info(f"Mod {mod.display_name!r} already installed.")

        rules: list[dict[str, Any]] = mods_data[file_name].get("rules", [])
        # Check for rules
        for overwriting_mod in mod.mod_conflicts:
            overwriting_mod_filename: str = self.__get_unique_file_name(overwriting_mod)

            # Skip mod if both mods already exist in database
            # since rule is very likely to exist, too
            # if overwriting_mod_filename in installed_mods:
            if instance.is_mod_installed(mod) and instance.is_mod_installed(
                overwriting_mod
            ):
                continue

            # Merge rules
            rule: dict[str, Any] = {
                "reference": {
                    "id": overwriting_mod_filename,
                    "idHint": overwriting_mod_filename,
                    "versionMatch": "*",
                },
                "type": "before",
            }
            rules.append(rule)
            self.log.debug(
                f"Added conflict rule for mod {mod.display_name!r} "
                f"overwritten by {overwriting_mod.display_name!r}."
            )

        if rules:
            mods_data[file_name]["rules"] = rules

        # Add mod to profile
        profiles_data: dict[str, Any] = (
            self.__level_db.load("persistent###profiles###")
            .setdefault("persistent", {})
            .setdefault("profiles", {})
        )
        profile_mods: dict[str, Any] = profiles_data.setdefault(
            instance_data.id, {}
        ).setdefault("modState", {})
        profile_mods[file_name] = {
            "enabled": mod.enabled,
            "enabledTime": int(time.time()),
        }
        self.__level_db.dump(profiles_data)

        instance.mods.append(mod)

    def __get_staging_folder(self, game: Game) -> Path:
        data: dict[str, Any] = self.__level_db.load("settings###mods###installPath")

        staging_folder_raw: Optional[str] = data.get(game.id.lower())

        if staging_folder_raw is None:
            return resolve(Path("%APPDATA%") / "Vortex" / game.id.lower() / "mods")

        vars: dict[str, str] = {
            "userdata": resolve("%APPDATA%/Vortex"),
            "game": game.id.lower(),
        }

        staging_folder = resolve(Path(staging_folder_raw), ("{", "}"), **vars)

        return staging_folder

    def add_tool(
        self,
        tool: Tool,
        instance: Instance,
        instance_data: ProfileInfo,
        use_hardlinks: bool,
        replace: bool,
        blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        self.log.info(f"Adding tool {tool.display_name!r}...")

    def get_additional_files_folder(self, instance_data: ProfileInfo) -> Path:
        appdata_path: Path = resolve(Path("%APPDATA%") / "Vortex")
        prof_path: Path = (
            appdata_path / instance_data.game.id.lower() / "profiles" / instance_data.id
        )

        return prof_path

    def is_deployed(self, game: Game) -> bool:
        """
        Checks if Vortex is currently deployed to the game folder.

        Args:
            game (Game): Game to check deployment for

        Returns:
            bool: `True` if Vortex is deployed, `False` otherwise
        """

        return (self.__get_staging_folder(game) / "vortex.deployment.msgpack").is_file()

    def prepare_migration(self, instance_data: ProfileInfo) -> None:
        appdata_path: Path = resolve(Path("%APPDATA%") / "Vortex")
        game_folder: Path = appdata_path / instance_data.game.id.lower()

        if not game_folder.is_dir():
            raise VortexNotInstalledError

    def finalize_migration(
        self, migrated_instance: Instance, migrated_instance_data: ProfileInfo
    ) -> None:
        settings_data: dict[str, Any] = self.__level_db.load("settings###").setdefault(
            "settings", {}
        )

        # Enable profile management
        settings_data.setdefault("interface", {})["profilesVisible"] = True

        # Set last active profile
        settings_data["interface"].setdefault("profiles", {}).setdefault(
            "lastActiveProfile", {}
        )[migrated_instance_data.game.id.lower()] = migrated_instance_data.id

        # Add game to managed games
        game_data: dict[str, Any] = (
            settings_data.setdefault("gameMode", {})
            .setdefault("discovered", {})
            .setdefault(migrated_instance_data.game.id.lower(), {})
        )

        if "path" not in game_data:
            game_data["path"] = str(migrated_instance_data.game.get_install_dir())
            game_data["pathSetManually"] = True
            # TODO: Add real "store" value to game data, eg. "steam"
            game_data["store"] = "other"
            self.log.debug(
                f"Set game directory in Vortex database to {game_data['path']!r}."
            )

        self.__level_db.dump(settings_data)
        self.__level_db.del_symlink_path()

    def get_completed_message(self, migrated_instance_data: ProfileInfo) -> str:
        text: str = super().get_completed_message(migrated_instance_data)

        if self.is_deployed(migrated_instance_data.game):
            text += "\n\n" + self.tr(
                "Vortex is currently deployed to the game folder. "
                "It is strongly recommended to purge the game directory "
                "before using the migrated instance."
            )

        return text

    def check_destination_disk_space(
        self, dst_info: ProfileInfo, src_size: int
    ) -> None:
        staging_folder: Path = self.__get_staging_folder(dst_info.game)

        free_space: int = get_free_disk_space(staging_folder.drive)
        if free_space < src_size:
            raise NotEnoughSpaceError(
                staging_folder.drive, scale_value(src_size), scale_value(free_space)
            )

    def __get_unique_file_name(self, mod: Mod) -> str:
        return mod.metadata.file_name or Vortex.create_unique_file_name(
            mod_name=mod.display_name,
            mod_id=mod.metadata.mod_id,
            file_id=mod.metadata.file_id,
            version=mod.metadata.version,
        )

    @staticmethod
    def get_logical_file_name(full_file_name: str, mod_id: int) -> str:
        """
        Strips Nexus Mods-specific suffix from a full file name of a mod.

        Examples:
        >>> Vortex.get_logical_file_name("(Part 1) SSE Engine Fixes for 1.5.39 - 1.5.97-17230-5-9-1-1664974289.7z")
        "(Part 1) SSE Engine Fixes for 1.5.39 - 1.5.97"

        Args:
            full_file_name (str): Full file name
            mod_id (int): Mod ID, used for splitting

        Returns:
            str: Logical file name
        """

        return full_file_name.rsplit(".", 1)[0].rsplit(f"-{mod_id}-")[0]

    @staticmethod
    def create_unique_file_name(
        mod_name: str,
        mod_id: Optional[int],
        file_id: Optional[int],
        version: Optional[str],
    ) -> str:
        """
        Creates a unique full file name for a mod based on its name,
        mod id, file id and version.

        Args:
            mod_name (str): Display name of the mod
            mod_id (Optional[int]): Nexus Mods Mod ID
            file_id (Optional[int]): Nexus Mods File ID
            version (Optional[str]): Mod version

        Returns:
            str: Unique full file name
        """

        full_file_name: str = clean_fs_string(mod_name)

        if mod_id:
            full_file_name += f"-{mod_id}"

        if file_id:
            full_file_name += f"-{file_id}"

        if version:
            full_file_name += f"-{version}"

        return clean_fs_string(full_file_name)
