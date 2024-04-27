"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
from pathlib import Path
from winsound import MessageBeep as alert

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import main
import managers
import utilities as utils

from .error_dialog import ErrorDialog


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
        self.log = logging.getLogger("DestinationDialog")

        # Configure dialog
        self.setWindowTitle(self.app.lang['select_destination'])
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
        columns = 2  # number of columns in grid
        self.modmanagers_widget.setLayout(manager_layout)

        # Label with instruction
        label = qtw.QLabel(self.app.lang["select_destination_text"])
        label.setObjectName("titlelabel")
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        manager_layout.addWidget(label, 0, 0, 1, columns)

        buttons: list[qtw.QPushButton] = []

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
        for i, modmanager in enumerate(utils.SUPPORTED_MODMANAGERS):
            button = qtw.QPushButton()
            button.setText(modmanager)
            button.setCheckable(True)
            button.clicked.connect(func(modmanager))
            row = i // columns  # calculate row
            col = i % columns  # calculate column
            buttons.append(button)
            manager_layout.addWidget(button, row + 1, col)

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
        self.instance_widget.hide()  # hide as default
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
        hardlink_notice = qtw.QLabel(self.app.lang["hardlink_notice"])
        hardlink_notice.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        details_layout.addWidget(hardlink_notice, 0, 0, 1, 3)
        # Add info label for copy mode
        copy_notice = qtw.QLabel(self.app.lang["copy_notice"])
        copy_notice.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        copy_notice.hide()
        details_layout.addWidget(copy_notice, 1, 0, 1, 3)

        # Add inputbox for name
        label = qtw.QLabel(self.app.lang["instance_name"])
        details_layout.addWidget(label, 2, 0)
        self.name_box = qtw.QLineEdit()
        self.name_box.setText(self.app.src_modinstance.name)
        details_layout.addWidget(self.name_box, 2, 1)

        # Add inputbox for instance path
        label = qtw.QLabel(self.app.lang["instance_path"])
        details_layout.addWidget(label, 3, 0)
        self.path_box = qtw.QLineEdit()
        if self.app.destination is not None:
            self.path_box.setText(
                os.path.join(
                    os.getenv("LOCALAPPDATA"),
                    self.app.destination,
                    self.name_box.text(),
                )
            )
        details_layout.addWidget(self.path_box, 3, 1)

        def browse_path():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang["browse"])
            file_dialog.setDirectory(str(Path(self.path_box.text()).parent))
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.path_box.setText(folder)
                self.name_box.setText(os.path.basename(folder))
                self.dlpath_box.setText(os.path.join(folder, "downloads"))
                self.modspath_box.setText(os.path.join(folder, "mods"))
                self.profilespath_box.setText(os.path.join(folder, "profiles"))
                self.overwritepath_box.setText(os.path.join(folder, "overwrite"))

        self.browse_button = qtw.QPushButton(self.app.lang["browse"])
        self.browse_button.clicked.connect(browse_path)
        details_layout.addWidget(self.browse_button, 3, 2)

        # Add inputbox for downloads path
        label = qtw.QLabel(self.app.lang["download_path"])
        details_layout.addWidget(label, 4, 0)
        self.dlpath_box = qtw.QLineEdit()
        self.dlpath_box.setText(os.path.join(self.path_box.text(), "downloads"))
        details_layout.addWidget(self.dlpath_box, 4, 1)

        def browse_dlpath():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang["browse"])
            file_dialog.setDirectory(self.dlpath_box.text())
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.dlpath_box.setText(folder)

        self.browse_dlpath_button = qtw.QPushButton(self.app.lang["browse"])
        self.browse_dlpath_button.clicked.connect(browse_dlpath)
        details_layout.addWidget(self.browse_dlpath_button, 4, 2)

        # Add inputbox for mods path
        label = qtw.QLabel(self.app.lang["mods_path"])
        details_layout.addWidget(label, 5, 0)
        self.modspath_box = qtw.QLineEdit()
        self.modspath_box.setText(os.path.join(self.path_box.text(), "mods"))
        details_layout.addWidget(self.modspath_box, 5, 1)

        def browse_modspath():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang["browse"])
            file_dialog.setDirectory(self.modspath_box.text())
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.modspath_box.setText(folder)

        self.browse_mods_button = qtw.QPushButton(self.app.lang["browse"])
        self.browse_mods_button.clicked.connect(browse_modspath)
        details_layout.addWidget(self.browse_mods_button, 5, 2)

        # Add inputbox for profiles path
        label = qtw.QLabel(self.app.lang["profiles_path"])
        details_layout.addWidget(label, 6, 0)
        self.profilespath_box = qtw.QLineEdit()
        self.profilespath_box.setText(os.path.join(self.path_box.text(), "profiles"))
        details_layout.addWidget(self.profilespath_box, 6, 1)

        def browse_profilespath():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang["browse"])
            file_dialog.setDirectory(self.profilespath_box.text())
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.profilespath_box.setText(folder)

        self.browse_profiles_button = qtw.QPushButton(self.app.lang["browse"])
        self.browse_profiles_button.clicked.connect(browse_profilespath)
        details_layout.addWidget(self.browse_profiles_button, 6, 2)

        # Add inputbox for overwrite path
        label = qtw.QLabel(self.app.lang["overwrite_path"])
        details_layout.addWidget(label, 7, 0)
        self.overwritepath_box = qtw.QLineEdit()
        self.overwritepath_box.setText(os.path.join(self.path_box.text(), "overwrite"))
        details_layout.addWidget(self.overwritepath_box, 7, 1)

        def browse_overwritepath():
            file_dialog = qtw.QFileDialog(self)
            file_dialog.setWindowTitle(self.app.lang["browse"])
            file_dialog.setDirectory(self.overwritepath_box.text())
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.overwritepath_box.setText(folder)

        self.browse_overwrites_button = qtw.QPushButton(self.app.lang["browse"])
        self.browse_overwrites_button.clicked.connect(browse_overwritepath)
        details_layout.addWidget(self.browse_overwrites_button, 7, 2)
        ##############################################################

        # Add widget for hardlink mode
        hardlink_mode_widget = qtw.QWidget()
        hardlink_mode_widget.hide()
        instance_layout.addWidget(hardlink_mode_widget, 1)

        # Add button for hardlink mode
        hardlink_mode_button = qtw.QPushButton(self.app.lang["hardlink_mode"])
        hardlink_mode_button.clicked.connect(
            lambda: (
                copy_mode_button.setChecked(False),
                copy_notice.hide(),
                hardlink_notice.show(),
                hardlink_mode_button.setChecked(True),
                self.app.set_mode("hardlink"),
            )
        )
        hardlink_mode_button.setCheckable(True)
        hardlink_mode_button.setChecked(True)
        mode_layout.addWidget(hardlink_mode_button)

        # Add button for copy mode
        copy_mode_button = qtw.QPushButton(self.app.lang["copy_mode"])
        copy_mode_button.clicked.connect(
            lambda: (
                hardlink_mode_button.setChecked(False),
                hardlink_notice.hide(),
                copy_notice.show(),
                copy_mode_button.setChecked(True),
                self.app.set_mode("copy"),
            )
        )
        copy_mode_button.setCheckable(True)
        mode_layout.addWidget(copy_mode_button)

        # Add spacing
        layout.addSpacing(25)

        # Add cancel and next button
        self.button_layout = qtw.QHBoxLayout()
        layout.addLayout(self.button_layout)

        # Cancel button
        self.cancel_button = qtw.QPushButton()
        self.cancel_button.setText(self.app.lang["cancel"])
        self.cancel_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.cancel_button)

        # Seperate cancel button with spacing
        self.button_layout.addSpacing(200)

        # Back button with icon
        self.back_button = qtw.QPushButton()
        self.back_button.setText(self.app.lang["back"])
        self.back_button.setIcon(
            qta.icon("fa5s.chevron-left", color=self.app.theme["text_color"])
        )
        self.back_button.setDisabled(True)
        self.button_layout.addWidget(self.back_button)

        # Next button with icon
        self.next_button = qtw.QPushButton()
        self.next_button.setLayoutDirection(  # switch icon and text
            qtc.Qt.LayoutDirection.RightToLeft
        )
        self.next_button.setText(self.app.lang["next"])
        self.next_button.setIcon(
            qta.icon("fa5s.chevron-right", color=self.app.theme["text_color"])
        )
        self.next_button.clicked.connect(self.goto_secnd_page)
        self.button_layout.addWidget(self.next_button)

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
        self.next_button.setText(self.app.lang["next"])
        self.next_button.clicked.connect(self.goto_secnd_page)
        self.next_button.setIcon(
            qta.icon("fa5s.chevron-right", color=self.app.theme["text_color"])
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
        vortex = self.app.destination == "Vortex"
        mo2 = self.app.destination == "ModOrganizer"
        if vortex:
            self.modinstance = managers.VortexInstance(self.app)

            app_path = Path(os.getenv("APPDATA"))
            app_path = app_path / "Vortex" / self.app.game.lower()
            self.path_box.setText(str(app_path))
            self.modspath_box.setText(str(self.modinstance.mods_path))
            self.dlpath_box.setText(str(self.modinstance.paths.get("download_dir", "")))
            self.profilespath_box.setText(str(app_path / "profiles"))
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
        self.next_button.setText(self.app.lang["done"])
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

        # Get user input
        name = self.name_box.text()
        instance_path = Path(self.path_box.text())
        mods_path = Path(self.modspath_box.text())
        dl_path = Path(self.dlpath_box.text())
        profs_path = Path(self.profilespath_box.text())
        overw_path = Path(self.overwritepath_box.text())

        # Check if paths are valid
        src_drive = self.app.src_modinstance.mods_path.drive.upper()
        dst_drive = mods_path.drive.upper()
        # Check if source and destination match
        if instance_path == self.app.src_modinstance.mods_path:
            raise utils.UiException(
                "[detected_same_path] Failed to create destination instance: \
source and destination paths must not be the same!"
            )
        # Check if drives match when mode is 'hardlink'
        if (self.app.mode == "hardlink") and (src_drive != dst_drive):
            self.log.error(
                f"\
Failed to create destination instance: \
Hardlinks must be on the same drive. \
(Source: {src_drive} | Destination: {dst_drive})"
            )
            alert()
            ErrorDialog(
                parent=self,
                app=self.app,
                title=self.app.lang["error"],
                text=self.app.lang["hardlink_drive_error"]
                .replace("[DESTDRIVE]", dst_drive)
                .replace("[SOURCEDRIVE]", src_drive),
                yesno=False,
            ).exec()
            return

        # Create destination instance
        if self.app.destination == "Vortex":
            instance_data = {"name": name}
        elif self.app.destination == "ModOrganizer":
            instance_data = {
                "name": name,
                "paths": {
                    "base_dir": instance_path,
                    "mods_dir": mods_path,
                    "download_dir": dl_path,
                    "profiles_dir": profs_path,
                    "overwrite_dir": overw_path,
                },
            }

            appdata_path = Path(os.getenv("LOCALAPPDATA"))
            appdata_path = appdata_path / "ModOrganizer" / name
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
                self.log.warning("Instance data will be wiped!")
                qtw.QMessageBox.warning(
                    self.app.root,
                    self.app.lang["warning"],
                    self.app.lang["wipe_notice"],
                    buttons=qtw.QMessageBox.StandardButton.Ok,
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
        self.app.dst_button.setText(self.app.lang["edit_destination"])
        self.app.dst_button.clicked.disconnect()
        self.back_button.setDisabled(True)
        self.app.dst_button.clicked.connect(self.show)

        # Update migrate button and icon
        self.app.mig_button.setDisabled(False)
        self.app.mig_icon.setPixmap(
            qta.icon("fa5s.chevron-right", color=self.app.theme["accent_color"]).pixmap(
                120, 120
            )
        )

        # Close dialog
        self.accept()
