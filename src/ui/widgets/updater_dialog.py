"""
Copyright (c) Cutleast
"""

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)
from semantic_version import Version

from ui.widgets.link_button import LinkButton


class UpdaterDialog(QDialog):
    """
    Class for updater dialog.
    """

    def __init__(
        self,
        installed_version: Version,
        latest_version: Version,
        changelog: str,
        download_url: str,
    ) -> None:
        super().__init__(QApplication.activeModalWidget())

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        title_label = QLabel(self.tr("An Update is available to download!"))
        title_label.setObjectName("title_label")
        vlayout.addWidget(title_label)

        version_label = QLabel(
            f"\
{self.tr('Installed Version')}: {installed_version} \
{self.tr('Latest Version')}: {latest_version}"
        )
        version_label.setObjectName("h3")
        vlayout.addWidget(version_label)

        changelog_box = QTextBrowser()
        changelog_box.setMarkdown(changelog)
        changelog_box.setCurrentFont(QFont("Arial"))
        vlayout.addWidget(changelog_box, 1)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.cancel_button = QPushButton(self.tr("Ignore Update"))
        self.cancel_button.clicked.connect(self.accept)
        hlayout.addWidget(self.cancel_button)

        hlayout.addStretch()

        download_button = LinkButton(
            url=download_url, display_text=self.tr("Download Update")
        )
        download_button.setObjectName("primary")
        download_button.clicked.connect(self.accept)
        hlayout.addWidget(download_button)

        self.show()
        self.resize(700, 400)
        self.exec()
