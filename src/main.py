"""
Name: Mod Manager Migrator
Author: Cutleast
Python Version: 3.11.2
Qt Version: 6.6.1
License: Attribution-NonCommercial-NoDerivative 4.0 International
"""

import argparse
import ctypes
import json
import logging
import os
import platform
import shutil
import sys
import time
import traceback
from datetime import datetime
from locale import getlocale
from pathlib import Path
from shutil import disk_usage
from winsound import MessageBeep as alert

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw


class MainApp(qtw.QApplication):
    """
    Main application class for ui.
    """

    theme_change_sign = qtc.Signal()
    migrate_mods_change_sign = qtc.Signal()

    loc: "utils.Localisator" = None

    def __init__(self):
        super().__init__([])

        # Initialize variables #######################################
        with open(".\\data\\version", "r", encoding="utf8") as file:
            self.version = file.read().strip()
        self.name = "Mod Manager Migrator"
        # check if compiled with nuitka (or in general)
        self.compiled = bool(
            ("__compiled__" in globals()) or (sys.argv[0].endswith(".exe"))
        )
        self.source: str = None  # has to be in SUPPORTED_MODMANAGERS
        self.destination: str = None  # has to be in SUPPORTED_MODMANAGERS
        self.src_modinstance: managers.ModInstance = None
        self.dst_modinstance: managers.ModInstance = None
        self.game: str = None  # has to be in SUPPORTED_GAMES
        self.game_instance: games.GameInstance = None
        self.mode: str = "hardlink"  # 'copy' or 'hardlink'
        self._details = False  # details variable for error message box
        self.fspace = 0  # free space
        self.rspace = 0  # required space
        self.src_widget: qtw.QWidget = None  # widget for source details
        self.dst_widget: qtw.QWidget = None  # widget for destination details
        self.start_date = time.strftime("%d.%m.%Y")
        self.start_time = time.strftime("%H:%M:%S")
        self.os_type = str("linux" if "Linux" in platform.system() else "windows")
        print(f"Current datetime: {self.start_date} {self.start_time}")

        self.cur_path = (  # Get path of executable/script depending on building status
            Path(sys.executable).parent.resolve()
            if getattr(sys, "frozen", False)
            else Path(__file__).parent.resolve()
        )
        self.app_path = Path(os.getenv("APPDATA")) / self.name
        self.con_path = self.app_path / "config.json"
        self.res_path = self.cur_path / "data"
        self.ico_path = self.res_path / "icons"
        self.qss_path = self.res_path / "style.qss"
        _buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, _buf)
        self.doc_path = Path(_buf.value)

        self.log_name = time.strftime("%d.%m.%Y-%H.%M.%S.log")
        self.log_path = self.app_path / "logs" / self.log_name
        if not self.app_path.is_dir():
            os.mkdir(self.app_path)
        if not self.log_path.parent.is_dir():
            os.mkdir(self.log_path.parent)
        self.protocol = ""

        self.default_conf = {
            "keep_logs_num": 5,  # Only keep 5 newest log files and delete rest
            "log_level": "debug",
            "ui_mode": "System",
            "language": "System",
            "accent_color": "#d78f46",
            "default_game": None,
        }

        # Create or load config file #################################
        try:
            # load config
            with open(self.con_path, "r", encoding="utf8") as file:
                config: dict = json.load(file)

            # Remove deprecated/unsupported settings
            if any(key not in self.default_conf for key in config):
                for key in config.copy():
                    if key not in self.default_conf:
                        config.pop(key)

            self.config = self.default_conf | config
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            # apply default config
            self.config = self.default_conf

            # save default config to config file
            with open(self.con_path, "w", encoding="utf8") as conffile:
                json.dump(self.config, conffile, indent=4)

        # Set up protocol structure ##################################
        self.log = logging.getLogger()
        log_fmt = "[%(asctime)s.%(msecs)03d]"
        log_fmt += "[%(levelname)s]"
        log_fmt += "[%(threadName)s.%(name)s.%(funcName)s]: "
        log_fmt += "%(message)s"
        self.log_fmt = logging.Formatter(log_fmt, datefmt="%d.%m.%Y %H:%M:%S")
        self.stdout = utils.StdoutPipe(self)
        self.log_str = logging.StreamHandler(self.stdout)
        self.log_str.setFormatter(self.log_fmt)
        self.log.addHandler(self.log_str)
        self.log_level = getattr(  # get log level integer from name
            logging, self.config["log_level"].upper(), 20  # info level
        )
        self.log.setLevel(self.log_level)
        sys.excepthook = self.handle_exception

        # Parse commandline arguments ################################
        help_msg = f"{self.name} v{self.version} by Cutleast"
        executable = Path(sys.executable)
        if self.compiled:
            parser = argparse.ArgumentParser(prog=executable.name, description=help_msg)
        else:
            parser = argparse.ArgumentParser(
                prog=f"{executable.name} {__file__}", description=help_msg
            )
        parser.add_argument(  # log level
            "-l",
            "--log-level",
            help="Specify logging level.",
            choices=list(utils.LOG_LEVELS.values()),
        )
        self.args = parser.parse_args()
        if self.args.log_level:
            self.log_level = getattr(  # log level integer from name
                logging, self.args.log_level.upper(), 20  # info level
            )
            self.log_str.setLevel(self.log_level)
            self.log.setLevel(self.log_level)

        # Start by logging basic information #########################
        width = 100
        log_title = self.name.center(width, "=")
        self.log.info(f"\n{'=' * width}\n{log_title}\n{'=' * width}")
        self.log.info("Starting program...")
        self.log.info(f"{'Program version':22}: {self.version}")
        self.log.info(f"{'Executable name':22}: {sys.executable}")
        self.log.info(f"{'Executable path':22}: {self.cur_path}")
        self.log.debug(f"{'Compiled':21}: {self.compiled}")
        self.log.info(f"{'Command line arguments':22}: {sys.argv}")
        self.log.info(f"{'Resource path':22}: {self.res_path}")
        self.log.info(f"{'Config path':22}: {self.con_path}")
        self.log.info(f"{'Log path':22}: {self.log_path}")
        self.log.info(f"{'Log level':22}: {utils.LOG_LEVELS[self.log.level]}")
        self.log.info(f"{'UI mode':22}: {self.config['ui_mode']}")
        self.log.info(f"{'System language':22}: {getlocale()[0]}")
        self.log.debug(
            f"{'Detected platform':21}: \
{platform.system()} \
{platform.version()} \
{platform.architecture()[0]}"
        )

        # Load language strings ######################################
        self.load_lang()

        # Initalize Qt App and Main Window ###########################
        self.setApplicationName(self.name)
        self.setApplicationDisplayName(f"{self.name} v{self.version}")
        self.setApplicationVersion(self.version)
        self.setWindowIcon(qtg.QIcon(str(self.ico_path / "mmm.svg")))

        self._theme = utils.Theme(self)
        self._theme.set_mode(self.config["ui_mode"])
        self.theme = self._theme.load_theme()
        self.theme["accent_color"] = self.config["accent_color"]
        self.stylesheet = self._theme.load_stylesheet()
        self.setStyleSheet(self.stylesheet)

        self.root = qtw.QMainWindow()
        self.root.setObjectName("root")
        self.root.setWindowTitle(f"{self.name} v{self.version}")

        # Fix link color
        palette = self.palette()
        palette.setColor(
            palette.ColorRole.Link, qtg.QColor(self.config["accent_color"])
        )
        self.setPalette(palette)

        # Initialize main user interface #############################
        # Create menu bar
        # Create file menu actions
        self.exit_action = qtg.QAction(self.loc.main.exit, self.root)

        # Create file menu
        self.file_menu = qtw.QMenu()
        self.file_menu.setTitle(self.loc.main.file)
        self.file_menu.setWindowFlags(
            qtc.Qt.WindowType.FramelessWindowHint
            | qtc.Qt.WindowType.Popup
            | qtc.Qt.WindowType.NoDropShadowWindowHint
        )
        self.file_menu.setAttribute(
            qtc.Qt.WidgetAttribute.WA_TranslucentBackground, on=True
        )
        self.file_menu.setStyleSheet(self.stylesheet)
        self.file_menu.addAction(self.exit_action)
        self.exit_action.triggered.connect(self.root.close)
        self.root.menuBar().addMenu(self.file_menu)

        # Create help menu actions
        self.config_action = qtg.QAction(self.loc.main.settings, self)
        self.log_action = qtg.QAction(self.loc.main.open_log_file, self)
        self.exception_test_action = qtg.QAction("Exception test", self)
        self.about_action = qtg.QAction(self.loc.main.about, self)
        self.about_qt_action = qtg.QAction(f"{self.loc.main.about} Qt", self)

        # Create help menu
        self.help_menu = qtw.QMenu()
        self.help_menu.setTitle(self.loc.main.help)
        self.help_menu.setWindowFlags(
            qtc.Qt.WindowType.FramelessWindowHint
            | qtc.Qt.WindowType.Popup
            | qtc.Qt.WindowType.NoDropShadowWindowHint
        )
        self.help_menu.setAttribute(
            qtc.Qt.WidgetAttribute.WA_TranslucentBackground, on=True
        )
        self.help_menu.setStyleSheet(self.stylesheet)
        self.help_menu.addAction(self.config_action)
        self.help_menu.addAction(self.log_action)

        # uncomment this to test error messages
        # self.help_menu.addAction(self.exception_test_action)

        self.help_menu.addSeparator()
        self.help_menu.addAction(self.about_action)
        self.help_menu.addAction(self.about_qt_action)
        self.config_action.triggered.connect(
            lambda: dialogs.SettingsDialog(self.root, self)
        )
        self.log_action.triggered.connect(lambda: os.startfile(self.log_path))

        def test_exception():
            raise Exception("Test exception")

        self.exception_test_action.triggered.connect(test_exception)
        self.about_action.triggered.connect(self.show_about_dialog)
        self.about_qt_action.triggered.connect(self.show_about_qt_dialog)
        self.root.menuBar().addMenu(self.help_menu)

        # Create main frame with main layout
        self.mainframe = qtw.QWidget()
        self.mainlayout = qtw.QGridLayout()
        self.mainlayout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.mainlayout.setRowStretch(1, 1)
        self.mainlayout.setRowStretch(0, 0)
        self.mainlayout.setColumnStretch(0, 1)
        self.mainlayout.setColumnStretch(2, 1)
        self.mainframe.setLayout(self.mainlayout)
        self.root.setCentralWidget(self.mainframe)

        # Create source button
        self.src_button = qtw.QPushButton(self.loc.main.select_source)
        self.src_button.clicked.connect(
            lambda: dialogs.SourceDialog(self.root, self).show()
        )
        self.mainlayout.addWidget(self.src_button, 0, 0)

        # Add game icon
        self.game_icon = qtw.QLabel()
        # self.game_icon.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        # size = qtc.QSize(120, 120)
        # self.game_icon.resize(size)
        # self.game_icon.setFixedSize(size)
        # self.game_icon.setScaledContents(True)
        # self.mainlayout.addWidget(self.game_icon, 0, 1)

        # Create migrate button
        self.mig_button = qtw.QPushButton(self.loc.main.migrate)
        self.mig_button.setIcon(
            qta.icon("fa5s.chevron-right", color=self.theme["text_color"])
        )
        self.mig_button.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
        self.mig_button.clicked.connect(self.migrate)
        self.mig_button.setDisabled(True)
        self.mainlayout.addWidget(self.mig_button, 0, 1)

        # Create destination button
        self.dst_button = qtw.QPushButton(self.loc.main.select_destination)
        self.dst_button.clicked.connect(
            lambda: dialogs.DestinationDialog(self.root, self).show()
        )
        self.dst_button.setDisabled(True)
        self.mainlayout.addWidget(self.dst_button, 0, 2)

        # Add right arrow icon
        self.mig_icon = qtw.QLabel()
        self.mig_icon.setPixmap(
            qta.icon("fa5s.chevron-right", color=self.theme["text_color"]).pixmap(
                120, 120
            )
        )
        self.mainlayout.addWidget(self.mig_icon, 1, 1)

        # Show window maximized
        # self.root.resize(1000, 600)
        self.root.showMaximized()

        # Check for updates
        if (new_version := utils.get_latest_version()) > float(self.version):
            self.log.info(
                f"A new version is available to download: \
Current version: {self.version} | Latest version: {new_version}"
            )

            message_box = qtw.QMessageBox(self.root)
            message_box.setWindowIcon(self.root.windowIcon())
            message_box.setStyleSheet(self.stylesheet)
            message_box.setWindowTitle(self.name)
            message_box.setText(
                self.loc.main.update_available.replace(
                    "[OLD_VERSION]", self.version
                ).replace("[NEW_VERSION]", str(new_version))
            )
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.No | qtw.QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.Yes)
            message_box.button(qtw.QMessageBox.StandardButton.Yes).setText(
                self.loc.main.yes
            )
            message_box.button(qtw.QMessageBox.StandardButton.No).setText(
                self.loc.main.no
            )
            choice = message_box.exec()

            # Handle the user's choice
            if choice == qtw.QMessageBox.StandardButton.Yes:
                # Open nexus mods file page
                os.startfile("https://www.nexusmods.com/site/mods/545?tab=files")
        elif new_version == 0.0:
            self.log.error("Failed to check for update.")
        else:
            self.log.info("No update available.")

        # Show game dialog
        for game in games.GAMES:
            if game(self).name == self.config["default_game"]:
                game = game(self)
                game.get_install_dir()
                self.game_instance = game
                self.game = self.game_instance.id
                icon = qtg.QPixmap(self.ico_path / self.game_instance.icon_name)
                self.game_icon.setPixmap(icon)
                self.log.info(f"Current game: {game.name}")
                break
        else:
            dialogs.GameDialog(self.root, self).show()

    def __repr__(self):
        return "MainApp"

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Processes uncatched exceptions and shows them in a QMessageBox.
        """

        # Pass through if exception is KeyboardInterrupt
        # for eg. CTRL+C
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        uiexception = issubclass(exc_type, utils.UiException)

        # Handle ui exceptions seperately
        if uiexception:
            self.log.error(f"An error occured: {exc_value}")

            # Get translation if available
            error_type = str(exc_value)
            error_type = error_type.strip("[")
            error_type, error_msg = error_type.split("]", 1)
            error_msg = getattr(self.loc.main, error_type, error_msg).strip()
            detailed_msg = ""
            yesno = False

        # Show normal uncatched exceptions
        else:
            tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            # Remove dev environment paths from traceback
            # cx_freeze, why ever, keeps them when building
            tb = tb.replace(
                "C:\\Users\\robin\\OneDrive\\Development\\SSE-Auto-Translator\\src\\",
                "",
            )
            self.log.critical("An uncaught exception occured:\n" + tb)

            # Get exception info
            error_msg = f"{self.loc.main.error_text} {exc_value}"
            detailed_msg = tb
            yesno = True

        # Create error messagebox
        messagebox = dialogs.ErrorDialog(
            parent=self.root,
            app=self,
            title=self.loc.main.error,
            text=error_msg,
            details=detailed_msg,
            yesno=yesno,
        )

        # Play system alarm sound
        alert()

        choice = messagebox.exec()

        if choice == qtw.QMessageBox.StandardButton.No:
            self.root.close()

    # Core function to migrate #######################################
    def migrate(self):
        """
        Main migration method.
        """

        self.log.info(f"Migrating instance from {self.source} to {self.destination}...")
        self.log.debug(f"Mode: {self.mode}")

        # Only continue if there is a valid game path
        self.game_instance.get_install_dir()

        # Calculate free and required disk space if copy mode
        if self.mode == "copy":
            self.fspace = 0  # free space
            self.rspace = 0  # required space

            # Get free space on destination drive
            self.fspace = disk_usage(self.dst_modinstance.mods_path.drive)[2]

            # Get required space by source instance
            self.rspace = self.src_modinstance.size

            self.log.debug(
                f"Free space: \
{utils.scale_value(self.fspace)} \
| Required space: {utils.scale_value(self.rspace)}"
            )

            # Check if there is enough free space
            if self.fspace <= self.rspace:
                self.log.error("Migration failed: not enough free space!")
                qtw.QMessageBox.critical(
                    self.root,
                    self.loc.main.error,
                    self.loc.main.enough_space_text.replace(
                        "FREE_SPACE", utils.scale_value(self.fspace)
                    ).replace("REQUIRED_SPACE", utils.scale_value(self.rspace)),
                )
                return

        # Wipe folders if they already exist
        if self.destination == "ModOrganizer":
            appdata_path = Path(os.getenv("LOCALAPPDATA"))
            appdata_path = appdata_path / "ModOrganizer"
            appdata_path = appdata_path / self.dst_modinstance.name
            instance_path = self.dst_modinstance.mods_path.parent

            # Wipe instance from MO2
            if appdata_path.is_dir():
                if list(appdata_path.iterdir()):
                    self.log.debug("Wiping existing instance...")

                    appdata_path = f"\\\\?\\{appdata_path}"

                    def process(ldialog: widgets.LoadingDialog):
                        ldialog.updateProgress(text1=self.loc.main.wiping_instance)

                        shutil.rmtree(appdata_path)

                    loadingdialog = widgets.LoadingDialog(
                        parent=self.root, app=self, func=process
                    )
                    loadingdialog.exec()

                    self.log.debug("Instance wiped.")

            # Wipe instance data
            if instance_path.is_dir():
                if list(instance_path.iterdir()):
                    self.log.debug("Wiping existing instance data...")

                    instance_path = f"\\\\?\\{instance_path}"

                    def process(ldialog: widgets.LoadingDialog):
                        ldialog.updateProgress(text1=self.loc.main.wiping_instance_data)

                        shutil.rmtree(instance_path)

                    loadingdialog = widgets.LoadingDialog(
                        parent=self.root, app=self, func=process
                    )
                    loadingdialog.exec()

                    self.log.debug("Instance data wiped.")

        # Transfer mods
        self.dst_modinstance.mods = self.src_modinstance.mods
        self.dst_modinstance.modfiles = self.src_modinstance.modfiles

        # Transfer loadorder
        self.dst_modinstance.loadorder = self.src_modinstance.loadorder

        # Transfer file conflicts
        self.src_modinstance.get_file_conflicts()
        self.dst_modinstance.set_file_conflicts()

        # Set up destination instance
        self.dst_modinstance.setup_instance()

        # Check for files that have to be copied
        # directly into the game folder
        # since MO2 cannot manage those
        if self.src_modinstance.root_mods:
            message_box = qtw.QMessageBox(self.root)
            message_box.setWindowIcon(self.root.windowIcon())
            message_box.setStyleSheet(self.stylesheet)
            message_box.setWindowTitle(self.loc.main.migrating_instance)
            message_box.setText(self.loc.main.detected_root_files)
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.Ignore
                | qtw.QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.Yes)
            ignore_button = message_box.button(qtw.QMessageBox.StandardButton.Ignore)
            ignore_button.setText(self.loc.main.ignore)
            continue_button = message_box.button(qtw.QMessageBox.StandardButton.Yes)
            continue_button.setText(self.loc.main._continue)

            # Wait for purge if source is Vortex
            if self.source == "Vortex":
                timer = qtc.QTimer()
                timer.setInterval(1000)
                deploy_file = (
                    self.src_modinstance.mods_path / "vortex.deployment.msgpack"
                )
                continue_button.setDisabled(deploy_file.is_file())

                def check_purged():
                    if message_box is not None:
                        if deploy_file.is_file():
                            timer.start()
                        else:
                            continue_button.setDisabled(False)

                timer.timeout.connect(check_purged)
                timer.start()

            choice = message_box.exec()
            message_box = None

            if choice == qtw.QMessageBox.StandardButton.Yes:
                # Copy root files directly into game directory
                def process(ldialog: widgets.LoadingDialog):
                    ldialog.updateProgress(text1=self.loc.main.copying_files)

                    installdir = self.game_instance.get_install_dir()
                    for i, mod in enumerate(self.src_modinstance.root_mods):
                        ldialog.updateProgress(
                            text1=f"{self.loc.main.copying_files} \
- {i}/{len(self.src_modinstance.root_mods)}",
                            value1=i,
                            max1=len(self.src_modinstance.root_mods),
                            show2=True,
                            text2=mod.metadata["name"],
                        )

                        src_path = mod.path
                        dst_path = installdir

                        try:
                            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                        except shutil.Error as ex:
                            self.log.error(
                                f"Failed to copy following files/folders: {ex}"
                            )

                loadingdialog = widgets.LoadingDialog(
                    parent=self.root, app=self, func=process
                )
                loadingdialog.exec()

        # Get start time for performance measurement
        starttime = time.time()

        # Copy mods to new instance
        loadingdialog = widgets.LoadingDialog(
            parent=self.root,
            app=self,
            func=self.dst_modinstance.copy_mods,
        )
        loadingdialog.exec()

        # Copy additional files like 'loadorder.txt', 'plugins.txt'
        self.dst_modinstance.copy_files()

        # Copy downloads if given to new instance
        # Work in progress!

        self.log.info("Migration complete.")
        dur = time.time() - starttime
        self.log.debug(
            f"Migration took: {dur:.2f} second(s) ({(dur / 60):.2f} minute(s))"
        )

        deploy_file = self.src_modinstance.mods_path / "vortex.deployment.msgpack"
        if self.source == "Vortex" and deploy_file.is_file():
            qtw.QMessageBox.information(
                self.root,
                self.loc.main.success,
                self.loc.main.migration_complete_purge_notice,
            )
        else:
            qtw.QMessageBox.information(
                self.root, self.loc.main.success, self.loc.main.migration_complete
            )

    ##################################################################

    def set_mode(self, mode: str):
        """
        Sets ui mod to mode. 'Light' or 'Dark'
        """

        self.mode = mode

    def show_about_dialog(self):
        """
        Displays about dialog.
        """

        dialog = qtw.QMessageBox(self.root)
        icon = self.root.windowIcon()
        pixmap = icon.pixmap(128, 128)
        dialog.setIconPixmap(pixmap)
        dialog.setWindowTitle(self.loc.main.about)
        dialog.setWindowIcon(self.root.windowIcon())
        dialog.setTextFormat(qtc.Qt.TextFormat.RichText)
        text = self.loc.main.about_text

        # Add translator credit if available
        if self.loc.main.translator_url.startswith("http"):
            text += "<br><br>Translation by "
            text += f"<a href='{self.loc.main.translator_url}'>"
            text += f"{self.loc.main.translator_name}</a>"

        dialog.setText(text)
        dialog.setStandardButtons(qtw.QMessageBox.StandardButton.Ok)

        # hacky way to set label width
        for label in dialog.findChildren(qtw.QLabel):
            if label.text() == self.loc.main.about_text:
                label.setFixedWidth(400)
                break

        dialog.exec()

    def show_about_qt_dialog(self):
        """
        Displays about Qt dialog.
        """

        qtw.QMessageBox.aboutQt(self.root, f"{self.loc.main.about} Qt")

    def exec(self):
        """
        Executes Qt application.
        """

        super().exec()

        # Exit and clean up
        self.log.info("Exiting program...")
        if self.config["keep_logs_num"] >= 0:
            while (
                len(log_files := os.listdir(self.log_path.parent))
                > self.config["keep_logs_num"]
            ):

                def func(name: str):
                    if name.startswith(self.name):
                        return datetime.strptime(name, f"{self.name}_%d.%m.%Y_-_%H.%M.%S.log")
                    else:
                        return datetime.strptime(name, "%d.%m.%Y-%H.%M.%S.log")

                log_files.sort(key=func)
                os.remove(self.log_path.parent / log_files[0])

    def load_lang(self, language=None):
        """
        Loads localisation strings from <language>.

        Falls back to english strings if localisation is outdated.
        """

        # Get language strings
        if not language:
            language = self.config["language"]

        self.loc = utils.Localisator(language, self.res_path / "locales")
        self.loc.load_lang()

        self.log.info(f"{'Program language':21}: {language}")


if __name__ == "__main__":
    import dialogs
    import games as games
    import managers as managers
    import utilities as utils
    import widgets

    mainapp = MainApp()
    mainapp.exec()
