"""
Copyright (c) Cutleast
"""

from typing import Optional

import qtawesome as qta
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QStatusBar

from app_context import AppContext
from core.utilities.logger import Logger
from core.utilities.trim import trim_string
from ui.widgets.log_window import LogWindow


class StatusBar(QStatusBar):
    """
    Status bar for main window.
    """

    log_signal: Signal = Signal(str)
    logger: Logger

    __log_window: Optional[LogWindow] = None

    def __init__(self) -> None:
        super().__init__()

        self.logger = AppContext.get_app().logger
        self.logger.set_callback(self.log_signal.emit)

        self.status_label = QLabel()
        self.status_label.setObjectName("protocol")
        self.status_label.setTextFormat(Qt.TextFormat.PlainText)
        self.log_signal.connect(
            lambda text: self.status_label.setText(
                trim_string(text.removesuffix("\n"), max_length=200)
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        self.status_label.setMinimumWidth(100)
        self.insertPermanentWidget(0, self.status_label, stretch=1)

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
        self.addPermanentWidget(copy_log_button)

        open_log_button = QPushButton()
        open_log_button.setFixedSize(20, 20)
        open_log_button.setIcon(
            qta.icon("fa5s.external-link-alt", color=self.palette().text().color())
        )
        open_log_button.setIconSize(QSize(16, 16))
        open_log_button.clicked.connect(self.__open_log_window)
        open_log_button.setToolTip(self.tr("View log"))
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
