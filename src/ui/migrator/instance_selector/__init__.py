"""
Copyright (c) Cutleast
"""

from .instance import InstanceWidget
from .modorganizer import ModOrganizerWidget
from .vortex import VortexWidget

INSTANCE_WIDGETS: list[type[InstanceWidget]] = [
    VortexWidget,
    ModOrganizerWidget,
]
"""
List of available instance widgets.
"""
