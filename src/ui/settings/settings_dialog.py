"""
Copyright (c) Cutleast
"""

import os
import subprocess

from cutleast_core_lib.core.utilities.exe_info import get_execution_info
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.config.app_config import AppConfig

from .settings_widget import SettingsWidget


class SettingsDialog(QDialog):
    """
    Dialog for application settings.
    """

    __app_config: AppConfig

    __vlayout: QVBoxLayout

    __settings_widget: SettingsWidget
    __save_button: QPushButton

    __restart_required: bool = False

    def __init__(self, app_config: AppConfig) -> None:
        super().__init__()

        self.__app_config = app_config

        self.__init_ui()
        self.setWindowTitle(self.tr("Settings"))
        self.setMinimumSize(800, 635)
        self.resize(800, 635)

        self.__settings_widget.changed_signal.connect(self.__on_change)
        self.__settings_widget.restart_required_signal.connect(
            self.__on_restart_required
        )

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_settings_widget()
        self.__init_footer()

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        hlayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.__vlayout.addLayout(hlayout)

        icon_label = QLabel()
        icon_label.setPixmap(IconProvider.get_qta_icon("mdi6.cog").pixmap(42, 42))
        hlayout.addWidget(icon_label)

        title_label = QLabel(self.tr("Settings"))
        title_label.setObjectName("h2")
        hlayout.addWidget(title_label)

        restart_hint_label = QLabel(
            self.tr("Settings marked with * require a restart to take effect.")
        )
        self.__vlayout.addWidget(restart_hint_label)

    def __init_settings_widget(self) -> None:
        self.__settings_widget = SettingsWidget(self.__app_config)
        self.__vlayout.addWidget(self.__settings_widget)

    def __init_footer(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.reject)
        hlayout.addWidget(cancel_button)

        hlayout.addStretch()

        self.__save_button = QPushButton(self.tr("Save"))
        self.__save_button.setDefault(True)
        self.__save_button.clicked.connect(self.__save)
        self.__save_button.setDisabled(True)
        hlayout.addWidget(self.__save_button)

    def __on_change(self) -> None:
        self.setWindowTitle(self.tr("Settings") + "*")
        self.__save_button.setEnabled(True)

    def __on_restart_required(self) -> None:
        self.__restart_required = True

    def __save(self) -> None:
        self.__settings_widget.apply(self.__app_config)
        self.__app_config.save()

        self.accept()

        if self.__restart_required:
            messagebox = QMessageBox()
            messagebox.setWindowTitle(self.tr("Restart required"))
            messagebox.setText(
                self.tr(
                    "The app must be restarted for the changes to take effect! Restart now?"
                )
            )
            messagebox.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            messagebox.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
            messagebox.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
            choice = messagebox.exec()

            if choice == QMessageBox.StandardButton.Yes:
                from app import App

                if App.get().main_window.close():
                    os.startfile(subprocess.list2cmdline(get_execution_info()[0]))
