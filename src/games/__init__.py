"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Type

from .enderal import EnderalInstance
from .enderalse import EnderalSEInstance
from .fallout3 import Fallout3Instance
from .fallout4 import Fallout4Instance
from .falloutnv import FalloutNVInstance
from .game import GameInstance
from .oblivion import OblivionInstance
from .skyrim import SkyrimInstance
from .skyrimse import SkyrimSEInstance

GAMES: list[Type[GameInstance]] = [
    SkyrimSEInstance,
    SkyrimInstance,
    Fallout4Instance,
    FalloutNVInstance,
    Fallout3Instance,
    EnderalSEInstance,
    EnderalInstance,
    OblivionInstance,
]
