"""
Part of MMM. Contains utility classes and functions.

Falls under license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

# Import libraries ###################################################
import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union

import plyvel as leveldb
import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw
import requests

from main import MainApp


# Create class to copy stdout to log file ############################
class StdoutPipe:
    """
    Class that copies sys.stdout and
    sys.stderr to file and/or console.

    Internal use only!
    """

    def __init__(self, app: MainApp, tag="stdout", encoding="utf8"):
        self.app = app
        self.tag = tag
        self.encoding = encoding
        self.file = open(self.app.log_path, "a", encoding=encoding)
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self

    def close(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        self.file.close()

    def write(self, string):
        """
        Writes <string> to file and console.
        """

        if string not in self.app.protocol:
            self.app.protocol += string
            try:
                self.file.write(string)
            except Exception as ex:
                print(f"Logging error occured: {str(ex)}")
        try:
            self.stdout.write(string)
        except AttributeError:
            pass

    def flush(self):
        """
        Flush.
        """

        self.file.flush()


# Create class for custom exceptions #################################
class UiException(Exception):
    """
    Subclass of Exception used for translated error messages.

    Usage:
        raise UiException("[<error id>] <raw error message>")
    """


class LevelDBError(Exception):
    """
    General exceptions for level db.
    """


class DBAlreadyInUse(LevelDBError):
    """
    Exception when database is already used
    (when Vortex is running).
    """


# Create class for mod ###############################################
class Mod:
    """
    Class for mods.
    Contains mod data like name, path, metadata, files and size.
    """

    def __init__(
        self,
        name: str,
        path: Path,
        metadata: Dict[str, Any],
        files: List[Path],
        size: int,
        enabled: bool,
        installed: bool,
    ):
        self.name = name  # full mod name
        self.path = path  # path of source mod folder
        self.metadata = metadata  # metadata
        self.files = files  # list of all files
        self.size = size  # size of all files
        self.enabled = enabled  # state in mod manager (True or False)
        self.selected = True  # True: mod is migrated; False: mod is ignored
        self.installed = installed  # state in instance (True or False)
        self.overwriting_mods: List[Mod] = []  # list of overwriting mods
        self.overwriting_files: List[Path] = []  # list of overwriting files (Vortex)
        self.overwritten_files: List[Path] = []  # list of overwritten files (MO2)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def set_selected(self, selected: bool):
        self.selected = selected


# Create class for listbox mod item ##################################
class ModItem(qtw.QListWidgetItem):
    def __init__(self, mod: Mod, mode: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mod = mod
        self.mode = mode
        self.checked = False

    def setCheckState(self, state: qtc.Qt.CheckState):
        super().setCheckState(state)

        self.checked = state == qtc.Qt.CheckState.Checked

    def onClick(self):
        if self.checked:
            self.setCheckState(qtc.Qt.CheckState.Unchecked)
        else:
            self.setCheckState(qtc.Qt.CheckState.Checked)

        if self.mode == "src":
            self.mod.set_selected(self.checked)
        else:
            self.mod.set_enabled(self.checked)

        return self.checked


# Create class for Vortex Level Database bindings ####################
class VortexDatabase:
    """
    Class for Vortex level database. Use only one instance at a time!
    """

    def __init__(self, app: MainApp):
        self.app = app
        self.data = {}
        appdir = Path(os.getenv("APPDATA")) / "Vortex"
        self.db_path = appdir / "state.v2"

        # Set whitelist to just load relevant db keys
        self.whitelist = [
            "persistent###profiles",
            "persistent###mods",
            "settings###mods###installPath",
            "settings###downloads###path",
        ]

        # Initialize class specific logger
        self.log = logging.getLogger(self.__repr__())
        self.log.addHandler(self.app.log_str)
        self.log.setLevel(self.app.log.level)

        # Initialize database
        try:
            self.db = leveldb.DB(str(self.db_path))
        except leveldb.IOError:
            raise DBAlreadyInUse

    def __repr__(self):
        return "LevelDB"

    def open_db(self):
        """
        Opens database if it is closed.

        Internal use only! Use load_db instead!
        """

        if self.db.closed:
            del self.db
            self.db = leveldb.DB(str(self.db_path))

    def close_db(self):
        """
        Closes database if it is opened.

        Internal use only! Use save_db instead!
        """

        if not self.db.closed:
            self.db.close()

    def load_db(self):
        """
        Loads database, converts it to dict and returns it
        """

        self.log.debug("Loading Vortex database...")

        self.open_db()
        data: dict[str, str] = {}
        for keys, value in self.db:
            keys, value = keys.decode(), value.decode()
            if any([keys.startswith(match) for match in self.whitelist]):
                data[keys] = value
        self.close_db()

        data = self.parse_flat_dict(data)
        self.data = data

        self.log.debug("Loaded Vortex database.")
        return data

    def save_db(self):
        """
        Converts dict to strings and saves them to database.
        """

        self.log.debug("Saving Vortex database...")

        # Delete old backup
        backup_path = f"{self.db_path}.mmm_backup"
        if os.path.isdir(backup_path):
            shutil.rmtree(backup_path)
        # Create new backup
        shutil.copytree(self.db_path, f"{self.db_path}.mmm_backup")
        self.log.debug("Created database backup.")

        data = self.flatten_nested_dict(self.data)

        self.open_db()
        with self.db.write_batch() as batch:
            for key, value in data.items():
                batch.put(key.encode(), value.encode())
        self.close_db()

        self.log.debug("Saved to database.")

    @staticmethod
    def flatten_nested_dict(nested_dict: dict) -> Dict[str, str]:
        """
        This function takes a nested dictionary
        and converts it back to a flat dictionary in the format of
        {'key1###subkey1###subsubkey1###subsubsubkey1': 'subsubsubvalue1'}.

        Parameters:
                nested_dict: dict (nested dictionary)
        Returns:
                dict (dictionary in the format above.)
        """

        flat_dict: Dict[str, str] = {}

        def flatten_dict_helper(dictionary, prefix=""):
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    flatten_dict_helper(value, prefix + key + "###")
                else:
                    flat_dict[prefix + key] = json.dumps(value, separators=(",", ":"))

        flatten_dict_helper(nested_dict)

        return flat_dict

    @staticmethod
    def parse_flat_dict(data: Dict[str, str]):
        """
        This function takes a dict in the
        format of
        {'key1###subkey1###subsubkey1###subsubsubkey1': 'subsubsubvalue1'}
        and converts it into a nested dictionary.

        Parameters:
            data: dict of format above

        Returns:
            result: dict (nested dictionary)
        """

        result: dict = {}

        for keys, value in data.items():
            try:
                keys = keys.strip().split("###")

                # Add keys and value to result
                current = result
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current: Dict[str, dict] = current[key]
                value = json.loads(value)
                current[keys[-1]] = value
            except ValueError:
                print(f"Failed to process key: {keys:20}...")
                continue

        return result


# Create class to parse and save ini files ###########################
class IniParser:
    """
    Parser for ini files. Supports loading, changing and saving.
    """

    def __init__(self, filename: Union[str, Path]):
        self.filename = filename
        self.data = {}

    def __repr__(self):
        return "IniParser"

    def save_file(self):
        """
        Saves data to file.
        """

        lines = []
        for section, data in self.data.items():
            lines.append(f"[{section}]\n")
            for key, value in data.items():
                if value is None:
                    value = ""
                lines.append(f"{key}={value}\n")

        dir = f"\\\\?\\{self.filename.parent}"
        filename = f"\\\\?\\{self.filename}"
        os.makedirs(dir, exist_ok=True)
        with open(filename, "w", encoding="utf8") as file:
            file.writelines(lines)

    def load_file(self):
        """
        Loads and parses data from file. Returns it as nested dict.
        """

        with open(self.filename, "r", encoding="utf8") as file:
            lines = file.readlines()

        data = {}
        cur_section = data
        for line in lines:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                cur_section = data[section] = {}
            elif line.endswith("="):
                continue
            elif "=" in line:
                key, value = line.split("=", 1)
                cur_section[key] = value.strip("\n")

        self.data = data
        return self.data


# Define function to get latest version from version file in repo ####
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


# Read blacklist
blacklist = []
with open(".\\data\\blacklist", "r", encoding="utf8") as file:
    for line in file.readlines():
        line = line.strip()
        if line:
            blacklist.append(line)
print(f"{blacklist = }")


# Read folder and save files with relative paths to list #############
def create_folder_list(folder: Path, lower=True):
    """
    Creates a list with all files
    with relative paths to <folder> and returns it.

    Lowers filenames if <lower> is True.
    """

    files: List[Path] = []

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


# Define function to scale value to format ###########################
def scale_value(value: Union[int, float], suffix="B"):
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


# Define function to calculate folder size ###########################
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


# Define function to move windows to center of parent ################
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


# Define function to get difference between two time strings #########
def get_diff(start_time: str, end_time: str, str_format: str = "%H:%M:%S"):
    """
    Returns difference between <start_time> and <end_time> in <str_format>.
    """

    tdelta = str(
        datetime.strptime(end_time, str_format)
        - datetime.strptime(start_time, str_format)
    )
    return tdelta


# Define function to wrap string #####################################
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


# Define function to clean string from illegal path chars ############
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


# Define function to clean file paths from illegal chars #############
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
