"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class ErrorSummaryDialog(QDialog):
    """
    Dialog for displaying a summary of the errors that occured while the migration.
    """

    __vlayout: QVBoxLayout
    __splitter: QSplitter

    __list_widget: QListWidget
    __error_text: QPlainTextEdit
    __error_items: dict[str, str]

    def __init__(self, parent: Optional[QWidget], errors: dict[str, str]) -> None:
        super().__init__(parent)

        self.setWindowTitle(self.tr("Error Summary"))

        self.__init_ui()
        self.__init_error_items(errors)

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        help_label = QLabel(self.tr("The following errors occured while migrating:"))
        self.__vlayout.addWidget(help_label)

        self.__init_splitter()
        self.__init_tree_widget()
        self.__init_error_text()

        self.__splitter.setSizes([int(0.3 * self.width()), int(0.7 * self.width())])

    def __init_splitter(self) -> None:
        self.__splitter = QSplitter()
        self.__splitter.setOrientation(Qt.Orientation.Horizontal)
        self.__vlayout.addWidget(self.__splitter, stretch=1)

    def __init_tree_widget(self) -> None:
        self.__list_widget = QListWidget()
        self.__list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.__list_widget.setAlternatingRowColors(True)
        self.__list_widget.currentItemChanged.connect(self.__on_error_selected)

        self.__splitter.addWidget(self.__list_widget)

    def __init_error_text(self) -> None:
        self.__error_text = QPlainTextEdit()
        self.__error_text.setReadOnly(True)
        self.__error_text.setObjectName("protocol")

        self.__splitter.addWidget(self.__error_text)

    def __on_error_selected(self, item: QListWidgetItem, prev: QListWidgetItem) -> None:
        self.__error_text.setPlainText(self.__error_items[item.text()])

    def __init_error_items(self, errors: dict[str, str]) -> None:
        self.__error_items = {}
        for error_name, error_text in errors.items():
            item = QListWidgetItem(error_name)
            self.__list_widget.addItem(item)
            self.__error_items[error_name] = error_text


def test() -> None:
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    errors: dict[str, str] = {
        "Item 1": "An error occured",
        "Item 2": "Another error occured",
        "Item 3": "A third error occured",
    }

    dialog = ErrorSummaryDialog(None, errors)
    dialog.show()

    app.exec()


if __name__ == "__main__":
    test()
