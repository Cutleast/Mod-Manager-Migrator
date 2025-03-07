"""
Copyright (c) Cutleast
"""

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow

from app_context import AppContext

from .instance.instance_overview_widget import InstanceOverviewWidget
from .menubar import MenuBar
from .statusbar import StatusBar


class MainWindow(QMainWindow):
    """
    Class for main installer window.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setMenuBar(MenuBar())
        self.setCentralWidget(InstanceOverviewWidget())
        self.setStatusBar(StatusBar())

        self.resize(1000, 700)
        self.setStyleSheet(AppContext.get_app().styleSheet())

    def closeEvent(self, event: QCloseEvent) -> None:
        statusbar: StatusBar = self.statusBar()  # type: ignore[assignment]
        statusbar.close_log_window()

        return super().closeEvent(event)
