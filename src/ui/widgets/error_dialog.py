"""
Copyright (c) Cutleast
"""

from typing import Optional

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton, QWidget


class ErrorDialog(QMessageBox):
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
        parent: Optional[QWidget],
        title: str,
        text: str,
        details: str = "",
        yesno: bool = True,
    ):
        super().__init__(parent)

        # Basic configuration
        self.setWindowTitle(title)
        self.setIcon(QMessageBox.Icon.Critical)
        self.setText(text)

        # Show 'continue' and 'cancel' button
        if yesno:
            self.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            self.button(QMessageBox.StandardButton.Yes).setText(self.tr("Continue"))
            self.button(QMessageBox.StandardButton.No).setText(self.tr("Exit"))

        # Only show 'ok' button
        else:
            self.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Add details button if details are given
        if details:
            self.details_button: QPushButton = self.addButton(
                self.tr("Show details..."), QMessageBox.ButtonRole.AcceptRole
            )
            self.details_button.setIcon(
                qta.icon("fa5s.chevron-down", color=self.palette().text().color())
            )

            self.copy_button: QPushButton = self.addButton(
                "", QMessageBox.ButtonRole.YesRole
            )
            self.copy_button.setText("")
            self.copy_button.setIcon(
                qta.icon("mdi6.content-copy", color=self.palette().text().color())
            )
            self.copy_button.clicked.disconnect()
            self.copy_button.clicked.connect(
                lambda: QApplication.clipboard().setText(details)
            )

            self._details = False
            label: Optional[QLabel] = self.findChild(QLabel)

            def toggle_details() -> None:
                # toggle details
                if not self._details:
                    self._details = True
                    self.details_button.setText(self.tr("Hide details..."))
                    self.details_button.setIcon(
                        qta.icon("fa5s.chevron-up", color=self.palette().text().color())
                    )
                    self.setInformativeText(
                        f"<font><p style='font-family: Consolas;font-size: 12px'>{details}</p>"
                    )
                    if label is not None:
                        label.setTextInteractionFlags(
                            Qt.TextInteractionFlag.TextSelectableByMouse
                        )
                        label.setCursor(Qt.CursorShape.IBeamCursor)
                else:
                    self._details = False
                    self.details_button.setText(self.tr("Show details..."))
                    self.details_button.setIcon(
                        qta.icon(
                            "fa5s.chevron-down", color=self.palette().text().color()
                        )
                    )
                    self.setInformativeText("")
                    if label is not None:
                        label.setTextInteractionFlags(
                            Qt.TextInteractionFlag.NoTextInteraction
                        )
                        label.setCursor(Qt.CursorShape.ArrowCursor)

                # update messagebox size
                self.adjustSize()

            self.details_button.clicked.disconnect()
            self.details_button.clicked.connect(toggle_details)
