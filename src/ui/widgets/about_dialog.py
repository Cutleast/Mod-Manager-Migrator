"""
Copyright (c) Cutleast
"""

from cutleast_core_lib.ui.widgets.about_dialog import AboutDialog as BaseAboutDialog
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QWidget


class AboutDialog(BaseAboutDialog):
    """
    About dialog.
    """

    def __init__(
        self,
        app_name: str,
        app_version: str,
        app_icon: QIcon,
        app_license: str,
        licenses: dict[str, str],
        parent: QWidget | None = None,
    ) -> None:
        text: str = QApplication.translate(
            "AboutDialog",
            "Created by Cutleast (<a href='https://www.nexusmods.com/users/65733731'>"
            "NexusMods</a> | <a href='https://github.com/cutleast'>GitHub</a> "
            "| <a href='https://ko-fi.com/cutleast'>Ko-Fi</a>)<br><br>Icon by "
            "Wuerfelhusten (<a href='https://www.nexusmods.com/users/122160268'>"
            "NexusMods</a>)<br><br>Licensed under "
            "Attribution-NonCommercial-NoDerivatives 4.0 International",
        )

        # Add translator credit if available
        translator_info: str = QApplication.translate(
            "AboutDialog", "<<Put your translator information here.>>"
        )
        if translator_info != "<<Put your translator information here.>>":
            text += "\n\n" + translator_info

        super().__init__(
            app_name, app_version, app_icon, app_license, licenses, text, parent
        )
