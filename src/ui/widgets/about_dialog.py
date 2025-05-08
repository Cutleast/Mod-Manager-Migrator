"""
Copyright (c) Cutleast
"""

import webbrowser
from typing import Optional

import qtawesome as qta
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from core.utilities.licenses import LICENSES


class AboutDialog(QDialog):
    """
    About dialog.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        app = AppContext.get_app()
        app_name: str = app.APP_NAME
        app_version: str = app.APP_VERSION
        app_icon: QIcon = app.windowIcon()

        self.setWindowTitle(self.tr("About"))

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        tab_widget = QTabWidget()
        tab_widget.tabBar().setExpanding(True)
        tab_widget.setObjectName("centered_tab")
        tab_widget.setIconSize(QSize(16, 16))
        vlayout.addWidget(tab_widget)

        about_tab = QWidget()
        about_tab.setObjectName("transparent")
        tab_widget.addTab(about_tab, self.tr("About"))
        tab_widget.setTabIcon(
            0, qta.icon("fa5s.info-circle", color=self.palette().text().color())
        )

        hlayout = QHBoxLayout()
        about_tab.setLayout(hlayout)

        hlayout.addSpacing(25)

        icon_label = QLabel()
        icon_label.setPixmap(app_icon.pixmap(128, 128))
        hlayout.addWidget(icon_label)

        hlayout.addSpacing(15)

        vlayout = QVBoxLayout()
        hlayout.addLayout(vlayout, 1)

        hlayout.addSpacing(25)
        vlayout.addSpacing(25)

        title_label = QLabel(f"{app_name} v{app_version}")
        title_label.setObjectName("h1")
        vlayout.addWidget(title_label)

        text: str = self.tr(
            "Created by Cutleast (<a href='https://www.nexusmods.com/users/65733731'>"
            "NexusMods</a> | <a href='https://github.com/cutleast'>GitHub</a> "
            "| <a href='https://ko-fi.com/cutleast'>Ko-Fi</a>)<br><br>Icon by "
            "Wuerfelhusten (<a href='https://www.nexusmods.com/users/122160268'>"
            "NexusMods</a>)<br><br>Licensed under "
            "Attribution-NonCommercial-NoDerivatives 4.0 International"
        )

        # Add translator credit if available
        translator_info: str = self.tr("<<Put your translator information here.>>")
        if translator_info != "<<Put your translator information here.>>":
            text += translator_info

        credits_label = QLabel(text)
        credits_label.setTextFormat(Qt.TextFormat.RichText)
        credits_label.setOpenExternalLinks(True)
        vlayout.addWidget(credits_label)

        vlayout.addSpacing(25)

        licenses_tab = QListWidget()
        tab_widget.addTab(licenses_tab, self.tr("Used Software"))
        tab_widget.setTabIcon(
            1, qta.icon("mdi6.script-text-outline", color=self.palette().text().color())
        )

        licenses_tab.addItems(list(LICENSES.keys()))

        licenses_tab.itemDoubleClicked.connect(
            lambda item: webbrowser.open(LICENSES[item.text()])
        )
