"""
Copyright (c) Cutleast
"""

import logging
from typing import Literal, Optional

import darkdetect
from PySide6.QtGui import QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

from core.utilities.qt_res_provider import load_json_resource, read_resource

from .ui_mode import UIMode


class StylesheetProcessor:
    """
    Class for processing stylesheet and configuring UI mode and accent colors.
    Applies stylesheet automatically to QApplication on changes.
    """

    log = logging.getLogger("StylesheetProcessor")

    app: QApplication
    ui_mode: UIMode
    theme: dict[str, str]

    def __init__(self, app: QApplication, ui_mode: UIMode = UIMode.System) -> None:
        self.app = app
        self.ui_mode = ui_mode

        self.__load_font()

        self.apply_app_stylesheet()

    def __load_font(self) -> None:
        """
        Loads font from resources and adds them to the QFontDatabase.
        """

        font_id: int = QFontDatabase.addApplicationFont(":/fonts/BebasNeue Book.otf")

        if font_id == -1:
            self.log.error("Failed to load font!")

    def set_ui_mode(self, ui_mode: UIMode) -> None:
        """
        Sets UI mode and reapplies stylesheet to app.

        Args:
            ui_mode (UIMode): New UI mode.
        """

        self.ui_mode = ui_mode
        self.apply_app_stylesheet()

    def get_ui_mode(self) -> UIMode:
        """
        Gets UI mode.

        Returns:
            UIMode: UI mode.
        """

        ui_mode: UIMode
        if self.ui_mode == UIMode.System:
            ui_mode = self.detect_system_ui_mode()
        else:
            ui_mode = self.ui_mode

        return ui_mode

    def apply_app_stylesheet(self) -> None:
        """
        Applies Stylesheet according to UI mode and accent colors to app.
        """

        ui_mode: str = self.get_ui_mode().name.lower()
        base_stylesheet_file: str = ":/base_stylesheet.qss"
        stylesheet_file: str = ":/" + ui_mode + "_stylesheet.qss"
        theme_file: str = ":/" + ui_mode + "_theme.json"

        base_stylesheet: str = read_resource(base_stylesheet_file)
        raw_stylesheet: str = read_resource(stylesheet_file)
        self.theme = load_json_resource(theme_file)

        stylesheet: str = StylesheetProcessor.prepare_stylesheet(
            base_stylesheet + raw_stylesheet, self.theme
        )
        self.log.debug(f"Applied theme {theme_file!r} to stylesheet.")

        self.app.setStyleSheet(stylesheet)
        palette = self.app.palette()
        palette.setColor(QPalette.ColorRole.Text, self.theme["icon_color"])
        palette.setColor(QPalette.ColorRole.Accent, self.theme["accent_color"])
        palette.setColor(QPalette.ColorRole.Highlight, self.theme["highlighted_accent"])
        palette.setColor(QPalette.ColorRole.Link, self.theme["accent_color"])
        self.app.setPalette(palette)
        self.log.debug(f"Applied stylesheet {stylesheet_file!r} to application.")

    @staticmethod
    def prepare_stylesheet(stylesheet: str, colors: dict[str, str]) -> str:
        """
        Prepares stylesheet by replacing placeholders with colors.

        Args:
            stylesheet (str): Raw stylesheet text to prepare.
            colors (dict[str, str]): Dictionary containing placeholder names and colors.

        Returns:
            str: Stylesheet that's ready to be applied to app.
        """

        result: str = stylesheet

        for key, value in colors.items():
            result = result.replace(f"<{key}>", value)

        return result

    @staticmethod
    def detect_system_ui_mode() -> Literal[UIMode.Light, UIMode.Dark]:
        """
        Detects system UI mode. Returns `UIMode.Dark` if detection fails.

        Returns:
            Literal[UIMode.Light, UIMode.Dark]: Detected UI mode.
        """

        system_mode: Optional[str] = darkdetect.theme()

        match system_mode:
            case "Light":
                return UIMode.Light
            case "Dark":
                return UIMode.Dark
            case None:
                StylesheetProcessor.log.warning("Failed to detect system UI mode!")
                return UIMode.Dark
            case unknown:
                StylesheetProcessor.log.warning(f"Unknown system UI mode {unknown!r}!")
                return UIMode.Dark
