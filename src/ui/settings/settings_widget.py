"""
Copyright (c) Cutleast
"""

from typing import override

import qtawesome as qta
from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.config.app_config import AppConfig
from core.utilities.localisation import Language
from core.utilities.logger import Logger
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

    __vlayout: QVBoxLayout

    __log_level_box: QComboBox
    __log_num_of_files_box: QSpinBox
    __language_box: QComboBox
    __ui_mode_box: QComboBox
    __use_hardlinks_box: QCheckBox
    __replace_when_merge_box: QCheckBox
    __activate_dst_instance_box: QCheckBox
    __modname_limit_box: QSpinBox

    def __init__(self, app_config: AppConfig) -> None:
        super().__init__()

        self.__app_config = app_config

        self.__init_ui()

    def __init_ui(self) -> None:
        scroll_widget = QWidget()
        scroll_widget.setObjectName("transparent")
        self.setWidget(scroll_widget)

        self.__vlayout = QVBoxLayout()
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_widget.setLayout(self.__vlayout)

        self.__init_app_settings()
        self.__init_migration_settings()

    def __init_app_settings(self) -> None:
        app_settings_group = QGroupBox(self.tr("App settings"))
        self.__vlayout.addWidget(app_settings_group)

        app_settings_glayout = QGridLayout()
        app_settings_glayout.setContentsMargins(0, 0, 0, 0)
        app_settings_group.setLayout(app_settings_glayout)

        log_level_label = QLabel(self.tr("Log level:"))
        app_settings_glayout.addWidget(log_level_label, 0, 0)

        self.__log_level_box = QComboBox()
        self.__log_level_box.setEditable(False)
        self.__log_level_box.addItems(
            [level.name.capitalize() for level in Logger.Level]
        )
        self.__log_level_box.setCurrentText(
            self.__app_config.log_level.name.capitalize()
        )
        self.__log_level_box.installEventFilter(self)
        self.__log_level_box.currentTextChanged.connect(lambda _: self.changed.emit())
        app_settings_glayout.addWidget(self.__log_level_box, 0, 1)

        log_num_of_files_label = QLabel(self.tr("Number of newest log files to keep:"))
        app_settings_glayout.addWidget(log_num_of_files_label, 1, 0)

        self.__log_num_of_files_box = QSpinBox()
        self.__log_num_of_files_box.setRange(-1, 255)
        self.__log_num_of_files_box.setValue(self.__app_config.log_num_of_files)
        self.__log_num_of_files_box.installEventFilter(self)
        self.__log_num_of_files_box.valueChanged.connect(lambda _: self.changed.emit())
        app_settings_glayout.addWidget(self.__log_num_of_files_box, 1, 1)

        language_label = QLabel(self.tr("Language:"))
        app_settings_glayout.addWidget(language_label, 2, 0)

        self.__language_box = QComboBox()
        self.__language_box.setEditable(False)
        self.__language_box.addItems([lang.name for lang in Language])
        self.__language_box.setCurrentText(self.__app_config.language.name)
        self.__language_box.installEventFilter(self)
        self.__language_box.currentTextChanged.connect(lambda _: self.changed.emit())
        app_settings_glayout.addWidget(self.__language_box, 2, 1)

        ui_mode_label = QLabel(self.tr("UI mode:"))
        app_settings_glayout.addWidget(ui_mode_label, 3, 0)

        self.__ui_mode_box = QComboBox()
        self.__ui_mode_box.setEditable(False)
        self.__ui_mode_box.addItems([m.name for m in UIMode])
        self.__ui_mode_box.setCurrentText(self.__app_config.ui_mode.capitalize())
        self.__ui_mode_box.installEventFilter(self)
        self.__ui_mode_box.currentTextChanged.connect(lambda _: self.changed.emit())
        app_settings_glayout.addWidget(self.__ui_mode_box, 3, 1)

    def __init_migration_settings(self) -> None:
        migration_settings_group = QGroupBox(self.tr("Migration settings"))
        self.__vlayout.addWidget(migration_settings_group)

        migration_settings_glayout = QGridLayout()
        migration_settings_glayout.setContentsMargins(0, 0, 0, 0)
        migration_settings_group.setLayout(migration_settings_glayout)

        use_hardlinks_label = QLabel(self.tr("Use hardlinks if possible:"))
        migration_settings_glayout.addWidget(use_hardlinks_label, 0, 0)

        hlayout = QHBoxLayout()
        migration_settings_glayout.addLayout(hlayout, 0, 1)
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
        migration_settings_glayout.addWidget(replace_when_merge_label, 1, 0)

        self.__replace_when_merge_box = QCheckBox()
        self.__replace_when_merge_box.setChecked(self.__app_config.replace_when_merge)
        self.__replace_when_merge_box.checkStateChanged.connect(
            lambda _: self.changed.emit()
        )
        migration_settings_glayout.addWidget(self.__replace_when_merge_box, 1, 1)

        activate_dst_instance_label = QLabel(
            self.tr(
                "Activate destination instance after migration "
                "if supported by the destination mod manager:"
            )
        )
        activate_dst_instance_label.setWordWrap(True)
        migration_settings_glayout.addWidget(activate_dst_instance_label, 2, 0)

        self.__activate_dst_instance_box = QCheckBox()
        self.__activate_dst_instance_box.setChecked(
            self.__app_config.activate_new_instance
        )
        self.__activate_dst_instance_box.checkStateChanged.connect(
            lambda _: self.changed.emit()
        )
        migration_settings_glayout.addWidget(self.__activate_dst_instance_box, 2, 1)

        modname_limit_label = QLabel(
            self.tr(
                "Character limit for mod names (strongly recommended when migrating to MO2):"
            )
        )
        modname_limit_label.setWordWrap(True)
        migration_settings_glayout.addWidget(modname_limit_label, 3, 0)

        self.__modname_limit_box = QSpinBox()
        self.__modname_limit_box.installEventFilter(self)
        self.__modname_limit_box.setRange(-1, 255)
        self.__modname_limit_box.setValue(self.__app_config.modname_limit)
        self.__modname_limit_box.valueChanged.connect(lambda _: self.changed.emit())
        migration_settings_glayout.addWidget(self.__modname_limit_box, 3, 1)

    @override
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

        self.__app_config.log_level = Logger.Level[
            self.__log_level_box.currentText().upper()
        ]
        self.__app_config.log_num_of_files = self.__log_num_of_files_box.value()
        self.__app_config.language = Language[self.__language_box.currentText()]
        self.__app_config.ui_mode = UIMode[self.__ui_mode_box.currentText()]
        self.__app_config.use_hardlinks = self.__use_hardlinks_box.isChecked()
        self.__app_config.replace_when_merge = self.__replace_when_merge_box.isChecked()
        self.__app_config.activate_new_instance = (
            self.__activate_dst_instance_box.isChecked()
        )
        self.__app_config.modname_limit = self.__modname_limit_box.value()
