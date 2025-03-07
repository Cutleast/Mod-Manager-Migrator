"""
Copyright (c) Cutleast
"""

import os
from typing import Any

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton


class BrowseLineEdit(QLineEdit):
    """
    Custom QLineEdit with a "Browse" button to open a QFileDialog.

    TODO: Fix overlapping text with browse button if text is too long
    """

    __browse_button: QPushButton
    __file_dialog: QFileDialog

    pathChanged = Signal(str, str)
    """
    This signal gets emitted when a file is selected in the QFileDialog.
    It emits the current text and the selected file.
    """

    def __init__(self, *args: Any, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[call-overload]

        self.__file_dialog = QFileDialog()

        hlayout: QHBoxLayout = QHBoxLayout(self)
        hlayout.setContentsMargins(0, 0, 0, 0)

        # Push Browse Button to the right-hand side
        hlayout.addStretch()

        self.__browse_button = QPushButton()
        self.__browse_button.setIcon(
            qta.icon(
                "fa5s.folder-open",
                color=self.palette().text().color(),
                scale_factor=1.5,
            )
        )
        self.__browse_button.clicked.connect(self.__browse)
        self.__browse_button.setCursor(Qt.CursorShape.ArrowCursor)
        hlayout.addWidget(self.__browse_button)

    def configureFileDialog(self, *args: Any, **kwargs: dict[str, Any]) -> None:
        """
        Redirects `args` and `kwargs` to constructor of `QFileDialog`.
        """

        self.__file_dialog = QFileDialog(*args, **kwargs)  # type: ignore[call-overload]

    def setFileMode(self, mode: QFileDialog.FileMode) -> None:
        """
        Redirects `mode` to `QFileDialog.setFileMode()`.
        """

        self.__file_dialog.setFileMode(mode)

    def setText(self, text: str) -> None:
        old_text: str = self.text()
        super().setText(text)
        self.pathChanged.emit(old_text, text)

    def __browse(self) -> None:
        current_text: str = self.text().strip()

        if current_text:
            current_path: str = os.path.normpath(current_text)
            if self.__file_dialog.fileMode() == QFileDialog.FileMode.Directory:
                self.__file_dialog.setDirectory(current_path)
            else:
                self.__file_dialog.setDirectory(os.path.dirname(current_path))
                self.__file_dialog.selectFile(os.path.basename(current_path))

        if self.__file_dialog.exec():
            selected_files: list[str] = self.__file_dialog.selectedFiles()

            if selected_files:
                file: str = os.path.normpath(selected_files.pop())
                self.setText(file)

                self.pathChanged.emit(current_text, file)


def test() -> None:
    from PySide6.QtWidgets import QApplication

    app = QApplication()

    edit = BrowseLineEdit()
    edit.setFileMode(QFileDialog.FileMode.AnyFile)
    edit.show()

    app.exec()


if __name__ == "__main__":
    test()
