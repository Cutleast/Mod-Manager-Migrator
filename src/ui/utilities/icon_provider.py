"""
Copyright (c) Cutleast
"""

from PySide6.QtGui import QPalette


def get_icon_name_for_palette(icon_name: str, palette: QPalette) -> str:
    """
    Returns the icon name for the text color of the specified palette.

    Args:
        icon_name (str): Base name of the icon
        palette (QPalette): Palette

    Raises:
        ValueError:
            when text color of the specified palette is neither #000000 nor #FFFFFF

    Returns:
        str: Full icon name with file suffix
    """

    text_color: str = palette.text().color().name().upper()

    match text_color:
        case "#000000":
            return f"{icon_name}_dark.svg"
        case "#FFFFFF":
            return f"{icon_name}_light.svg"
        case _:
            raise ValueError(f"Unknown text color: {text_color}")
