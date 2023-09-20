"""
This script builds the MMM.exe and packs
all its dependencies in one folder.
"""

import os
from pathlib import Path

DIST_FOLDER = Path("main.dist").resolve()
APPNAME="Mod Manager Migrator"
VERSION="2.3"
AUTHOR="Cutleast"
LICENSE="Attribution-NonCommercial-NoDerivatives 4.0 International"
UNUSED_FILES = [
    DIST_FOLDER / "qt6datavisualization.dll",
    DIST_FOLDER / "qt6network.dll",
    DIST_FOLDER / "qt6pdf.dll",
    DIST_FOLDER / "PySide6" / "QtNetwork.pyd",
    DIST_FOLDER / "PySide6" / "QtDataVisualization.pyd",
    # DIST_FOLDER / "libcrypto-1_1.dll"
]

print("Building with nuitka...")
cmd = f'nuitka \
--msvc="latest" \
--standalone \
--disable-console \
--include-data-dir="./src/data=./data" \
--include-data-dir="./src/venv/Lib/site-packages/qtawesome=./qtawesome" \
--enable-plugin=pyside6 \
--remove-output \
--company-name="{AUTHOR}" \
--product-name="{APPNAME}" \
--file-version="{VERSION}" \
--product-version="{VERSION}" \
--file-description="{APPNAME}" \
--copyright="{LICENSE}" \
--nofollow-import-to=tkinter \
--windows-icon-from-ico="./src/data/icons/mmm.ico" \
--output-filename="MMM.exe" \
"./src/main.py"'
os.system(cmd)

print("Deleting unused files...")
for file in UNUSED_FILES:
    if not file.is_file():
        continue
    os.remove(file)
    print(f"Removed '{file.name}'.")

print("Done!")
