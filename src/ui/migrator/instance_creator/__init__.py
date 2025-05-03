"""
Copyright (c) Cutleast
"""

from .base_creator_widget import BaseCreatorWidget
from .modorganizer_creator_widget import ModOrganizerCreatorWidget
from .vortex_creator_widget import VortexCreatorWidget

INSTANCE_WIDGETS: list[type[BaseCreatorWidget]] = [
    VortexCreatorWidget,
    ModOrganizerCreatorWidget,
]
"""
List of available instance widgets.
"""
