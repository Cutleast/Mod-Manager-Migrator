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
    Base class for selecting instances from a preselected mod manager.
    """

    id: str
    """
    Id of the corresponding mod manager.
    """

    _instance_names: list[str]
    """
    List of possible instance names.
    """

    changed = Signal()
    """
    This signal gets emitted everytime the selected instance changes.
    """

    valid = Signal(bool)
    """
    This signal gets emitted when the validation of the selected instance changes.
    """

    def __init__(self, instance_names: list[str] = []):
        super().__init__()

        self._instance_names = instance_names

        self._init_ui()

        self.changed.connect(self.__on_change)

    @abstractmethod
    def _init_ui(self) -> None: ...

    def __on_change(self) -> None:
        self.valid.emit(self.validate())

    @abstractmethod
    def _update(self) -> None: ...

    def set_instances(self, instance_names: list[str]) -> None:
        """
        Sets the list of possible instances.

        Args:
            instance_names (list[str]): The list of possible instances
        """

        self._instance_names = instance_names

        self._update()

    @abstractmethod
    def validate(self) -> bool:
        """
        Validates the selected instance.

        Returns:
            bool: `True` if the selected instance is valid, `False` otherwise
        """

    @abstractmethod
    def get_instance(self, game: Game) -> InstanceInfo:
        """
        Returns the data for the selected instance.

        Returns:
            InstanceInfo: The data for the selected instance
        """
