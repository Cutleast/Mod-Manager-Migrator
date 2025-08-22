"""
Copyright (c) Cutleast
"""

from typing import Annotated

from cutleast_core_lib.core.config.app_config import AppConfig as BaseAppConfig
from cutleast_core_lib.core.utilities.dynamic_default_model import default_factory
from pydantic import Field

from core.utilities.localisation import Language


class AppConfig(BaseAppConfig):
    """
    Class for managing application settings.
    """

    language: Language = Language.System
    """App language"""

    use_hardlinks: bool = True
    """Use hardlinks instead of copying files when merging mods"""

    replace_when_merge: bool = True
    """Replace existing files when merging mods"""

    activate_new_instance: bool = True
    """Activate the migrated instance (if supported by the mod manager)"""

    modname_limit: Annotated[int, Field(ge=-1, le=255)] = 100
    """
    Character limit for mod names
    (especially relevant for MO2 where mod name = folder name)
    """

    @default_factory("log_visible")
    @classmethod
    def _show_log(cls) -> bool:
        return True
