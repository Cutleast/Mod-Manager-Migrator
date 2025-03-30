"""
Copyright (c) Cutleast

Script to build the MMM executables and pack all their dependencies in one folder.
"""

import os
import shutil
import zipfile
from pathlib import Path

import jstyleson as json
from cx_Freeze import Executable, setup

APPNAME = "Mod Manager Migrator"
DISPLAY_VERSION = "3.0.0-alpha-1"
FILE_VERSION = "3.0.0.0"
AUTHOR = "Cutleast"
LICENSE = "Attribution-NonCommercial-NoDerivatives 4.0 International"
BUILD_FOLDER = Path("main.dist")
DIST_FOLDER = Path("dist")
OUTPUT_FOLDER = DIST_FOLDER / "MMM"
OUTPUT_ARCHIVE = DIST_FOLDER / f"MMM v{DISPLAY_VERSION}.zip"
RES_FOLDER: Path = Path("res")
UNUSED_FILES = [
    BUILD_FOLDER / "qt6datavisualization.dll",
    BUILD_FOLDER / "qt6network.dll",
    BUILD_FOLDER / "qt6pdf.dll",
    BUILD_FOLDER / "PySide6" / "QtNetwork.pyd",
    BUILD_FOLDER / "PySide6" / "QtDataVisualization.pyd",
]
ADDITIONAL_ITEMS: dict[Path, Path] = {}

# Add external resources from res/ext_resources.json
with open("res/ext_resources.json", encoding="utf8") as f:
    for item in json.load(f):
        for i in RES_FOLDER.glob(item):
            ADDITIONAL_ITEMS[i] = BUILD_FOLDER / "res" / i.relative_to(RES_FOLDER)

build_options = {
    "replace_paths": [("*", "")],
    "include_files": [("./.venv/Lib/site-packages/plyvel_ci.libs", "./lib/plyvel")],
    "include_path": "./src",
    "packages": ["ctypes"],
    "includes": ["ctypes.wintypes"],
    "build_exe": BUILD_FOLDER.name,
}

executables = [
    Executable(
        "./src/main.py",
        base="gui",
        target_name="MMM.exe",
        icon="./res/icons/mmm.ico",
        copyright=LICENSE,
    ),
    Executable(
        "./src/main.py",
        base="console",
        target_name="MMM_cli.exe",
        icon="./res/icons/mmm.ico",
        copyright=LICENSE,
    ),
]

print("Building with cx_freeze...")
setup(
    version=FILE_VERSION,
    options={"build_exe": build_options},
    executables=executables,
).run_command("build_exe")

print(f"Copying {len(ADDITIONAL_ITEMS)} additional item(s)...")
for item, dest in ADDITIONAL_ITEMS.items():
    if item.is_dir():
        shutil.copytree(item, dest, dirs_exist_ok=True, copy_function=os.link)
    elif item.is_file():
        os.makedirs(dest.parent, exist_ok=True)
        os.link(item, dest)
    else:
        print(f"{str(item)!r} does not exist!")
        continue

    print(f"Copied {str(item)!r} to {str(dest.relative_to(BUILD_FOLDER))!r}.")

print("Deleting unused files...")
for file in UNUSED_FILES:
    if not file.is_file():
        continue
    os.remove(file)
    print(f"Removed '{file.name}'.")

print("Renaming Output folder...")
if OUTPUT_FOLDER.is_dir():
    shutil.rmtree(OUTPUT_FOLDER)
    print(f"Deleted already existing {OUTPUT_FOLDER.name!r} folder.")
DIST_FOLDER.mkdir(exist_ok=True)
os.rename(BUILD_FOLDER, OUTPUT_FOLDER)

print("Packing into zip archive...")
if OUTPUT_ARCHIVE.is_file():
    os.remove(OUTPUT_ARCHIVE)
    print("Deleted already existing zip archive.")


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


zip_folder(OUTPUT_FOLDER, OUTPUT_ARCHIVE)

print("Done!")
