"""
Copyright (c) Cutleast
"""

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app_context import AppContext
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
        self.setMinimumSize(800, 585)
        self.resize(800, 585)

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
        icon_label.setPixmap(
            qta.icon("mdi6.cog", color=self.palette().text().color()).pixmap(42, 42)
        )
        hlayout.addWidget(icon_label)

        title_label = QLabel(self.tr("Settings"))
        title_label.setObjectName("h2")
        hlayout.addWidget(title_label)

        self.__vlayout.addSpacing(15)

    def __init_settings_widget(self) -> None:
        self.__settings_widget = SettingsWidget(self.__app_config)
        self.__settings_widget.changed.connect(self.__on_change)
        self.__settings_widget.restart_required.connect(self.__on_restart_required)
        self.__vlayout.addWidget(self.__settings_widget)

        self.__vlayout.addSpacing(15)

    def __init_footer(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.reject)
        hlayout.addWidget(cancel_button)

        hlayout.addStretch()

        self.__save_button = QPushButton(self.tr("Save"))
        self.__save_button.setObjectName("primary")
        self.__save_button.clicked.connect(self.__save)
        self.__save_button.setDisabled(True)
        hlayout.addWidget(self.__save_button)

    def __on_change(self) -> None:
        self.setWindowTitle(self.tr("Settings") + "*")
        self.__save_button.setEnabled(True)

    def __on_restart_required(self) -> None:
        self.__restart_required = True

    def __save(self) -> None:
        self.__settings_widget.apply_settings()
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
                AppContext.get_app().restart_application()
