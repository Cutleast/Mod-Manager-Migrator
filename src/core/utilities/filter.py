"""
Copyright (c) Cutleast
"""

from typing import Callable, Optional


def matches_filter(
    text: str, filter: Optional[str], case_sensitive: bool = False
) -> bool:
    """
    Checks if a string matches a filter.

    Args:
        text (str): Text to check.
        filter (Optional[str]): Filter to check against.
        case_sensitive (bool, optional): Case sensitivity. Defaults to False.

    Returns:
        bool: True if string matches filter or filter is None, False otherwise.
    """

    if filter is None:
        return True

    if not case_sensitive:
        text = text.lower()
        filter = filter.lower()

    return filter.strip() in text.strip()


def get_first_match[T](items: list[T], filter_func: Callable[[T], bool]) -> T:
    """
    Returns the first item of the specified list the specified filter function
    returns True for.

    Args:
        items (list[T]): List of items to check.
        filter_func (Callable[[T], bool]): Filter function.

    Raises:
        ValueError: If no item matches the filter function.

    Returns:
        T: First item that matches the filter function.
    """

    for item in items:
        if filter_func(item):
            return item

    raise ValueError("No item matches the filter function")
