# Name: Modmanager Migration Tool ####################################
# Author: Cutleast ###################################################
# Python Version 3.10.9 ##############################################
# Qt Version: 6.4.2 ##################################################
# Type: Utility ######################################################

# Import libraries ###################################################
import argparse
import ctypes
import json
import logging
import os
import platform
import shutil
import sys
import threading
import time
import traceback
from locale import getlocale
from shutil import disk_usage
from typing import Callable

import darkdetect
import msgpack
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
    50: "fatal/critical/exception"      # FATAL/CRITICAL/EXCEPTION
}
SUPPORTED_MODMANAGERS = [
    "Vortex",
    "ModOrganizer"
]
NUMBER_OF_THREADS = 4 # tests have shown that this is the ideal number

# Create class for main application ##################################
class MainApp(qtw.QApplication):
    theme_change_sign = qtc.Signal()
    change_sign = qtc.Signal()

    def __init__(self):
        super().__init__([])

        # Initialize variables #######################################
        self.version = "1.0"
        self.name = f"Mod Manager Migrator"
        # check if compiled with nuitka (or in general)
        self.compiled = ("__compiled__" in globals()) or (sys.argv[0].endswith('.exe'))
        self._imgdata = None
        self.encrypt_key = None
        self.unsaved_changes = False
        self.change_sign.connect(self.on_change)
        self.unsaved_settings = False
        self.source = None
        self.destination = None
        self.stagefile = None
        self.src_modinstance = None # VortexInstance or MO2Instance
        self.dst_modinstance = None # VortexInstance or MO2Instance
        self.mode = 'hardlink' # 'copy' or 'hardlink'
        self.load_order = []
        self.start_date = time.strftime("%d.%m.%Y")
        self.start_time = time.strftime("%H:%M:%S")
        self.os_type = "linux" if "Linux" in platform.system() else "windows"
        print(f"Current datetime: {self.start_date} {self.start_time}")
        # paths
        self.cur_path = os.path.dirname(__file__)
        self.app_path = os.path.join(os.getenv('APPDATA'), self.name)
        self.con_path = os.path.join(self.app_path, 'config.json')
        self.res_path = os.path.join(self.cur_path, 'data')
        self.ico_path = os.path.join(self.res_path, 'icons')
        self.theme_path = os.path.join(self.res_path, 'theme.json')
        self.qss_path = os.path.join(self.res_path, 'style.qss')
        _buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, _buf)
        self.doc_path = os.path.normpath(os.path.join(_buf.value, 'My Games', 'Skyrim Special Edition'))
        # logging
        self.log_name = f"{self.name}_{self.start_date}_-_{self.start_time.replace(':', '.')}.log"
        #self.log_path = os.path.join(self.res_path, 'logs', self.log_name)
        self.log_path = os.path.join(os.getenv('APPDATA'), self.name, 'logs', self.log_name)
        if not os.path.isdir(os.path.join(os.getenv('APPDATA'), self.name)):
            os.mkdir(os.path.join(os.getenv('APPDATA'), self.name))
        if not os.path.isdir(os.path.dirname(self.log_path)):
            os.mkdir(os.path.dirname(self.log_path))
        self.protocol = ""
        # config
        self.default_conf = {
            'save_logs': False, 
            'log_level': 'debug',
            'ui_mode': 'System',
            'language': 'System',
            'accent_color': '#d78f46',
        }

        # Create or load config file #################################
        try:
            # load config
            config = json.load(open(self.con_path, 'r'))

            if len(config.keys()) < len(self.default_conf.keys()):
                # update outdated config
                print(f"Detected incomplete (outdated) config file. Updating with default config...")
                new_keys = [key for key in self.default_conf.keys() if key not in config.keys()]
                for key in new_keys:
                    config[key] = self.default_conf[key]

                # try to save updated config to config file
                try:
                    with open(self.con_path, "w") as conffile:
                        json.dump(config, conffile, indent=4)
                    print(f"Saved updated config to config file.")
                # ignore if access denied by os
                except OSError:
                    print(f"Failed to update config file: Access denied.")

            # apply config
            self.config = config
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            # apply default config
            self.config = self.default_conf

            # save default config to config file
            with open(self.con_path, "w") as conffile:
                json.dump(self.config, conffile, indent=4)
        
        # Set up protocol structure ##################################
        self.log = logging.getLogger(self.__repr__())
        log_fmt = "[%(asctime)s.%(msecs)03d][%(levelname)s][%(threadName)s.%(name)s.%(funcName)s]: %(message)s"
        self.log_fmt = logging.Formatter(log_fmt, datefmt="%d.%m.%Y %H:%M:%S")
        self.stdout = core.StdoutPipe(self)
        self.log_str = logging.StreamHandler(self.stdout)
        self.log_str.setFormatter(self.log_fmt)
        self.log.addHandler(self.log_str)
        self.log_level = getattr(logging, self.config['log_level'].upper(), 20) # info level
        self.log.setLevel(self.log_level)
        sys.excepthook = self.handle_exception

        # Parse commandline arguments ################################
        help_msg = f"{self.name} v{self.version} by Cutleast"
        if self.compiled:
            parser = argparse.ArgumentParser(prog=os.path.basename(sys.executable), description=help_msg)
        else:
            parser = argparse.ArgumentParser(prog=f"{os.path.basename(sys.executable)} {__file__}", description=help_msg)
        parser.add_argument("-l", "--log-level", help="Specify logging level.", choices=list(LOG_LEVELS.values()))
        parser.add_argument("--no-log", help="Disable log file.", action="store_true")
        parser.add_argument("--keep-log", help="Keep log file. (Overwrites --no-log)", action="store_true")
        self.args = parser.parse_args()
        if self.args.no_log:
            self.config['save_logs'] = False
        if self.args.keep_log:
            self.config['save_logs'] = True
        if self.args.log_level:
            self.log_level = getattr(logging, self.args.log_level.upper(), 20)
            self.log.setLevel(self.log_level)
        
        # Start by logging basic information #########################
        log_title = "-" * 40 + f" {self.name} " + "-" * 40
        self.log.info(f"\n{'-' * len(log_title)}\n{log_title}\n{'-' * len(log_title)}")
        self.log.info(f"Starting program...")
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
        self.log.debug(f"{'Detected platform':21}: {platform.system()} {platform.version()} {platform.architecture()[0]}")

        # Load language strings ######################################
        self.load_lang()

        # Initalize Qt App and Main Window ###########################
        self.root = qtw.QMainWindow()
        self.root.setObjectName("root")
        self.root.setWindowTitle(self.name)
        self.root.setWindowIcon(qtg.QIcon(os.path.join(self.ico_path, "mmm.svg")))
        self._theme = Theme(self)
        self._theme.set_mode(self.config['ui_mode'])
        self.theme = self._theme.load_theme()
        self.theme['accent_color'] = self.config['accent_color']
        self.stylesheet = self._theme.load_stylesheet()
        self.root.setStyleSheet(self.stylesheet)

        # Fix link color
        palette = self.palette()
        palette.setColor(palette.ColorRole.Link, qtg.QColor(self.config['accent_color']))
        self.setPalette(palette)

        # Initialize main user interface #############################
        # Create menu bar
        # Create file menu actions
        self.exit_action = qtg.QAction(self.lang['exit'], self.root)
        # Create file menu
        self.file_menu = qtw.QMenu()
        self.file_menu.setTitle(self.lang['file'])
        self.file_menu.setWindowFlags(qtc.Qt.WindowType.FramelessWindowHint | qtc.Qt.WindowType.Popup | qtc.Qt.WindowType.NoDropShadowWindowHint)
        self.file_menu.setAttribute(qtc.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.file_menu.setStyleSheet(self.stylesheet)
        self.file_menu.addAction(self.exit_action)
        self.exit_action.triggered.connect(self.root.close)
        self.root.menuBar().addMenu(self.file_menu)
        # Create help menu actions
        self.config_action = qtg.QAction(self.lang['settings'], self)
        self.log_action = qtg.QAction(self.lang['open_log_file'], self)
        self.about_action = qtg.QAction(self.lang['about'], self)
        self.about_qt_action = qtg.QAction(f"{self.lang['about']} Qt", self)
        # Create help menu
        self.help_menu = qtw.QMenu()
        self.help_menu.setTitle(self.lang['help'])
        self.help_menu.setWindowFlags(qtc.Qt.WindowType.FramelessWindowHint | qtc.Qt.WindowType.Popup | qtc.Qt.WindowType.NoDropShadowWindowHint)
        self.help_menu.setAttribute(qtc.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.help_menu.setStyleSheet(self.stylesheet)
        self.help_menu.addAction(self.config_action)
        self.help_menu.addAction(self.log_action)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.about_action)
        self.help_menu.addAction(self.about_qt_action)
        self.config_action.triggered.connect(lambda: dialogs.SettingsDialog(self.root, self))
        self.log_action.triggered.connect(lambda: os.startfile(self.log_path))
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
        self.src_button.clicked.connect(lambda: dialogs.SourceDialog(self.root, self).show())
        self.mainlayout.addWidget(self.src_button, 0, 0)
        # Create migrate button
        self.mig_button = qtw.QPushButton(self.lang['migrate'])
        self.mig_button.setIcon(qta.icon('fa5s.chevron-right', color=self.theme['text_color']))
        self.mig_button.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
        self.mig_button.clicked.connect(self.migrate)
        self.mig_button.setDisabled(True)
        self.mainlayout.addWidget(self.mig_button, 0, 1)
        # Create destination button
        self.dst_button = qtw.QPushButton(self.lang['select_destination'])
        self.dst_button.clicked.connect(lambda: dialogs.DestinationDialog(self.root, self).show())
        self.dst_button.setDisabled(True)
        self.mainlayout.addWidget(self.dst_button, 0, 2)

        # Add right arrow icon
        self.mig_icon = qtw.QLabel()
        self.mig_icon.setPixmap(qta.icon('fa5s.chevron-right', color=self.theme['text_color']).pixmap(120, 120))
        self.mainlayout.addWidget(self.mig_icon, 1, 1)

        # Show window maximized
        #self.root.resize(1000, 600)
        self.root.showMaximized()

        # Check for updates
        if (new_version := core.get_latest_version()) > float(self.version):
            self.log.info(f"A new version is available to download: Current version: {self.version} | Latest version: {new_version}")

            message_box = qtw.QMessageBox(self.root)
            message_box.setWindowIcon(self.root.windowIcon())
            message_box.setStyleSheet(self.stylesheet)
            message_box.setWindowTitle(self.name)
            message_box.setText(self.lang['update_available'].replace("[OLD_VERSION]", self.version).replace("[NEW_VERSION]", str(new_version)))
            message_box.setStandardButtons(qtw.QMessageBox.StandardButton.No | qtw.QMessageBox.StandardButton.Yes)
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.Yes)
            message_box.button(qtw.QMessageBox.StandardButton.Yes).setText(self.lang['yes'])
            message_box.button(qtw.QMessageBox.StandardButton.No).setText(self.lang['no'])
            core.center(message_box, self.root)
            choice = message_box.exec()
            
            # Handle the user's choice
            if choice == qtw.QMessageBox.StandardButton.Yes:
                # Open nexus mods file page
                os.startfile("https://www.nexusmods.com/skyrimspecialedition/mods/87160?tab=files")
        elif new_version == 0.0:
            self.log.error("Failed to check for update.")

    def __repr__(self):
        return "MainApp"
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        self.log.critical(f"An uncaught exception occured:", exc_info=(exc_type, exc_value, exc_traceback))
        mb = qtw.QMessageBox(self.root)
        mb.setWindowTitle(f"{self.name} - {self.lang['error']}")
        mb.setIcon(qtw.QMessageBox.Icon.Critical)
        mb.setText(f"{self.lang['error_text']}\n{exc_value}")
        mb.setStandardButtons(qtw.QMessageBox.StandardButton.Yes | qtw.QMessageBox.StandardButton.No)
        mb.button(qtw.QMessageBox.StandardButton.Yes).setText(self.lang['continue'])
        mb.button(qtw.QMessageBox.StandardButton.No).setText(self.lang['exit'])
        # add details button
        button = mb.addButton(self.lang['show_details'], qtw.QMessageBox.ButtonRole.YesRole)
        self._details = False
        def toggle_details():
            # toggle details
            if not self._details:
                self._details = True
                button.setText(self.lang['hide_details'])
                mb.setInformativeText(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            else:
                self._details = False
                button.setText(self.lang['show_details'])
                mb.setInformativeText("")
            
            # update mb size and move mb to center of screen
            mb.adjustSize()
            mb.move(self.primaryScreen().availableGeometry().center() - mb.rect().center())
        button.clicked.disconnect()
        button.clicked.connect(toggle_details)
        choice = mb.exec()

        if choice == qtw.QMessageBox.StandardButton.No:
            self.root.close()

    # Core function to migrate #######################################
    def migrate(self):
        self.log.info(f"Migrating instance from {self.source} to {self.destination}...")

        starttime = time.time()

        # Calculate free and required disk space if copy mode
        if self.mode == 'copy':
            self.fspace = 0 # free space
            self.rspace = 0 # required space
            def process(psignal: qtc.Signal):
                psignal.emit({'text': self.lang['calc_size']})
                self.fspace = disk_usage(os.path.splitdrive(self.dst_modinstance.paths['instance_path'])[0])[2]
                self.rspace = self.src_modinstance.get_size()
                self.log.debug(f"Free space: {core.get_size(self.fspace)} | Required space: {core.get_size(self.rspace)}")
            loadingdialog = dialogs.LoadingDialog(self.root, self, process)
            loadingdialog.exec()

            # Check if there is enough free space
            if self.fspace <= self.rspace:
                self.log.error(f"Migration failed: not enough free space!")
                qtw.QMessageBox.critical(
                    self.root,
                    self.lang['error'],
                    self.lang['enough_space_text'].replace(
                        'FREE_SPACE', core.get_size(self.fspace)).replace(
                        'REQUIRED_SPACE', core.get_size(self.rspace)))
                return

        # Wipe folders if they already exist
        if self.destination == 'ModOrganizer':
            appdata_path = os.path.join(os.getenv('LOCALAPPDATA'), 'ModOrganizer', self.dst_modinstance.name)
            instance_path = self.dst_modinstance.paths['instance_path']
            if os.path.isdir(appdata_path):
                self.log.debug("Wiping existing instance...")
                def process(psignal: qtc.Signal):
                    psignal.emit({'text': self.lang['wiping_instance']})
                    shutil.rmtree(appdata_path)
                loadingdialog = dialogs.LoadingDialog(self.root, self, process)
                loadingdialog.exec()
                self.log.debug("Instance wiped.")
            if os.path.isdir(instance_path):
                self.log.debug("Wiping existing instance data...")
                def process(psignal: qtc.Signal):
                    psignal.emit({'text': self.lang['wiping_instance_data']})
                    shutil.rmtree(instance_path)
                loadingdialog = dialogs.LoadingDialog(self.root, self, process)
                loadingdialog.exec()
                self.log.debug("Instance data wiped.")

        # Create destination mod instance with ini files and loadorder
        def process(psignal: qtc.Signal):
            psignal.emit({'text': self.lang['sorting_loadorder']})
            self.dst_modinstance.loadorder = self.src_modinstance.get_loadorder(psignal)
            # Fetch and copy metadata
            for i, mod in enumerate(self.dst_modinstance.loadorder):
                data = self.src_modinstance.get_mod_metadata(mod)
                self.dst_modinstance.loadorder[i] = data['name']
                self.dst_modinstance.metadata[mod] = data
        loadingdialog = dialogs.LoadingDialog(self.root, self, process)
        loadingdialog.exec()
        self.dst_modinstance.create_instance()

        # Check for files that have to be copied
        # directly into the skyrim folder
        # since MO2 cannot manage those
        if self.source == 'Vortex':
            if self.src_modinstance.stagefiles:
                message_box = qtw.QMessageBox(self.root)
                message_box.setWindowIcon(self.root.windowIcon())
                message_box.setStyleSheet(self.stylesheet)
                message_box.setWindowTitle(self.lang['migrating_instance'])
                message_box.setText(self.lang['detected_root_files'])
                message_box.setStandardButtons(qtw.QMessageBox.StandardButton.Ignore | qtw.QMessageBox.StandardButton.Yes)
                message_box.setDefaultButton(qtw.QMessageBox.StandardButton.Yes)
                ignore_button = message_box.button(qtw.QMessageBox.StandardButton.Ignore)
                ignore_button.setText(self.lang['ignore'])
                continue_button = message_box.button(qtw.QMessageBox.StandardButton.Yes)
                continue_button.setText(self.lang['continue'])
                continue_button.setDisabled(True)

                timer = qtc.QTimer()
                timer.setInterval(1000)
                def check_purged():
                    if message_box is not None:
                        if os.path.isfile(self.src_modinstance.stagefile.path):
                            timer.start()
                        else:
                            continue_button.setDisabled(False)
                timer.timeout.connect(check_purged)
                timer.start()

                choice = message_box.exec()
                message_box = None
                
                if choice == qtw.QMessageBox.StandardButton.Yes:
                    # Copy root files directly into game directory
                    def process(psignal: qtc.Signal):
                        mods_to_copy = []
                        skyrim_path = os.path.join(core.get_steam_path(), 'steamapps', 'common', 'Skyrim Special Edition')
                        for stagefile in self.src_modinstance.stagefiles:
                            for mod in stagefile.modfiles.keys():
                                mods_to_copy.append(mod)
                        for c, mod in enumerate(mods_to_copy):
                            psignal.emit({'value': c, 'max': len(mods_to_copy), 'text': f"{self.src_modinstance.get_mod_metadata(mod)['name']} - {c}/{len(mods_to_copy)}"})
                            shutil.copytree(os.path.join(self.src_modinstance.stagefile.dir, mod), skyrim_path, dirs_exist_ok=True)
                    loadingdialog = dialogs.LoadingDialog(self.root, self, process, text=self.lang['copying_files'])
                    loadingdialog.exec()

        # Copy mods to new instance
        def process(psignal: qtc.Signal):
            for c, mod in enumerate(self.src_modinstance.mods.keys()):
                modname = self.src_modinstance.get_mod_metadata(os.path.basename(mod))['name']
                if self.mode == 'copy':
                    progress = {
                        'value': c, 
                        'max': len(self.src_modinstance.mods), 
                        'text': f"{self.lang['migrating_instance']} ({c}/{len(self.src_modinstance.mods)})",
                        'show2': True,
                        'text2': self.lang['copying_mod'].replace("[MOD]", f"'{modname}'")
                    }
                else:
                    progress = {
                        'value': c, 
                        'max': len(self.src_modinstance.mods), 
                        'text': f"{self.lang['migrating_instance']} ({c}/{len(self.src_modinstance.mods)})",
                        'show2': True,
                        'text2': self.lang['linking_mod'].replace("[MOD]", f"'{modname}'")
                    }
                psignal.emit(progress)
                self.dst_modinstance.import_mod(os.path.join(self.src_modinstance.paths['instance_path'], mod), psignal)
        loadingdialog = dialogs.LoadingDialog(self.root, self, process)
        loadingdialog.exec()

        # Copy downloads if given to new instance
        if self.src_modinstance.paths.get('download_path', None):
            def process(psignal: qtc.Signal):
                for c, archive in enumerate(os.listdir(self.src_modinstance.paths['download_path'])):
                    if self.mode == 'copy':
                        progress = {
                            'value': c, 
                            'max': len(self.src_modinstance.mods),
                            'text': self.lang['migrating_instance'],
                            'show2': True,
                            'text2': self.lang['copying_download'].replace("[NAME]", f"'{os.path.basename(archive)}'")
                        }
                    else:
                        progress = {
                            'value': c, 
                            'max': len(self.src_modinstance.mods),
                            'text': self.lang['migrating_instance'],
                            'show2': True,
                            'text2': self.lang['linking_download'].replace("[NAME]", f"'{os.path.basename(archive)}'")
                        }
                    psignal.emit()
                    src_path = os.path.join(self.src_modinstance.paths['download_path'])
                    dst_path = os.path.join(self.dst_modinstance.paths['download_path'])
                    if self.mode == 'copy':
                        shutil.copyfile(src_path, dst_path)
                    else:
                        os.link(src_path, dst_path)
            loadingdialog = dialogs.LoadingDialog(self.root, self, process, self.lang['migrating_instance'])
            loadingdialog.exec()

        self.log.info("Migration complete.")
        dur = time.time() - starttime
        self.log.debug(f"Migration took: {dur} second(s) ({(dur / 60):.2f} minute(s))")
        if self.source == 'Vortex':
            qtw.QMessageBox.information(self.root, self.lang['success'], self.lang['migration_complete_purge_notice'])
        else:
            qtw.QMessageBox.information(self.root, self.lang['success'], self.lang['migration_complete'])
   ###################################################################

    def set_mode(self, mode: str):
        self.mode = mode

    def update_title(self):
        # build title string
        title = f"{self.name}"
        if self.unsaved_changes:
            title += "*"
        
        # apply title to window
        self.root.setWindowTitle(title)
    
    def on_change(self):
        self.unsaved_changes = True
        self.update_title()

    def show_about_dialog(self):
        #qtw.QMessageBox.about(self.root, self.lang['about'], self.lang['about_text'])
        mb = qtw.QMessageBox(self.root)
        icon = self.root.windowIcon()
        pixmap = icon.pixmap(128, 128)
        mb.setIconPixmap(pixmap)
        mb.setWindowTitle(self.lang['about'])
        mb.setWindowIcon(self.root.windowIcon())
        mb.setTextFormat(qtc.Qt.TextFormat.RichText)
        mb.setText(self.lang['about_text'])
        mb.setStandardButtons(qtw.QMessageBox.StandardButton.Ok)

        # hacky way to set label width
        for label in mb.findChildren(qtw.QLabel):
            if label.text() == self.lang['about_text']:
                label.setFixedWidth(400)
                break
        
        mb.exec()
    
    def show_about_qt_dialog(self):
        qtw.QMessageBox.aboutQt(self.root, f"{self.lang['about']} Qt")
 
    def exec(self):
        super().exec()

        # Exit and clean up
        self.log.info("Exiting program...")
        if (not self.config['save_logs']) or (self.config['save_logs'] == 'False'):
            self.log.info("Cleaning log file...")
            self.stdout.__del__()
            os.remove(self.log_path)
    
    def load_lang(self, language=None):
        # Get language strings
        if not language:
            language = self.config['language']
        if language.lower() == "system":
            language = getlocale()[0]
        language = language.replace("_", "-")
        
        # Get language path
        langpath = os.path.join(self.res_path, 'locales', f"{language}.json")
        if not os.path.isfile(langpath):
            self.log.error(f"Failed loading localisation for language '{language}': Not found.")
            language = "en-US"
            langpath = os.path.join(self.res_path, 'locales', f"{language}.json")
        
        # Load language
        with open(langpath, "r", encoding='utf-8') as langfile:
            self.lang = json.load(langfile)
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
        ## load theme if file exists
        #if os.path.exists(self.app.theme_path):
        #    with open(self.app.theme_path, 'r') as file:
        #        theme = dict(json.load(file))
        #    # check theme
        #    if len(theme) == len(self.default_theme):
        #        self.theme = theme
        #
        ## create theme file with default theme
        #else:
        #    with open(self.app.theme_path, 'w') as file:
        #        theme = json.dumps(self.default_theme, indent=4)
        #        file.write(theme)
        if self.mode == 'light':
            self.theme = self.default_light_theme
        elif self.mode == 'dark':
            self.theme = self.default_dark_theme
        
        return self.theme
    
    def load_stylesheet(self):
        # load stylesheet from qss file
        with open(self.app.qss_path, 'r') as file:
            stylesheet = file.read()

        self.default_stylesheet = stylesheet
        
        # parse stylesheet with theme
        self.stylesheet = self.parse_stylesheet(self.theme, stylesheet)

        return self.stylesheet
    
    def set_stylesheet(self, stylesheet: str=None):
        if not stylesheet:
            stylesheet = self.stylesheet
        self.app.root.setStyleSheet(stylesheet)
        self.app.setStyleSheet(stylesheet)

    @staticmethod
    def parse_stylesheet(theme: dict, stylesheet: str):
        for property, value in theme.items():
            stylesheet = stylesheet.replace(f"<{property}>", value)
        
        return stylesheet


# Start main application #############################################
if __name__ == '__main__':
    import core
    import dialogs
    app = MainApp()
    app.exec()

