"""
Copyright (c) Cutleast
"""

import qtawesome as qta
from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QWidget,
)

from core.config.app_config import AppConfig
from ui.utilities.ui_mode import UIMode
from ui.widgets.link_button import LinkButton
from ui.widgets.smooth_scroll_area import SmoothScrollArea


class SettingsWidget(SmoothScrollArea):
    """
    Widget for configuring application settings.
    """

    changed = Signal()
    """
    This signal gets emitted when a setting changes.
    """

    __app_config: AppConfig

    __glayout: QGridLayout

    __log_level_box: QComboBox
    __log_num_of_files_box: QSpinBox
    __language_box: QComboBox
    __ui_mode_box: QComboBox
    __use_hardlinks_box: QCheckBox
    __replace_when_merge_box: QCheckBox

    def __init__(self, app_config: AppConfig) -> None:
        super().__init__()

        self.__app_config = app_config

        self.__init_ui()

    def __init_ui(self) -> None:
        scroll_widget = QWidget()
        scroll_widget.setObjectName("transparent")
        self.setWidget(scroll_widget)

        self.__glayout = QGridLayout()
        self.__glayout.setContentsMargins(0, 0, 0, 0)
        self.__glayout.setColumnStretch(0, 1)
        self.__glayout.setColumnStretch(1, 3)
        self.__glayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_widget.setLayout(self.__glayout)

        self.__init_settings()

    def __init_settings(self) -> None:
        log_level_label = QLabel(self.tr("Log level:"))
        self.__glayout.addWidget(log_level_label, 0, 0)

        self.__log_level_box = QComboBox()
        self.__log_level_box.setEditable(False)
        self.__log_level_box.addItems(
            [
                "Debug",
                "Info",
                "Warning",
                "Error",
                "Critical",
            ]
        )
        self.__log_level_box.setCurrentText(self.__app_config.log_level.capitalize())
        self.__log_level_box.installEventFilter(self)
        self.__log_level_box.currentTextChanged.connect(lambda _: self.changed.emit())
        self.__glayout.addWidget(self.__log_level_box, 0, 1)

        log_num_of_files_label = QLabel(self.tr("Number of newest log files to keep:"))
        self.__glayout.addWidget(log_num_of_files_label, 1, 0)

        self.__log_num_of_files_box = QSpinBox()
        self.__log_num_of_files_box.setRange(-1, 100)
        self.__log_num_of_files_box.setValue(self.__app_config.log_num_of_files)
        self.__log_num_of_files_box.installEventFilter(self)
        self.__log_num_of_files_box.valueChanged.connect(lambda _: self.changed.emit())
        self.__glayout.addWidget(self.__log_num_of_files_box, 1, 1)

        language_label = QLabel(self.tr("Language:"))
        self.__glayout.addWidget(language_label, 2, 0)

        self.__language_box = QComboBox()
        self.__language_box.setEditable(False)
        self.__language_box.addItems(["System", "en_US", "de_DE"])
        self.__language_box.setCurrentText(self.__app_config.language)
        self.__language_box.installEventFilter(self)
        self.__language_box.currentTextChanged.connect(lambda _: self.changed.emit())
        self.__glayout.addWidget(self.__language_box, 2, 1)

        ui_mode_label = QLabel(self.tr("UI mode:"))
        self.__glayout.addWidget(ui_mode_label, 3, 0)

        self.__ui_mode_box = QComboBox()
        self.__ui_mode_box.setEditable(False)
        self.__ui_mode_box.addItems([m.name for m in UIMode])
        self.__ui_mode_box.setCurrentText(self.__app_config.ui_mode.capitalize())
        self.__ui_mode_box.installEventFilter(self)
        self.__ui_mode_box.currentTextChanged.connect(lambda _: self.changed.emit())
        self.__glayout.addWidget(self.__ui_mode_box, 3, 1)

        use_hardlinks_label = QLabel(self.tr("Use hardlinks if possible:"))
        self.__glayout.addWidget(use_hardlinks_label, 4, 0)

        hlayout = QHBoxLayout()
        self.__glayout.addLayout(hlayout, 4, 1)
        self.__use_hardlinks_box = QCheckBox()
        self.__use_hardlinks_box.setChecked(self.__app_config.use_hardlinks)
        self.__use_hardlinks_box.checkStateChanged.connect(
            lambda _: self.changed.emit()
        )
        hlayout.addWidget(self.__use_hardlinks_box)

        hardlinks_help_button = LinkButton(
            url="https://github.com/Cutleast/Mod-Manager-Migrator/Hardlinks.md",
            display_text=self.tr("What are hardlinks?"),
            icon=qta.icon("mdi6.help", color=self.palette().text().color()),
        )
        hlayout.addWidget(hardlinks_help_button)

        replace_when_merge_label = QLabel(
            self.tr("Replace existing files when merging instances:")
        )
        self.__glayout.addWidget(replace_when_merge_label, 5, 0)

        self.__replace_when_merge_box = QCheckBox()
        self.__replace_when_merge_box.setChecked(self.__app_config.replace_when_merge)
        self.__replace_when_merge_box.checkStateChanged.connect(
            lambda _: self.changed.emit()
        )
        self.__glayout.addWidget(self.__replace_when_merge_box, 5, 1)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if (
            event.type() == QEvent.Type.Wheel
            and (isinstance(source, QComboBox) or isinstance(source, QSpinBox))
            and isinstance(event, QWheelEvent)
        ):
            self.wheelEvent(event)
            return True

        return super().eventFilter(source, event)

    def apply_settings(self) -> None:
        """
        Applies the current settings to the AppConfig.
        """

        self.__app_config.log_level = self.__log_level_box.currentText().lower()
        self.__app_config.log_num_of_files = self.__log_num_of_files_box.value()
        self.__app_config.language = self.__language_box.currentText()
        self.__app_config.ui_mode = self.__ui_mode_box.currentText().lower()
        self.__app_config.use_hardlinks = self.__use_hardlinks_box.isChecked()
        self.__app_config.replace_when_merge = self.__replace_when_merge_box.isChecked()
