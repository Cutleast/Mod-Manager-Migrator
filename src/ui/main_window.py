"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow

from app_context import AppContext
from core.config.app_config import AppConfig

from .main_widget import MainWidget
from .menubar import MenuBar
from .statusbar import StatusBar


class MainWindow(QMainWindow):
    """
    Class for main installer window.
    """

    def __init__(self, app_config: AppConfig) -> None:
        super().__init__()

        self.setMenuBar(MenuBar())
        self.setCentralWidget(MainWidget(app_config))
        self.setStatusBar(StatusBar())

        self.resize(1300, 800)
        self.setStyleSheet(AppContext.get_app().styleSheet())

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        statusbar: StatusBar = self.statusBar()  # type: ignore[assignment]
        statusbar.close_log_window()

        return super().closeEvent(event)
