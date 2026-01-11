"""
Copyright (c) Cutleast
"""

from typing import cast, override

from cutleast_core_lib.core.config.app_config import AppConfig as BaseAppConfig
from cutleast_core_lib.ui.settings.app_settings import AppSettings
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from cutleast_core_lib.ui.widgets.enum_dropdown import EnumDropdown
from cutleast_core_lib.ui.widgets.link_button import LinkButton
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
)

from core.config.app_config import AppConfig
from core.utilities.localisation import Language


class SettingsWidget(AppSettings):
    """
    Widget for configuring application settings.
    """

    HARDLINKS_URL: str = (
        "https://github.com/Cutleast/Mod-Manager-Migrator/blob/main/Hardlinks.md"
    )
    """URL to Hardlinks.md file on GitHub."""

    __language_box: EnumDropdown[Language]

    __use_hardlinks_box: QCheckBox
    __replace_when_merge_box: QCheckBox
    __activate_dst_instance_box: QCheckBox
    __modname_limit_box: QSpinBox

    def __init__(self, initial_config: AppConfig) -> None:
        super().__init__(initial_config)

        self._basic_flayout.setRowVisible(3, False)  # Hide accent color field

        self.__language_box.currentValueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__language_box.currentValueChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )

        self.__use_hardlinks_box.checkStateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__replace_when_merge_box.checkStateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__activate_dst_instance_box.checkStateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__modname_limit_box.valueChanged.connect(
            lambda _: self.changed_signal.emit()
        )

    @override
    def _init_ui(self) -> None:
        super()._init_ui()

        self.__init_app_settings()
        self.__init_migration_settings()

    def __init_app_settings(self) -> None:
        config = cast(AppConfig, self._initial_config)
        self.__language_box = EnumDropdown(Language, config.language)
        self.__language_box.installEventFilter(self)
        self._basic_flayout.insertRow(
            5, "*" + self.tr("App language:"), self.__language_box
        )

    def __init_migration_settings(self) -> None:
        config = cast(AppConfig, self._initial_config)

        migration_settings_group = QGroupBox(self.tr("Migration settings"))
        self._vlayout.addWidget(migration_settings_group)

        migration_settings_glayout = QGridLayout()
        migration_settings_group.setLayout(migration_settings_glayout)

        use_hardlinks_label = QLabel(self.tr("Use hardlinks if possible:"))
        migration_settings_glayout.addWidget(use_hardlinks_label, 0, 0)

        hlayout = QHBoxLayout()
        migration_settings_glayout.addLayout(hlayout, 0, 1)
        self.__use_hardlinks_box = QCheckBox()
        self.__use_hardlinks_box.setChecked(config.use_hardlinks)
        hlayout.addWidget(self.__use_hardlinks_box)

        hlayout.addStretch()

        hardlinks_help_button = LinkButton(
            url=SettingsWidget.HARDLINKS_URL,
            display_text=self.tr("What are hardlinks?"),
            icon=IconProvider.get_qta_icon("ri.information-line"),
        )
        hlayout.addWidget(hardlinks_help_button)

        replace_when_merge_label = QLabel(
            self.tr("Replace existing files when merging instances:")
        )
        migration_settings_glayout.addWidget(replace_when_merge_label, 1, 0)

        self.__replace_when_merge_box = QCheckBox()
        self.__replace_when_merge_box.setChecked(config.replace_when_merge)
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
        self.__activate_dst_instance_box.setChecked(config.activate_new_instance)
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
        self.__modname_limit_box.setValue(config.modname_limit)
        migration_settings_glayout.addWidget(self.__modname_limit_box, 3, 1)

    @override
    def apply(self, config: BaseAppConfig) -> None:
        super().apply(config)

        config = cast(AppConfig, config)

        config.language = self.__language_box.getCurrentValue()

        config.use_hardlinks = self.__use_hardlinks_box.isChecked()
        config.replace_when_merge = self.__replace_when_merge_box.isChecked()
        config.activate_new_instance = self.__activate_dst_instance_box.isChecked()
        config.modname_limit = self.__modname_limit_box.value()
