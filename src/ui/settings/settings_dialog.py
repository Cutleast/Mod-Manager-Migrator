"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

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

    def __init__(self, app_config: AppConfig) -> None:
        super().__init__()

        self.__app_config = app_config

        self.__init_ui()
        self.setMinimumSize(700, 500)
        self.resize(700, 500)

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_settings_widget()
        self.__init_footer()

    def __init_header(self) -> None:
        title_label = QLabel(self.tr("Settings"))
        title_label.setObjectName("h2")
        self.__vlayout.addWidget(title_label)

        self.__vlayout.addSpacing(15)

    def __init_settings_widget(self) -> None:
        self.__settings_widget = SettingsWidget(self.__app_config)
        self.__settings_widget.changed.connect(self.__on_change)
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

    def __save(self) -> None:
        self.__settings_widget.apply_settings()
        self.__app_config.save()

        self.accept()
