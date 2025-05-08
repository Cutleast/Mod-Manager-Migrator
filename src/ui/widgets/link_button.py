"""
Copyright (c) Cutleast
"""

import os

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton


class LinkButton(QPushButton):
    """
    Custom QPushButton adapted for hyperlinks.
    """

    def __init__(
        self, url: str, display_text: str | None = None, icon: QIcon | None = None
    ) -> None:
        super().__init__()

        if display_text is not None:
            self.setText(display_text)

        if icon is not None:
            self.setIcon(icon)

        self.clicked.connect(lambda: os.startfile(url))
        self.setToolTip(url)
