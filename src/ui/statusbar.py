"""
Copyright (c) Cutleast
"""

from typing import Optional

import qtawesome as qta
from cutleast_core_lib.core.utilities.logger import Logger
from cutleast_core_lib.core.utilities.truncate import raw_string
from cutleast_core_lib.ui.widgets.link_button import LinkButton
from cutleast_core_lib.ui.widgets.log_window import LogWindow
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QStatusBar


class StatusBar(QStatusBar):
    """
    Status bar for main window.
    """

    log_signal: Signal = Signal(str)
    logger: Logger

    KOFI_URL: str = "https://ko-fi.com/cutleast"
    """URL to Ko-fi page."""

    __log_window: Optional[LogWindow] = None

    def __init__(self, log_visible: bool) -> None:
        super().__init__()

        self.logger = Logger.get()
        self.logger.set_callback(self.log_signal.emit)

        self.status_label = QLabel()
        self.status_label.setObjectName("protocol")
        self.status_label.setTextFormat(Qt.TextFormat.PlainText)
        self.log_signal.connect(
            lambda text: self.status_label.setText(
                raw_string(text.removesuffix("\n"), max_length=200)
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        self.status_label.setMinimumWidth(100)
        self.status_label.setVisible(log_visible)
        self.insertPermanentWidget(0, self.status_label, stretch=1)

        kofi_button = LinkButton(
            StatusBar.KOFI_URL,
            self.tr("Support me on Ko-fi"),
            QIcon(":/icons/ko-fi.png"),
        )
        # kofi_button.setFixedHeight(20)
        self.addPermanentWidget(kofi_button)

        copy_log_button = QPushButton()
        copy_log_button.setFixedSize(20, 20)
        copy_log_button.setIcon(
            qta.icon("mdi6.content-copy", color=self.palette().text().color())
        )
        copy_log_button.setIconSize(QSize(16, 16))
        copy_log_button.clicked.connect(
            lambda: QApplication.clipboard().setText(self.logger.get_content())
        )
        copy_log_button.setToolTip(self.tr("Copy log to clipboard"))
        copy_log_button.setVisible(log_visible)
        self.addPermanentWidget(copy_log_button)

        open_log_button = QPushButton()
        open_log_button.setFixedSize(20, 20)
        open_log_button.setIcon(
            qta.icon("fa5s.external-link-alt", color=self.palette().text().color())
        )
        open_log_button.setIconSize(QSize(16, 16))
        open_log_button.clicked.connect(self.__open_log_window)
        open_log_button.setToolTip(self.tr("View log"))
        open_log_button.setVisible(log_visible)
        self.addPermanentWidget(open_log_button)

    def __open_log_window(self) -> None:
        self.__log_window = LogWindow(self.logger.get_content())
        self.log_signal.connect(
            self.__log_window.addMessage, Qt.ConnectionType.QueuedConnection
        )
        self.__log_window.show()

    def close_log_window(self) -> None:
        if self.__log_window is not None:
            self.__log_window.close()

        self.__log_window = None
