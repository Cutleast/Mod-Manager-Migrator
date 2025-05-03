"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit

from core.game.game import Game
from core.mod_manager.vortex.profile_info import ProfileInfo
from core.mod_manager.vortex.vortex import Vortex

from .base_creator_widget import BaseCreatorWidget


class VortexCreatorWidget(BaseCreatorWidget[ProfileInfo]):
    """
    Class for creating and customizing Vortex profiles.
    """

    __glayout: QGridLayout
    __profile_name_entry: QLineEdit

    @override
    @staticmethod
    def get_id() -> str:
        return Vortex.get_id()

    @override
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

    @override
    def validate(self) -> bool:
        return bool(self.__profile_name_entry.text().strip())

    @override
    def get_instance(self, game: Game) -> ProfileInfo:
        profile = ProfileInfo(
            display_name=self.__profile_name_entry.text(),
            game=game,
            id=Vortex.generate_id(),
        )

        return profile
