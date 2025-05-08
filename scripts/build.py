"""
Copyright (c) Cutleast

Script to build the MMM executables and pack all their dependencies in one folder.
"""

import logging
import os
import re
import shutil
import sys
import tomllib
import zipfile
from pathlib import Path
from typing import Any

import jstyleson as json
from cx_Freeze import Executable, setup
from semantic_version import Version

project_file = Path("pyproject.toml")
project_data: dict[str, Any] = tomllib.loads(project_file.read_text(encoding="utf8"))[
    "project"
]
project_name: str = project_data["description"]
project_version: Version = Version(project_data["version"])
project_author: str = project_data["authors"][0]["name"]
project_license: str = (
    Path(project_data["license"]["file"]).read_text(encoding="utf8").splitlines()[0]
)

VERSION_PATTERN: re.Pattern[str] = re.compile(r'(?<=APP_VERSION: str = ")[^"]+(?=")')

logging.basicConfig(level=logging.DEBUG)

logging.info(f"Project name: {project_name}")
logging.info(f"Project version: {project_version}")
logging.info(f"Project author: {project_author}")
logging.info(f"Project license: {project_license}")


def prepare_src() -> None:
    logging.info(f"Preparing source code for '{project_name}'...")

    logging.debug("Copying source code to build directory...")
    shutil.rmtree("build", ignore_errors=True)
    shutil.copytree("src", "build")

    # Set version string in app file
    logging.debug("Setting version string in app file...")
    app_file: Path = Path("build") / "app.py"
    app_file.write_text(
        VERSION_PATTERN.sub(str(project_version), app_file.read_text(encoding="utf8"))
    )


def run_cx_freeze() -> None:
    logging.info("Configuring cx_Freeze...")

    prev_cwd: str = os.getcwd()
    os.chdir("build")

    build_options: dict[str, Any] = {
        "replace_paths": [("*", "")],
        "include_files": [
            ("../.venv/Lib/site-packages/plyvel_ci.libs", "./lib/plyvel")
        ],
        "include_path": ".",
        "packages": ["ctypes"],
        "includes": ["ctypes.wintypes"],
        "excludes": ["tkinter", "unittest"],
        "zip_include_packages": ["encodings", "PySide6", "shiboken6"],
        "build_exe": "../dist/MMM",
    }

    executables: list[Executable] = [
        Executable(
            "main.py",
            base="gui",
            target_name="MMM.exe",
            icon="../res/icons/mmm.ico",
            copyright=project_license,
        ),
        Executable(
            "main.py",
            base="console",
            target_name="MMM_cli.exe",
            icon="../res/icons/mmm.ico",
            copyright=project_license,
        ),
    ]

    file_version = str(project_version.truncate())
    if project_version.prerelease:
        file_version += "." + project_version.prerelease[0].rsplit("-", 1)[1]

    setup(
        name=project_name,
        version=file_version,
        description=project_name,
        author=project_author,
        license=project_license,
        options={"build_exe": build_options},
        executables=executables,
    )

    os.chdir(prev_cwd)


def build() -> None:
    logging.info("Building application with cx_Freeze...")

    if Path("dist/MMM").is_dir():
        shutil.rmtree("dist/MMM")
        logging.debug("Removed old build output folder.")

    prepare_src()

    logging.info("Running cx_Freeze build_exe...")
    if "build_exe" not in sys.argv:
        sys.argv.append("build_exe")
    run_cx_freeze()

    finalize_build()
    logging.info("Done.")


def zip_folder(folder_path: Path, output_path: Path) -> None:
    folder_name = folder_path.name

    # Create the zip file
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Walk the directory tree
        for root, _, files in os.walk(folder_path):
            for file in files:
                # Create the full filepath by joining root directory and the file
                full_path = os.path.join(root, file)
                # Create the archive name by removing the leading directory path
                arcname = os.path.join(
                    folder_name, os.path.relpath(full_path, folder_path)
                )
                # Write the file to the zip archive
                zipf.write(full_path, arcname)


def finalize_build() -> None:
    logging.info("Finalizing build...")

    additional_items: dict[Path, Path] = {}
    for item in json.loads(Path("res/ext_resources.json").read_text(encoding="utf8")):
        for i in Path("res").glob(item):
            additional_items[i] = Path("dist/MMM") / "res" / i.relative_to(Path("res"))

    logging.info(f"Copying {len(additional_items)} additional item(s)...")
    for item, dest in additional_items.items():
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True, copy_function=os.link)
        elif item.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.link(item, dest)
        else:
            logging.error(f"{str(item)!r} does not exist!")
            continue

        logging.info(
            f"Copied {str(item)!r} to {str(dest.relative_to(Path('dist/MMM')))!r}."
        )

    logging.info("Packing into zip archive...")
    output_archive: Path = Path("dist") / f"{project_name} v{project_version}.zip"
    if output_archive.is_file():
        os.unlink(output_archive)
        logging.info("Deleted already existing zip archive.")

    zip_folder(Path("dist/MMM"), output_archive)

    logging.info(f"Packed into '{output_archive}'.")


if __name__ == "__main__":
    try:
        build()
    except Exception as ex:
        logging.error(f"Failed to build application with cx_Freeze: {ex}", exc_info=ex)

        shutil.rmtree("dist/MMM", ignore_errors=True)

    else:
        shutil.rmtree("build", ignore_errors=True)
        logging.debug("Deleted build directory.")
