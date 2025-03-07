"""
Copyright (c) Cutleast
"""

from abc import abstractmethod

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from core.game.game import Game
from core.mod_manager.instance_info import InstanceInfo


class InstanceWidget(QWidget):
    """
    Base class for customizing an instance for a preselected mod manager.
    """

    id: str
    """
    Id of the corresponding mod manager.
    """

    valid = Signal(bool)
    """
    This signal gets emitted when the validation of the customized instance changes.
    """

    def __init__(self) -> None:
        super().__init__()

        self._init_ui()

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
    def get_instance(self, game: Game) -> InstanceInfo:
        """
        Gets the data for the customized instance.

        Args:
            game (Game): The game of the instance

        Returns:
            InstanceInfo: The data for the customized instance
        """
