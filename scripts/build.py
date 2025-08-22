"""
Copyright (c) Cutleast

Script to build the MMM executables and pack all their dependencies in one folder.
"""

import logging
import re
from pathlib import Path
from typing import Any, override

from cutleast_core_lib.builder.backends.cx_freeze_backend import CxFreezeBackend
from cutleast_core_lib.builder.build_config import BuildConfig
from cutleast_core_lib.builder.build_metadata import BuildMetadata
from cutleast_core_lib.builder.builder import Builder


class Backend(CxFreezeBackend):
    """
    Backend that injects the project version into the app module before building.
    """

    # this injects the version at, e.g. `APP_VERSION: str = "development"`
    VERSION_PATTERN: re.Pattern[str] = re.compile(
        r'(?<=APP_VERSION: str = ")[^"]+(?=")'
    )

    @override
    def preprocess_source(self, source_folder: Path, metadata: BuildMetadata) -> None:
        app_module: Path = source_folder / "app.py"
        app_module.write_text(
            Backend.VERSION_PATTERN.sub(
                str(metadata.project_version), app_module.read_text(encoding="utf8")
            ),
            encoding="utf8",
        )
        self.log.info(
            f"Injected version '{metadata.project_version}' into '{app_module}'."
        )

    @override
    def get_additional_build_options(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Path | None,
        metadata: BuildMetadata,
    ) -> dict[str, Any]:
        return {
            "include_files": [
                (".venv/Lib/site-packages/plyvel_ci.libs", "./lib/plyvel")
            ],
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    config = BuildConfig(
        exe_stem="MMM",
        ext_resources_json=Path("res") / "ext_resources.json",
        icon_path=Path("res") / "icons" / "mmm.ico",
        delete_list=[
            Path("lib") / "PySide6" / "Qt6DataVisualization.dll",
            Path("lib") / "PySide6" / "Qt6Network.dll",
            Path("lib") / "PySide6" / "Qt6OpenGL.dll",
            Path("lib") / "PySide6" / "Qt6OpenGLWidgets.dll",
            Path("lib") / "PySide6" / "Qt6Pdf.dll",
            Path("lib") / "PySide6" / "Qt6Qml.dll",
            Path("lib") / "PySide6" / "Qt6QmlMeta.dll",
            Path("lib") / "PySide6" / "Qt6QmlModels.dll",
            Path("lib") / "PySide6" / "Qt6QmlWorkerScript.dll",
            Path("lib") / "PySide6" / "Qt6Quick.dll",
            Path("lib") / "PySide6" / "Qt6VirtualKeyboard.dll",
            Path("lib") / "PySide6" / "QtDataVisualization.pyd",
            Path("lib") / "PySide6" / "QtNetwork.pyd",
            Path("lib") / "PySide6" / "QtOpenGL.pyd",
            Path("lib") / "PySide6" / "QtOpenGLWidgets.pyd",
            Path("lib") / "libcrypto-3.dll",
            Path("lib") / "mfc140u.dll",
        ],
    )
    backend = Backend()
    builder = Builder(config, backend)

    builder.run()
