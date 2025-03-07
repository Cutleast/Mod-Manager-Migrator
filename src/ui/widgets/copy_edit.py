"""
Copyright (c) Cutleast
"""

from typing import Any

import qtawesome as qta
from PySide6.QtWidgets import QApplication, QLineEdit


class CopyLineEdit(QLineEdit):
    """
    LineEdit with copy button.
    """

    def __init__(self, *args: Any, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[call-overload]

        self.copy_action = self.addAction(
            qta.icon("fa5s.copy", color="#ffffff"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.copy_action.triggered.connect(
            lambda: (
                QApplication.clipboard().setText(self.text())
                if self.text().strip()
                else None
            )
        )
