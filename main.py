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
import sys
import threading
import time
import traceback
from locale import getlocale
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
    "ModOrganizer 2 (MO2)"
]


# Create class for main application ##################################
class MainApp(qtw.QApplication):
    theme_change_sign = qtc.Signal()
    change_sign = qtc.Signal()

    def __init__(self):
        super().__init__([])

        # Initialize variables #######################################
        self.version = "1.0"
        self.name = f"Modmanager Migration Tool"
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
        self.modinstance = None # VortexInstance or MO2Instance
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
            'log_level': 'info',
            'ui_mode': 'System',
            'language': 'System',
            'accent_color': '#f38064',
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
        self.stdout = StdoutPipe(self)
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
        parser.add_argument('inputfile', help="Optional file to open with.", nargs='?', type=argparse.FileType('rb'))
        self.args = parser.parse_args()
        if self.args.no_log:
            self.config['save_logs'] = False
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
        self.touched = False
        self.root_close = self.root.closeEvent
        self.root.closeEvent = self.exit
        self.root.setObjectName("root")
        self.root.setWindowTitle(self.name)
        #icon = qtg.QPixmap()
        #icon.loadFromData(self.ico_data['BitGallery'])
        self.root.setWindowIcon(qtg.QIcon(os.path.join(self.ico_path, "mmt.svg")))
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
        self.config_action.triggered.connect(self.open_settings)
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
        self.mainlayout.setColumnStretch(1, 1)
        self.mainframe.setLayout(self.mainlayout)
        self.root.setCentralWidget(self.mainframe)

        # Create source button
        self.src_button = qtw.QPushButton(self.lang['select_source'])
        self.src_button.clicked.connect(self.add_source)
        self.mainlayout.addWidget(self.src_button, 0, 0)
        # Create destination button
        self.dst_button = qtw.QPushButton(self.lang['select_destination'])
        self.dst_button.clicked.connect(self.add_destination)
        self.dst_button.setDisabled(True)
        self.mainlayout.addWidget(self.dst_button, 0, 1)
        # Create migrate button
        self.mig_button = qtw.QPushButton("Migrate")
        self.mig_button.clicked.connect(self.migrate)
        self.mig_button.setDisabled(True)
        self.mainlayout.addWidget(self.mig_button, 0, 2)

        # Show window maximized
        self.root.resize(1000, 600)
        self.root.showMaximized()

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
            self.exit(silent=True)

    # Core function to migrate #######################################
    def migrate(self):
        self.log.info(f"Migrating instance from {self.source} to {self.destination}...")
        self.log.info("Migration complete.")

    # Source dialog ##################################################
    def add_source(self):
        # Create dialog to choose mod manager and instance/profile
        self.source_dialog = qtw.QDialog(self.root)
        self.source_dialog.setWindowTitle(f"{self.name} - {self.lang['select_source']}")
        self.source_dialog.setWindowIcon(self.root.windowIcon())
        self.source_dialog.setModal(True)
        self.source_dialog.setObjectName("root")
        #self.source_dialog.setMinimumWidth(1000)
        self.source_dialog.closeEvent = self.cancel_src
        layout = qtw.QVBoxLayout(self.source_dialog)
        self.source_dialog.setLayout(layout)

        # Create widget for mod manager selection ####################
        self.src_modmanagers_widget = qtw.QWidget()
        layout.addWidget(self.src_modmanagers_widget)

        # Create layout for mod managers
        manager_layout = qtw.QGridLayout()
        columns = 2 # number of columns in grid
        self.src_modmanagers_widget.setLayout(manager_layout)
        
        # Label with instruction
        label = qtw.QLabel(self.lang['select_source_text'])
        label.setObjectName("titlelabel")
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        manager_layout.addWidget(label, 0, 0, 1, columns)

        buttons = []
        # Define functions for selection logic
        def set_src(source: str):
            self.source = source
            for button in buttons:
                if button.text() != source:
                    button.setChecked(False)
                else:
                    button.setChecked(True)
        def func(source):
            return lambda: set_src(source)

        # Create button for each supported mod manager
        for i, modmanager in enumerate(SUPPORTED_MODMANAGERS):
            button = qtw.QPushButton()
            button.setText(modmanager)
            button.setCheckable(True)
            if modmanager != 'Vortex':
                button.setDisabled(True)
                button.setToolTip("Work in Progress...")
            button.clicked.connect(func(modmanager))
            row = i // columns # calculate row
            col = i % columns # calculate column
            buttons.append(button)
            manager_layout.addWidget(button, row+1, col)
        
        # Select first mod manager as default
        buttons[0].setChecked(True)
        self.source = SUPPORTED_MODMANAGERS[0]
        ##############################################################

        # Create widget for instance selection #######################
        self.src_instances_widget = qtw.QWidget()
        self.src_instances_widget.hide()
        layout.addWidget(self.src_instances_widget)
        # Create layout
        self.instances_layout = qtw.QVBoxLayout()
        self.src_instances_widget.setLayout(self.instances_layout)
        # Add label with instruction
        label = qtw.QLabel()
        label.setText(self.lang['select_src_instance_text'])
        label.setObjectName("titlelabel")
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        self.instances_layout.addWidget(label)
        # Add listbox for instances
        self.instances_box = qtw.QListWidget()
        self.instances_box.setSelectionMode(qtw.QListWidget.SelectionMode.SingleSelection)
        self.instances_box.setMinimumHeight(200)
        self.instances_layout.addWidget(self.instances_box, 1)
        ##############################################################

        # Create widget for vortex staging path ######################
        self.src_vortex_widget = qtw.QWidget()
        self.src_vortex_widget.hide()
        layout.addWidget(self.src_vortex_widget)
        # Create layout
        self.vortex_layout = qtw.QVBoxLayout()
        self.src_vortex_widget.setLayout(self.vortex_layout)
        # Add label with instruction
        label = qtw.QLabel()
        label.setText(self.lang['select_src_instance_text'])
        label.setObjectName("titlelabel")
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        self.vortex_layout.addWidget(label)
        # Add label with notice for Vortex users
        label = qtw.QLabel()
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        label.setText(self.lang['vortex_notice'])
        self.vortex_layout.addWidget(label)
        # Add lineedit for staging path
        self.staging_box = qtw.QLineEdit()
        self.vortex_layout.addWidget(self.staging_box)
        # Bind staging path to next/done button
        def on_edit(text: str):
            # Enable button if path is valid
            if os.path.isdir(text):
                self.src_next_button.setDisabled(False)
            # Disable it otherwise
            else:
                self.src_next_button.setDisabled(True)
        self.staging_box.textChanged.connect(on_edit)
        # Add browse function
        def browse():
            file_dialog = qtw.QFileDialog(self.source_dialog)
            file_dialog.setWindowTitle(self.lang['browse'])
            file_dialog.setDirectory(os.path.join(os.getenv('APPDATA'), 'Vortex', 'skyrimse'))
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.staging_box.setText(folder)
        # Add browse button
        button = qtw.QPushButton()
        button.setText(self.lang['browse'])
        button.clicked.connect(browse)
        self.vortex_layout.addWidget(button)
        ##############################################################
        
        # Add spacing
        layout.addSpacing(25)
        
        # Add cancel and next button
        self.src_button_layout = qtw.QHBoxLayout()
        layout.addLayout(self.src_button_layout)
        # Cancel button
        self.src_cancel_button = qtw.QPushButton()
        self.src_cancel_button.setText(self.lang['cancel'])
        self.src_cancel_button.clicked.connect(self.cancel_src)
        self.src_button_layout.addWidget(self.src_cancel_button)
        # Seperate cancel button with spacing
        self.src_button_layout.addSpacing(200)
        # Back button with icon
        self.src_back_button = qtw.QPushButton()
        self.src_back_button.setText(self.lang['back'])
        self.src_back_button.setIcon(qta.icon('fa5s.chevron-left', color=self.theme['text_color']))
        self.src_back_button.setDisabled(True)
        self.src_button_layout.addWidget(self.src_back_button)
        # Next button with icon
        self.src_next_button = qtw.QPushButton()
        self.src_next_button.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
        self.src_next_button.setText(self.lang['next'])
        self.src_next_button.setIcon(qta.icon('fa5s.chevron-right', color=self.theme['text_color']))
        self.src_next_button.clicked.connect(self.src_last_page)
        self.src_button_layout.addWidget(self.src_next_button)
        # Bind next button to instances list box
        self.instances_box.itemSelectionChanged.connect(lambda: self.src_next_button.setDisabled(False))

        # Show popup
        self.source_dialog.show()
    
    def src_first_page(self):
        # Go to first page
        self.src_instances_widget.hide()
        self.src_vortex_widget.hide()
        self.src_modmanagers_widget.show()

        # Update back button
        self.src_back_button.setDisabled(True)
        self.src_back_button.clicked.disconnect()

        # Update next button
        self.src_next_button.clicked.disconnect()
        self.src_next_button.setText(self.lang['next'])
        self.src_next_button.clicked.connect(self.src_last_page)
        self.src_next_button.setIcon(qta.icon('fa5s.chevron-right', color=self.theme['text_color']))
        self.src_next_button.setDisabled(False)

        # Update dialog height
        size = self.source_dialog.sizeHint()
        size.setWidth(self.source_dialog.width())
        self.source_dialog.resize(size)
    
    def src_last_page(self):
        # Check if source is Vortex
        if self.source == 'Vortex':
            # Hide first page
            self.src_modmanagers_widget.hide()
            # Show Vortex page
            self.src_vortex_widget.show()
            # Disable next button
            self.src_next_button.setDisabled(True)

        # Load instances from source otherwise
        else:
            self.instances = []
            def process(psignal: qtc.Signal):
                if self.source == 'ModOrganizer 2 (MO2)':
                    self.instances = core.MO2Instance.get_instances(self)
            loading_dialog = LoadingDialog(self.source_dialog, self, lambda p: process(p), self.lang['loading_instances'])
            loading_dialog.exec()
            # Check if instances were found
            if self.instances:
                self.instances_box.clear()
                self.instances_box.addItems(self.instances)
                self.instances_box.setCurrentRow(0)
            # Go to first page otherwise
            else:
                qtw.QMessageBox.critical(self.source_dialog, self.lang['error'], self.lang['error_no_instances'])
                self.src_first_page()

            # Go to instances page
            self.src_modmanagers_widget.hide()
            self.src_instances_widget.show()

        # Bind next button to done
        self.src_next_button.clicked.disconnect()
        self.src_next_button.setText(self.lang['done'])
        self.src_next_button.clicked.connect(self.finish_src)
        self.src_next_button.setIcon(qtg.QIcon())

        # Bind back button to previous page
        self.src_back_button.clicked.connect(self.src_first_page)
        self.src_back_button.setDisabled(False)

        # Update dialog height
        size = self.source_dialog.sizeHint()
        size.setWidth(self.source_dialog.width())
        self.source_dialog.resize(size)

    def cancel_src(self, event=None):
        self.source_dialog.accept()

    def finish_src(self):
        instance_data = {} # keys: name, paths, mods, loadorder, custom executables
        
        if self.source == 'Vortex':
            instance_data['name'] = ""
            self.log.debug("Loading active Vortex profile...")
            instance_data['paths'] = {
                'staging_folder': self.staging_box.text(),
                'skyrim_ini': os.path.join(self.doc_path, 'Skyrim.ini'),
                'skyrim_prefs_ini': os.path.join(self.doc_path, 'SkyrimPrefs.ini')
            }
            stagefile = os.path.join(instance_data['paths']['staging_folder'], 'vortex.deployment.msgpack')
            if os.path.isfile(stagefile):
                instance_data['paths']['stagefile'] = stagefile
                self.modinstance = core.VortexInstance(self, instance_data)
                #self.stagefile = StageFile(stagefile)
                #self.stagefile.parse_file()
                #self.stagefile.get_modlist()
            else:
                qtw.QMessageBox.critical(self.source_dialog, self.lang['error'], self.lang['invalid_staging_folder'])
                return
            #instance_data['mods'] = self.stagefile.mods
            self.log.debug(f"Staging folder: {instance_data['paths']['staging_folder']}")
        elif self.source == 'ModOrganizer 2 (MO2)':
            instance_data['name'] = self.instances_box.currentItem().text()
            self.log.debug(f"Loading mod instance '{instance_data['name']}'...")
            self.log.debug(f"Mod manager: {self.source}")
            instance_path = os.path.join(os.getenv('LOCALAPPDATA'), 'ModOrganizer', instance_data['name'])
            instance_data['paths'] = {}
            # Get paths from instance ini file
            ini_file = os.path.join(instance_path, 'ModOrganizer.ini')
            with open(ini_file, 'r') as file:
                for line in file.readlines():
                    if line.startswith("base_directory="):
                        instance_data['paths']['instance_path'] = os.path.normpath(line.split("=", 1)[1].strip())
                        instance_path = instance_data['paths']['instance_path']
                    elif line.startswith("download_directory="):
                        instance_data['paths']['download_path'] = os.path.normpath(line.split("=", 1)[1])
            # Get mods from mods folder
            mods = [os.path.join(instance_path, 'mods', mod) for mod in os.listdir(os.path.join(instance_path, 'mods')) if os.path.isdir(os.path.join(instance_path, 'mods', mod))]
            instance_data['mods'] = mods
            self.modinstance = core.MO2Instance(self, instance_data)
            self.log.debug(f"Instance path: {instance_data['paths']['instance_path']}")
        else:
            raise Exception(f"Mod manager '{self.source}' is unsupported!")

        # Create source widget with instance details #################
        self.source_widget = qtw.QWidget()
        self.source_widget.setObjectName("panel")
        self.mainlayout.addWidget(self.source_widget, 1, 0)
        # Create layout
        self.source_layout = qtw.QGridLayout()
        self.source_layout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.source_widget.setLayout(self.source_layout)
        self.source_layout.setColumnStretch(1, 1)
        # Add label with mod manager name
        label = qtw.QLabel()
        label.setText(f"{self.lang['mod_manager']}:")
        self.source_layout.addWidget(label, 0, 0)
        manager_label = qtw.QLabel()
        manager_label.setText(self.source)
        self.source_layout.addWidget(manager_label, 0, 1)
        if self.modinstance.name:
            # Add label with instance name
            label = qtw.QLabel(f"{self.lang['instance_name']}:")
            self.source_layout.addWidget(label, 1, 0)
            instance_label = qtw.QLabel(self.modinstance.name)
            self.source_layout.addWidget(instance_label, 1, 1)
        # Add label with instance paths
        label = qtw.QLabel(self.lang['paths'])
        self.source_layout.addWidget(label, 2, 0)
        paths_label = qtw.QLabel()
        paths_label.setTextInteractionFlags(qtc.Qt.TextInteractionFlag.TextSelectableByMouse)
        paths_label.setCursor(qtg.QCursor(qtc.Qt.CursorShape.IBeamCursor))
        paths = ""
        for pathname, path in self.modinstance.paths.items():
            paths += f"\n{pathname}: {path}"
        paths_label.setText(paths.strip())
        self.source_layout.addWidget(paths_label, 2, 1)
        # Add label with number of mods
        label = qtw.QLabel("Mods:")
        self.source_layout.addWidget(label, 3, 0)
        mod_label = qtw.QLabel(str(len(self.modinstance.mods)))
        self.source_layout.addWidget(mod_label, 3, 1)
        ##############################################################

        # Disable add source button
        self.src_button.setDisabled(True)
        self.dst_button.setDisabled(False)

        # Close dialog
        self.source_dialog.accept()
    
    # Destination dialog #############################################
    def add_destination(self):
        # Create dialog to choose mod manager and instance/profile
        self.destination_dialog = qtw.QDialog(self.root)
        self.destination_dialog.setWindowTitle(f"{self.name} - {self.lang['select_destination']}")
        self.destination_dialog.setWindowIcon(self.root.windowIcon())
        self.destination_dialog.setModal(True)
        self.destination_dialog.setObjectName("root")
        #self.destination_dialog.setMinimumWidth(1000)
        self.destination_dialog.closeEvent = self.cancel_dst
        layout = qtw.QVBoxLayout(self.destination_dialog)
        self.destination_dialog.setLayout(layout)

        # Create widget for mod manager selection ####################
        self.dst_modmanagers_widget = qtw.QWidget()
        layout.addWidget(self.dst_modmanagers_widget)

        # Create layout for mod managers
        manager_layout = qtw.QGridLayout()
        columns = 2 # number of columns in grid
        self.dst_modmanagers_widget.setLayout(manager_layout)
        
        # Label with instruction
        label = qtw.QLabel(self.lang['select_destination_text'])
        label.setObjectName("titlelabel")
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        manager_layout.addWidget(label, 0, 0, 1, columns)

        buttons = []
        # Define functions for selection logic
        def set_dst(destination: str):
            self.destination = destination
            for button in buttons:
                if button.text() != destination:
                    button.setChecked(False)
                else:
                    button.setChecked(True)
        def func(destination):
            return lambda: set_dst(destination)

        # Create button for each supported mod manager
        for i, modmanager in enumerate(SUPPORTED_MODMANAGERS):
            button = qtw.QPushButton()
            button.setText(modmanager)
            # Disable button if it is source
            if modmanager == self.source:
                button.setDisabled(True)
            # Disable button if it is Vortex,
            # because Vortex is not supported as destination, yet
            if modmanager == 'Vortex':
                button.setDisabled(True)
                button.setToolTip("Work in Progress...")

            button.setCheckable(True)
            button.clicked.connect(func(modmanager))
            row = i // columns # calculate row
            col = i % columns # calculate column
            buttons.append(button)
            manager_layout.addWidget(button, row+1, col)
        
        # Select first mod manager that is not source as default
        for button in buttons:
            if (button.text() != self.source) and (button.text() != 'Vortex'):
                button.setChecked(True)
                self.destination = button.text()
                break
        ##############################################################

        # Create widget for instance settings ########################
        self.dst_instance_widget = qtw.QWidget()
        self.dst_instance_widget.hide()
        layout.addWidget(self.dst_instance_widget)

        # Add layout for instance settings
        instance_layout = qtw.QVBoxLayout()
        self.dst_instance_widget.setLayout(instance_layout)
        
        # Add layout for modes (copy mode or hardlink mode)
        mode_layout = qtw.QHBoxLayout()
        instance_layout.addLayout(mode_layout, 0)
        
        # Add widget for copy mode
        copy_mode_widget = qtw.QWidget()
        instance_layout.addWidget(copy_mode_widget, 1)

        # Add layout for copy mode
        copy_mode_layout = qtw.QGridLayout()
        copy_mode_widget.setLayout(copy_mode_layout)

        # Add inputbox for name
        label = qtw.QLabel(self.lang['instance_name'])
        copy_mode_layout.addWidget(label, 0, 0)
        self.dst_name_box = qtw.QLineEdit()
        self.dst_name_box.setText(self.modinstance.name)
        copy_mode_layout.addWidget(self.dst_name_box, 0, 1)
        
        # Add inputbox for instance path
        label = qtw.QLabel(self.lang['instance_path'])
        copy_mode_layout.addWidget(label, 1, 0)
        self.dst_path_box = qtw.QLineEdit()
        copy_mode_layout.addWidget(self.dst_path_box, 1, 1)

        # Add widget for hardlink mode
        hardlink_mode_widget = qtw.QWidget()
        hardlink_mode_widget.hide()
        instance_layout.addWidget(hardlink_mode_widget, 1)

        # Add button for copy mode
        copy_mode_button = qtw.QPushButton(self.lang['copy_mode'])
        copy_mode_button.clicked.connect(lambda: (
            hardlink_mode_button.setChecked(False),
            hardlink_mode_widget.hide(),
            copy_mode_widget.show(),
            copy_mode_button.setChecked(True)
        ))
        copy_mode_button.setCheckable(True)
        copy_mode_button.setChecked(True)
        mode_layout.addWidget(copy_mode_button)

        # Add button for hardlink mode
        hardlink_mode_button = qtw.QPushButton(self.lang['hardlink_mode'])
        hardlink_mode_button.clicked.connect(lambda: (
            copy_mode_button.setChecked(False),
            copy_mode_widget.hide(),
            hardlink_mode_widget.show(),
            hardlink_mode_button.setChecked(True)
        ))
        hardlink_mode_button.setDisabled(True)
        hardlink_mode_button.setToolTip("Work in progress...")
        hardlink_mode_button.setCheckable(True)
        mode_layout.addWidget(hardlink_mode_button)
        ##############################################################
        
        # Add spacing
        layout.addSpacing(25)
        
        # Add cancel and next button
        self.button_layout = qtw.QHBoxLayout()
        layout.addLayout(self.button_layout)
        # Cancel button
        self.dst_cancel_button = qtw.QPushButton()
        self.dst_cancel_button.setText(self.lang['cancel'])
        self.dst_cancel_button.clicked.connect(self.cancel_dst)
        self.button_layout.addWidget(self.dst_cancel_button)
        # Seperate cancel button with spacing
        self.button_layout.addSpacing(200)
        # Back button with icon
        self.dst_back_button = qtw.QPushButton()
        self.dst_back_button.setText(self.lang['back'])
        self.dst_back_button.setIcon(qta.icon('fa5s.chevron-left', color=self.theme['text_color']))
        self.dst_back_button.setDisabled(True)
        self.button_layout.addWidget(self.dst_back_button)
        # Next button with icon
        self.dst_next_button = qtw.QPushButton()
        self.dst_next_button.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
        self.dst_next_button.setText(self.lang['next'])
        self.dst_next_button.setIcon(qta.icon('fa5s.chevron-right', color=self.theme['text_color']))
        self.dst_next_button.clicked.connect(self.dst_last_page)
        self.button_layout.addWidget(self.dst_next_button)

        # Show popup
        self.destination_dialog.show()
    
    def cancel_dst(self, event=None):
        self.destination_dialog.accept()

    def dst_first_page(self):
        # Go to first page
        self.dst_instance_widget.hide()
        #self.src_vortex_widget.hide()
        self.dst_modmanagers_widget.show()

        # Update back button
        self.dst_back_button.setDisabled(True)
        self.dst_back_button.clicked.disconnect(self.dst_first_page)

        # Update next button
        #self.dst_next_button.clicked.disconnect(self.finish_dst)
        self.dst_next_button.setText(self.lang['next'])
        self.dst_next_button.clicked.connect(self.dst_last_page)
        self.dst_next_button.setIcon(qta.icon('fa5s.chevron-right', color=self.theme['text_color']))
        self.dst_next_button.setDisabled(False)

        # Update dialog height
        size = self.destination_dialog.sizeHint()
        size.setWidth(self.destination_dialog.width())
        self.destination_dialog.resize(size)
    
    def dst_last_page(self):

        # Go to instances page
        self.dst_modmanagers_widget.hide()
        self.dst_instance_widget.show()

        # Bind next button to done
        self.dst_next_button.clicked.disconnect(self.dst_last_page)
        self.dst_next_button.setText(self.lang['done'])
        #self.dst_next_button.clicked.connect(self.finish_dst)
        self.dst_next_button.setIcon(qtg.QIcon())

        # Bind back button to previous page
        self.dst_back_button.clicked.connect(self.dst_first_page)
        self.dst_back_button.setDisabled(False)

        # Update dialog height
        size = self.destination_dialog.sizeHint()
        size.setWidth(self.destination_dialog.width())
        self.destination_dialog.resize(size)
    
    # Settings functions #############################################
    def open_settings(self):
        # create popup window
        self.settings_popup = qtw.QDialog(self.root)
        self.settings_popup.setModal(True)
        self.settings_popup.setStyleSheet(self.stylesheet)
        self.settings_popup.setWindowTitle(f"{self.name} - {self.lang['settings']}...")
        self.settings_popup.setWindowIcon(self.root.windowIcon())
        self.settings_popup.setObjectName("root")
        self.settings_popup.setMinimumWidth(600)
        self.settings_popup.closeEvent = self.cancel_settings
        layout = qtw.QVBoxLayout(self.settings_popup)
        self.settings_popup.setLayout(layout)

        # create detail frame with grid layout
        detail_frame = qtw.QWidget()
        detail_frame.setObjectName("detailframe")
        detail_layout = qtw.QGridLayout()
        detail_frame.setLayout(detail_layout)
        layout.addWidget(detail_frame, stretch=1)
        self.settings_widgets = []
        for r, (config, value) in enumerate(self.config.items()):
            label = qtw.QLabel()
            #label.setObjectName(config)
            label.setText(self.lang.get(config, config))
            detail_layout.addWidget(label, r, 0)
            if isinstance(value, bool):
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems([self.lang['true'], self.lang['false']])
                dropdown.setCurrentText(self.lang[str(value).lower()])
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(lambda e: self.on_setting_change())
                dropdown.bool = None
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif isinstance(value, int):
                spinbox = qtw.QSpinBox()
                spinbox.setObjectName(config)
                spinbox.setRange(1, 100)
                spinbox.setValue(value)
                spinbox.valueChanged.connect(lambda e: self.on_setting_change())
                self.settings_widgets.append(spinbox)
                detail_layout.addWidget(spinbox, r, 1)
            elif config == 'ui_mode':
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems([self.lang['dark'], self.lang['light'], "System"])
                dropdown.setCurrentText(self.lang.get(value.lower(), value))
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(lambda e: self.on_setting_change())
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif config == 'language':
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems([self.lang['de-DE'], self.lang['en-US'], "System"])
                dropdown.setCurrentText(self.lang.get(value, value))
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(lambda e: self.on_setting_change())
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif config == 'log_level':
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems([loglevel.capitalize() for loglevel in LOG_LEVELS.values()])
                dropdown.setCurrentText(value.capitalize())
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(lambda e: self.on_setting_change())
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif config == 'accent_color':
                button = qtw.QPushButton()
                button.setObjectName(config)
                button.color = self.config['accent_color']
                def choose_color():
                    colordialog = qtw.QColorDialog(self.settings_popup)
                    colordialog.setOption(colordialog.ColorDialogOption.DontUseNativeDialog, True)
                    colordialog.setCustomColor(0, qtg.QColor('#f38064'))
                    color = button.color
                    if qtg.QColor.isValidColor(color):
                        colordialog.setCurrentColor(qtg.QColor(color))
                    if colordialog.exec():
                        button.color = colordialog.currentColor().name(qtg.QColor.NameFormat.HexRgb)
                        button.setIcon(qta.icon('mdi6.square-rounded', color=button.color))        
                        self.on_setting_change()
                button.setText(self.lang['select_color'])
                button.setIcon(qta.icon('mdi6.square-rounded', color=button.color))
                button.setIconSize(qtc.QSize(24, 24))
                button.clicked.connect(choose_color)
                self.settings_widgets.append(button)
                detail_layout.addWidget(button, r, 1)

        # create frame with cancel and done button
        command_frame = qtw.QWidget()
        command_layout = qtw.QHBoxLayout(command_frame)
        command_frame.setLayout(command_layout)
        layout.addWidget(command_frame)
        # cancel
        cancel_button = qtw.QPushButton(self.lang['cancel'])
        cancel_button.clicked.connect(self.cancel_settings)
        command_layout.addWidget(cancel_button)
        # done
        self.settings_done_button = qtw.QPushButton(self.lang['done'])
        self.settings_done_button.clicked.connect(self.finish_settings)
        self.settings_done_button.setDisabled(True)
        command_layout.addWidget(self.settings_done_button)

        self.settings_popup.setFixedHeight(self.settings_popup.sizeHint().height())

        # update changes variable
        self.unsaved_settings = False

        # show popup
        self.settings_popup.exec()
    
    def finish_settings(self):
        config = self.config.copy()
        for widget in self.settings_widgets:
            if isinstance(widget, qtw.QComboBox):
                if hasattr(widget, 'bool'):
                    config[widget.objectName()] = (widget.currentText() == self.lang['true'])
                elif widget.objectName() == 'ui_mode':
                    config[widget.objectName()] = 'System' if widget.currentText() == 'System' else ('Dark' if widget.currentText() == self.lang['dark'] else 'Light')
                elif widget.objectName() == 'language':
                    config[widget.objectName()] = 'System' if widget.currentText() == 'System' else ('de-DE' if widget.currentText() == self.lang['de-DE'] else 'en-US')
                elif widget.objectName() == 'log_level':
                    config[widget.objectName()] = widget.currentText().lower()
            elif isinstance(widget, qtw.QSpinBox):
                config[widget.objectName()] = widget.value()
            elif isinstance(widget, qtw.QPushButton):
                config[widget.objectName()] = widget.color
        
        # save config
        if config['ui_mode'] != self.config['ui_mode']:
            self._theme.set_mode(config['ui_mode'].lower())
            self.theme = self._theme.load_theme()
            self.stylesheet = self._theme.load_stylesheet()
            self.root.setStyleSheet(self.stylesheet)
            self.file_menu.setStyleSheet(self.stylesheet)
            self.help_menu.setStyleSheet(self.stylesheet)
            self.theme_change_sign.emit()
        self.config = config
        with open(self.con_path, 'w') as file:
            file.write(json.dumps(self.config, indent=4))
        self.unsaved_settings = False
        self.log.info("Saved config to file.")

        # update accent color
        self.theme['accent_color'] = self.config['accent_color']
        self.stylesheet = self._theme.load_stylesheet()
        self.root.setStyleSheet(self.stylesheet)
        # Fix link color
        palette = self.palette()
        palette.setColor(palette.ColorRole.Link, qtg.QColor(self.config['accent_color']))
        self.setPalette(palette)

        # close settings popup
        self.settings_popup.accept()
        self.settings_popup = None
    
    def on_setting_change(self):
        if (not self.unsaved_settings) and (self.settings_popup is not None):
            self.unsaved_settings = True
            self.settings_done_button.setDisabled(False)
            self.settings_popup.setWindowTitle(f"{self.settings_popup.windowTitle()}*")
    
    def cancel_settings(self, event=None):
        if self.unsaved_settings:
            message_box = qtw.QMessageBox(self.settings_popup)
            message_box.setWindowIcon(self.root.windowIcon())
            message_box.setStyleSheet(self.stylesheet)
            message_box.setWindowTitle(self.lang['cancel'])
            message_box.setText(self.lang['unsaved_cancel'])
            message_box.setStandardButtons(qtw.QMessageBox.StandardButton.No | qtw.QMessageBox.StandardButton.Yes)
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.No)
            message_box.button(qtw.QMessageBox.StandardButton.No).setText(self.lang['no'])
            message_box.button(qtw.QMessageBox.StandardButton.Yes).setText(self.lang['yes'])
            choice = message_box.exec()
            
            if choice == qtw.QMessageBox.StandardButton.Yes:
                self.settings_popup.accept()
                self.settings_popup = None
            elif event:
                event.ignore()
        else:
            self.settings_popup.accept()
            self.settings_popup = None
    ##################################################################
    
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
    
    def exit(self, event: qtg.QCloseEvent=None, silent=False):
        confirmation = silent
        if not silent:
            if self.unsaved_changes:
                message_box = qtw.QMessageBox(self.root)
                message_box.setWindowIcon(self.root.windowIcon())
                message_box.setStyleSheet(self.stylesheet)
                message_box.setWindowTitle(self.lang['exit'])
                message_box.setText(self.lang['unsaved_exit'])
                message_box.setStandardButtons(qtw.QMessageBox.StandardButton.Cancel | qtw.QMessageBox.StandardButton.Save | qtw.QMessageBox.StandardButton.Discard)
                message_box.setDefaultButton(qtw.QMessageBox.StandardButton.Save)
                message_box.button(qtw.QMessageBox.StandardButton.Cancel).setText(self.lang['cancel'])
                message_box.button(qtw.QMessageBox.StandardButton.Save).setText(self.lang['save_and_exit'])
                message_box.button(qtw.QMessageBox.StandardButton.Discard).setText(self.lang['exit_without_save'])
                choice = message_box.exec()
                
                # Handle the user's choice
                if choice == qtw.QMessageBox.StandardButton.Save:
                    # Save the file and exit
                    self.save_file()
                    confirmation = True
                elif choice == qtw.QMessageBox.StandardButton.Discard:
                    # Exit without saving
                    confirmation = True
                else:
                    # Cancel the close event
                    confirmation = False
            else:
                confirmation = True

        if confirmation:
            if event:
                self.root_close(event)
            else:
                self.root.destroy()
            super().exit()
        elif event:
            event.ignore()

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


