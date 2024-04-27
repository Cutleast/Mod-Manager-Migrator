"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import darkdetect

from main import MainApp


class Theme:
    """Class for ui theme. Manages theme and stylesheet."""

    default_dark_theme = {
        "primary_bg": "#202020",
        "secondary_bg": "#2d2d2d",
        "tertiary_bg": "#383838",
        "highlight_bg": "#696969",
        "accent_color": "#d78f46",
        "text_color": "#ffffff",
        "font": "Segoe UI",
        "font_size": "14px",
        "title_font": "Segoe UI",
        "title_size": "28px",
        "subtitle_size": "22px",
        "console_font": "Consolas",
        "console_size": "14px",
        "checkbox_indicator": "url(./data/icons/checkmark_light.svg)",
        "dropdown_arrow": "url(./data/icons/dropdown_light.svg)",
    }
    default_light_theme = {
        "primary_bg": "#f3f3f3",
        "secondary_bg": "#e9e9e9",
        "tertiary_bg": "#dadada",
        "highlight_bg": "#b6b6b6",
        "accent_color": "#d78f46",
        "text_color": "black",
        "font": "Segoe UI",
        "font_size": "14px",
        "title_font": "Segoe UI",
        "title_size": "28px",
        "subtitle_size": "22px",
        "console_font": "Consolas",
        "console_size": "14px",
        "checkbox_indicator": "url(./data/icons/checkmark.svg)",
        "dropdown_arrow": "url(./data/icons/dropdown.svg)",
    }
    default_mode = "dark"
    default_theme = default_dark_theme
    default_stylesheet = ""
    stylesheet = ""

    def __init__(self, app: MainApp):
        self.app = app
        self.mode = self.default_mode
        self.theme = self.default_theme

    def set_mode(self, mode: str):
        """
        Sets <mode> as ui mode.
        """

        mode = mode.lower()
        if mode == "system":
            mode = darkdetect.theme().lower()
        self.mode = mode
        if self.mode == "light":
            self.default_theme = self.default_light_theme
        elif self.mode == "dark":
            self.default_theme = self.default_dark_theme

        return self.default_theme

    def load_theme(self):
        """
        Loads theme according to mode
        """

        if self.mode == "light":
            self.theme = self.default_light_theme
        elif self.mode == "dark":
            self.theme = self.default_dark_theme

        return self.theme

    def load_stylesheet(self):
        """
        Loads stylesheet from data\\style.qss.
        """

        # load stylesheet from qss file
        with open(self.app.qss_path, "r", encoding="utf8") as file:
            stylesheet = file.read()

        self.default_stylesheet = stylesheet

        # parse stylesheet with theme
        self.stylesheet = self.parse_stylesheet(self.theme, stylesheet)

        return self.stylesheet

    def set_stylesheet(self, stylesheet: str = None):
        """
        Sets <stylesheet> as current stylesheet.
        """

        if not stylesheet:
            stylesheet = self.stylesheet

        self.app.setStyleSheet(stylesheet)

    @staticmethod
    def parse_stylesheet(theme: dict, stylesheet: str):
        """
        Parses <stylesheet> by replacing placeholders with values
        from <theme>.
        """

        for setting, value in theme.items():
            stylesheet = stylesheet.replace(f"<{setting}>", value)

        return stylesheet
