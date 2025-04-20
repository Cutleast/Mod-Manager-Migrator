"""
Copyright (c) Cutleast
"""

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton

from ui.utilities.icon_provider import get_icon_name_for_palette


class SearchBar(QLineEdit):
    """
    Adapted QLineEdit with search icon, clear button and case sensitivity toggle.
    """

    __live_mode: bool = True

    searchChanged = Signal(str, bool)
    """
    This signal is emitted when the search text changes
    or when the case sensitivity is toggled or when a return is pressed.
    """

    __cs_toggle: QPushButton
    __clear_button: QPushButton

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)

        self.addAction(
            QIcon(":/icons/" + get_icon_name_for_palette("search", self.palette())),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.setPlaceholderText(self.tr("Search..."))

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hlayout)

        hlayout.addStretch()

        self.__cs_toggle = QPushButton()
        self.__cs_toggle.setCursor(Qt.CursorShape.ArrowCursor)
        self.__cs_toggle.setIcon(
            qta.icon(
                "mdi6.format-letter-case",
                color=self.palette().text().color(),
                scale_factor=1.5,
            )
        )
        self.__cs_toggle.setCheckable(True)
        self.__cs_toggle.clicked.connect(self.setFocus)
        self.__cs_toggle.clicked.connect(self.__on_search_change)
        self.__cs_toggle.setToolTip(self.tr("Toggle case sensitivity"))
        self.__cs_toggle.hide()
        hlayout.addWidget(self.__cs_toggle)

        self.__clear_button = QPushButton()
        self.__clear_button.setCursor(Qt.CursorShape.ArrowCursor)
        self.__clear_button.setIcon(
            qta.icon("fa.close", color=self.palette().text().color())
        )
        self.__clear_button.clicked.connect(lambda: self.setText(""))
        self.__clear_button.clicked.connect(self.setFocus)
        self.__clear_button.clicked.connect(self.returnPressed.emit)
        self.__clear_button.hide()
        hlayout.addWidget(self.__clear_button)

        self.textChanged.connect(self.__on_text_change)
        self.returnPressed.connect(lambda: self.__on_search_change(True))

    def __on_text_change(self, text: str) -> None:
        self.__clear_button.setVisible(bool(text.strip()))
        self.__cs_toggle.setVisible(bool(text.strip()))

        self.__on_search_change()

    def __on_search_change(self, return_pressed: bool = False) -> None:
        if self.__live_mode or return_pressed:
            self.searchChanged.emit(self.text(), self.__cs_toggle.isChecked())

    def setLiveMode(self, live_mode: bool) -> None:
        """
        Set the live mode state. If live mode is enabled, the search bar
        will emit the `searchChanged` signal when the text changes.
        Otherwise it gets only emitted when a return is pressed.

        Args:
            live_mode (bool): `True` if live mode is enabled, `False` otherwise.
        """

        self.__live_mode = live_mode

    def getCaseSensitivity(self) -> bool:
        """
        Get the case sensitivity state.

        Returns:
            bool: `True` if case sensitivity is enabled, `False` otherwise
        """

        return self.__cs_toggle.isChecked()