# Create class to copy stdout to log file ############################
class StdoutPipe:
    def __init__(self, app, tag="stdout", encoding="utf8"):
        self.app = app
        self.tag = tag
        self.encoding = encoding
        self.file = open(self.app.log_path, "a")
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    def __del__(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        self.file.close()
    def write(self, string):
        if string not in self.app.protocol:
            self.app.protocol += string
            try:
                self.file.write(string)
            except Exception as ex:
                print(f"Logging error occured: {str(ex)}")
        try:
            self.stdout.write(string)
        except AttributeError:
            pass
    def flush(self):
        self.file.flush()


# Create class for loading dialog ####################################
class LoadingDialog(qtw.QProgressDialog):
    start_signal = qtc.Signal()
    stop_signal = qtc.Signal()
    progress_signal = qtc.Signal(dict)

    def __init__(self, parent: qtw.QWidget, app: MainApp, func: Callable, text: str):
        super().__init__(parent)
        # Set up variables
        self.app = app
        self.success = True
        self.func = lambda: (self.start_signal.emit(), func(self.progress_signal), self.stop_signal.emit())
        #self.func = lambda: func(self.progress_signal)
        self.Thread = LoadingDialogThread(self, target=self.func, daemon=True, name='BackgroundThread')
        self._text = text
        
        # Connect signals
        self.start_signal.connect(self.on_start)
        self.stop_signal.connect(self.on_finish)
        self.progress_signal.connect(self.setProgress)

        # Configure dialog
        self.setWindowTitle(self.app.name)
        self.setWindowIcon(self.app.root.windowIcon())
        self.setStyleSheet(self.app.stylesheet)
        self.setCancelButton(None)
        self.setWindowFlag(qtc.Qt.WindowType.WindowCloseButtonHint, False)

    def setLabelText(self, text: str):
        super().setLabelText(text)
        self.setFixedSize(self.sizeHint())
        self.move(self.app.primaryScreen().availableGeometry().center() - self.rect().center())
    
    def setText(self, text: str):
        if text.strip():
            text = text.strip().split('(')[1].strip(')')
            self.setLabelText(f"{self._text} ({text})")
    
    def setProgress(self, progress: dict):
        value = progress.get('value', None)
        max = progress.get('max', None)
        text = progress.get('text', "")
        if max is not None:
            self.setRange(0, int(max))
        if value is not None:
            self.setValue(int(value))
        if text.strip():
            self.setLabelText(f"{self._text} ({text})")
        else:
            self.setLabelText(self._text)

    def exec(self):
        #self.start_signal.emit()
        self.Thread.start()

        super().exec()

        if self.Thread.exception is not None:
            raise self.Thread.exception
    
    def on_start(self):
        self.setRange(0, 0)
        self.setLabelText(self._text)
        self.show()
    
    def on_finish(self):
        self.setRange(0, 1)
        self.setValue(1)
        self.cancel()


class LoadingDialogThread(threading.Thread):
    exception = None
    
    def __init__(self, dialog: LoadingDialog, target: Callable, *args, **kwargs):
        super().__init__(target=target, *args, **kwargs)

        self.dialog = dialog
    
    def run(self):
        try:
            super().run()
        except Exception as ex:
            self.exception = ex
            self.dialog.stop_signal.emit()


# Create class for ui theme ##########################################
class Theme:
    """Class for ui theme. Manages theme and stylesheet."""

    default_dark_theme = {
        'primary_bg': '#202020',
        'secondary_bg': '#2d2d2d',
        'tertiary_bg': '#383838',
        'highlight_bg': '#696969',
        'accent_color': '#f38064',
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
        'accent_color': '#f38064',
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
    app = MainApp()
    app.exec()
