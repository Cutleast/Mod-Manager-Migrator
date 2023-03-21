"""
Part of MMM. Contains dialogs.
"""

import json
import os
import threading
import time
from glob import glob
from typing import Callable

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import core
import main


# Source dialog ##################################################
class SourceDialog(qtw.QDialog):
    def __init__(self, parent: qtw.QWidget, app: main.MainApp):
        super().__init__(parent)

        self.app = app

        # Create dialog to choose mod manager and instance/profile
        self.setWindowTitle(f"{self.app.name} - {self.app.lang['select_source']}")
        self.setWindowIcon(self.app.root.windowIcon())
        self.setModal(True)
        self.setObjectName("root")
        #self.setMinimumWidth(1000)
        layout = qtw.QVBoxLayout(self)
        self.setLayout(layout)

        # Create widget for mod manager selection ####################
        self.modmanagers_widget = qtw.QWidget()
        layout.addWidget(self.modmanagers_widget)

        # Create layout for mod managers
        manager_layout = qtw.QGridLayout()
        columns = 2 # number of columns in grid
        self.modmanagers_widget.setLayout(manager_layout)
        
        # Label with instruction
        label = qtw.QLabel(self.app.lang['select_source_text'])
        label.setObjectName("titlelabel")
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        manager_layout.addWidget(label, 0, 0, 1, columns)

        buttons = []
        # Define functions for selection logic
        def set_src(source: str):
            self.app.source = source
            for button in buttons:
                if button.text() != source:
                    button.setChecked(False)
                else:
                    button.setChecked(True)
        def func(source):
            return lambda: set_src(source)

        # Create button for each supported mod manager
        for i, modmanager in enumerate(main.SUPPORTED_MODMANAGERS):
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
        self.app.source = main.SUPPORTED_MODMANAGERS[0]
        ##############################################################

        # Create widget for instance selection #######################
        self.instances_widget = qtw.QWidget()
        self.instances_widget.hide()
        layout.addWidget(self.instances_widget)
        # Create layout
        self.instances_layout = qtw.QVBoxLayout()
        self.instances_widget.setLayout(self.instances_layout)
        # Add label with instruction
        label = qtw.QLabel()
        label.setText(self.app.lang['select_src_instance_text'])
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
        self.vortex_widget = qtw.QWidget()
        self.vortex_widget.hide()
        layout.addWidget(self.vortex_widget)

        # Create layout
        self.src_vortex_layout = qtw.QGridLayout()
        self.vortex_widget.setLayout(self.src_vortex_layout)

        # Add label with instruction
        label = qtw.QLabel(self.app.lang['select_src_instance_text'])
        label.setObjectName("titlelabel")
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        self.src_vortex_layout.addWidget(label, 0, 0, 1, 3)

        # Add label with notice for Vortex users
        label = qtw.QLabel(self.app.lang['vortex_notice'])
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        self.src_vortex_layout.addWidget(label, 1, 0, 1, 3)

        # Add lineedit for staging path
        label = qtw.QLabel(self.app.lang['staging_folder'])
        self.src_vortex_layout.addWidget(label, 2, 0)
        self.stagefolder_box = qtw.QLineEdit()
        self.src_vortex_layout.addWidget(self.stagefolder_box, 2, 1)
        # Bind staging path to next/done button
        def on_stagefolder_edit(text: str):
            # Enable button if path is valid
            if os.path.isdir(text):
                self.next_button.setDisabled(False)
            # Disable it otherwise
            else:
                self.next_button.setDisabled(True)
        self.stagefolder_box.textChanged.connect(on_stagefolder_edit)
        # Add browse function
        def browse_stagefolder():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang['browse'])
            file_dialog.setDirectory(os.path.join(os.getenv('APPDATA'), 'Vortex', 'skyrimse'))
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.stagefolder_box.setText(folder)
        # Add browse button
        button = qtw.QPushButton()
        button.setText(self.app.lang['browse'])
        button.clicked.connect(browse_stagefolder)
        self.src_vortex_layout.addWidget(button, 2, 2)

        # Add lineedit for optional download path
        label = qtw.QLabel(self.app.lang['optional_download_path'])
        self.src_vortex_layout.addWidget(label, 3, 0)
        self.dlpath_box = qtw.QLineEdit()
        self.src_vortex_layout.addWidget(self.dlpath_box, 3, 1)
        # Bind staging path to next/done button
        def on_dlpath_edit(text: str):
            # Enable button if path is valid or empty
            if os.path.isdir(text) or (not text.strip()):
                self.next_button.setDisabled(False)
            # Disable it otherwise
            else:
                self.next_button.setDisabled(True)
        self.dlpath_box.textChanged.connect(on_dlpath_edit)
        # Add browse function
        def browse_dlpath():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang['browse'])
            file_dialog.setDirectory(os.path.join(os.getenv('APPDATA'), 'Vortex', 'skyrimse'))
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.dlpath_box.setText(folder)
        # Add browse button
        button = qtw.QPushButton()
        button.setText(self.app.lang['browse'])
        button.clicked.connect(browse_dlpath)
        self.src_vortex_layout.addWidget(button, 3, 2)
        ##############################################################
        
        # Add spacing
        layout.addSpacing(25)
        
        # Add cancel and next button
        self.button_layout = qtw.QHBoxLayout()
        layout.addLayout(self.button_layout)
        # Cancel button
        self.src_cancel_button = qtw.QPushButton()
        self.src_cancel_button.setText(self.app.lang['cancel'])
        self.src_cancel_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.src_cancel_button)
        # Seperate cancel button with spacing
        self.button_layout.addSpacing(200)
        # Back button with icon
        self.back_button = qtw.QPushButton()
        self.back_button.setText(self.app.lang['back'])
        self.back_button.setIcon(qta.icon('fa5s.chevron-left', color=self.app.theme['text_color']))
        self.back_button.setDisabled(True)
        self.button_layout.addWidget(self.back_button)
        # Next button with icon
        self.next_button = qtw.QPushButton()
        self.next_button.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
        self.next_button.setText(self.app.lang['next'])
        self.next_button.setIcon(qta.icon('fa5s.chevron-right', color=self.app.theme['text_color']))
        self.next_button.clicked.connect(self.last_page)
        self.button_layout.addWidget(self.next_button)
        # Bind next button to instances list box
        self.instances_box.itemSelectionChanged.connect(lambda: self.next_button.setDisabled(False))

        # Show popup
        #self.show()
    
    def first_page(self):
        # Go to first page
        self.instances_widget.hide()
        self.vortex_widget.hide()
        self.modmanagers_widget.show()

        # Update back button
        self.back_button.setDisabled(True)
        self.back_button.clicked.disconnect()

        # Update next button
        self.next_button.clicked.disconnect()
        self.next_button.setText(self.app.lang['next'])
        self.next_button.clicked.connect(self.last_page)
        self.next_button.setIcon(qta.icon('fa5s.chevron-right', color=self.app.theme['text_color']))
        self.next_button.setDisabled(False)

        # Update dialog height
        size = self.sizeHint()
        size.setWidth(self.width())
        self.resize(size)

        # Move dialog to center of screen
        core.center(self)
    
    def last_page(self):
        # Check if source is Vortex
        if self.app.source == 'Vortex':
            # Hide first page
            self.modmanagers_widget.hide()
            # Show Vortex page
            self.vortex_widget.show()
            # Disable next button
            self.next_button.setDisabled(True)

        # Load instances from source otherwise
        else:
            self.instances = []
            def process(psignal: qtc.Signal):
                if self.app.source == 'ModOrganizer':
                    self.instances = core.MO2Instance.get_instances(self)
            loading_dialog = LoadingDialog(self, self.app, lambda p: process(p), self.app.lang['loading_instances'])
            loading_dialog.exec()
            # Check if instances were found
            if self.instances:
                self.instances_box.clear()
                self.instances_box.addItems(self.instances)
                self.instances_box.setCurrentRow(0)
            # Go to first page otherwise
            else:
                qtw.QMessageBox.critical(self, self.app.lang['error'], self.app.lang['error_no_instances'])
                self.first_page()

            # Go to instances page
            self.modmanagers_widget.hide()
            self.instances_widget.show()

        # Bind next button to done
        self.next_button.clicked.disconnect()
        self.next_button.setText(self.app.lang['done'])
        self.next_button.clicked.connect(self.finish)
        self.next_button.setIcon(qtg.QIcon())
        # Enable next button if path is valid
        if os.path.isdir(self.stagefolder_box.text()):
            self.next_button.setDisabled(False)
        # Disable it otherwise
        else:
            self.next_button.setDisabled(True)

        # Bind back button to previous page
        self.back_button.clicked.connect(self.first_page)
        self.back_button.setDisabled(False)

        # Update dialog height
        size = self.sizeHint()
        size.setWidth(self.width())
        self.resize(size)

        # Move dialog to center of screen
        core.center(self)

    def finish(self):
        instance_data = {} # keys: name, paths, mods, loadorder, custom executables
        
        if self.app.source == 'Vortex':
            instance_data['name'] = "Migrated Vortex Instance"
            self.app.log.debug("Loading active Vortex profile...")
            instance_data['paths'] = {
                'staging_folder': self.stagefolder_box.text(),
                'instance_path': self.stagefolder_box.text(),
                'download_path': self.dlpath_box.text(),
                'skyrim_ini': os.path.join(self.app.doc_path, 'Skyrim.ini'),
                'skyrim_prefs_ini': os.path.join(self.app.doc_path, 'SkyrimPrefs.ini')
            }
            stagefile = os.path.join(instance_data['paths']['staging_folder'], 'vortex.deployment.msgpack')
            if os.path.isfile(stagefile):
                instance_data['paths']['stagefile'] = stagefile
                def process(psignal: qtc.Signal):
                    progress = {
                        'text': self.app.lang['loading_stagingfolder']
                    }
                    psignal.emit(progress)
                    self.app.src_modinstance = core.VortexInstance(self.app, instance_data)
                loadingdialog = LoadingDialog(self, self.app, process)
                loadingdialog.exec()
            else:
                qtw.QMessageBox.critical(self, self.app.lang['error'], self.app.lang['invalid_staging_folder'])
                return
            #instance_data['mods'] = self.stagefile.mods
            self.app.log.debug(f"Staging folder: {instance_data['paths']['staging_folder']}")
        elif self.app.source == 'ModOrganizer':
            instance_data['name'] = self.instances_box.currentItem().text()
            self.app.log.debug(f"Loading mod instance '{instance_data['name']}'...")
            self.app.log.debug(f"Mod manager: {self.app.source}")
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
            self.app.src_modinstance = core.MO2Instance(self.app, instance_data)
            self.app.log.debug(f"Instance path: {instance_data['paths']['instance_path']}")
        else:
            raise Exception(f"Mod manager '{self.app.source}' is unsupported!")

        # Create source widget with instance details #################
        if (item := self.app.mainlayout.itemAtPosition(1, 0)) is not None:
            item.widget().destroy()
        self.source_widget = qtw.QWidget()
        self.source_widget.setObjectName("panel")
        self.app.mainlayout.addWidget(self.source_widget, 1, 0)
        # Create layout
        self.source_layout = qtw.QGridLayout()
        self.source_layout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.source_widget.setLayout(self.source_layout)
        self.source_layout.setColumnStretch(1, 1)
        # Add label with mod manager name
        label = qtw.QLabel()
        label.setText(f"{self.app.lang['mod_manager']}:")
        self.source_layout.addWidget(label, 0, 0)
        manager_label = qtw.QLabel()
        manager_label.setText(self.app.source)
        self.source_layout.addWidget(manager_label, 0, 1)
        if self.app.src_modinstance.name:
            # Add label with instance name
            label = qtw.QLabel(f"{self.app.lang['instance_name']}:")
            self.source_layout.addWidget(label, 1, 0)
            instance_label = qtw.QLabel(self.app.src_modinstance.name)
            self.source_layout.addWidget(instance_label, 1, 1)
        # Add label with instance paths
        label = qtw.QLabel(f"{self.app.lang['paths']}:")
        self.source_layout.addWidget(label, 2, 0)
        paths_label = qtw.QLabel()
        paths_label.setTextInteractionFlags(qtc.Qt.TextInteractionFlag.TextSelectableByMouse)
        paths_label.setCursor(qtg.QCursor(qtc.Qt.CursorShape.IBeamCursor))
        paths = ""
        for pathname, path in self.app.src_modinstance.paths.items():
            if path.strip():
                paths += f"\n{pathname}: {path}"
        paths_label.setText(paths.strip())
        self.source_layout.addWidget(paths_label, 2, 1)
        # Add label with number of mods
        label = qtw.QLabel("Mods:")
        self.source_layout.addWidget(label, 3, 0)
        mod_label = qtw.QLabel(str(len(self.app.src_modinstance.mods)))
        self.source_layout.addWidget(mod_label, 3, 1)
        ##############################################################

        # Disable add source button
        #self.src_button.setDisabled(True)
        self.app.src_button.setText(self.app.lang['edit_source'])
        self.app.src_button.clicked.disconnect()
        self.app.src_button.clicked.connect(self.edit)
        self.app.dst_button.setDisabled(False)

        # Close dialog
        self.accept()
    
    def edit(self):
        self.show()


