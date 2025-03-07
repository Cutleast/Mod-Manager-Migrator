"""
Copyright (c) Cutleast
"""

from typing import Any

import qtawesome as qta
from PySide6.QtWidgets import QApplication, QLineEdit


class PasteLineEdit(QLineEdit):
    """
    LineEdit with paste button.
    """

    def __init__(self, *args: Any, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[call-overload]

        self.paste_action = self.addAction(
            qta.icon("fa5s.paste", color="#ffffff"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.paste_action.triggered.connect(
            lambda: (
                self.setText(QApplication.clipboard().text())
                if QApplication.clipboard().text().strip()
                else None
            )
        )
