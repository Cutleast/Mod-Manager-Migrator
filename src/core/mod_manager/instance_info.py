"""
Copyright (c) Cutleast
"""

from abc import ABC
from dataclasses import dataclass

from core.game.game import Game


@dataclass(frozen=True)
class InstanceInfo(ABC):
    """
    Base class for holding general instance attributes like name, id, etc.

    Used for identifying or creating an instance within a mod manager.
    """

    display_name: str
    """
    The display name of the instance.
    """

    game: Game
    """
    The primary game of this instance.
    """
