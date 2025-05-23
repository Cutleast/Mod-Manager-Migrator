"""
Copyright (c) Cutleast
"""

import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from argparse import Namespace
from pathlib import Path
from typing import override

from PySide6.QtCore import QTranslator
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

import resources_rc  # type: ignore # noqa: F401
from core.config.app_config import AppConfig
from core.utilities.env_resolver import resolve
from core.utilities.exception_handler import ExceptionHandler
from core.utilities.filesystem import get_documents_folder
from core.utilities.localisation import Language, detect_system_locale
from core.utilities.logger import Logger
from core.utilities.path_limit_fixer import PathLimitFixer
from core.utilities.updater import Updater
from ui.main_window import MainWindow
from ui.utilities.stylesheet_processor import StylesheetProcessor
from ui.utilities.ui_mode import UIMode


class App(QApplication):
    """
    Main application class.
    """

    APP_NAME: str = "Mod Manager Migrator"
    APP_VERSION: str = "development"

    args: Namespace
    app_config: AppConfig

    cur_path: Path = Path.cwd()
    data_path: Path = cur_path / "data"
    res_path: Path = cur_path / "res"
    config_path: Path = data_path / "config"

    log: logging.Logger = logging.getLogger("App")
    logger: Logger
    log_path: Path = data_path / "logs"

    main_window: MainWindow
    stylesheet_processor: StylesheetProcessor
    exception_handler: ExceptionHandler

    doc_path: Path

    def __init__(self, args: Namespace) -> None:
        super().__init__()

        self.args = args

    def init(self) -> None:
        """
        Initializes application.
        """

        self.app_config = AppConfig.load(self.config_path)
        self.doc_path = get_documents_folder()

        log_file: Path = self.log_path / time.strftime(self.app_config.log_file_name)
        self.logger = Logger(
            log_file, self.app_config.log_format, self.app_config.log_date_format
        )
        self.logger.setLevel(self.app_config.log_level)

        self.setApplicationName(App.APP_NAME)
        self.setApplicationDisplayName(f"{App.APP_NAME} v{App.APP_VERSION}")
        self.setApplicationVersion(App.APP_VERSION)
        self.setWindowIcon(QIcon(":/icons/mmm.ico"))
        self.load_translation()

        ui_mode: UIMode = UIMode.get(self.app_config.ui_mode, UIMode.System)
        self.stylesheet_processor = StylesheetProcessor(self, ui_mode)
        self.exception_handler = ExceptionHandler(self)
        self.main_window = MainWindow(self.app_config)

        self.log_basic_info()
        self.app_config.print_settings_to_log()
        self.log.info("App started.")

    def log_basic_info(self) -> None:
        """
        Logs basic information.
        """

        width = 100
        log_title = f" {App.APP_NAME} ".center(width, "=")
        self.log.info(f"\n{'=' * width}\n{log_title}\n{'=' * width}")
        self.log.info(f"Program Version: {App.APP_VERSION}")
        self.log.info(f"Executed command: {subprocess.list2cmdline(sys.argv)}")
        self.log.info(f"Current Path: {self.cur_path}")
        self.log.info(f"Resource Path: {self.res_path}")
        self.log.info(f"Data Path: {self.data_path}")
        self.log.info(f"Log Path: {self.log_path}")
        self.log.info(
            "Detected Platform: "
            f"{platform.system()} {platform.version()} {platform.architecture()[0]}"
        )

    def load_translation(self) -> None:
        """
        Loads translation for the configured language
        and installs the translator into the app.
        """

        translator = QTranslator(self)

        language: str
        if self.app_config.language == Language.System:
            language = detect_system_locale() or "en_US"
        else:
            language = self.app_config.language.value

        if language != "en_US":
            translator.load(f":/loc/{language}.qm")
            self.installTranslator(translator)

            self.log.info(f"Loaded localisation for {language}.")

    @override
    def exec(self) -> int:
        """
        Executes application and shows main window.
        """

        self.__clean_old_data()

        try:
            Updater(self.APP_VERSION).run()
        except Exception as ex:
            self.log.warning(f"Failed to check for updates: {ex}", exc_info=ex)

        self.main_window.show()
        self.detect_path_limit()

        retcode: int = super().exec()

        self.clean()

        self.log.info("Exiting application...")

        return retcode

    def __clean_old_data(self) -> None:
        """
        Cleans up the data folder of older MMM versions.
        """

        old_data_path: Path = resolve(Path("%APPDATA%")) / "Mod Manager Migrator"
        if old_data_path.is_dir():
            shutil.rmtree(old_data_path)
            self.log.info("Deleted old data folder.")

    def detect_path_limit(self) -> None:
        """
        Detects if the NTFS path length limit is enabled
        and asks if the user wants to disable it.
        """

        path_limit_enabled: bool = PathLimitFixer.is_path_limit_enabled()
        self.log.info(f"Path length limit enabled: {path_limit_enabled}")

        if path_limit_enabled:
            reply = QMessageBox.question(
                self.main_window,
                self.tr("Path Limit Enabled"),
                self.tr(
                    "The NTFS path length limit is enabled and paths longer than 255 "
                    "characters will cause issues. Would you like to disable it "
                    "(admin rights may be required)? "
                    "A reboot is required for this to take effect."
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                PathLimitFixer.disable_path_limit(self.res_path)

    def clean(self) -> None:
        """
        Cleans up and exits application.
        """

        self.log.info("Cleaning...")

        # Clean up log files
        self.logger.clean_log_folder(
            self.log_path,
            self.app_config.log_file_name,
            self.app_config.log_num_of_files,
        )

    def restart_application(self) -> None:
        """
        Restarts the application.
        """

        self.log.info("Restarting application...")

        os.startfile(subprocess.list2cmdline(sys.argv))

        self.exit()
