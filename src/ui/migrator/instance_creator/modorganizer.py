"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
)

from core.game.game import Game
from core.mod_manager.instance_info import InstanceInfo
from core.mod_manager.modorganizer.mo2_instance_info import MO2InstanceInfo
from core.utilities.env_resolver import resolve
from ui.widgets.browse_edit import BrowseLineEdit

from .instance import InstanceWidget


class ModOrganizerWidget(InstanceWidget):
    """
    Class for creating and customizing ModOrganizer instances.
    """

    id = "modorganizer"
    log: logging.Logger = logging.getLogger("ModOrganizerWidget")

    __glayout: QGridLayout
    __instance_name_entry: QLineEdit
    __use_portable: QRadioButton
    __use_global: QRadioButton
    __instance_path_entry: BrowseLineEdit
    __mods_path_entry: BrowseLineEdit
    __install_mo2: QCheckBox
    __use_root_builder: QCheckBox

    @override
    def _init_ui(self) -> None:
        self.__glayout = QGridLayout()
        self.__glayout.setContentsMargins(0, 0, 0, 0)
        self.__glayout.setColumnStretch(0, 1)
        self.__glayout.setColumnStretch(1, 3)
        self.__glayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__glayout)

        instance_name_label = QLabel(self.tr("Instance name:"))
        self.__glayout.addWidget(instance_name_label, 0, 0)
        self.__instance_name_entry = QLineEdit()
        self.__instance_name_entry.setPlaceholderText(
            self.tr("eg. My Migrated Instance")
        )
        self.__instance_name_entry.textChanged.connect(
            lambda _: self.valid.emit(self.validate())
        )
        self.__instance_name_entry.textChanged.connect(self.__on_name_change)
        self.__glayout.addWidget(self.__instance_name_entry, 0, 1)

        instance_type_label = QLabel(self.tr("Instance type:"))
        self.__glayout.addWidget(instance_type_label, 3, 0)

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.__glayout.addLayout(hlayout, 3, 1)

        self.__use_portable = QRadioButton(self.tr("Portable instance"))
        self.__use_portable.toggled.connect(lambda _: self.valid.emit(self.validate()))
        hlayout.addWidget(self.__use_portable)

        self.__use_global = QRadioButton(self.tr("Global instance"))
        self.__use_global.toggled.connect(lambda _: self.valid.emit(self.validate()))
        self.__use_global.toggled.connect(self.__on_global_toggled)
        hlayout.addWidget(self.__use_global)

        instance_path_label = QLabel(self.tr("Instance path:"))
        self.__glayout.addWidget(instance_path_label, 1, 0)
        self.__instance_path_entry = BrowseLineEdit()
        self.__instance_path_entry.setPlaceholderText(
            self.tr("eg. C:\\Modding\\My Migrated Instance")
        )
        self.__instance_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        self.__instance_path_entry.textChanged.connect(
            lambda _: self.valid.emit(self.validate())
        )
        self.__instance_path_entry.pathChanged.connect(self.__on_path_change)
        self.__glayout.addWidget(self.__instance_path_entry, 1, 1)

        mods_path_label = QLabel(self.tr("Mods path:"))
        self.__glayout.addWidget(mods_path_label, 2, 0)
        self.__mods_path_entry = BrowseLineEdit()
        self.__mods_path_entry.setPlaceholderText(
            self.tr("eg. C:\\Modding\\My Migrated Instance\\mods")
        )
        self.__mods_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        self.__mods_path_entry.textChanged.connect(
            lambda _: self.valid.emit(self.validate())
        )
        self.__glayout.addWidget(self.__mods_path_entry, 2, 1)

        install_mo2_label = QLabel(self.tr("Install Mod Organizer 2:"))
        self.__glayout.addWidget(install_mo2_label, 4, 0)

        self.__install_mo2 = QCheckBox()
        self.__install_mo2.toggled.connect(lambda _: self.valid.emit(self.validate()))
        self.__glayout.addWidget(self.__install_mo2, 4, 1)

        use_root_builder_label = QLabel(self.tr("Use Root Builder plugin:"))
        self.__glayout.addWidget(use_root_builder_label, 5, 0)
        self.__use_root_builder = QCheckBox()
        self.__use_root_builder.setToolTip(
            self.tr(
                "If enabled, mod files for the game's root folder will be moved to a "
                '"Root" subfolder in their mod instead of copied to the game\'s root folder.'
            )
        )
        self.__use_root_builder.toggled.connect(
            lambda _: self.valid.emit(self.validate())
        )
        self.__glayout.addWidget(self.__use_root_builder, 5, 1)

        self.__use_global.setChecked(True)

    def __on_name_change(self, new_name: str) -> None:
        if (
            self.__instance_path_entry.text().strip()
            and not self.__use_global.isChecked()
        ):
            instance_path = Path(self.__instance_path_entry.text())

            try:
                self.__instance_path_entry.setText(str(instance_path.parent / new_name))
            except Exception as ex:
                self.log.warning("Failed to update instance path!", exc_info=ex)

        elif self.__use_global.isChecked():
            self.__instance_path_entry.setText(
                resolve("%LOCALAPPDATA%\\ModOrganizer\\") + new_name
            )

    def __on_path_change(self, old_path_text: str, new_path_text: str) -> None:
        if new_path_text.strip():
            new_instance_path = Path(new_path_text)

            if not self.__use_global.isChecked():
                self.__instance_name_entry.setText(new_instance_path.name)

            if old_path_text.strip() and self.__mods_path_entry.text().strip():
                old_instance_path = Path(old_path_text)
                mods_path = Path(self.__mods_path_entry.text())

                if mods_path.is_relative_to(old_instance_path):
                    try:
                        self.__mods_path_entry.setText(
                            str(
                                new_instance_path
                                / mods_path.relative_to(old_instance_path)
                            )
                        )
                    except Exception as ex:
                        self.log.warning("Failed to update mods path!", exc_info=ex)

            elif not self.__mods_path_entry.text().strip():
                self.__mods_path_entry.setText(str(new_instance_path / "mods"))

    def __on_global_toggled(self, checked: bool) -> None:
        if checked:
            self.__instance_path_entry.setDisabled(True)
            self.__instance_path_entry.setText(
                resolve("%LOCALAPPDATA%\\ModOrganizer\\")
                + self.__instance_name_entry.text()
            )

            self.__mods_path_entry.setText(
                resolve("%LOCALAPPDATA%\\ModOrganizer\\")
                + self.__instance_name_entry.text()
                + "\\mods"
            )

            self.__install_mo2.setChecked(False)
        else:
            self.__instance_path_entry.setText("")
            self.__mods_path_entry.setText("")

        self.__install_mo2.setDisabled(checked)
        self.__instance_path_entry.setDisabled(checked)

    @override
    def validate(self) -> bool:
        valid: bool = True

        if not self.__instance_name_entry.text().strip():
            valid = False

        instance_path = Path(self.__instance_path_entry.text())
        if (
            not self.__instance_path_entry.text().strip()
            or not instance_path.parent.is_dir()
        ):
            valid = False

        mods_path = Path(self.__mods_path_entry.text())
        if not self.__mods_path_entry.text().strip() or (
            not mods_path.parent.is_dir()
            and not mods_path.is_relative_to(instance_path)
        ):
            valid = False

        if self.__use_global.isChecked() and self.__install_mo2.isChecked():
            valid = False

        return valid

    @override
    def get_instance(self, game: Game) -> InstanceInfo:
        mo2_instance = MO2InstanceInfo(
            display_name=self.__instance_name_entry.text(),
            game=game,
            profile="Default",
            is_global=self.__use_global.isChecked(),
            base_folder=Path(self.__instance_path_entry.text()),
            mods_folder=Path(self.__mods_path_entry.text()),
            profiles_folder=Path(self.__instance_path_entry.text()) / "profiles",
            install_mo2=self.__install_mo2.isChecked(),
            use_root_builder=self.__use_root_builder.isChecked(),
        )

        return mo2_instance