# Create class for destination dialog ################################
class DestinationDialog(qtw.QDialog):
    def __init__(self, parent: qtw.QWidget, app: main.MainApp):
        super().__init__(parent)

        self.app = app

        # Create dialog to choose mod manager and instance/profile
        self.setWindowTitle(f"{self.app.name} - {self.app.lang['select_destination']}")
        self.setWindowIcon(self.app.root.windowIcon())
        self.setModal(True)
        self.setObjectName("root")
        self.setMinimumWidth(1000)
        layout = qtw.QVBoxLayout(self)
        self.setLayout(layout)

        # Create widget for mod manager selection ####################
        self.mod_managers_widget = qtw.QWidget()
        layout.addWidget(self.mod_managers_widget)

        # Create layout for mod managers
        manager_layout = qtw.QGridLayout()
        columns = 2 # number of columns in grid
        self.mod_managers_widget.setLayout(manager_layout)
        
        # Label with instruction
        label = qtw.QLabel(self.app.lang['select_destination_text'])
        label.setObjectName("titlelabel")
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        manager_layout.addWidget(label, 0, 0, 1, columns)

        buttons = []
        # Define functions for selection logic
        def set_dst(destination: str):
            self.app.destination = destination
            for button in buttons:
                if button.text() != destination:
                    button.setChecked(False)
                else:
                    button.setChecked(True)
        def func(destination):
            return lambda: set_dst(destination)

        # Create button for each supported mod manager
        for i, modmanager in enumerate(main.SUPPORTED_MODMANAGERS):
            button = qtw.QPushButton()
            button.setText(modmanager)
            # Disable button if it is source
            if modmanager == self.app.source:
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
            if (button.text() != self.app.source) and (button.text() != 'Vortex'):
                button.setChecked(True)
                self.app.destination = button.text()
                break
        ##############################################################

        # Create widget for instance settings ########################
        self.instances_widget = qtw.QWidget()
        self.instances_widget.hide()
        layout.addWidget(self.instances_widget)

        # Add layout for instance settings
        instance_layout = qtw.QVBoxLayout()
        self.instances_widget.setLayout(instance_layout)
        # Add layout for modes (copy mode or hardlink mode)
        mode_layout = qtw.QHBoxLayout()
        instance_layout.addLayout(mode_layout, 0)
        # Add layout for instance settings
        details_layout = qtw.QGridLayout()
        instance_layout.addLayout(details_layout, 1)

        # Add info label for hardlink mode
        hardlink_notice = qtw.QLabel(self.app.lang['hardlink_notice'])
        hardlink_notice.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        details_layout.addWidget(hardlink_notice, 0, 0, 1, 3)
        # Add info label for copy mode
        copy_notice = qtw.QLabel(self.app.lang['copy_notice'])
        copy_notice.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        copy_notice.hide()
        details_layout.addWidget(copy_notice, 1, 0, 1, 3)

        # Add inputbox for name
        label = qtw.QLabel(self.app.lang['instance_name'])
        details_layout.addWidget(label, 2, 0)
        self.name_box = qtw.QLineEdit()
        self.name_box.setText(self.app.src_modinstance.name)
        details_layout.addWidget(self.name_box, 2, 1)
        
        # Add inputbox for instance path
        label = qtw.QLabel(self.app.lang['instance_path'])
        details_layout.addWidget(label, 3, 0)
        self.path_box = qtw.QLineEdit()
        self.path_box.setText(os.path.join(os.getenv('LOCALAPPDATA'), self.app.destination, self.name_box.text()))
        details_layout.addWidget(self.path_box, 3, 1)
        def browse_path():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang['browse'])
            #file_dialog.setDirectory(os.path.join(os.getenv('LOCALAPPDATA'), self.app.destination, self.name_box.text(), 'downloads'))
            file_dialog.setDirectory(self.path_box.text())
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.path_box.setText(folder)
                self.name_box.setText(os.path.basename(folder))
                self.dlpath_box.setText(os.path.join(folder, 'downloads'))
                self.modspath_box.setText(os.path.join(folder, 'mods'))
                self.profilespath_box.setText(os.path.join(folder, 'profiles'))
                self.overwritepath_box.setText(os.path.join(folder, 'overwrite'))
        browse_button = qtw.QPushButton(self.app.lang['browse'])
        browse_button.clicked.connect(browse_path)
        details_layout.addWidget(browse_button, 3, 2)

        # Add inputbox for downloads path
        label = qtw.QLabel(self.app.lang['download_path'])
        details_layout.addWidget(label, 4, 0)
        self.dlpath_box = qtw.QLineEdit()
        self.dlpath_box.setText(os.path.join(self.path_box.text(), 'downloads'))
        details_layout.addWidget(self.dlpath_box, 4, 1)
        def browse_dlpath():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang['browse'])
            #file_dialog.setDirectory(os.path.join(os.getenv('LOCALAPPDATA'), self.app.destination, self.name_box.text(), 'downloads'))
            file_dialog.setDirectory(self.dlpath_box.text())
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.dlpath_box.setText(folder)
        browse_button = qtw.QPushButton(self.app.lang['browse'])
        browse_button.clicked.connect(browse_dlpath)
        details_layout.addWidget(browse_button, 4, 2)

        # Add inputbox for mods path
        label = qtw.QLabel(self.app.lang['mods_path'])
        details_layout.addWidget(label, 5, 0)
        self.modspath_box = qtw.QLineEdit()
        self.modspath_box.setText(os.path.join(self.path_box.text(), 'mods'))
        details_layout.addWidget(self.modspath_box, 5, 1)
        def browse_modspath():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang['browse'])
            #file_dialog.setDirectory(os.path.join(os.getenv('LOCALAPPDATA'), self.app.destination, self.name_box.text(), 'mods'))
            file_dialog.setDirectory(self.modspath_box.text())
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.modspath_box.setText(folder)
        browse_button = qtw.QPushButton(self.app.lang['browse'])
        browse_button.clicked.connect(browse_modspath)
        details_layout.addWidget(browse_button, 5, 2)

        # Add inputbox for profiles path
        label = qtw.QLabel(self.app.lang['profiles_path'])
        details_layout.addWidget(label, 6, 0)
        self.profilespath_box = qtw.QLineEdit()
        self.profilespath_box.setText(os.path.join(self.path_box.text(), 'profiles'))
        details_layout.addWidget(self.profilespath_box, 6, 1)
        def browse_profilespath():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang['browse'])
            #file_dialog.setDirectory(os.path.join(os.getenv('LOCALAPPDATA'), self.app.destination, self.name_box.text(), 'profiles'))
            file_dialog.setDirectory(self.profilespath_box.text())
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.profilespath_box.setText(folder)
        browse_button = qtw.QPushButton(self.app.lang['browse'])
        browse_button.clicked.connect(browse_profilespath)
        details_layout.addWidget(browse_button, 6, 2)

        # Add inputbox for overwrite path
        label = qtw.QLabel(self.app.lang['overwrite_path'])
        details_layout.addWidget(label, 7, 0)
        self.overwritepath_box = qtw.QLineEdit()
        self.overwritepath_box.setText(os.path.join(self.path_box.text(), 'overwrite'))
        details_layout.addWidget(self.overwritepath_box, 7, 1)
        def browse_overwritepath():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang['browse'])
            #file_dialog.setDirectory(os.path.join(os.getenv('LOCALAPPDATA'), self.app.destination, self.name_box.text(), 'overwrite'))
            file_dialog.setDirectory(self.overwritepath_box.text())
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.overwritepath_box.setText(folder)
        browse_button = qtw.QPushButton(self.app.lang['browse'])
        browse_button.clicked.connect(browse_overwritepath)
        details_layout.addWidget(browse_button, 7, 2)

        # Add widget for hardlink mode
        hardlink_mode_widget = qtw.QWidget()
        hardlink_mode_widget.hide()
        instance_layout.addWidget(hardlink_mode_widget, 1)

        # Add button for hardlink mode
        hardlink_mode_button = qtw.QPushButton(self.app.lang['hardlink_mode'])
        hardlink_mode_button.clicked.connect(lambda: (
            copy_mode_button.setChecked(False),
            copy_notice.hide(),
            hardlink_notice.show(),
            hardlink_mode_button.setChecked(True),
            self.app.set_mode('hardlink'),
        ))
        hardlink_mode_button.setCheckable(True)
        hardlink_mode_button.setChecked(True)
        mode_layout.addWidget(hardlink_mode_button)

        # Add button for copy mode
        copy_mode_button = qtw.QPushButton(self.app.lang['copy_mode'])
        copy_mode_button.clicked.connect(lambda: (
            hardlink_mode_button.setChecked(False),
            hardlink_notice.hide(),
            copy_notice.show(),
            copy_mode_button.setChecked(True),
            self.app.set_mode('copy'),
        ))
        copy_mode_button.setCheckable(True)
        mode_layout.addWidget(copy_mode_button)

        ##############################################################
        
        # Add spacing
        layout.addSpacing(25)
        
        # Add cancel and next button
        self.button_layout = qtw.QHBoxLayout()
        layout.addLayout(self.button_layout)
        # Cancel button
        self.cancel_button = qtw.QPushButton()
        self.cancel_button.setText(self.app.lang['cancel'])
        self.cancel_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.cancel_button)
        # Seperate cancel button with spacing
        self.button_layout.addSpacing(200)
        # Back button with icon
        self.back_button = qtw.QPushButton()
        self.back_button.setText(self.app.lang['back'])
        self.back_button.setIcon(qta.icon('fa5s.chevron-left', color=self.app.theme['text_color']))
        self.back_button.setDisabled(True)
        self.button_layout.addWidget(self.back_button)
        # Next button with icon
        self.next_button = qtw.QPushButton()
        self.next_button.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
        self.next_button.setText(self.app.lang['next'])
        self.next_button.setIcon(qta.icon('fa5s.chevron-right', color=self.app.theme['text_color']))
        self.next_button.clicked.connect(self.last_page)
        self.button_layout.addWidget(self.next_button)

        # Show popup
        #self.show()

    def first_page(self):
        # Go to first page
        self.instances_widget.hide()
        #self.vortex_widget.hide()
        self.mod_managers_widget.show()

        # Update back button
        self.back_button.setDisabled(True)
        self.back_button.clicked.disconnect(self.first_page)

        # Update next button
        self.next_button.clicked.disconnect(self.finish)
        self.next_button.setText(self.app.lang['next'])
        self.next_button.clicked.connect(self.last_page)
        self.next_button.setIcon(qta.icon('fa5s.chevron-right', color=self.app.theme['text_color']))
        self.next_button.setDisabled(False)

        # Update dialog height
        size = self.sizeHint()
        size.setWidth(self.width())
        self.resize(size)

        # Move dialog to center of screen
        core.center(self)
    
    def last_page(self):

        # Go to instances page
        self.mod_managers_widget.hide()
        self.instances_widget.show()

        # Bind next button to done
        self.next_button.clicked.disconnect(self.last_page)
        self.next_button.setText(self.app.lang['done'])
        self.next_button.clicked.connect(self.finish)
        self.next_button.setIcon(qtg.QIcon())

        # Bind back button to previous page
        self.back_button.clicked.connect(self.first_page)
        self.back_button.setDisabled(False)

        # Update dialog height
        size = self.sizeHint()
        size.setWidth(self.width())
        self.resize(size)

        # Move dialog to center of screen
        core.center(self)
    
    def finish(self):
        # Check if paths are same
        instance_path = self.path_box.text()
        src_drive = self.app.src_modinstance.paths['instance_path'].split("\\", 1)[0]
        dst_drive = instance_path.split("\\", 1)[0]
        if instance_path == self.app.src_modinstance.paths['instance_path']:
            self.app.log.error("Failed to create destination instance: source and destination paths must not be same!")
            qtw.QMessageBox.critical(self, self.app.lang['error'], self.app.lang['detected_same_path'], buttons=qtw.QMessageBox.StandardButton.Ok)
            return
        elif (self.app.mode == 'hardlink') and (src_drive != dst_drive):
            self.app.log.error(f"Failed to create destination instance: Hardlinks must be on the same drive. (Source: {src_drive} | Destination: {dst_drive})")
            qtw.QMessageBox.critical(self, self.app.lang['error'], self.app.lang['hardlink_drive_error'].replace("[DESTDRIVE]", dst_drive).replace("[SOURCEDRIVE]", src_drive), buttons=qtw.QMessageBox.StandardButton.Ok)
            return
        
        if (self.app.mode == 'hardlink') and self.app.src_modinstance.paths.get('download_path', None):
            src_drive = self.app.src_modinstance.paths['download_path'].split("\\", 1)[0]
            dst_drive = self.dlpath_box.text().split("\\")[0]
            if src_drive != dst_drive:
                self.app.log.error(f"Failed to create destination instance: Hardlinks must be on the same drive. (Source: {src_drive} | Destination: {dst_drive})")
                qtw.QMessageBox.critical(self, self.app.lang['error'], self.app.lang['hardlink_drive_error'].replace("[DESTDRIVE]", dst_drive).replace("[SOURCEDRIVE]", src_drive), buttons=qtw.QMessageBox.StandardButton.Ok)
                return

        # Create destination instance
        if self.app.destination == 'Vortex':
            instance_data = {
                'name': "",
                'paths': {
                    'staging_folder': ""
                }
            }
            self.app.dst_modinstance = core.VortexInstance(self.app, instance_data)
        elif self.app.destination == 'ModOrganizer':
            instance_data = {
                'name': self.name_box.text(),
                'paths': {
                    'instance_path': self.path_box.text(),
                    'download_path': self.dlpath_box.text(),
                    'mods_path': self.modspath_box.text(),
                    'profiles_path': self.profilespath_box.text(),
                    'overwrite_path': self.overwritepath_box.text()
                },
                'mods': self.app.src_modinstance.mods
            }
            self.app.dst_modinstance = core.MO2Instance(self.app, instance_data)
            appdata_path = os.path.join(os.getenv('LOCALAPPDATA'), 'ModOrganizer', instance_data['name'])
            instance_path = self.app.dst_modinstance.paths['instance_path']
            exist = False
            if os.path.isdir(appdata_path):
                if os.listdir(appdata_path):
                    exist = True
            elif os.path.isdir(instance_path):
                if os.listdir(instance_path):
                    exist = True
            if exist:
                self.app.log.warning("Instance data will be wiped!")
                qtw.QMessageBox.warning(self.app.root, self.app.lang['warning'], self.app.lang['wipe_notice'], buttons=qtw.QMessageBox.StandardButton.Ok)

        # Create destination widget with instance details ############
        if (item := self.app.mainlayout.itemAtPosition(1, 2)) is not None:
            item.widget().destroy()
        self.destination_widget = qtw.QWidget()
        self.destination_widget.setObjectName("panel")
        self.app.mainlayout.addWidget(self.destination_widget, 1, 2)
        # Create layout
        self.destination_layout = qtw.QGridLayout()
        self.destination_layout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.destination_widget.setLayout(self.destination_layout)
        self.destination_layout.setColumnStretch(1, 1)
        # Add label with mod manager name
        label = qtw.QLabel()
        label.setText(f"{self.app.lang['mod_manager']}:")
        self.destination_layout.addWidget(label, 0, 0)
        manager_label = qtw.QLabel()
        manager_label.setText(self.app.destination)
        self.destination_layout.addWidget(manager_label, 0, 1)
        # Add label with instance name
        label = qtw.QLabel(f"{self.app.lang['instance_name']}:")
        self.destination_layout.addWidget(label, 1, 0)
        instance_label = qtw.QLabel(self.app.dst_modinstance.name)
        self.destination_layout.addWidget(instance_label, 1, 1)

        # Add label with migration mode
        label = qtw.QLabel(f"{self.app.lang['mode']}:")
        self.destination_layout.addWidget(label, 2, 0)
        mode_label = qtw.QLabel()
        if self.app.mode == 'hardlink':
            mode_label.setText(self.app.lang['hardlink_mode'])
        else:
            mode_label.setText(self.app.lang['copy_mode'])
        self.destination_layout.addWidget(mode_label, 2, 1)
        
        # Add label with instance path
        label = qtw.QLabel(f"{self.app.lang['instance_path']}:")
        self.destination_layout.addWidget(label, 3, 0)
        path_label = qtw.QLabel(self.app.dst_modinstance.paths['instance_path'])
        self.destination_layout.addWidget(path_label, 3, 1)

        # Add label with downloads path
        label = qtw.QLabel(f"{self.app.lang['download_path']}:")
        self.destination_layout.addWidget(label, 4, 0)
        dlpath_label = qtw.QLabel(self.app.dst_modinstance.paths['download_path'])
        self.destination_layout.addWidget(dlpath_label, 4, 1)

        # Add label with mods path
        label = qtw.QLabel(f"{self.app.lang['mods_path']}:")
        self.destination_layout.addWidget(label, 5, 0)
        modpath_label = qtw.QLabel(self.app.dst_modinstance.paths['mods_path'])
        self.destination_layout.addWidget(modpath_label, 5, 1)

        # Add label with profiles path
        label = qtw.QLabel(f"{self.app.lang['profiles_path']}:")
        self.destination_layout.addWidget(label, 6, 0)
        profilespath_label = qtw.QLabel(self.app.dst_modinstance.paths['profiles_path'])
        self.destination_layout.addWidget(profilespath_label, 6, 1)

        # Add label with overwrite path
        label = qtw.QLabel(f"{self.app.lang['overwrite_path']}:")
        self.destination_layout.addWidget(label, 7, 0)
        overwritepath_label = qtw.QLabel(self.app.dst_modinstance.paths['overwrite_path'])
        self.destination_layout.addWidget(overwritepath_label, 7, 1)
        ##############################################################

        # Disable add source button
        #self.dst_button.setDisabled(True)
        self.app.dst_button.setText(self.app.lang['edit_destination'])
        self.app.dst_button.clicked.disconnect()
        self.app.dst_button.clicked.connect(self.edit)
        self.app.mig_button.setDisabled(False)

        # Colorize migration icon
        self.app.mig_icon.setPixmap(qta.icon('fa5s.chevron-right', color=self.app.theme['accent_color']).pixmap(120, 120))

        # Close dialog
        self.accept()
    
    def edit(self):
        self.show()


