"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import qtpy.QtWidgets as qtw
import requests

from .exceptions import *
from .ini_parser import IniParser
from .localisation import Localisator
from .mod import Mod
from .mod_item import ModItem
from .stdout_pipe import StdoutPipe
from .theme import Theme
from .vortex_database import VortexDatabase


def get_latest_version():
    """
    Gets latest available program version by
    reading version file in the repository.

    Returns it as float.
    """

    try:
        url = "https://raw.githubusercontent.com/Cutleast/Mod-Manager-Migrator/main/version"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            new_version = response.content.decode(encoding="utf8", errors="ignore")
            new_version = float(new_version.strip())
            return new_version

        raise ValueError(f"Status code: {response.status_code}")
    except ValueError:
        return 0.0


blacklist = []
with open(".\\data\\blacklist", "r", encoding="utf8") as file:
    for line in file.readlines():
        line = line.strip()
        if line:
            blacklist.append(line)
print(f"{blacklist = }")


def create_folder_list(folder: Path, lower=True):
    """
    Creates a list with all files
    with relative paths to <folder> and returns it.

    Lowers filenames if <lower> is True.
    """

    files: list[Path] = []

    for root, _, _files in os.walk(folder):
        for f in _files:
            if f not in blacklist:  # check if in blacklist
                path = os.path.join(root, f)
                path = path.removeprefix(f"{folder}\\")
                if lower:
                    path = path.lower()
                path = Path(path)
                files.append(path)

    return files


def scale_value(value: int | float, suffix="B"):
    """
    Scales <value> to its proper format
    with <suffix> as unit
    and returns it as string; for e.g:

    1253656 => '1.20MB'

    1253656678 => '1.17GB'
    """

    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P", "H"]:
        if value < factor:
            if f"{value:.2f}".split(".")[1] == "00":
                return f"{int(value)}{unit}{suffix}"

            return f"{value:.2f}{unit}{suffix}"

        value /= factor

    return str(value)


def get_folder_size(folder: str):
    """
    Calculates total size of files in <folder>
    and returns it in bytes as integer.
    """

    total_size = 0
    for dirpath, _, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)

            # Skip if it is symbolic link
            if not os.path.islink(fp):
                try:
                    total_size += os.path.getsize(fp)
                # Ignore errors like PermissionError
                # or similar os errors
                except Exception:
                    continue

    return total_size


def center(widget: qtw.QWidget, referent: qtw.QWidget = None):
    """
    Moves <widget> to center of its parent or if given to
    center of <referent>.

    Parameters:
        widget: QWidget (widget to move)
        referent: QWidget (widget reference for center coords;
        uses widget.parent() if None)
    """

    size = widget.size()
    w = size.width()
    h = size.height()

    if referent is None:
        rsize = qtw.QApplication.primaryScreen().size()
    else:
        rsize = referent.size()
    rw = rsize.width()
    rh = rsize.height()

    x = int((rw / 2) - (w / 2))
    y = int((rh / 2) - (h / 2))

    widget.move(x, y)


def get_diff(start_time: str, end_time: str, str_format: str = "%H:%M:%S"):
    """
    Returns difference between <start_time> and <end_time> in <str_format>.
    """

    tdelta = str(
        datetime.strptime(end_time, str_format)
        - datetime.strptime(start_time, str_format)
    )
    return tdelta


def wrap_string(string: str, wrap_length: int):
    """
    Inserts spaces in <string> in <wrap_length> interval.
    """

    if len(string) > wrap_length and " " not in string:
        characters = list(string)
        w = 0
        for i, c in enumerate(string):
            if w == wrap_length:
                characters.insert(i, " ")
                w = 0
            w += 1
        return "".join(characters)
    else:
        return string


def clean_string(source: str):
    """
    Cleans <source> from illegal characters like '%', ':' or '/'.

    Args:
        source (str): the string to be cleaned.

    Returns:
        (str): A cleaned-up string.
    """

    illegal_chars = """;<>\\/{}[]+=|*?&,:'"`"""

    output = "".join([c for c in source if c not in illegal_chars])

    return output


def clean_filepath(filepath: Path):
    """
    Cleans <filepath> from illegal characters like '%', ':' or '/'.

    Args:
        | filepath (Path): the file path to be cleaned.

    Returns:
        | (Path): A cleaned-up file path.
    """

    path_parts = list(filepath.parts)

    for i, part in enumerate(path_parts):
        if i == 0 and Path(part).is_dir():
            continue
        cleaned_part = clean_string(part)

        path_parts[i] = cleaned_part

    cleaned_path = Path(*path_parts)

    return cleaned_path


def comp_dicts(dict1: dict, dict2: dict, use_json: bool = False):
    """
    Compares two dicts and returns the different key-value pairs.

    For example:
        dict1 = original dict

        dict2 = modified version of dict1

        -> returns different key-value pairs from dict2
    """

    if not use_json:
        diff = {key: value for key, value in dict2.items() if dict1.get(key) != value}
    else:
        diff = {}

        for key, value1 in dict1.items():
            value2 = dict2.get(key)

            if value2:
                if json.loads(value1) != json.loads(value2):
                    diff[key] = value2
            else:
                diff[key] = value1

    return diff


# Constant variables #################################################
LOG_LEVELS = {
    10: "debug",  # DEBUG
    20: "info",  # INFO
    30: "warning",  # WARNING
    40: "error",  # ERROR
    50: "critical",  # CRITICAL
}
SUPPORTED_MODMANAGERS = ["Vortex", "ModOrganizer"]
SUPPORTED_GAMES = ["SkyrimSE", "Skyrim", "Fallout4", "EnderalSE", "Enderal"]
