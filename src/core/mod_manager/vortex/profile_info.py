"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass

from ..instance_info import InstanceInfo


@dataclass(frozen=True)
class ProfileInfo(InstanceInfo):
    """
    Class for identifying a Vortex profile.
    """

    id: str
    """
    The ID of the profile.
    """
