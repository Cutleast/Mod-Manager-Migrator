"""
Copyright (c) Cutleast
"""

import random
import string
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

    @staticmethod
    def generate_id(length: int = 9) -> str:
        """
        Generates a unique profile id for a new profile.

        Args:
            length (int): The length of the generated profile id

        Returns:
            str: The generated profile id
        """

        return "".join(
            [random.choice(string.ascii_letters + string.digits) for _ in range(length)]
        )
