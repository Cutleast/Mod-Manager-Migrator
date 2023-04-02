"""
Name: Mod Manager Migrator
Author: Cutleast
Python Version: 3.9.13
Qt Version: 6.4.3
Type: Main File
License: Attribution-NonCommercial-NoDerivative 4.0 International (see repo for more info)
"""

# Import libraries ###################################################
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
from winsound import MessageBeep as alert
from locale import getlocale
from pathlib import Path
from shutil import disk_usage
from typing import Dict

import darkdetect
import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

# Constant variables #################################################
LOG_LEVELS = {
    10: "debug",                        # DEBUG
    20: "info",                         # INFO
    30: "warning",                      # WARNING
    40: "error",                        # ERROR
    50: "critical"                      # CRITICAL
}
SUPPORTED_MODMANAGERS = [
    "Vortex",
    "ModOrganizer"
]
SUPPORTED_GAMES = [
    "SkyrimSE",
    "Skyrim",
    "Fallout4",
    "EnderalSE",
    "Enderal"
]


# Create class for main application ##################################
class MainApp(qtw.QApplication):
    """
    Main application class for ui.
    """

    theme_change_sign = qtc.Signal()
    migrate_mods_change_sign = qtc.Signal()

    def __init__(self):
        super().__init__([])

        # Initialize variables #######################################
        with open(".\\data\\version", 'r', encoding='utf8') as file:
            self.version = file.read().strip()
        self.name = "Mod Manager Migrator"
        # check if compiled with nuitka (or in general)
        self.compiled = bool(
            ("__compiled__" in globals())
            or (sys.argv[0].endswith('.exe'))
        )
        self.exception: bool = False # will be set to True if an uncatched exception occurs
        self.source: str = None # has to be in SUPPORTED_MODMANAGERS
        self.destination: str = None # has to be in SUPPORTED_MODMANAGERS
        self.src_modinstance: managers.ModInstance = None
        self.dst_modinstance: managers.ModInstance = None
        self.game: str = None # has to be in SUPPORTED_GAMES
        self.game_instance: games.GameInstance = None
        self.mode: str = 'hardlink' # 'copy' or 'hardlink'
        self._details = False # details variable for error message box
        self.fspace = 0 # free space
        self.rspace = 0 # required space
        self.src_widget: qtw.QWidget = None # widget for source details
        self.dst_widget: qtw.QWidget = None # widget for destination details
        self.start_date = time.strftime("%d.%m.%Y")
        self.start_time = time.strftime("%H:%M:%S")
        self.os_type = str(
            "linux"
            if "Linux" in platform.system()
            else "windows"
        )
        print(f"Current datetime: {self.start_date} {self.start_time}")
        # paths
        self.cur_path = Path(__file__).parent
        self.app_path = Path(os.getenv('APPDATA')) / self.name
        self.con_path = self.app_path / 'config.json'
        self.res_path = self.cur_path / 'data'
        self.ico_path = self.res_path / 'icons'
        self.qss_path = self.res_path / 'style.qss'
        _buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, _buf)
        self.doc_path = Path(_buf.value)
        # logging
        self.log_name = f"{self.name}_{self.start_date}_-_{self.start_time.replace(':', '.')}.log"
        self.log_path = self.app_path / 'logs' / self.log_name
        if not self.app_path.is_dir():
            os.mkdir(self.app_path)
        if not self.log_path.parent.is_dir():
            os.mkdir(self.log_path.parent)
        self.protocol = ""
        # config
        self.default_conf = {
            'save_logs': False, 
            'log_level': 'debug',
            'ui_mode': 'System',
            'language': 'System',
            'accent_color': '#d78f46',
            'default_game': None,
        }

        # Create or load config file #################################
        try:
            # load config
            with open(self.con_path, 'r', encoding='utf8') as file:
                config = json.load(file)

            if len(config.keys()) < len(self.default_conf.keys()):
                # update outdated config
                print(
                    "Detected incomplete (outdated) config file. \
Updating with default config..."
                )
                new_keys = [
                    key for key in self.default_conf
                    if key not in config.keys()
                ]
                for key in new_keys:
                    config[key] = self.default_conf[key]

                # try to save updated config to config file
                try:
                    with open(self.con_path, 'w', encoding='utf8') as conffile:
                        json.dump(config, conffile, indent=4)
                    print("Saved updated config to config file.")
                # ignore if access denied by os
                except OSError:
                    print(
                        "Failed to update config file: Access denied."
                    )

            # apply config
            self.config = config
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            # apply default config
            self.config = self.default_conf

            # save default config to config file
            with open(self.con_path, 'w', encoding='utf8') as conffile:
                json.dump(self.config, conffile, indent=4)

        # Set up protocol structure ##################################
        self.log = logging.getLogger(self.__repr__())
        log_fmt = "[%(asctime)s.%(msecs)03d]"
        log_fmt += "[%(levelname)s]"
        log_fmt += "[%(threadName)s.%(name)s.%(funcName)s]: "
        log_fmt += "%(message)s"
        self.log_fmt = logging.Formatter(
            log_fmt,
            datefmt="%d.%m.%Y %H:%M:%S"
        )
        self.stdout = utils.StdoutPipe(self)
        self.log_str = logging.StreamHandler(self.stdout)
        self.log_str.setFormatter(self.log_fmt)
        self.log.addHandler(self.log_str)
        self.log_level = getattr( # get log level integer from name
            logging,
            self.config['log_level'].upper(),
            20 # info level
        )
        self.log.setLevel(self.log_level)
        sys.excepthook = self.handle_exception

        # Parse commandline arguments ################################
        help_msg = f"{self.name} v{self.version} by Cutleast"
        executable = Path(sys.executable)
        if self.compiled:
            parser = argparse.ArgumentParser(
                prog=executable.name,
                description=help_msg
            )
        else:
            parser = argparse.ArgumentParser(
                prog=f"{executable.name} {__file__}",
                description=help_msg
            )
        parser.add_argument( # log level
            "-l",
            "--log-level",
            help="Specify logging level.",
            choices=list(LOG_LEVELS.values())
        )
        parser.add_argument( # keep log
            "--keep-log",
            help="Keep log file. (Overwrites user config.)",
            action="store_true"
        )
        self.args = parser.parse_args()
        if self.args.keep_log:
            self.config['save_logs'] = True
        if self.args.log_level:
            self.log_level = getattr( # log level integer from name
                logging,
                self.args.log_level.upper(),
                20 # info level
            )
            self.log_str.setLevel(self.log_level)
            self.log.setLevel(self.log_level)

        # Start by logging basic information #########################
        #log_title = "-" * 40 + f" {self.name} " + "-" * 40
        width = 100
        log_title = self.name.center(width, '=')
        self.log.info(
            f"\n{'=' * width}\n{log_title}\n{'=' * width}"
        )
        self.log.info("Starting program...")
        self.log.info(f"{'Program version':22}: {self.version}")
        self.log.info(f"{'Executable name':22}: {sys.executable}")
        self.log.info(f"{'Executable path':22}: {self.cur_path}")
        self.log.debug(f"{'Compiled':21}: {self.compiled}")
        self.log.info(f"{'Command line arguments':22}: {sys.argv}")
        self.log.info(f"{'Resource path':22}: {self.res_path}")
        self.log.info(f"{'Config path':22}: {self.con_path}")
        self.log.info(f"{'Log path':22}: {self.log_path}")
        self.log.info(f"{'Log level':22}: {LOG_LEVELS[self.log.level]}")
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
        self.root = qtw.QMainWindow()
        self.root.setObjectName("root")
        self.root.setWindowTitle(self.name)
        self.root.setWindowIcon(qtg.QIcon(os.path.join(
            self.ico_path,
            "mmm.svg"
            ))
        )
        self._theme = Theme(self)
        self._theme.set_mode(self.config['ui_mode'])
        self.theme = self._theme.load_theme()
        self.theme['accent_color'] = self.config['accent_color']
        self.stylesheet = self._theme.load_stylesheet()
        self.root.setStyleSheet(self.stylesheet)

        # Fix link color
        palette = self.palette()
        palette.setColor(
            palette.ColorRole.Link,
            qtg.QColor(self.config['accent_color'])
        )
        self.setPalette(palette)

        # Initialize main user interface #############################
        # Create menu bar
        # Create file menu actions
        self.exit_action = qtg.QAction(self.lang['exit'], self.root)

        # Create file menu
        self.file_menu = qtw.QMenu()
        self.file_menu.setTitle(self.lang['file'])
        self.file_menu.setWindowFlags(
            qtc.Qt.WindowType.FramelessWindowHint
            | qtc.Qt.WindowType.Popup
            | qtc.Qt.WindowType.NoDropShadowWindowHint
        )
        self.file_menu.setAttribute(
            qtc.Qt.WidgetAttribute.WA_TranslucentBackground,
            on=True
        )
        self.file_menu.setStyleSheet(self.stylesheet)
        self.file_menu.addAction(self.exit_action)
        self.exit_action.triggered.connect(self.root.close)
        self.root.menuBar().addMenu(self.file_menu)

        # Create help menu actions
        self.config_action = qtg.QAction(self.lang['settings'], self)
        self.log_action = qtg.QAction(self.lang['open_log_file'], self)
        self.exception_test_action = qtg.QAction("Exception test", self)
        self.about_action = qtg.QAction(self.lang['about'], self)
        self.about_qt_action = qtg.QAction(f"{self.lang['about']} Qt", self)

        # Create help menu
        self.help_menu = qtw.QMenu()
        self.help_menu.setTitle(self.lang['help'])
        self.help_menu.setWindowFlags(
            qtc.Qt.WindowType.FramelessWindowHint
            | qtc.Qt.WindowType.Popup
            | qtc.Qt.WindowType.NoDropShadowWindowHint
        )
        self.help_menu.setAttribute(
            qtc.Qt.WidgetAttribute.WA_TranslucentBackground,
            on=True
        )
        self.help_menu.setStyleSheet(self.stylesheet)
        self.help_menu.addAction(self.config_action)
        self.help_menu.addAction(self.log_action)

        # uncomment this to test error messages
        #self.help_menu.addAction(self.exception_test_action)

        self.help_menu.addSeparator()
        self.help_menu.addAction(self.about_action)
        self.help_menu.addAction(self.about_qt_action)
        self.config_action.triggered.connect(
            lambda: dialogs.SettingsDialog(self.root, self)
        )
        self.log_action.triggered.connect(
            lambda: os.startfile(self.log_path)
        )
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
        self.src_button = qtw.QPushButton(self.lang['select_source'])
        self.src_button.clicked.connect(
            lambda: dialogs.SourceDialog(self.root, self).show()
        )
        self.mainlayout.addWidget(self.src_button, 0, 0)
        
        # Add game icon
        self.game_icon = qtw.QLabel()
        #self.game_icon.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        #size = qtc.QSize(120, 120)
        #self.game_icon.resize(size)
        #self.game_icon.setFixedSize(size)
        #self.game_icon.setScaledContents(True)
        #self.mainlayout.addWidget(self.game_icon, 0, 1)

        # Create migrate button
        self.mig_button = qtw.QPushButton(self.lang['migrate'])
        self.mig_button.setIcon(qta.icon(
            'fa5s.chevron-right',
            color=self.theme['text_color']
            )
        )
        self.mig_button.setLayoutDirection(
            qtc.Qt.LayoutDirection.RightToLeft
        )
        self.mig_button.clicked.connect(self.migrate)
        self.mig_button.setDisabled(True)
        self.mainlayout.addWidget(self.mig_button, 0, 1)

        # Create destination button
        self.dst_button = qtw.QPushButton(self.lang['select_destination'])
        self.dst_button.clicked.connect(
            lambda: dialogs.DestinationDialog(self.root, self).show()
        )
        self.dst_button.setDisabled(True)
        self.mainlayout.addWidget(self.dst_button, 0, 2)

        # Add right arrow icon
        self.mig_icon = qtw.QLabel()
        self.mig_icon.setPixmap(qta.icon(
            'fa5s.chevron-right',
            color=self.theme['text_color']
            ).pixmap(120, 120)
        )
        self.mainlayout.addWidget(self.mig_icon, 1, 1)

        # Show window maximized
        #self.root.resize(1000, 600)
        self.root.showMaximized()

        # Check for updates
        if ((new_version := utils.get_latest_version())
            > float(self.version)):
            self.log.info(
                f"A new version is available to download: \
Current version: {self.version} | Latest version: {new_version}"
            )

            message_box = qtw.QMessageBox(self.root)
            message_box.setWindowIcon(self.root.windowIcon())
            message_box.setStyleSheet(self.stylesheet)
            message_box.setWindowTitle(self.name)
            message_box.setText(
                self.lang['update_available'].replace(
                    "[OLD_VERSION]",
                    self.version
                ).replace(
                    "[NEW_VERSION]",
                    str(new_version)
                )
            )
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.No
                | qtw.QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(
                qtw.QMessageBox.StandardButton.Yes
            )
            message_box.button(
                qtw.QMessageBox.StandardButton.Yes
            ).setText(self.lang['yes'])
            message_box.button(
                qtw.QMessageBox.StandardButton.No
            ).setText(self.lang['no'])
            utils.center(message_box, self.root)
            choice = message_box.exec()

            # Handle the user's choice
            if choice == qtw.QMessageBox.StandardButton.Yes:
                # Open nexus mods file page
                os.startfile(
                    "https://www.nexusmods.com/site/mods/545?tab=files"
                )
        elif new_version == 0.0:
            self.log.error("Failed to check for update.")
        else:
            self.log.info("No update available.")

        # Show game dialog
        for game in games.GAMES:
            if game(self).name == self.config['default_game']:
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
            error_msg = self.lang.get(error_type, error_msg).strip()
            detailed_msg = ""
            yesno = False

        # Show normal uncatched exceptions
        else:
            self.log.critical(
                "An uncaught exception occured:",
                exc_info=(exc_type, exc_value, exc_traceback)
            )

            # Get exception info
            error_msg = f"{self.lang['error_text']} {exc_value}"
            detailed_msg = ''.join(traceback.format_exception(
                    exc_type,
                    exc_value,
                    exc_traceback
                )
            )
            yesno = True

            # Set exception to True
            # to save log file when exit
            # this ignores user configuration
            self.exception = True

        # Create error messagebox
        messagebox = dialogs.ErrorDialog(
            parent=self.root,
            app=self,
            title=f"{self.root.windowTitle()} - {self.lang['error']}",
            text=error_msg,
            details=detailed_msg,
            yesno=yesno
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

        self.log.info(
            f"Migrating instance from {self.source} to {self.destination}..."
        )
        self.log.debug(f"Mode: {self.mode}")

        # Only continue if there is a valid game path
        self.game_instance.get_install_dir()

        # Calculate free and required disk space if copy mode
        if self.mode == 'copy':
            self.fspace = 0 # free space
            self.rspace = 0 # required space
            
            # Get free space on destination drive
            self.fspace = disk_usage(
                self.dst_modinstance.mods_path.drive
            )[2]

            # Get required space by source instance
            self.rspace = self.src_modinstance.size

            self.log.debug(
                f"Free space: \
{utils.scale_value(self.fspace)} \
| Required space: {utils.scale_value(self.rspace)}"
            )

            # Check if there is enough free space
            if self.fspace <= self.rspace:
                self.log.error(
                    "Migration failed: not enough free space!"
                )
                qtw.QMessageBox.critical(
                    self.root,
                    self.lang['error'],
                    self.lang['enough_space_text'].replace(
                        'FREE_SPACE',
                        utils.scale_value(self.fspace)
                    ).replace(
                        'REQUIRED_SPACE',
                        utils.scale_value(self.rspace)
                    )
                )
                return

        # Wipe folders if they already exist
        if self.destination == 'ModOrganizer':
            appdata_path = Path(os.getenv('LOCALAPPDATA'))
            appdata_path = appdata_path / 'ModOrganizer'
            appdata_path = appdata_path / self.dst_modinstance.name
            instance_path = self.dst_modinstance.mods_path.parent

            # Wipe instance from MO2
            if appdata_path.is_dir():
                if list(appdata_path.iterdir()):
                    self.log.debug("Wiping existing instance...")

                    appdata_path = f"\\\\?\\{appdata_path}"
                    def process(ldialog: LoadingDialog):
                        ldialog.updateProgress(
                            text1=self.lang['wiping_instance']
                        )
                        
                        shutil.rmtree(appdata_path)

                    loadingdialog = LoadingDialog(
                        parent=self.root,
                        app=self,
                        func=process
                    )
                    loadingdialog.exec()

                    self.log.debug("Instance wiped.")

            # Wipe instance data
            if instance_path.is_dir():
                if list(instance_path.iterdir()):
                    self.log.debug("Wiping existing instance data...")

                    instance_path = f"\\\\?\\{instance_path}"
                    def process(ldialog: LoadingDialog):
                        ldialog.updateProgress(
                            text1=self.lang['wiping_instance_data']
                        )

                        shutil.rmtree(instance_path)

                    loadingdialog = LoadingDialog(
                        parent=self.root,
                        app=self,
                        func=process
                    )
                    loadingdialog.exec()

                    self.log.debug("Instance data wiped.")

        # Transfer mods
        self.dst_modinstance.mods = self.src_modinstance.mods

        # Transfer loadorder
        self.dst_modinstance.loadorder = self.src_modinstance.loadorder

        # Set up destination instance
        self.dst_modinstance.setup_instance()

        # Check for files that have to be copied
        # directly into the game folder
        # since MO2 cannot manage those
        if self.src_modinstance.root_mods:
            message_box = qtw.QMessageBox(self.root)
            message_box.setWindowIcon(self.root.windowIcon())
            message_box.setStyleSheet(self.stylesheet)
            message_box.setWindowTitle(self.lang['migrating_instance'])
            message_box.setText(self.lang['detected_root_files'])
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.Ignore
                | qtw.QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.Yes)
            ignore_button = message_box.button(
                qtw.QMessageBox.StandardButton.Ignore
            )
            ignore_button.setText(self.lang['ignore'])
            continue_button = message_box.button(
                qtw.QMessageBox.StandardButton.Yes
            )
            continue_button.setText(self.lang['continue'])

            # Wait for purge if source is Vortex
            if self.source == 'Vortex':
                timer = qtc.QTimer()
                timer.setInterval(1000)
                deploy_file = self.src_modinstance.mods_path / 'vortex.deployment.msgpack'
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
                def process(ldialog: LoadingDialog):
                    ldialog.updateProgress(
                        text1=self.lang['copying_files']
                    )

                    installdir = self.game_instance.get_install_dir()
                    for i, mod in enumerate(self.src_modinstance.root_mods):
                        ldialog.updateProgress(
                            text1=f"{self.lang['copying_files']} \
- {i}/{len(self.src_modinstance.root_mods)}",
                            value1=i,
                            max1=len(self.src_modinstance.root_mods),

                            show2=True,
                            text2=mod.metadata['name']
                        )

                        src_path = mod.path
                        dst_path = installdir

                        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

                loadingdialog = LoadingDialog(
                    parent=self.root,
                    app=self,
                    func=process
                )
                loadingdialog.exec()

        # Get start time for performance measurement
        starttime = time.time()

        # Copy mods to new instance
        loadingdialog = LoadingDialog(
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

        deploy_file = self.src_modinstance.mods_path / 'vortex.deployment.msgpack'
        if self.source == 'Vortex' and deploy_file.is_file():
            qtw.QMessageBox.information(
                self.root,
                self.lang['success'],
                self.lang['migration_complete_purge_notice']
            )
        else:
            qtw.QMessageBox.information(
                self.root,
                self.lang['success'],
                self.lang['migration_complete']
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
        dialog.setWindowTitle(self.lang['about'])
        dialog.setWindowIcon(self.root.windowIcon())
        dialog.setTextFormat(qtc.Qt.TextFormat.RichText)
        text = self.lang['about_text']

        # Add translator credit if available
        if self.lang['translator_url'].startswith('http'):
            text += "<br><br>Translation by "
            text += f"<a href='{self.lang['translator_url']}'>"
            text += f"{self.lang['translator_name']}</a>"

        dialog.setText(text)
        dialog.setStandardButtons(qtw.QMessageBox.StandardButton.Ok)

        # hacky way to set label width
        for label in dialog.findChildren(qtw.QLabel):
            if label.text() == self.lang['about_text']:
                label.setFixedWidth(400)
                break

        dialog.exec()

    def show_about_qt_dialog(self):
        """
        Displays about Qt dialog.
        """

        qtw.QMessageBox.aboutQt(self.root, f"{self.lang['about']} Qt")

    def exec(self):
        """
        Executes Qt application.
        """

        super().exec()

        # Exit and clean up
        self.log.info("Exiting program...")
        #self.exception = False
        if ((not self.config['save_logs']
            or (self.config['save_logs'] == 'False'))
            and (not self.exception)):
            self.log.info("Cleaning log file...")
            self.stdout.close()
            os.remove(self.log_path)

    def load_lang(self, language=None):
        """
        Loads localisation strings from <language>.
        
        Falls back to english strings if localisation is outdated.
        """

        # Get language strings
        if not language:
            language = self.config['language']
        if language.lower() == "system":
            language = getlocale()[0]
        language = language.replace("_", "-")

        # Get language path
        langpath = self.res_path / 'locales' / f"{language}.json"
        if not os.path.isfile(langpath):
            self.log.error(
                f"Failed loading localisation for language '{language}': Not found."
            )
            language = "en-US"
            langpath = self.res_path / 'locales' / f"{language}.json"

        # Load language
        with open(langpath, "r", encoding='utf-8') as langfile:
            lang: Dict[str, str] = json.load(langfile)

        # Load english language as fallback
        eng_path = self.res_path / 'locales' / 'en-US.json'
        with open(eng_path, 'r', encoding='utf-8') as engfile:
            eng_lang: Dict[str, str] = json.load(engfile)

        if len(eng_lang) > len(lang):
            self.log.warning(f"Detected outdated localisation: '{language}'!")
            self.log.debug(f"Missing strings: {len(eng_lang) - len(lang)}")

            for key, value in eng_lang.items():
                if key not in lang.keys():
                    lang[key] = value

            self.log.debug("Filled missing strings from en-US strings.")

        self.lang: Dict[str, str] = lang

        self.log.info(f"{'Program language':21}: {language}")


# Create class for ui theme ##########################################
class Theme:
    """Class for ui theme. Manages theme and stylesheet."""

    default_dark_theme = {
        'primary_bg': '#202020',
        'secondary_bg': '#2d2d2d',
        'tertiary_bg': '#383838',
        'highlight_bg': '#696969',
        'accent_color': '#d78f46',
        'text_color': '#ffffff',
        'font': 'Arial',
        'font_size': '14px',
        'title_font': 'Arial Black',
        'title_size': '28px',
        'subtitle_size': '22px',
        'console_font': 'Cascadia Mono',
        'console_size': '14px',
        'checkbox_indicator': 'url(./data/icons/checkmark_light.svg)',
        'dropdown_arrow': 'url(./data/icons/dropdown_light.svg)',
    }
    default_light_theme = {
        'primary_bg': '#f3f3f3',
        'secondary_bg': '#e9e9e9',
        'tertiary_bg': '#dadada',
        'highlight_bg': '#b6b6b6',
        'accent_color': '#d78f46',
        'text_color': 'black',
        'font': 'Arial',
        'font_size': '14px',
        'title_font': 'Arial Black',
        'title_size': '28px',
        'subtitle_size': '22px',
        'console_font': 'Cascadia Mono',
        'console_size': '14px',
        'checkbox_indicator': 'url(./data/icons/checkmark.svg)',
        'dropdown_arrow': 'url(./data/icons/dropdown.svg)',
    }
    default_mode = 'dark'
    default_theme = default_dark_theme
    default_stylesheet = ""
    stylesheet = ""

    def __init__(self, app: MainApp):
        self.app = app
        self.mode = self.default_mode
        self.theme = self.default_theme

    def set_mode(self, mode: str):
        """
        Sets <mode> as ui mode.
        """

        mode = mode.lower()
        if mode == 'system':
            mode = darkdetect.theme().lower()
        self.mode = mode
        if self.mode == 'light':
            self.default_theme = self.default_light_theme
        elif self.mode == 'dark':
            self.default_theme = self.default_dark_theme

        return self.default_theme

    def load_theme(self):
        """
        Loads theme according to mode
        """

        if self.mode == 'light':
            self.theme = self.default_light_theme
        elif self.mode == 'dark':
            self.theme = self.default_dark_theme

        return self.theme

    def load_stylesheet(self):
        """
        Loads stylesheet from data\\style.qss.
        """

        # load stylesheet from qss file
        with open(self.app.qss_path, 'r', encoding='utf8') as file:
            stylesheet = file.read()

        self.default_stylesheet = stylesheet

        # parse stylesheet with theme
        self.stylesheet = self.parse_stylesheet(self.theme, stylesheet)

        return self.stylesheet

    def set_stylesheet(self, stylesheet: str=None):
        """
        Sets <stylesheet> as current stylesheet.
        """

        if not stylesheet:
            stylesheet = self.stylesheet
        self.app.root.setStyleSheet(stylesheet)
        self.app.setStyleSheet(stylesheet)

    @staticmethod
    def parse_stylesheet(theme: dict, stylesheet: str):
        """
        Parses <stylesheet> by replacing placeholders with values
        from <theme>.
        """

        for setting, value in theme.items():
            stylesheet = stylesheet.replace(f"<{setting}>", value)

        return stylesheet


# Start main application #############################################
if __name__ == '__main__':
    import utils
    import dialogs
    import games
    import managers
    from loadingdialog import LoadingDialog

    mainapp = MainApp()
    mainapp.exec()
