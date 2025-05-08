"""
Copyright (c) Cutleast
"""

from .mod_manager import ModManager
from .modorganizer.modorganizer import ModOrganizer
from .vortex.vortex import Vortex

MOD_MANAGERS: list[type[ModManager]] = [
    Vortex,
    ModOrganizer,
]
"""
This list contains all available mod managers.
"""
