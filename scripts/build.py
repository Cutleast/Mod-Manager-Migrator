"""
Copyright (c) Cutleast

Script to build the MMM executables and pack all their dependencies in one folder.
"""

import os
import shutil
import sys
import zipfile
from pathlib import Path

import jstyleson as json

APP_VERSION: str = "3.0.0-alpha-2"
DIST_FOLDER = Path("dist")
OUTPUT_FOLDER = DIST_FOLDER / "MMM"
OUTPUT_ARCHIVE = DIST_FOLDER / f"MMM v{APP_VERSION}.zip"
RES_FOLDER: Path = Path("res")
ADDITIONAL_ITEMS: dict[Path, Path] = {
    Path(".venv") / "Lib" / "site-packages" / "plyvel_ci.libs": OUTPUT_FOLDER
    / "lib"
    / "plyvel"
}

# Add external resources from res/ext_resources.json
with open("res/ext_resources.json", encoding="utf8") as f:
    for item in json.load(f):
        for i in RES_FOLDER.glob(item):
            ADDITIONAL_ITEMS[i] = OUTPUT_FOLDER / "res" / i.relative_to(RES_FOLDER)

if OUTPUT_FOLDER.is_dir():
    shutil.rmtree(OUTPUT_FOLDER)
    print(f"Deleted already existing '{OUTPUT_FOLDER}' folder.")

print("Building with cx_freeze...")
if os.system("cxfreeze build"):
    sys.exit(1)

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

    print(f"Copied {str(item)!r} to {str(dest.relative_to(OUTPUT_FOLDER))!r}.")

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
