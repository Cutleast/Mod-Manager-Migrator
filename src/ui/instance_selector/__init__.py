"""
Copyright (c) Cutleast
"""

from ui.instance_selector.modorganizer import ModOrganizerWidget

from .instance import InstanceWidget
from .vortex import VortexWidget

INSTANCE_WIDGETS: list[type[InstanceWidget]] = [
    VortexWidget,
    ModOrganizerWidget,
]
"""
List of available instance widgets.
"""
