"""
Copyright (c) Cutleast
"""

from typing import Optional


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
