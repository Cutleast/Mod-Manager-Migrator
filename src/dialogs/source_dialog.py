"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import main
import managers
import utilities as utils
from widgets import LoadingDialog

from .dest_dialog import DestinationDialog


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

        # Configure dialog
        self.setWindowTitle(self.app.lang['select_source'])
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
        label = qtw.QLabel(self.app.lang["select_source_text"])
        label.setObjectName("titlelabel")
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        manager_layout.addWidget(label, 0, 0, 1, columns)

        buttons: list[qtw.QPushButton] = []

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
        for i, modmanager in enumerate(utils.SUPPORTED_MODMANAGERS):
            button = qtw.QPushButton()
            button.setText(modmanager)
            button.setCheckable(True)
            button.clicked.connect(func(modmanager))
            row = i // columns  # calculate row
            col = i % columns  # calculate column
            buttons.append(button)
            manager_layout.addWidget(button, row + 1, col)

        # Select first mod manager as default
        buttons[0].setChecked(True)
        self.app.source = utils.SUPPORTED_MODMANAGERS[0]
        ##############################################################

        # Create second page (instance selection) ####################
        self.instances_widget = qtw.QWidget()
        self.instances_widget.hide()  # hide as default
        layout.addWidget(self.instances_widget)

        # Create layout for instances
        instances_layout = qtw.QVBoxLayout()
        self.instances_widget.setLayout(instances_layout)

        # Add label with instruction
        label = qtw.QLabel()
        label.setText(self.app.lang["select_src_instance_text"])
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
        self.src_cancel_button = qtw.QPushButton(self.app.lang["cancel"])
        self.src_cancel_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.src_cancel_button)

        # Seperate cancel button with spacing
        self.button_layout.addSpacing(200)

        # Back button with icon
        self.back_button = qtw.QPushButton(self.app.lang["back"])
        self.back_button.setIcon(
            qta.icon("fa5s.chevron-left", color=self.app.theme["text_color"])
        )
        self.back_button.setDisabled(True)
        self.button_layout.addWidget(self.back_button)

        # Next button with icon
        self.next_button = qtw.QPushButton(self.app.lang["next"])
        self.next_button.setLayoutDirection(  # Switch icon and text
            qtc.Qt.LayoutDirection.RightToLeft
        )
        self.next_button.setIcon(
            qta.icon("fa5s.chevron-right", color=self.app.theme["text_color"])
        )
        self.next_button.clicked.connect(self.goto_secnd_page)
        self.button_layout.addWidget(self.next_button)

        # Bind next button to instances list box
        self.instances_box.itemSelectionChanged.connect(
            lambda: self.next_button.setDisabled(False)
        )

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

        # Create source mod manager instance
        # if not already done
        if self.app.source == "Vortex":
            self.modinstance = managers.VortexInstance(self.app)
        elif self.app.source == "ModOrganizer":
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
            raise utils.UiException("[error_no_instances] Found no instances!")

        # Hide first page and show second page
        self.modmanagers_widget.hide()
        self.instances_widget.show()

        # Bind next button to done
        self.next_button.clicked.disconnect()
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
        Loads selected instance, displays
        it in main window and closes dialog.
        """

        # Load instance from source mod manager
        name = self.instances_box.currentItem().text()
        loadingdialog = LoadingDialog(
            parent=self,
            app=self.app,
            func=lambda ldialog: (self.modinstance.load_instance(name, ldialog)),
        )
        loadingdialog.exec()
        self.app.src_modinstance = self.modinstance

        # Hide old source panel if existing
        if self.app.src_widget:
            self.app.src_widget.hide()
            self.app.src_widget.destroy()

        # Create source widget with instance details
        self.modinstance.show_src_widget()

        # Update source button
        self.app.src_button.setText(self.app.lang["edit_source"])
        self.app.src_button.clicked.disconnect()
        # self.back_button.setDisabled(True)
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
        self.app.dst_button.setText(self.app.lang["select_source"])
        self.app.dst_button.clicked.disconnect()
        self.app.dst_button.clicked.connect(
            lambda: DestinationDialog(self.app.root, self.app).show()
        )
        self.app.mig_icon.setPixmap(
            qta.icon("fa5s.chevron-right", color=self.app.theme["text_color"]).pixmap(
                120, 120
            )
        )

        # Close dialog
        self.accept()
