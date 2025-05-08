"""
Copyright (c) Cutleast
"""

import locale
import logging
from typing import Optional

import win32api

from .base_enum import BaseEnum

log: logging.Logger = logging.getLogger("Utilities.Localisation")


class Language(BaseEnum):
    """
    Enum for supported application languages.
    """

    System = "System"
    German = "de_DE"
    English = "en_US"


def detect_system_locale() -> Optional[str]:
    """
    Attempts to detect the system locale.

    Returns:
        str: System locale
    """

    log.info("Detecting system locale...")

    system_locale: Optional[str] = None

    try:
        language_id = win32api.GetUserDefaultLangID()
        system_language = locale.windows_locale[language_id]
        log.debug(f"Detected system language: {system_language}")

        system_locale = Language.get_by_value(system_language, Language.English).value

    except Exception as ex:
        log.error(f"Failed to get system language: {ex}", exc_info=ex)

    return system_locale
