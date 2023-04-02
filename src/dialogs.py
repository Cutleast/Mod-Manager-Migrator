"""
Part of MMM. Contains dialogs.

Falls under license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

# Import libraries ###################################################
import json
import os
import logging
from typing import List
from pathlib import Path

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utils
import main
import managers
import games
from loadingdialog import LoadingDialog


# Source class for source dialog #####################################
class SourceDialog(qtw.QDialog):
    """
    Dialog for source selection.
    """

    def __init__(self, parent: qtw.QWidget, app: main.MainApp):
        super().__init__(parent)

        self.app = app
        self.modinstance: managers.ModInstance = None
        self.source_widget: qtw.QWidget = None
        self.mods_box: qtw.QListWidget = None

        # Initialize class specific logger
        self.log = logging.getLogger(self.__repr__())
        self.log.addHandler(self.app.log_str)
        self.log.setLevel(self.app.log.level)

        # Configure dialog
        self.setWindowTitle(
            f"{self.app.name} - {self.app.lang['select_source']}"
        )
        self.setWindowIcon(self.app.root.windowIcon())
        self.setModal(True)
        self.setObjectName("root")

        # Create main layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # Create first page (mod manager selection) ##################
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

        buttons: List[qtw.QPushButton] = []
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
            button.clicked.connect(func(modmanager))
            row = i // columns # calculate row
            col = i % columns # calculate column
            buttons.append(button)
            manager_layout.addWidget(button, row+1, col)

        # Select first mod manager as default
        buttons[0].setChecked(True)
        self.app.source = main.SUPPORTED_MODMANAGERS[0]
        ##############################################################

        # Create second page (instance selection) ####################
        self.instances_widget = qtw.QWidget()
        self.instances_widget.hide() # hide as default
        layout.addWidget(self.instances_widget)

        # Create layout for instances
        instances_layout = qtw.QVBoxLayout()
        self.instances_widget.setLayout(instances_layout)

        # Add label with instruction
        label = qtw.QLabel()
        label.setText(self.app.lang['select_src_instance_text'])
        label.setObjectName("titlelabel")
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        instances_layout.addWidget(label)

        # Add listbox for instances
        self.instances_box = qtw.QListWidget()
        self.instances_box.setSelectionMode(
            qtw.QListWidget.SelectionMode.SingleSelection
        )
        self.instances_box.doubleClicked.connect(self.finish)
        self.instances_box.setMinimumHeight(200)
        instances_layout.addWidget(self.instances_box, 1)
        ##############################################################

        # Add spacing
        layout.addSpacing(25)

        # Add cancel and next button
        self.button_layout = qtw.QHBoxLayout()
        layout.addLayout(self.button_layout)

        # Cancel button
        self.src_cancel_button = qtw.QPushButton(self.app.lang['cancel'])
        self.src_cancel_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.src_cancel_button)

        # Seperate cancel button with spacing
        self.button_layout.addSpacing(200)

        # Back button with icon
        self.back_button = qtw.QPushButton(self.app.lang['back'])
        self.back_button.setIcon(qta.icon(
            'fa5s.chevron-left',
            color=self.app.theme['text_color']
            )
        )
        self.back_button.setDisabled(True)
        self.button_layout.addWidget(self.back_button)

        # Next button with icon
        self.next_button = qtw.QPushButton(self.app.lang['next'])
        self.next_button.setLayoutDirection( # Switch icon and text
            qtc.Qt.LayoutDirection.RightToLeft
        )
        self.next_button.setIcon(qta.icon(
            'fa5s.chevron-right',
            color=self.app.theme['text_color']
            )
        )
        self.next_button.clicked.connect(self.goto_secnd_page)
        self.button_layout.addWidget(self.next_button)

        # Bind next button to instances list box
        self.instances_box.itemSelectionChanged.connect(
            lambda: self.next_button.setDisabled(False)
        )

    def __repr__(self):
        return "SourceDialog"

    def goto_first_page(self):
        """
        Hides second page and shows first page.
        """

        # Hide second page and show first page
        self.instances_widget.hide()
        self.modmanagers_widget.show()

        # Update back button
        self.back_button.setDisabled(True)
        self.back_button.clicked.disconnect(self.goto_first_page)

        # Update next button
        self.next_button.clicked.disconnect()
        self.next_button.setText(self.app.lang['next'])
        self.next_button.clicked.connect(self.goto_secnd_page)
        self.next_button.setIcon(qta.icon(
            'fa5s.chevron-right',
            color=self.app.theme['text_color']
            )
        )
        self.next_button.setDisabled(False)

        # Update dialog height
        size = self.sizeHint()
        size.setWidth(self.width())
        self.resize(size)

        # Move dialog to center of screen
        utils.center(self)

    def goto_secnd_page(self):
        """
        Loads instances from selected mod manager,
        hides first page and shows second page.
        """

        # Create source mod manager instance
        # if not already done
        if self.app.source == 'Vortex':
            self.modinstance = managers.VortexInstance(self.app)
        elif self.app.source == 'ModOrganizer':
            self.modinstance = managers.MO2Instance(self.app)
        else:
            raise utils.UiException(
                f"[unsupported_mod_manager] Mod manager '{self.app.source}' is unsupported!"
            )

        # Load instances from source mod manager
        instances = self.modinstance.load_instances()

        # Check if instances were found
        if instances:
            self.instances_box.clear()
            self.instances_box.addItems(instances)
            self.instances_box.setCurrentRow(0)
        
        # Show error message and
        # go to first page otherwise
        else:
            raise utils.UiException(
                "[error_no_instances] Found no instances!"
            )

        # Hide first page and show second page
        self.modmanagers_widget.hide()
        self.instances_widget.show()

        # Bind next button to done
        self.next_button.clicked.disconnect()
        self.next_button.setText(self.app.lang['done'])
        self.next_button.clicked.connect(self.finish)
        self.next_button.setIcon(qtg.QIcon())

        # Bind back button to previous page
        self.back_button.clicked.connect(self.goto_first_page)
        self.back_button.setDisabled(False)

        # Update dialog height
        size = self.sizeHint()
        size.setWidth(self.width())
        self.resize(size)

        # Move dialog to center of screen
        utils.center(self)

    def finish(self):
        """
        Loads selected instance, displays
        it in main window and closes dialog.        
        """

        # Load instance from source mod manager
        name = self.instances_box.currentItem().text()
        loadingdialog = LoadingDialog(
            parent=self,
            app=self.app,
            func=lambda ldialog: (
                self.modinstance.load_instance(name, ldialog)
            )
        )
        loadingdialog.exec()
        self.app.src_modinstance = self.modinstance

        # Create source widget with instance details
        self.modinstance.show_src_widget()

        # Update source button
        self.app.src_button.setText(self.app.lang['edit_source'])
        self.app.src_button.clicked.disconnect()
        #self.back_button.setDisabled(True)
        self.app.src_button.clicked.connect(self.show)

        # Enable destination button
        self.app.dst_button.setDisabled(False)

        # Ensure that migrate button is disabled after changes
        self.app.mig_button.setDisabled(True)

        # Delete destination widget after changes
        if self.app.dst_widget:
            self.app.dst_widget.hide()
            self.app.dst_widget.destroy()
        self.app.dst_widget = None
        self.app.destination = None
        self.app.dst_modinstance = None
        self.app.dst_button.setText(self.app.lang['select_source'])
        self.app.dst_button.clicked.disconnect()
        self.app.dst_button.clicked.connect(
            lambda: DestinationDialog(self.app.root, self.app).show()
        )
        self.app.mig_icon.setPixmap(qta.icon(
            'fa5s.chevron-right',
            color=self.app.theme['text_color']
            ).pixmap(120, 120)
        )

        # Close dialog
        self.accept()


# Create class for destination dialog ################################
class DestinationDialog(qtw.QDialog):
    """
    Dialog for destination selection and configuration.
    """

    def __init__(self, parent: qtw.QWidget, app: main.MainApp):
        super().__init__(parent)

        self.app = app
        self.modinstance: managers.ModInstance = None
        self.destination_widget: qtw.QWidget = None
        self.mods_box: qtw.QListWidget = None

        # Initialize class specific logger
        self.log = logging.getLogger(self.__repr__())
        self.log.addHandler(self.app.log_str)
        self.log.setLevel(self.app.log.level)

        # Configure dialog
        self.setWindowTitle(
            f"{self.app.name} - {self.app.lang['select_destination']}"
        )
        self.setWindowIcon(self.app.root.windowIcon())
        self.setModal(True)
        self.setObjectName("root")

        # Create main layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # Create first page (mod manager selection) ##################
        self.modmanagers_widget = qtw.QWidget()
        layout.addWidget(self.modmanagers_widget)

        # Create layout for mod managers
        manager_layout = qtw.QGridLayout()
        columns = 2 # number of columns in grid
        self.modmanagers_widget.setLayout(manager_layout)

        # Label with instruction
        label = qtw.QLabel(self.app.lang['select_destination_text'])
        label.setObjectName("titlelabel")
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        manager_layout.addWidget(label, 0, 0, 1, columns)

        buttons: List[qtw.QPushButton] = []
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
            button.setCheckable(True)
            button.clicked.connect(func(modmanager))
            row = i // columns # calculate row
            col = i % columns # calculate column
            buttons.append(button)
            manager_layout.addWidget(button, row+1, col)

            # Disable button if it is source
            if modmanager == self.app.source:
                button.setDisabled(True)

        # Select first mod manager as default
        # Select first mod manager that is not source as default
        for button in buttons:
            if button.text() != self.app.source and button.isEnabled():
                button.setChecked(True)
                self.app.destination = button.text()
                break
        ##############################################################

        # Create second page (instance selection) ####################
        self.instance_widget = qtw.QWidget()
        self.instance_widget.hide() # hide as default
        layout.addWidget(self.instance_widget)

        # Add layout for instance settings
        instance_layout = qtw.QVBoxLayout()
        self.instance_widget.setLayout(instance_layout)
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
        if self.app.destination is not None:
            self.path_box.setText(os.path.join(
                    os.getenv('LOCALAPPDATA'),
                    self.app.destination,
                    self.name_box.text()
                )
            )
        details_layout.addWidget(self.path_box, 3, 1)
        def browse_path():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang['browse'])
            file_dialog.setDirectory(str(Path(self.path_box.text()).parent))
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.path_box.setText(folder)
                self.name_box.setText(os.path.basename(folder))
                self.dlpath_box.setText(
                    os.path.join(folder, 'downloads')
                )
                self.modspath_box.setText(
                    os.path.join(folder, 'mods')
                )
                self.profilespath_box.setText(
                    os.path.join(folder, 'profiles')
                )
                self.overwritepath_box.setText(
                    os.path.join(folder, 'overwrite')
                )
        self.browse_button = qtw.QPushButton(self.app.lang['browse'])
        self.browse_button.clicked.connect(browse_path)
        details_layout.addWidget(self.browse_button, 3, 2)

        # Add inputbox for downloads path
        label = qtw.QLabel(self.app.lang['download_path'])
        details_layout.addWidget(label, 4, 0)
        self.dlpath_box = qtw.QLineEdit()
        self.dlpath_box.setText(os.path.join(
                self.path_box.text(),
                'downloads'
            )
        )
        details_layout.addWidget(self.dlpath_box, 4, 1)
        def browse_dlpath():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang['browse'])
            file_dialog.setDirectory(self.dlpath_box.text())
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.dlpath_box.setText(folder)
        self.browse_dlpath_button = qtw.QPushButton(self.app.lang['browse'])
        self.browse_dlpath_button.clicked.connect(browse_dlpath)
        details_layout.addWidget(self.browse_dlpath_button, 4, 2)

        # Add inputbox for mods path
        label = qtw.QLabel(self.app.lang['mods_path'])
        details_layout.addWidget(label, 5, 0)
        self.modspath_box = qtw.QLineEdit()
        self.modspath_box.setText(os.path.join(
                self.path_box.text(),
                'mods'
            )
        )
        details_layout.addWidget(self.modspath_box, 5, 1)
        def browse_modspath():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang['browse'])
            file_dialog.setDirectory(self.modspath_box.text())
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.modspath_box.setText(folder)
        self.browse_mods_button = qtw.QPushButton(self.app.lang['browse'])
        self.browse_mods_button.clicked.connect(browse_modspath)
        details_layout.addWidget(self.browse_mods_button, 5, 2)

        # Add inputbox for profiles path
        label = qtw.QLabel(self.app.lang['profiles_path'])
        details_layout.addWidget(label, 6, 0)
        self.profilespath_box = qtw.QLineEdit()
        self.profilespath_box.setText(os.path.join(
                self.path_box.text(),
                'profiles'
            )
        )
        details_layout.addWidget(self.profilespath_box, 6, 1)
        def browse_profilespath():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang['browse'])
            file_dialog.setDirectory(self.profilespath_box.text())
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.profilespath_box.setText(folder)
        self.browse_profiles_button = qtw.QPushButton(
            self.app.lang['browse']
        )
        self.browse_profiles_button.clicked.connect(browse_profilespath)
        details_layout.addWidget(self.browse_profiles_button, 6, 2)

        # Add inputbox for overwrite path
        label = qtw.QLabel(self.app.lang['overwrite_path'])
        details_layout.addWidget(label, 7, 0)
        self.overwritepath_box = qtw.QLineEdit()
        self.overwritepath_box.setText(os.path.join(
                self.path_box.text(),
                'overwrite'
            )
        )
        details_layout.addWidget(self.overwritepath_box, 7, 1)
        def browse_overwritepath():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang['browse'])
            file_dialog.setDirectory(self.overwritepath_box.text())
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.overwritepath_box.setText(folder)
        self.browse_overwrites_button = qtw.QPushButton(
            self.app.lang['browse']
        )
        self.browse_overwrites_button.clicked.connect(
            browse_overwritepath
        )
        details_layout.addWidget(self.browse_overwrites_button, 7, 2)
        ##############################################################

        # Add widget for hardlink mode
        hardlink_mode_widget = qtw.QWidget()
        hardlink_mode_widget.hide()
        instance_layout.addWidget(hardlink_mode_widget, 1)

        # Add button for hardlink mode
        hardlink_mode_button = qtw.QPushButton(
            self.app.lang['hardlink_mode']
        )
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
        copy_mode_button = qtw.QPushButton(
            self.app.lang['copy_mode']
        )
        copy_mode_button.clicked.connect(lambda: (
            hardlink_mode_button.setChecked(False),
            hardlink_notice.hide(),
            copy_notice.show(),
            copy_mode_button.setChecked(True),
            self.app.set_mode('copy'),
        ))
        copy_mode_button.setCheckable(True)
        mode_layout.addWidget(copy_mode_button)

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
        self.back_button.setIcon(qta.icon(
                'fa5s.chevron-left',
                color=self.app.theme['text_color']
            )
        )
        self.back_button.setDisabled(True)
        self.button_layout.addWidget(self.back_button)

        # Next button with icon
        self.next_button = qtw.QPushButton()
        self.next_button.setLayoutDirection( # switch icon and text
            qtc.Qt.LayoutDirection.RightToLeft
        )
        self.next_button.setText(self.app.lang['next'])
        self.next_button.setIcon(qta.icon(
                'fa5s.chevron-right',
                color=self.app.theme['text_color']
            )
        )
        self.next_button.clicked.connect(self.goto_secnd_page)
        self.button_layout.addWidget(self.next_button)

    def __repr__(self):
        return "DestinationDialog"

    def goto_first_page(self):
        """
        Hides second page and shows first page.        
        """

        # Hide second page and show first page
        self.instance_widget.hide()
        self.modmanagers_widget.show()

        # Update back button
        self.back_button.setDisabled(True)
        self.back_button.clicked.disconnect(self.goto_first_page)

        # Update next button
        self.next_button.clicked.disconnect(self.finish)
        self.next_button.setText(self.app.lang['next'])
        self.next_button.clicked.connect(self.goto_secnd_page)
        self.next_button.setIcon(qta.icon(
                'fa5s.chevron-right',
                color=self.app.theme['text_color']
            )
        )
        self.next_button.setDisabled(False)

        # Update dialog height
        size = self.sizeHint()
        size.setWidth(self.width())
        self.resize(size)

        # Move dialog to center of screen
        utils.center(self)

    def goto_secnd_page(self):
        """
        Loads instances from selected mod manager,
        hides first page and shows second page.
        """

        # Preconfigure instance if Vortex is
        # selected as destination since most of
        # the paths are fixed in its database
        vortex = self.app.destination == 'Vortex'
        mo2 = self.app.destination == 'ModOrganizer'
        if vortex:
            self.modinstance = managers.VortexInstance(self.app)

            app_path = Path(os.getenv('APPDATA'))
            app_path = app_path / 'Vortex' / self.app.game.lower()
            self.path_box.setText(str(app_path))
            self.modspath_box.setText(str(self.modinstance.mods_path))
            self.dlpath_box.setText(
                str(self.modinstance.paths.get('download_dir', ""))
            )
            self.profilespath_box.setText(
                str(app_path / 'profiles')
            )
            self.overwritepath_box.setText("")
        elif mo2:
            self.modinstance = managers.MO2Instance(self.app)
        else:
            raise ValueError(f"Unsupported destination: {self.app.destination}")

        # Update entry states
        # If 'vortex' is True, disable them
        # Enable them otherwise
        self.modspath_box.setDisabled(vortex)
        self.dlpath_box.setDisabled(vortex)
        self.path_box.setDisabled(vortex)
        self.browse_button.setDisabled(vortex)
        self.browse_dlpath_button.setDisabled(vortex)
        self.browse_mods_button.setDisabled(vortex)
        self.profilespath_box.setDisabled(vortex)
        self.browse_profiles_button.setDisabled(vortex)
        self.overwritepath_box.setDisabled(vortex)
        self.browse_overwrites_button.setDisabled(vortex)

        # Hide first page and show second page
        self.modmanagers_widget.hide()
        self.instance_widget.show()

        # Bind next button to done
        self.next_button.clicked.disconnect(self.goto_secnd_page)
        self.next_button.setText(self.app.lang['done'])
        self.next_button.clicked.connect(self.finish)
        self.next_button.setIcon(qtg.QIcon())

        # Bind back button to previous page
        self.back_button.clicked.connect(self.goto_first_page)
        self.back_button.setDisabled(False)

        # Update dialog height
        size = self.sizeHint()
        size.setWidth(self.width())
        self.resize(size)

        # Move dialog to center of screen
        utils.center(self)

    def finish(self):
        """
        Merges instance settings with instance from source.
        Displays data in main window and closes dialog.        
        """

        # Check if paths are valid
        instance_path = Path(self.path_box.text())
        src_drive = self.app.src_modinstance.mods_path.drive
        dst_drive = instance_path.drive
        # Check if source and destination match
        if instance_path == self.app.src_modinstance.mods_path:
            raise utils.UiException(
                "[detected_same_path] Failed to create destination instance: \
source and destination paths must not be same!"
            )
        # Check if drives match when mode is 'hardlink'
        if (self.app.mode == 'hardlink') and (src_drive != dst_drive):
            self.app.log.error(
                f"\
Failed to create destination instance: \
Hardlinks must be on the same drive. \
(Source: {src_drive} | Destination: {dst_drive})"
            )
            print("\a", end='\r')
            ErrorDialog(
                parent=self,
                app=self.app,
                title=self.app.lang['error'],
                text=self.app.lang['hardlink_drive_error']\
                .replace("[DESTDRIVE]", dst_drive)\
                .replace("[SOURCEDRIVE]", src_drive),
                yesno=False
            ).exec()
            return

        # Get user input
        name = self.name_box.text()
        instance_path = Path(self.path_box.text())
        mods_path = Path(self.modspath_box.text())
        dl_path = Path(self.dlpath_box.text())
        profs_path = Path(self.profilespath_box.text())
        overw_path = Path(self.overwritepath_box.text())

        # Create destination instance
        if self.app.destination == 'Vortex':
            instance_data = {
                'name': name
            }
        elif self.app.destination == 'ModOrganizer':
            instance_data = {
                'name': name,
                'paths': {
                    'base_dir': instance_path,
                    'mods_dir': mods_path,
                    'download_dir': dl_path,
                    'profiles_dir': profs_path,
                    'overwrite_dir': overw_path
                }
            }

            appdata_path = Path(os.getenv('LOCALAPPDATA'))
            appdata_path = appdata_path / 'ModOrganizer' / name
            # Check if folders already exist
            exist = False
            if appdata_path.is_dir():
                if list(appdata_path.iterdir()):
                    exist = True
            elif instance_path.is_dir():
                if list(instance_path.iterdir()):
                    exist = True

            # Warn user that they will be wiped
            if exist:
                self.app.log.warning("Instance data will be wiped!")
                qtw.QMessageBox.warning(
                    self.app.root,
                    self.app.lang['warning'],
                    self.app.lang['wipe_notice'],
                    buttons=qtw.QMessageBox.StandardButton.Ok
                )
        else:
            raise ValueError(f"Unsupported mod manager: {self.app.destination}")

        self.modinstance.name = name
        self.modinstance.instance_data = instance_data
        self.modinstance.mods_path = mods_path
        self.app.dst_modinstance = self.modinstance
        self.app.dst_modinstance.mods = self.app.src_modinstance.mods
        self.app.dst_modinstance.loadorder = self.app.src_modinstance.loadorder

        # Create destination widget with instance details
        self.modinstance.show_dst_widget()

        # Update destination button
        self.app.dst_button.setText(self.app.lang['edit_destination'])
        self.app.dst_button.clicked.disconnect()
        self.back_button.setDisabled(True)
        self.app.dst_button.clicked.connect(self.show)

        # Update migrate button and icon
        self.app.mig_button.setDisabled(False)
        self.app.mig_icon.setPixmap(qta.icon(
                'fa5s.chevron-right',
                color=self.app.theme['accent_color']
            ).pixmap(120, 120)
        )

        # Close dialog
        self.accept()


# Create class for game dialog #######################################
class GameDialog(qtw.QDialog):
    """
    Dialog for game selection.
    """

    def __init__(self, parent: qtw.QWidget, app: main.MainApp):
        super().__init__(parent)

        self.app = app
        self.game: str = None
        self.game_instance: games.GameInstance = None

        # Initialize class specific logger
        self.log = logging.getLogger(self.__repr__())
        self.log.addHandler(self.app.log_str)
        self.log.setLevel(self.app.log.level)

        # Configure dialog
        self.setWindowTitle(
            f"{self.app.name} - {self.app.lang['select_game']}"
        )
        self.setWindowIcon(self.app.root.windowIcon())
        self.setModal(True)
        self.setObjectName("root")
        self.setFixedSize(720, 350)

        # Create main layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # Add label with instruction
        label = qtw.QLabel()
        label.setText(self.app.lang['select_game_text'])
        label.setObjectName("titlelabel")
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(label)

        # Add listbox for games
        self.games_box = qtw.QListWidget()
        self.games_box.setSelectionMode(
            qtw.QListWidget.SelectionMode.SingleSelection
        )
        self.games_box.doubleClicked.connect(self.finish)
        self.games_box.setMinimumHeight(200)
        layout.addWidget(self.games_box, 1)

        # Add games to listbox
        for game in games.GAMES:
            game = game(self.app)
            text = game.name
            if game.name != "Skyrim Special Edition":
                text += " (EXPERIMENTAL)"
            if game.icon_name:
                icon = qtg.QIcon(str(self.app.ico_path / game.icon_name))
                item = qtw.QListWidgetItem(
                    icon,
                    text
                )
            else:
                item = qtw.QListWidgetItem(
                    text=text
                )

            self.games_box.addItem(item)
        self.games_box.setCurrentRow(0)

        # Add remember checkbox
        self.rem_checkbox = qtw.QCheckBox(self.app.lang['do_not_ask_again'])
        layout.addWidget(self.rem_checkbox, alignment=qtc.Qt.AlignmentFlag.AlignHCenter)

        # Add cancel and done button
        button_layout = qtw.QHBoxLayout()
        layout.addLayout(button_layout)

        # Cancel button
        cancel_button = qtw.QPushButton(self.app.lang['exit'])
        cancel_button.clicked.connect(self.app.exit)
        button_layout.addWidget(cancel_button)

        # Seperate cancel button with spacing
        button_layout.addSpacing(200)

        # Done button
        done_button = qtw.QPushButton(self.app.lang['done'])
        done_button.clicked.connect(self.finish)
        button_layout.addWidget(done_button)

        utils.center(self)
    
    def __repr__(self):
        return "GameDialog"

    def closeEvent(self, event):
        super().closeEvent(event)

        if not self.game_instance:
            self.app.exit()

    def finish(self):
        sel_game = self.games_box.currentItem().text()
        if '(EXPERIMENTAL)' in sel_game:
            sel_game = sel_game.replace('(EXPERIMENTAL)', '').strip()
        for game in games.GAMES:
            if game(self.app).name == sel_game:
                self.game_instance = game(self.app)
                break
        else:
            raise utils.UiException(
                f"[game_not_supported] Game '{sel_game}' not supported."
            )

        dir = self.game_instance.get_install_dir()
        if str(dir).strip() and dir.is_dir():
            self.game = self.game_instance.id
            self.app.game_instance = self.game_instance
            self.app.game = self.game

            self.log.info(f"Current game: {self.game_instance.name}")

            self.accept()

            # Save game to config if rem checkbox is selected
            if self.rem_checkbox.isChecked():
                self.app.config['default_game'] = self.app.game_instance.name
                with open(self.app.con_path, 'w', encoding='utf8') as file:
                    json.dump(self.app.config, file, indent=4)


# Create class for settings dialog ###################################
class SettingsDialog(qtw.QDialog):
    """
    Shows settings dialog.    
    """

    def __init__(self, parent: qtw.QWidget, app: main.MainApp):
        super().__init__(parent)
        self.app = app

        self.stylesheet = self.app._theme.load_stylesheet()

        # initialize class specific logger
        self.log = logging.getLogger(self.__repr__())
        self.log.addHandler(self.app.log_str)
        self.log.setLevel(self.app.log.level)

        # create popup window
        self.setModal(True)
        self.setStyleSheet(self.app.stylesheet)
        self.setWindowTitle(
            f"{self.app.name} - {self.app.lang['settings']}..."
        )
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
            label.setText(self.app.lang.get(config, config))
            detail_layout.addWidget(label, r, 0)
            if isinstance(value, bool):
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems([
                        self.app.lang['true'],
                        self.app.lang['false']
                    ]
                )
                dropdown.setCurrentText(self.app.lang[str(value).lower()])
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(
                    lambda e: self.on_setting_change()
                )
                dropdown.bool = None
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif isinstance(value, int):
                spinbox = qtw.QSpinBox()
                spinbox.setObjectName(config)
                spinbox.setRange(1, 100)
                spinbox.setValue(value)
                spinbox.valueChanged.connect(
                    lambda e: self.on_setting_change()
                )
                self.settings_widgets.append(spinbox)
                detail_layout.addWidget(spinbox, r, 1)
            elif config == 'ui_mode':
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems([
                        self.app.lang['dark'],
                        self.app.lang['light'],
                        "System"
                    ]
                )
                dropdown.setCurrentText(
                    self.app.lang.get(value.lower(), value)
                )
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(
                    lambda e: self.on_setting_change()
                )
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif config == 'language':
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItem("System")
                loc_path = self.app.res_path / 'locales'
                for lang in loc_path.glob('??-??.json'):
                    lang = lang.stem
                    dropdown.addItem(lang)
                dropdown.setCurrentText(self.app.config['language'])
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(
                    lambda e: self.on_setting_change()
                )
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif config == 'log_level':
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems([
                        loglevel.capitalize()
                        for loglevel in main.LOG_LEVELS.values()
                    ]
                )
                dropdown.setCurrentText(value.capitalize())
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(
                    lambda e: self.on_setting_change()
                )
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif config == 'accent_color':
                button = qtw.QPushButton()
                button.setObjectName(config)
                button.color = self.app.config['accent_color']
                def choose_color():
                    colordialog = qtw.QColorDialog(self)
                    colordialog.setOption(
                        colordialog.ColorDialogOption.DontUseNativeDialog,
                        on=True
                    )
                    colordialog.setCustomColor(0, qtg.QColor('#d78f46'))
                    color = button.color
                    if qtg.QColor.isValidColor(color):
                        colordialog.setCurrentColor(qtg.QColor(color))
                    if colordialog.exec():
                        button.color = colordialog.currentColor().name(
                            qtg.QColor.NameFormat.HexRgb
                        )
                        button.setIcon(
                            qta.icon('mdi6.square-rounded', color=button.color)
                        )
                        self.on_setting_change()
                button.setText(self.app.lang['select_color'])
                button.setIcon(
                    qta.icon('mdi6.square-rounded', color=button.color)
                )
                button.setIconSize(qtc.QSize(24, 24))
                button.clicked.connect(choose_color)
                self.settings_widgets.append(button)
                detail_layout.addWidget(button, r, 1)
            elif config == 'default_game':
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems([
                        game(self.app).name
                        for game in games.GAMES
                    ]
                )
                dropdown.addItem(self.app.lang['ask_always'])
                if value is not None:
                    dropdown.setCurrentText(value)
                else:
                    dropdown.setCurrentText(self.app.lang['ask_always'])
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(
                    lambda e: self.on_setting_change()
                )
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)

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

    def __repr__(self):
        return "Settings"
    
    def finish_settings(self):
        """
        Gets user input and saves config to file.        
        """

        # Get config
        config = self.app.config.copy()
        for widget in self.settings_widgets:
            name = widget.objectName()
            if isinstance(widget, qtw.QComboBox):
                if hasattr(widget, 'bool'):
                    config[name] = (
                        widget.currentText() == self.app.lang['true']
                    )
                elif name == 'ui_mode':
                    config[name] = (
                        'System'
                        if widget.currentText() == 'System'
                        else (
                            'Dark'
                            if widget.currentText() == self.app.lang['dark']
                            else 'Light'
                        )
                    )
                elif name == 'language':
                    config[name] = widget.currentText()
                elif name == 'log_level':
                    config[name] = widget.currentText().lower()
                elif name == 'default_game':
                    value = widget.currentText()
                    if value == self.app.lang['ask_always']:
                        value = None
                    config[name] = value
            elif isinstance(widget, qtw.QSpinBox):
                config[name] = widget.value()
            elif isinstance(widget, qtw.QPushButton):
                config[name] = widget.color

        # Save config
        if config['ui_mode'] != self.app.config['ui_mode']:
            self.app._theme.set_mode(config['ui_mode'].lower())
            self.app.theme = self.app._theme.load_theme()
            self.app.stylesheet = self.app._theme.load_stylesheet()
            self.app.root.setStyleSheet(self.app.stylesheet)
            self.app.file_menu.setStyleSheet(self.app.stylesheet)
            self.app.help_menu.setStyleSheet(self.app.stylesheet)
            self.app.theme_change_sign.emit()
        self.app.config = config
        with open(self.app.con_path, 'w', encoding='utf8') as file:
            json.dump(self.app.config, file, indent=4)
        self.app.unsaved_settings = False
        self.log.info("Saved config to file.")

        # Update accent color
        self.app.theme['accent_color'] = self.app.config['accent_color']
        self.stylesheet = self.app._theme.load_stylesheet()
        self.app.root.setStyleSheet(self.app.stylesheet)

        # Update icons
        self.app.mig_button.setIcon(
            qta.icon('fa5s.chevron-right', color=self.app.theme['text_color'])
        )
        if self.app.source and self.app.destination:
            self.app.mig_icon.setPixmap(qta.icon(
                    'fa5s.chevron-right',
                    color=self.app.theme['accent_color']
                ).pixmap(120, 120)
            )
        else:
            self.app.mig_icon.setPixmap(qta.icon(
                    'fa5s.chevron-right',
                    color=self.app.theme['text_color']
                ).pixmap(120, 120)
            )

        # Fix link color
        palette = self.app.palette()
        palette.setColor(
            palette.ColorRole.Link,
            qtg.QColor(self.app.config['accent_color'])
        )
        self.app.setPalette(palette)

        # Close settings popup
        self.accept()

    def on_setting_change(self):
        """
        Callback for user actions. Triggers unsaved state.        
        """

        if (not self.unsaved_settings) and (self is not None):
            self.unsaved_settings = True
            self.settings_done_button.setDisabled(False)
            self.setWindowTitle(f"{self.windowTitle()}*")

    def cancel_settings(self, event=None):
        """
        Closes dialog without saving.
        Asks user to continue if state is unsaved.        
        """

        if self.unsaved_settings:
            message_box = qtw.QMessageBox(self)
            message_box.setWindowIcon(self.app.root.windowIcon())
            message_box.setStyleSheet(self.app.stylesheet)
            message_box.setWindowTitle(self.app.lang['cancel'])
            message_box.setText(self.app.lang['unsaved_cancel'])
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.No
                | qtw.QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.No)
            message_box.button(
                qtw.QMessageBox.StandardButton.No
            ).setText(self.app.lang['no'])
            message_box.button(
                qtw.QMessageBox.StandardButton.Yes
            ).setText(self.app.lang['yes'])
            choice = message_box.exec()

            if choice == qtw.QMessageBox.StandardButton.Yes:
                self.accept()
                del self
            elif event:
                event.ignore()
        else:
            self.accept()
            del self


# Create class for error messagebox ##################################
class ErrorDialog(qtw.QMessageBox):
    """
    Custom error messagebox with short text
    and detailed text functionality.

    Parameters:
        parent: QWidget (parent window)
        app: MainApp (for localisation of buttons)
        title: str (window title)
        text: str (short message)
        details: str (will be displayed when details are shown)
        yesno: bool (determines if 'continue' and 'cancel' buttons are shown
        or only an 'ok' button)
    """

    def __init__(
            self,
            parent: qtw.QWidget,
            app: main.MainApp,
            title: str,
            text: str,
            details: str="",
            yesno: bool=True,
        ):
        super().__init__(parent)
        self.app = app

        # Basic configuration
        self.setWindowTitle(title)
        self.setIcon(qtw.QMessageBox.Icon.Critical)
        self.setText(text)
        
        # Show 'continue' and 'cancel' button
        if yesno:
            self.setStandardButtons(
                qtw.QMessageBox.StandardButton.Yes
                | qtw.QMessageBox.StandardButton.No
            )
            self.button(
                qtw.QMessageBox.StandardButton.Yes
            ).setText(self.app.lang['continue'])
            self.button(
                qtw.QMessageBox.StandardButton.No
            ).setText(self.app.lang['exit'])
        
        # Only show 'ok' button
        else:
            self.setStandardButtons(
                qtw.QMessageBox.StandardButton.Ok
            )

        # Add details button if details are given
        if details:
            self.details_button: qtw.QPushButton = self.addButton(
                self.app.lang['show_details'],
                qtw.QMessageBox.ButtonRole.YesRole
            )

            self._details = False
            def toggle_details():
                # toggle details
                if not self._details:
                    self._details = True
                    self.details_button.setText(self.app.lang['hide_details'])
                    self.setInformativeText(details)
                else:
                    self._details = False
                    self.details_button.setText(self.app.lang['show_details'])
                    self.setInformativeText("")

                # update messagebox size
                # and move messagebox to center of screen
                self.adjustSize()
                utils.center(self)

            self.details_button.clicked.disconnect()
            self.details_button.clicked.connect(toggle_details)
