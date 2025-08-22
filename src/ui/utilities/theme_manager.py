"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.utilities.qt_res_provider import (
    load_json_resource,
    read_resource,
)
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from cutleast_core_lib.ui.utilities.theme_manager import (
    ThemeManager as BaseThemeManager,
)
from PySide6.QtGui import QPalette


class ThemeManager(BaseThemeManager):
    """
    ThemeManager implementation for MMM.
    """

    @override
    def _get_stylesheet(self) -> str:
        ui_mode: str = self.ui_mode.name.lower()
        base_stylesheet_file: str = ":/base_stylesheet.qss"
        stylesheet_file: str = ":/" + ui_mode + "_stylesheet.qss"
        mmm_stylesheet_file: str = ":/style.qss"

        base_stylesheet: str = read_resource(base_stylesheet_file)
        raw_stylesheet: str = read_resource(stylesheet_file)
        mmm_stylesheet: str = read_resource(mmm_stylesheet_file)
        final_stylesheet: str = (
            base_stylesheet + "\n" + raw_stylesheet + "\n" + mmm_stylesheet
        )

        colors: dict[str, str] = self.__get_colors()
        for placeholder_name, color in colors.items():
            final_stylesheet = final_stylesheet.replace(f"<{placeholder_name}>", color)

        return final_stylesheet

    def __get_colors(self) -> dict[str, str]:
        ui_mode: str = self.ui_mode.name.lower()

        return load_json_resource(f":/{ui_mode}_theme.json")

    @override
    def _apply_to_palette(self, palette: QPalette) -> None:
        colors: dict[str, str] = self.__get_colors()

        palette.setColor(QPalette.ColorRole.Text, colors["text_color"])
        palette.setColor(QPalette.ColorRole.Accent, colors["accent_color"])
        palette.setColor(QPalette.ColorRole.Highlight, colors["highlighted_accent"])
        palette.setColor(QPalette.ColorRole.Link, colors["accent_color"])

    @override
    def _init_icon_provider(self) -> IconProvider:
        return IconProvider(self.ui_mode, self.__get_colors()["text_color"])
