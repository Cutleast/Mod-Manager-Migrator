"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QWidget


def move_to_center(widget: QWidget, referent: QWidget | None = None) -> None:
    """
    Moves `widget` to center of its parent or if given to center of `referent`.

    Args:
        widget (QWidget): Widget to move.
        referent (QWidget, optional): Widget reference for center coords.
            Defaults to `widget.parent()`.
    """

    size: QSize = widget.size()
    w: int = size.width()
    h: int = size.height()

    rsize: QSize
    if referent is None:
        rsize = QApplication.primaryScreen().size()
    else:
        rsize = referent.size()

    rw = rsize.width()
    rh = rsize.height()

    x = int((rw / 2) - (w / 2))
    y = int((rh / 2) - (h / 2))

    widget.move(x, y)


def apply_shadow(widget: QWidget, size: int = 4, shadow_color: str = "#181818") -> None:
    """
    Applies standardized shadow effect to a widget.
    Replaces existing graphics effects.

    Args:
        widget (QWidget): Widget to apply shadow
        size (int, optional): Shadow size. Defaults to 4.
        shadow_color (str, optional): Shadow color. Defaults to "#181818".
    """

    shadoweffect = QGraphicsDropShadowEffect(widget)
    shadoweffect.setBlurRadius(size)
    shadoweffect.setXOffset(size)
    shadoweffect.setYOffset(size)
    shadoweffect.setColor(QColor.fromString(shadow_color))
    widget.setGraphicsEffect(shadoweffect)
