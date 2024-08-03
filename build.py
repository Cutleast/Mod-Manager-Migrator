"""
This script builds the MMM.exe and packs
all its dependencies in one folder.
"""

import os
import shutil
import zipfile
from pathlib import Path

COMPILER = "cx_freeze"  # "cx_freeze" or "nuitka"

DIST_FOLDER = Path("main.dist").resolve()
APPNAME = "Mod Manager Migrator"
VERSION = "2.5"
AUTHOR = "Cutleast"
LICENSE = "Attribution-NonCommercial-NoDerivatives 4.0 International"
OUTPUT_FOLDER = DIST_FOLDER.with_name("MMM")
UNUSED_FILES = [
    DIST_FOLDER / "qt6datavisualization.dll",
    DIST_FOLDER / "qt6network.dll",
    DIST_FOLDER / "qt6pdf.dll",
    DIST_FOLDER / "PySide6" / "QtNetwork.pyd",
    DIST_FOLDER / "PySide6" / "QtDataVisualization.pyd",
    # DIST_FOLDER / "libcrypto-1_1.dll"
]
ADDITIONAL_ITEMS: dict[Path, Path] = {
    Path("src") / "data": DIST_FOLDER / "data",
}
OUTPUT_ARCHIVE = Path(f"MMM v{VERSION}.zip").resolve()

print(f"Building with {COMPILER}...")
if COMPILER == "nuitka":
    cmd = f'nuitka \
    --msvc="latest" \
    --standalone \
    --disable-console \
    --include-data-dir="./.venv/Lib/site-packages/qtawesome=./qtawesome" \
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

elif COMPILER == "cx_freeze":
    import sys

    from cx_Freeze import Executable, setup

    build_options = {
        "include_files": [("./.venv/Lib/site-packages/plyvel_ci.libs", "./lib/plyvel")],
        "include_path": "./src",
        "build_exe": DIST_FOLDER.name,
    }

    base = "gui"

    executables = [
        Executable(
            "./src/main.py",
            base=base,
            target_name="MMM.exe",
            icon="./src/data/icons/mmm.ico",
            copyright=LICENSE,
        )
    ]

    sys.argv.append("build_exe")

    setup(
        name=APPNAME,
        version=VERSION,
        description=APPNAME,
        author=AUTHOR,
        license=LICENSE,
        options={"build_exe": build_options},
        executables=executables,
    )

else:
    raise ValueError(f"Compiler {COMPILER!r} is not supported!")

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

    print(f"Copied {str(item)!r} to {str(dest.relative_to(DIST_FOLDER))!r}.")

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
os.rename(DIST_FOLDER, OUTPUT_FOLDER)

print("Packing into zip archive...")
if OUTPUT_ARCHIVE.is_file():
    os.remove(OUTPUT_ARCHIVE)
    print("Deleted already existing zip archive.")

def zip_folder(folder_path: Path, output_path: Path):
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
