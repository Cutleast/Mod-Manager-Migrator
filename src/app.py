"""
Copyright (c) Cutleast
"""

import shutil
from argparse import Namespace
from pathlib import Path
from typing import Optional, cast, override

from cutleast_core_lib.base_app import BaseApp
from cutleast_core_lib.core.config.app_config import AppConfig as BaseAppConfig
from cutleast_core_lib.core.utilities.env_resolver import resolve
from cutleast_core_lib.core.utilities.qt_res_provider import read_resource
from cutleast_core_lib.core.utilities.singleton import Singleton
from mod_manager_lib.core.game_service import GameService
from PySide6.QtCore import QTranslator
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow

from core.config.app_config import AppConfig
from core.utilities.localisation import Language, detect_system_locale
from ui.main_window import MainWindow
from ui.utilities.theme_manager import ThemeManager


class App(BaseApp, Singleton):
    """
    Main application class.
    """

    APP_NAME: str = "Mod Manager Migrator"
    APP_VERSION: str = "development"

    def __init__(self, args: Namespace) -> None:
        Singleton.__init__(self)
        super().__init__(args)

    @override
    def _init(self) -> None:
        self.setApplicationName(App.APP_NAME)
        self.setApplicationVersion(App.APP_VERSION)
        self.setWindowIcon(QIcon(":/icons/mmm.ico"))

        super()._init()

    @override
    def _load_app_config(self) -> BaseAppConfig:
        return AppConfig.load(self.config_path)

    @override
    def _init_main_window(self) -> QMainWindow:
        self.__load_translation()

        GameService(read_resource(":/games.json"))

        return MainWindow(cast(AppConfig, self.app_config))

    def __load_translation(self) -> None:
        """
        Loads translation for the configured language and installs the translator into
        the app.
        """

        translator = QTranslator(self)

        app_config: AppConfig = cast(AppConfig, self.app_config)

        language: str
        if app_config.language == Language.System:
            language = detect_system_locale() or "en_US"
        else:
            language = app_config.language.value

        if language != "en_US":
            res_file: str = f":/loc/{language}.qm"
            if not translator.load(res_file):
                self.log.error(
                    f"Failed to load localisation for {language} from '{res_file}'."
                )
            else:
                self.installTranslator(translator)
                self.log.info(f"Loaded localisation for {language}.")

    @override
    def exec(self) -> int:
        self.__clean_old_data()

        return super().exec()

    def __clean_old_data(self) -> None:
        """
        Cleans up the data folder of older MMM versions.
        """

        old_data_path: Path = resolve(Path("%APPDATA%")) / "Mod Manager Migrator"
        if old_data_path.is_dir():
            shutil.rmtree(old_data_path)
            self.log.info("Deleted old data folder.")

    @override
    def _get_theme_manager(self) -> ThemeManager:
        return ThemeManager(
            self.app_config.accent_color,
            self.app_config.ui_mode,
            [":/fonts/BebasNeue Book.otf"],
        )

    @override
    @classmethod
    def get_repo_owner(cls) -> Optional[str]:
        return "Cutleast"

    @override
    @classmethod
    def get_repo_name(cls) -> Optional[str]:
        return "Mod-Manager-Migrator"

    @override
    @classmethod
    def get_repo_branch(cls) -> Optional[str]:
        return "main"
