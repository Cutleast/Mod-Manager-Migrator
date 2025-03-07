"""
Copyright (c) Cutleast
"""

from .enderal import Enderal
from .enderalse import EnderalSE
from .fallout3 import Fallout3
from .fallout4 import Fallout4
from .falloutnv import FalloutNV
from .game import Game
from .oblivion import Oblivion
from .skyrim import Skyrim
from .skyrimse import SkyrimSE

GAMES: list[type[Game]] = [
    SkyrimSE,
    Skyrim,
    Fallout4,
    FalloutNV,
    Fallout3,
    EnderalSE,
    Enderal,
    Oblivion,
]
"""
This list contains all available games.
"""
