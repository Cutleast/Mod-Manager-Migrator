"""
Copyright (c) Cutleast
"""

from shutil import disk_usage


def get_free_disk_space(disk: str) -> int:
    """
    Gets free space of a disk.

    Args:
        disk (str): Name of disk (for eg. "C:")

    Returns:
        int: free space in bytes.
    """

    return disk_usage(disk).free
