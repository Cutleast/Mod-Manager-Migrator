"""
Copyright (c) Cutleast
"""

import logging
from abc import abstractmethod

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from core.game.game import Game
from core.mod_manager.instance_info import InstanceInfo


class BaseCreatorWidget[I: InstanceInfo](QWidget):
    """
    Base class for customizing an instance for a preselected mod manager.
    """

    valid = Signal(bool)
    """
    This signal gets emitted when the validation of the customized instance changes.
    """

    log: logging.Logger

    def __init__(self) -> None:
        super().__init__()

        self.log = logging.getLogger(self.__class__.__name__)

        self._init_ui()

    @staticmethod
    @abstractmethod
    def get_id() -> str:
        """
        Returns:
            str: The internal id of the corresponding mod manager.
        """

    @abstractmethod
    def _init_ui(self) -> None: ...

    @abstractmethod
    def validate(self) -> bool:
        """
        Validates the customized instance data.

        Returns:
            bool: `True` if the customized instance is valid, `False` otherwise
        """

    @abstractmethod
    def get_instance(self, game: Game) -> I:
        """
        Gets the data for the customized instance.

        Args:
            game (Game): The game of the instance

        Returns:
            I: The data for the customized instance
        """
