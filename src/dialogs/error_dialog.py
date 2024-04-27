"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import pyperclip
import qtawesome as qta
import qtpy.QtWidgets as qtw

import main
import utilities as utils


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
        details: str = "",
        yesno: bool = True,
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
                qtw.QMessageBox.StandardButton.Yes | qtw.QMessageBox.StandardButton.No
            )
            self.button(qtw.QMessageBox.StandardButton.Yes).setText(
                self.app.loc.main._continue
            )
            self.button(qtw.QMessageBox.StandardButton.No).setText(
                self.app.loc.main.exit
            )

        # Only show 'ok' button
        else:
            self.setStandardButtons(qtw.QMessageBox.StandardButton.Ok)

        # Add details button if details are given
        if details:
            self.details_button: qtw.QPushButton = self.addButton(
                self.app.loc.main.show_details, qtw.QMessageBox.ButtonRole.AcceptRole
            )

            self._details = False

            def toggle_details():
                # toggle details
                if not self._details:
                    self._details = True
                    self.details_button.setText(self.app.loc.main.hide_details)
                    self.setInformativeText(details)
                else:
                    self._details = False
                    self.details_button.setText(self.app.loc.main.show_details)
                    self.setInformativeText("")

                # update messagebox size
                # and move messagebox to center of screen
                self.adjustSize()
                utils.center(self)

            self.details_button.clicked.disconnect()
            self.details_button.clicked.connect(toggle_details)
            self.copy_button: qtw.QPushButton = self.addButton(
                "", qtw.QMessageBox.ButtonRole.AcceptRole
            )
            self.copy_button.setIcon(
                qta.icon("mdi6.content-copy", color=self.app.theme["text_color"])
            )
            self.copy_button.clicked.disconnect()
            self.copy_button.clicked.connect(lambda: pyperclip.copy(details))
