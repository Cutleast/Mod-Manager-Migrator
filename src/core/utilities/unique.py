"""
Copyright (c) Cutleast
"""

from typing import Any, Callable, Iterable, Optional, TypeVar

T = TypeVar("T")


def unique(iterable: Iterable[T], key: Optional[Callable[[T], Any]] = None) -> list[T]:
    """
    Removes all duplicates from an iterable.

    Args:
        iterable (Iterable[T]): Iterable with duplicates.
        key (Optional[Callable[[T], Any]], optional):
            Key function to identify unique elements. Defaults to None.

    Returns:
        list[T]: List without duplicates.
    """

    if key is None:
        return list(set(iterable))

    else:
        return list({key(item): item for item in iterable}.values())
