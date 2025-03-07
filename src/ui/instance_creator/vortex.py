"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit

from core.game.game import Game
from core.mod_manager.instance_info import InstanceInfo
from core.mod_manager.vortex.profile_info import ProfileInfo

from .instance import InstanceWidget


class VortexWidget(InstanceWidget):
    """
    Class for creating and customizing Vortex profiles.
    """

    id = "vortex"

    __glayout: QGridLayout
    __profile_name_entry: QLineEdit

    def _init_ui(self) -> None:
        self.__glayout = QGridLayout()
        self.__glayout.setContentsMargins(0, 0, 0, 0)
        self.__glayout.setColumnStretch(0, 1)
        self.__glayout.setColumnStretch(1, 3)
        self.__glayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__glayout)

        profile_name_label = QLabel(self.tr("Profile name:"))
        self.__glayout.addWidget(profile_name_label, 0, 0)

        self.__profile_name_entry = QLineEdit()
        self.__profile_name_entry.textChanged.connect(
            lambda _: self.valid.emit(self.validate())
        )
        self.__glayout.addWidget(self.__profile_name_entry, 0, 1)

    def validate(self) -> bool:
        return bool(self.__profile_name_entry.text().strip())

    def get_instance(self, game: Game) -> InstanceInfo:
        profile = ProfileInfo(
            display_name=self.__profile_name_entry.text(),
            game=game,
            id=ProfileInfo.generate_id(),
        )

        return profile
