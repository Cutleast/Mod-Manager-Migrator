"""
Copyright (c) Cutleast
"""

import ctypes
import ctypes.wintypes
import logging
from os import makedirs
from pathlib import Path
from shutil import copyfile, disk_usage
from typing import Optional

from .progress_update import ProgressCallback, ProgressUpdate, safe_run_callback

log: logging.Logger = logging.getLogger("Filesystem")


def create_folder_list(folder: Path) -> list[Path]:
    """
    Creates a list of all files in all subdirectories of a folder.

    Args:
        folder (Path): Folder to get list of files of.

    Returns:
        list[Path]: List of relative file paths from folder and all subdirectories.
    """

    return [item.relative_to(folder) for item in folder.glob("**/*") if item.is_file()]


def get_free_disk_space(disk: str) -> int:
    """
    Gets free space of a disk.

    Args:
        disk (str): Name of disk (for eg. "C:")

    Returns:
        int: free space in bytes.
    """

    return disk_usage(disk).free


def copy_folder(
    src: Path, dst: Path, progress_callback: Optional[ProgressCallback]
) -> None:
    """
    `shutil.copytree`-inspired function to copy entire
    directory trees but with a progress callback.

    Args:
        src (Path): Source folder
        dst (Path): Destination folder
        progress_callback (Optional[ProgressCallback]): Progress callback
    """

    files: list[Path] = [file.relative_to(src) for file in create_folder_list(src)]

    log.info(f"Copying {len(files)} files from {str(src)!r} to {str(dst)!r}...")

    total_size: int = sum((src / file).stat().st_size for file in files)
    current_size: int = 0
    for f, file in enumerate(files):
        log.debug(f"Copying {str(file)!r}... ({f + 1} / {len(files)})")

        src_file = src / file
        dst_file = dst / file

        makedirs(dst_file.parent, exist_ok=True)
        copyfile(src_file, dst_file)

        current_size += dst_file.stat().st_size
        safe_run_callback(progress_callback, ProgressUpdate(current_size, total_size))

    log.info("Copying completed.")


def get_documents_folder() -> Path:
    """
    Gets the path to the user's documents folder.

    Returns:
        Path: Path to user's documents folder
    """

    _buf: ctypes.Array[ctypes.c_wchar] = ctypes.create_unicode_buffer(
        ctypes.wintypes.MAX_PATH
    )
    ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, _buf)
    doc_path: Path = Path(_buf.value)

    return doc_path


def get_common_files(
    files1: list[str], files2: list[str], ignore_case: bool = True
) -> list[str]:
    """
    Gets common files between two lists.

    Args:
        files1 (list[str]): First list of files
        files2 (list[str]): Second list of files
        ignore_case (bool, optional): Toggles whether to ignore case. Defaults to True.

    Returns:
        list[str]: List of common files
    """

    return [
        file
        for file in files1
        if file in files2
        or (file.lower() in [f.lower() for f in files2] and ignore_case)
    ]


def clean_fs_string(text: str) -> str:
    """
    Cleans a string from illegal path characters like '%', ':' or '/'.
    Also removes leading and trailing whitespace and trailing '.'.

    Args:
        text (str): the string to be cleaned.

    Returns:
        str: A cleaned-up string.
    """

    illegal_chars: str = """;<>\\/{}[]+=|*?&,:'"`"""
    output: str = "".join([c for c in text if c not in illegal_chars])
    output = output.strip().rstrip(".")

    return output