# Create class for loading dialog ####################################
class LoadingDialog(qtw.QDialog):
    """
    QDialog designed for progress bars.
    
    Parameters:
        parent: QWidget
        app: main.MainApp
        func: function or method that is run in a background thread
    """

    start_signal = qtc.Signal()
    stop_signal = qtc.Signal()
    progress_signal = qtc.Signal(dict)

    def __init__(self, parent: qtw.QWidget, app: main.MainApp, func: Callable):
        super().__init__(parent)
        
        # Force focus
        self.setModal(True)

        # Set up variables
        self.app = app
        self.success = True
        self.func = lambda: (self.start_signal.emit(), func(self.progress_signal), self.stop_signal.emit())
        self.Thread = LoadingDialogThread(self, target=self.func, daemon=True, name='BackgroundThread')
        self.starttime = None

        # Set up dialog layout
        self.layout = qtw.QVBoxLayout()
        self.layout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.layout)

        # Set up first label and progressbar
        self.label1 = qtw.QLabel()
        self.label1.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(self.label1)
        self.pbar1 = qtw.QProgressBar()
        self.pbar1.setTextVisible(False)
        self.pbar1.setFixedHeight(3)
        self.layout.addWidget(self.pbar1)

        # Set up second label and progressbar
        self.label2 = qtw.QLabel()
        self.label2.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        self.label2.hide()
        self.layout.addWidget(self.label2)
        self.pbar2 = qtw.QProgressBar()
        self.pbar2.setTextVisible(False)
        self.pbar2.setFixedHeight(3)
        self.pbar2.hide()
        self.layout.addWidget(self.pbar2)

        # Set up third label and progressbar
        self.label3 = qtw.QLabel()
        self.label3.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        self.label3.hide()
        self.layout.addWidget(self.label3)
        self.pbar3 = qtw.QProgressBar()
        self.pbar3.setTextVisible(False)
        self.pbar3.setFixedHeight(3)
        self.pbar3.hide()
        self.layout.addWidget(self.pbar3)
        
        # Connect signals
        self.start_signal.connect(self.on_start)
        self.stop_signal.connect(self.on_finish)
        self.progress_signal.connect(self.setProgress)

        # Configure dialog
        self.setWindowTitle(self.app.name)
        self.setWindowIcon(self.parent().windowIcon())
        self.setStyleSheet(self.parent().styleSheet())
        self.setWindowFlag(qtc.Qt.WindowType.WindowCloseButtonHint, False)
    
    def setProgress(self, progress: dict):
        value = progress.get('value', None)
        max = progress.get('max', None)
        text = progress.get('text', "")
        show2 = progress.get('show2', False)
        value2 = progress.get('value2', None)
        max2 = progress.get('max2', None)
        text2 = progress.get('text2', "")
        show3 = progress.get('show3', False)
        value3 = progress.get('value3', None)
        max3 = progress.get('max3', None)
        text3 = progress.get('text3', "")

        #print(progress, end='\r')
        
        # first row (always shown)
        if max is not None:
            self.pbar1.setRange(0, int(max))
        #else:
        #    self.pbar1.setRange(0, 0)
        if value is not None:
            self.pbar1.setValue(int(value))
        if text.strip():
            self.label1.setText(text)
        #self.setFixedHeight(50)

        # second row
        if show2:
            self.pbar2.show()
            self.label2.show()
            if max2 is not None:
                self.pbar2.setRange(0, int(max2))
            #else:
            #    self.pbar2.setRange(0, 0)
            if value2 is not None:
                self.pbar2.setValue(int(value2))
            if text2.strip():
                self.label2.setText(text2)
            #self.setFixedHeight(100)
        else:
            self.pbar2.hide()
            self.label2.hide()

        # third row
        if show3:
            self.pbar3.show()
            self.label3.show()
            if max3 is not None:
                self.pbar3.setRange(0, int(max3))
            #else:
            #    self.pbar3.setRange(0, 0)
            if value3 is not None:
                self.pbar3.setValue(int(value3))
            if text3.strip():
                self.label3.setText(text3)
            #self.setFixedHeight(150)
        else:
            self.pbar3.hide()
            self.label3.hide()
        
        self.setFixedHeight(self.sizeHint().height())

        # Move back to center
        core.center(self, self.app.root)

    def timerEvent(self, event: qtc.QTimerEvent):
        super().timerEvent(event)

        self.setWindowTitle(f"{self.app.name} - {self.app.lang['elapsed']}: {core.get_diff(self.starttime, time.strftime('%H:%M:%S'))}")
    
    def exec(self):
        #self.start_signal.emit()
        self.Thread.start()

        self.starttime = time.strftime("%H:%M:%S")
        self.startTimer(1000)

        super().exec()

        if self.Thread.exception is not None:
            raise self.Thread.exception
    
    def on_start(self):
        self.pbar1.setRange(0, 0)
        self.pbar2.setRange(0, 0)
        self.pbar3.setRange(0, 0)
        self.show()
    
    def on_finish(self):
        self.pbar1.setRange(0, 1)
        self.pbar1.setValue(1)
        self.pbar2.setRange(0, 1)
        self.pbar2.setValue(1)
        self.pbar3.setRange(0, 1)
        self.pbar3.setValue(1)
        self.accept()


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


