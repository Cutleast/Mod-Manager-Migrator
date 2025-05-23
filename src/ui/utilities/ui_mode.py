"""
Copyright (c) Cutleast
"""

from enum import StrEnum

from core.utilities.base_enum import BaseEnum


class UIMode(StrEnum, BaseEnum):
    """
    Enum for UI modes (Dark, Light, System)
    """

    Dark = "Dark"
    Light = "Light"
    System = "System"
