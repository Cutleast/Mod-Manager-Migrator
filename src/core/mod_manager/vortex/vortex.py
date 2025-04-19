"""
Copyright (c) Cutleast
"""

import datetime
import random
import shutil
import string
import time
from copy import copy
from pathlib import Path
from typing import Any, Optional, override

import plyvel

from core.game.exceptions import GameNotFoundError
from core.game.game import Game
from core.instance.instance import Instance
from core.instance.metadata import Metadata
from core.instance.mod import Mod
from core.instance.tool import Tool
from core.utilities.env_resolver import resolve
from core.utilities.filesystem import clean_fs_string
from core.utilities.leveldb import LevelDB
from ui.widgets.loading_dialog import LoadingDialog

from ..exceptions import InstanceNotFoundError
from ..mod_manager import ModManager
from .exceptions import (
    VortexIsRunningError,
    VortexNotFullySetupError,
)
from .profile_info import ProfileInfo


class Vortex(ModManager[ProfileInfo]):
    """
    Mod manager class for Vortex.
    """

    display_name = "Vortex"
    id = "vortex"
    icon_name = ":/icons/vortex.png"

    __games: dict[str, Game]
    """
    Dict of game names in the meta.ini file to game classes.
    """

    db_path: Path = resolve(Path("%APPDATA%") / "Vortex" / "state.v2")
    __level_db: LevelDB

    __conflict_rules: Optional[dict[Mod, list[dict]]] = None

    def __init__(self) -> None:
        super().__init__()

        self.__level_db = LevelDB(
            self.db_path, use_symlink=not LevelDB.is_db_readable(self.db_path)
        )

        self.__games = {
            "skyrimse": Game.get_game_by_id("skyrimse"),
        }

    @override
    def __repr__(self) -> str:
        return "Vortex"

    @override
    def get_instance_names(self, game: Game) -> list[str]:
        self.log.info(f"Getting profiles for {game.id} from database...")

        if not self.db_path.is_dir():
            self.log.debug("Found no Vortex database.")
            return []

        try:
            data = self.__level_db.load("persistent###profiles###")
        except plyvel.IOError as ex:
            raise VortexIsRunningError from ex

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

    @override
    def load_instance(
        self,
        instance_data: ProfileInfo,
        modname_limit: int,
        file_blacklist: list[str] = [],
        game_folder: Optional[Path] = None,
        ldialog: Optional[LoadingDialog] = None,
    ) -> Instance:
        instance_name: str = instance_data.display_name
        game: Game = instance_data.game

        if instance_name not in self.get_instance_names(game):
            raise InstanceNotFoundError(instance_name)

        key: str = (
            f"settings###gameMode###discovered###{instance_data.game.id.lower()}###path"
        )

        raw_game_folder: Optional[str] = self.__level_db.get_key(key)
        if raw_game_folder is not None:
            game_folder = Path(raw_game_folder)
        elif game_folder is None:
            raise GameNotFoundError

        self.log.info(f"Loading profile {instance_name!r}...")
        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Loading profile {0}...").format(instance_name),
            )

        mods: list[Mod] = self._load_mods(
            instance_data, modname_limit, game_folder, file_blacklist, ldialog
        )
        tools: list[Tool] = self._load_tools(
            instance_data, mods, game_folder, file_blacklist, ldialog
        )
        instance = Instance(
            display_name=instance_name, game_folder=game_folder, mods=mods, tools=tools
        )

        self.log.info(
            f"Loaded profile {instance_name!r} with {len(mods)} mod(s) "
            f"and {len(instance.tools)} tool(s)."
        )

        return instance

    @override
    def _load_mods(
        self,
        instance_data: ProfileInfo,
        modname_limit: int,
        game_folder: Path,
        file_blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> list[Mod]:
        instance_name: str = instance_data.display_name
        profile_id: str = instance_data.id
        game: Game = instance_data.game

        self.log.debug(f"Loading mods from instance {instance_name!r}...")
        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Loading mods from profile {0}...").format(instance_name),
            )

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

        if not mods_data:
            return []

        installed_mods: dict[str, dict] = mods_data["persistent"]["mods"][game_id]
        staging_folder: Path = self.__get_staging_folder(game)

        mods: list[Mod] = []
        conflict_rules: dict[Mod, list[dict]] = {}
        file_overrides: dict[Mod, list[str]] = {}
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
            )[:modname_limit].strip("-_. ")  # Limit mod name as it can get very long
            mod_path: Path = staging_folder / moddata.get("installationPath", modname)
            file_name: str = mod_meta_data.get("fileName", mod_path.name)

            deploy_path: Optional[Path] = None
            modtype: Optional[str] = moddata.get("type") or None

            # Set deploy path to game's root folder
            if modtype is not None and modtype != "collection":
                self.log.debug(f"Mod '{display_name}' has type '{modtype}'.")
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

            mod_id: Optional[int] = None
            if mod_meta_data.get("modId"):
                mod_id = int(mod_meta_data["modId"])
            file_id: Optional[int] = None
            if mod_meta_data.get("fileId"):
                file_id = int(mod_meta_data["fileId"])
            version: str = mod_meta_data.get("version") or ""

            # Remove trailing .0 if any
            while version.endswith(".0") and version.count(".") > 1:
                version = version.removesuffix(".0")

            dl_game_id: str = instance_data.game.nexus_id
            if (
                "downloadGame" in mod_meta_data
                and mod_meta_data["downloadGame"] in self.__games
            ):
                dl_game_id = self.__games[mod_meta_data["downloadGame"]].nexus_id
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
            overrides: list[str] = moddata.get("fileOverrides", [])
            if overrides:
                file_overrides[mod] = overrides

        self.__process_conflict_rules(mods, conflict_rules)

        mod_overrides: dict[Mod, list[Mod]] = self._get_reversed_mod_conflicts(mods)
        self.__process_file_overrides(
            file_overrides, file_blacklist, mod_overrides, game, game_folder
        )

        self.log.debug(f"Loaded {len(mods)} mod(s) from instance {instance_name!r}.")

        return mods

    def __process_conflict_rules(
        self, mods: list[Mod], conflict_rules: dict[Mod, list[dict]]
    ) -> None:
        self.log.info(f"Processing conflict rules for {len(conflict_rules)} mod(s)...")
        mods_by_file_name: dict[str, Mod] = {
            self.__get_unique_file_name(mod).rsplit(".", 1)[0]: mod for mod in mods
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

        self.log.info("Processing conflict rules successful.")

    def __process_file_overrides(
        self,
        file_overrides: dict[Mod, list[str]],
        file_blacklist: list[str],
        mod_overrides: dict[Mod, list[Mod]],
        game: Game,
        game_folder: Path,
    ) -> None:
        self.log.info(f"Processing file overrides for {len(file_overrides)} mod(s)...")

        mods_folder: Path = game_folder / game.mods_folder

        for mod, files in file_overrides.items():
            if mod not in mod_overrides:
                continue

            overwriting_files: dict[str, list[Mod]] = self._index_modlist(
                mod_overrides[mod], file_blacklist
            )
            if not overwriting_files:
                self.log.debug(
                    f"Mod {mod.display_name!r} has irrelevant file overrides: {files}."
                )
                continue

            for file in files:
                if Path(file).is_relative_to(mods_folder):
                    file = str(Path(file).relative_to(mods_folder))
                overwriting_mods: list[Mod] = overwriting_files.get(file.lower(), [])

                if len(overwriting_mods) > 1:
                    self.log.warning(
                        "Detected file override for multiple mods: "
                        f"{', '.join(m.display_name for m in overwriting_mods)} "
                        f"override {mod.display_name!r} for file {file!r}."
                    )

                if len(overwriting_mods) >= 1:
                    mod.file_conflicts[file] = overwriting_mods[0]

        self.log.info("Processing file overrides successful.")

    @override
    def _load_tools(
        self,
        instance_data: ProfileInfo,
        mods: list[Mod],
        game_folder: Path,
        file_blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> list[Tool]:
        self.log.debug("Loading tools from Vortex...")
        if ldialog is not None:
            ldialog.updateProgress(self.tr("Loading tools from Vortex..."))

        mods_by_folders: dict[Path, Mod] = {m.path: m for m in mods}
        game_id: str = instance_data.game.id.lower()
        tools_data: dict[str, Any] = (
            self.__level_db.load(
                f"settings###gameMode###discovered###{game_id}###tools"
            )
            .get("settings", {})
            .get("gameMode", {})
            .get("discovered", {})
            .get(game_id, {})
            .get("tools", {})
        )

        tools: list[Tool] = []
        for tool_id, tool_data in tools_data.items():
            try:
                name: str = tool_data["name"]
                raw_exe_path: str = tool_data["path"]
                raw_working_dir: Optional[str] = tool_data.get("workingDir") or None
                args: list[str] = tool_data.get("parameters") or []
            except Exception as ex:
                self.log.error(
                    f"Failed to load tool with id {tool_id!r}: {ex}", exc_info=ex
                )
                continue

            exe_path = Path(raw_exe_path)
            working_dir: Optional[Path] = (
                Path(raw_working_dir) if raw_working_dir is not None else None
            )
            if working_dir == game_folder:
                working_dir = None

            mod: Optional[Mod] = Vortex._get_mod_for_path(exe_path, mods_by_folders)
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
                commandline_args=args,
                working_dir=working_dir,
                is_in_game_dir=is_in_game_dir,
            )
            tools.append(tool)

        self.log.info(f"Loaded {len(tools)} tools from Vortex.")

        return tools

    @override
    def create_instance(
        self,
        instance_data: ProfileInfo,
        game_folder: Path,
        ldialog: Optional[LoadingDialog] = None,
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
            "lastActivated": Vortex.format_unix_timestamp(time.time()),
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

        return Instance(
            display_name=instance_data.display_name,
            game_folder=game_folder,
            mods=[],
            tools=self._load_tools(instance_data, [], game_folder, ldialog=ldialog),
        )

    @override
    def install_mod(
        self,
        mod: Mod,
        instance: Instance,
        instance_data: ProfileInfo,
        file_redirects: dict[Path, Path],
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
        staging_folder: Path = self.__get_staging_folder(instance_data.game)
        mods_data: dict[str, Any] = (
            self.__level_db.load(f"persistent###mods###{game_id}###")
            .setdefault("persistence", {})
            .setdefault("mods", {})
            .setdefault(game_id, {})
        )

        file_name: str = self.__get_unique_file_name(mod).rsplit(".", 1)[0]
        mod_folder: Path = staging_folder / file_name

        if file_name not in mods_data:
            logical_file_name: str = Vortex.get_logical_file_name(
                self.__get_unique_file_name(mod), mod.metadata.mod_id or 0
            )
            source: str = "nexus" if mod.metadata.mod_id else "other"
            modtype: Optional[str] = "dinput" if mod.deploy_path else None

            moddata: dict[str, Any] = {
                "attributes": {
                    "customFileName": mod.display_name,
                    "downloadGame": game_id,
                    "installTime": Vortex.format_utc_timestamp(time.time()),
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
                "type": modtype,
            }
            mods_data[file_name] = moddata

            self._migrate_mod_files(
                mod,
                mod_folder,
                file_redirects,
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
            overwriting_mod_filename: str = self.__get_unique_file_name(
                overwriting_mod
            ).rsplit(".", 1)[0]

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

        self.__level_db.dump(mods_data, prefix=f"persistent###mods###{game_id}###")

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
            "enabledTime": Vortex.format_unix_timestamp(time.time()),
        }
        self.__level_db.dump(profiles_data, prefix="persistent###profiles###")

        if not instance.is_mod_installed(mod):
            new_mod: Mod = Mod.copy(mod)
            new_mod.path = mod_folder
            instance.mods.append(new_mod)

    def __get_staging_folder(self, game: Game) -> Path:
        appdata_path: Path = resolve(Path("%APPDATA%") / "Vortex")
        game_id: str = game.id.lower()

        try:
            staging_folder_value: Optional[str] = self.__level_db.get_key(
                f"settings###mods###installPath###{game_id}"
            )
        except plyvel.IOError as ex:
            raise VortexIsRunningError from ex

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

        return staging_folder

    @override
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

        if tool in instance.tools:
            self.log.info(f"Tool {tool.display_name!r} already exists.")
            return

        game_id: str = instance_data.game.id.lower()
        tool_id: str = Vortex.generate_id(length=11)
        new_tool: Tool = copy(tool)
        if new_tool.mod is not None:
            # Map tool to the installed mod
            new_tool.mod = instance.get_installed_mod(new_tool.mod)
        tool_data: dict[str, Any] = {
            "custom": True,
            "defaultPrimary": False,
            "detach": True,
            "exclusive": False,
            "executable": None,
            "id": tool_id,
            "logo": f"{tool_id}.png",
            "name": new_tool.display_name,
            "parameters": [],
            "path": str(new_tool.get_full_executable_path(instance.game_folder)),
            "requiredFiles": [],
            "shell": False,
            "timestamp": int(time.time()),
            "workingDirectory": str(new_tool.working_dir or ""),
        }

        tool_prefix: str = (
            f"settings###gameMode###discovered###{game_id}###tools###{tool_id}###"
        )
        self.__level_db.dump(tool_data, prefix=tool_prefix)
        instance.tools.append(new_tool)

    @override
    def get_instance_ini_dir(self, instance_data: ProfileInfo) -> Path:
        appdata_path: Path = resolve(Path("%APPDATA%") / "Vortex")
        prof_path: Path = (
            appdata_path / instance_data.game.id.lower() / "profiles" / instance_data.id
        )

        return prof_path

    @override
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

    @override
    def prepare_migration(self, instance_data: ProfileInfo) -> None:
        appdata_path: Path = resolve(Path("%APPDATA%") / "Vortex")
        game_folder: Path = appdata_path / instance_data.game.id.lower()

        if not game_folder.is_dir():
            raise VortexNotFullySetupError

        game_path_key: str = (
            f"settings###gameMode###discovered###{instance_data.game.id.lower()}###path"
        )
        game_path: Optional[str] = self.__level_db.get_key(game_path_key)
        if game_path is None:
            raise VortexNotFullySetupError

        profile_management_key: str = "settings###interface###profilesVisible"
        profile_management_enabled: bool = (
            self.__level_db.get_key(profile_management_key) or False
        )
        if not profile_management_enabled:
            raise VortexNotFullySetupError

        # Make a backup of the original Vortex database
        backup_path: Path = appdata_path / (
            "state.v2-mmm_" + time.strftime("%Y-%m-%d_%H-%M-%S")
        )
        shutil.copytree(appdata_path / "state.v2", backup_path)
        self.log.info(f"Created backup of Vortex database at '{backup_path}'.")

    def __set_file_overrides(
        self, mods: list[Mod], game: Game, game_folder: Path
    ) -> None:
        for mod in mods:
            if not mod.file_conflicts:
                continue

            self.log.info(f"Setting file overrides for {mod.display_name!r}...")
            full_mod_name: str = self.__get_unique_file_name(mod).rsplit(".", 1)[0]
            prefix: str = f"persistent###mods###{game.id.lower()}###{full_mod_name}"
            mod_data: dict[str, Any] = self.__level_db.load(prefix)["persistent"][
                "mods"
            ][game.id.lower()][full_mod_name]
            mod_data["fileOverrides"] = [
                str(game_folder / game.mods_folder / file)
                for file in mod.file_conflicts
            ]
            self.__level_db.dump(mod_data, prefix + "###")

    @override
    def finalize_migration(
        self,
        migrated_instance: Instance,
        migrated_instance_data: ProfileInfo,
        order_matters: bool,
        activate_new_instance: bool,
    ) -> None:
        profile_data: dict[str, Any] = self.__level_db.load(
            f"persistent###profiles###{migrated_instance_data.id}"
        )
        profile_data.setdefault("features", {})["local_game_settings"] = (
            migrated_instance.separate_ini_files
        )
        profile_data["features"]["local_saves"] = migrated_instance.separate_save_games
        self.__level_db.dump(profile_data)

        # Set file overrides
        self.__set_file_overrides(
            migrated_instance.mods,
            migrated_instance_data.game,
            migrated_instance.game_folder,
        )

        if activate_new_instance:
            # Activate new profile
            key: str = "settings###profiles###activeProfileId"
            self.__level_db.set_key(key, migrated_instance_data.id)

            # Set last active profile
            key = "settings###profiles###lastActiveProfile###"
            key += migrated_instance_data.game.id.lower()
            self.__level_db.set_key(key, migrated_instance_data.id)

        self.__level_db.del_symlink_path()

    @override
    def get_completed_message(self, migrated_instance_data: ProfileInfo) -> str:
        text: str = ""

        if self.is_deployed(migrated_instance_data.game):
            text = self.tr(
                "Vortex is currently deployed to the game folder. "
                "It is strongly recommended to purge the game directory "
                "before using the migrated instance."
            )

        return text

    @override
    def get_mods_path(self, instance_data: ProfileInfo) -> Path:
        return self.__get_staging_folder(instance_data.game)

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

    @staticmethod
    def format_utc_timestamp(timestamp: float) -> str:
        """
        Formats a timestamp to a UTC string suffixed by a "Z" for insertion
        into the Vortex database.

        Args:
            timestamp (float): Unix timestamp (seconds since epoch)

        Returns:
            str: UTC string in ISO format
        """

        return (
            datetime.datetime.fromtimestamp(
                timestamp, datetime.timezone.utc
            ).isoformat()[:-6]  # remove timezone, Vortex doesn't want it
            + "Z"
        )

    @staticmethod
    def format_unix_timestamp(timestamp: float) -> int:
        """
        Formats a Unix timestamp for the Vortex database.

        Args:
            timestamp (float): Unix timestamp

        Returns:
            int: Formatted timestamp with 3 decimal places without decimal point
        """

        return int(str(round(timestamp, 3)).replace(".", ""))

    @staticmethod
    def generate_id(length: int = 9) -> str:
        """
        Generates a unique id for a new profile or tool.

        Args:
            length (int): The length of the generated profile/tool id

        Returns:
            str: The generated profile/tool id
        """

        return "".join(
            [random.choice(string.ascii_letters + string.digits) for _ in range(length)]
        )