# Create class for settings dialog ###################################
class SettingsDialog(qtw.QDialog):
    def __init__(self, parent: qtw.QWidget, app: main.MainApp):
        super().__init__(parent)
        self.app = app

        # create popup window
        self.setModal(True)
        self.setStyleSheet(self.app.stylesheet)
        self.setWindowTitle(f"{self.app.name} - {self.app.lang['settings']}...")
        self.setWindowIcon(self.app.root.windowIcon())
        self.setObjectName("root")
        self.setMinimumWidth(600)
        self.closeEvent = self.cancel_settings
        layout = qtw.QVBoxLayout(self)
        self.setLayout(layout)

        # create detail frame with grid layout
        detail_frame = qtw.QWidget()
        detail_frame.setObjectName("detailframe")
        detail_layout = qtw.QGridLayout()
        detail_frame.setLayout(detail_layout)
        layout.addWidget(detail_frame, stretch=1)
        self.settings_widgets = []
        for r, (config, value) in enumerate(self.app.config.items()):
            label = qtw.QLabel()
            #label.setObjectName(config)
            label.setText(self.app.lang.get(config, config))
            detail_layout.addWidget(label, r, 0)
            if isinstance(value, bool):
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems([self.app.lang['true'], self.app.lang['false']])
                dropdown.setCurrentText(self.app.lang[str(value).lower()])
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
                dropdown.addItems([self.app.lang['dark'], self.app.lang['light'], "System"])
                dropdown.setCurrentText(self.app.lang.get(value.lower(), value))
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(lambda e: self.on_setting_change())
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif config == 'language':
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItem("System")
                for lang in glob(os.path.join(self.app.res_path, 'locales', '??-??.json')):
                    lang = os.path.basename(lang).rsplit(".", 1)[0]
                    dropdown.addItem(lang)
                dropdown.setCurrentText(self.app.config['language'])
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(lambda e: self.on_setting_change())
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif config == 'log_level':
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems([loglevel.capitalize() for loglevel in main.LOG_LEVELS.values()])
                dropdown.setCurrentText(value.capitalize())
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(lambda e: self.on_setting_change())
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif config == 'accent_color':
                button = qtw.QPushButton()
                button.setObjectName(config)
                button.color = self.app.config['accent_color']
                def choose_color():
                    colordialog = qtw.QColorDialog(self)
                    colordialog.setOption(colordialog.ColorDialogOption.DontUseNativeDialog, True)
                    colordialog.setCustomColor(0, qtg.QColor('#d78f46'))
                    color = button.color
                    if qtg.QColor.isValidColor(color):
                        colordialog.setCurrentColor(qtg.QColor(color))
                    if colordialog.exec():
                        button.color = colordialog.currentColor().name(qtg.QColor.NameFormat.HexRgb)
                        button.setIcon(qta.icon('mdi6.square-rounded', color=button.color))        
                        self.on_setting_change()
                button.setText(self.app.lang['select_color'])
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
        cancel_button = qtw.QPushButton(self.app.lang['cancel'])
        cancel_button.clicked.connect(self.cancel_settings)
        command_layout.addWidget(cancel_button)
        # done
        self.settings_done_button = qtw.QPushButton(self.app.lang['done'])
        self.settings_done_button.clicked.connect(self.finish_settings)
        self.settings_done_button.setDisabled(True)
        command_layout.addWidget(self.settings_done_button)

        self.setFixedHeight(self.sizeHint().height())

        # update changes variable
        self.unsaved_settings = False

        # show popup
        self.exec()
    
    def finish_settings(self):
        config = self.app.config.copy()
        for widget in self.settings_widgets:
            if isinstance(widget, qtw.QComboBox):
                if hasattr(widget, 'bool'):
                    config[widget.objectName()] = (widget.currentText() == self.app.lang['true'])
                elif widget.objectName() == 'ui_mode':
                    config[widget.objectName()] = 'System' if widget.currentText() == 'System' else ('Dark' if widget.currentText() == self.app.lang['dark'] else 'Light')
                elif widget.objectName() == 'language':
                    config[widget.objectName()] = widget.currentText()
                elif widget.objectName() == 'log_level':
                    config[widget.objectName()] = widget.currentText().lower()
            elif isinstance(widget, qtw.QSpinBox):
                config[widget.objectName()] = widget.value()
            elif isinstance(widget, qtw.QPushButton):
                config[widget.objectName()] = widget.color
        
        # save config
        if config['ui_mode'] != self.app.config['ui_mode']:
            self.app._theme.set_mode(config['ui_mode'].lower())
            self.app.theme = self.app._theme.load_theme()
            self.app.stylesheet = self.app._theme.load_stylesheet()
            self.app.root.setStyleSheet(self.app.stylesheet)
            self.app.file_menu.setStyleSheet(self.app.stylesheet)
            self.app.help_menu.setStyleSheet(self.app.stylesheet)
            self.app.theme_change_sign.emit()
        self.app.config = config
        with open(self.app.con_path, 'w') as file:
            file.write(json.dumps(self.app.config, indent=4))
        self.app.unsaved_settings = False
        self.app.log.info("Saved config to file.")

        # update accent color
        self.app.theme['accent_color'] = self.app.config['accent_color']
        self.stylesheet = self.app._theme.load_stylesheet()
        self.app.root.setStyleSheet(self.app.stylesheet)
        # Update icons
        self.app.mig_button.setIcon(qta.icon('fa5s.chevron-right', color=self.app.theme['text_color']))
        if self.app.source and self.app.destination:
            self.app.mig_icon.setPixmap(qta.icon('fa5s.chevron-right', color=self.app.theme['accent_color']).pixmap(120, 120))
        else:
            self.app.mig_icon.setPixmap(qta.icon('fa5s.chevron-right', color=self.app.theme['text_color']).pixmap(120, 120))
        # Fix link color
        palette = self.app.palette()
        palette.setColor(palette.ColorRole.Link, qtg.QColor(self.app.config['accent_color']))
        self.app.setPalette(palette)

        # close settings popup
        self.accept()
    
    def on_setting_change(self):
        if (not self.unsaved_settings) and (self is not None):
            self.unsaved_settings = True
            self.settings_done_button.setDisabled(False)
            self.setWindowTitle(f"{self.windowTitle()}*")
    
    def cancel_settings(self, event=None):
        if self.unsaved_settings:
            message_box = qtw.QMessageBox(self)
            message_box.setWindowIcon(self.app.root.windowIcon())
            message_box.setStyleSheet(self.app.stylesheet)
            message_box.setWindowTitle(self.app.lang['cancel'])
            message_box.setText(self.app.lang['unsaved_cancel'])
            message_box.setStandardButtons(qtw.QMessageBox.StandardButton.No | qtw.QMessageBox.StandardButton.Yes)
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.No)
            message_box.button(qtw.QMessageBox.StandardButton.No).setText(self.app.lang['no'])
            message_box.button(qtw.QMessageBox.StandardButton.Yes).setText(self.app.lang['yes'])
            choice = message_box.exec()
            
            if choice == qtw.QMessageBox.StandardButton.Yes:
                self.accept()
                self = None
            elif event:
                event.ignore()
        else:
            self.accept()
            self = None
    

