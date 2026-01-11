"""
Copyright (c) Cutleast
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

import jstyleson as json
import plyvel as ldb
import pyuac


class LevelDB:
    """
    Class for accessing Vortex' LevelDB database.

    Consumers are encouraged to use these in-memory methods:
    - `get_section()`
    - `set_section()`
    - `get_key()`
    - `set_key()`

    and then save their changes with `save()`.
    """

    __path: Path
    __use_symlink: bool
    __symlink_path: Optional[Path]

    __data: dict[str, str]
    __changes_pending: bool

    log: logging.Logger = logging.getLogger("LevelDB")

    def __init__(self, path: Path, use_symlink: bool = True) -> None:
        """
        Args:
            path (Path): Path to Vortex' state.v2 folder.
            use_symlink (bool, optional): Whether to use symlinks. Defaults to True.
        """

        self.__path = path
        self.__use_symlink = use_symlink

        self.__symlink_path = None
        self.__data = {}
        self.__changes_pending = False

    def get_symlink_path(self) -> Path:
        """
        Creates a symlink to Vortex's database to avoid a database path with
        non-ASCII characters which are not supported by plyvel.

        Asks for admin rights to create the symlink if it is required.

        Raises:
            RuntimeError: when the user did not grant admin rights.

        Returns:
            Path: Path to symlink or path to database if symlink is not used.
        """

        if not self.__use_symlink:
            return self.__path

        if self.__symlink_path is None:
            self.log.debug("Creating symlink to database...")

            symlink_path = Path("C:\\Users\\Public\\vortex_db")

            if symlink_path.is_symlink():
                symlink_path.unlink()
                self.log.debug("Removed already existing symlink.")

            try:
                os.symlink(self.__path, symlink_path, target_is_directory=True)
            except OSError as ex:
                self.log.error(f"Failed to create symlink: {ex}")

                if (
                    pyuac.runAsAdmin(
                        [
                            "cmd",
                            "/c",
                            "mklink",
                            "/D",
                            str(symlink_path),
                            str(self.__path),
                        ]
                    )
                    != 0
                ):
                    raise RuntimeError("Failed to create symlink.")

            self.__symlink_path = symlink_path

            self.log.debug(f"Created symlink from '{symlink_path}' to '{self.__path}'.")

        return self.__symlink_path

    def del_symlink_path(self) -> None:
        """
        Deletes database symlink if it exists.
        """

        if self.__symlink_path is not None:
            self.log.debug("Deleting symlink...")

            if self.__symlink_path.is_symlink():
                os.unlink(self.__symlink_path)

            self.__symlink_path = None
            self.log.debug("Symlink deleted.")

    def load(self, prefix: Optional[str | bytes] = None) -> dict[str, Any]:
        """
        Loads all database entries matching an optional prefix into memory.
        Unsaved in-memory changes that match the prefix are overwritten by this
        operation.

        Args:
            prefix (Optional[str | bytes], optional):
                The prefix to match. Defaults to None.

        Returns:
            dict[str, Any]: The loaded data.
        """

        db_path: Path = self.get_symlink_path()
        self.log.info(f"Loading database from '{db_path}' with prefix {prefix!r}...")

        raw_data: dict[str, str] = {}

        if isinstance(prefix, str):
            prefix = prefix.encode()

        with ldb.DB(str(db_path)) as database:
            for key, value in database.iterator(prefix=prefix):
                raw_data[key.decode()] = value.decode()

        self.__data.update(raw_data)
        self.log.info("Database loaded.")

        return LevelDB.parse_flat_dict(raw_data)

    def save(self) -> None:
        """
        Writes all pending changes to the database.
        """

        if not self.__changes_pending:
            self.log.info("No changes pending, skipping save.")
            return

        db_path: Path = self.get_symlink_path()
        self.log.info(f"Saving database to '{db_path}'...")

        with ldb.DB(str(db_path)) as database:
            with database.write_batch() as batch:
                for key, value in self.__data.items():
                    batch.put(key.encode(), value.encode())

        self.__changes_pending = False
        self.log.info("Database saved.")

    def get_section(self, prefix: str) -> dict[str, Any]:
        """
        Returns all key-value pairs in the database that start with the given prefix.
        Missing keys are loaded from the database if necessary without overwriting
        pending changes.

        Args:
            prefix (str): The prefix to filter keys.

        Returns:
            dict[str, Any]: The nested dictionary.
        """

        prefix_bytes: bytes = prefix.encode()

        # load missing keys from database
        db_path: Path = self.get_symlink_path()
        with ldb.DB(str(db_path)) as database:
            for raw_key, raw_value in database.iterator(prefix=prefix_bytes):
                key: str = raw_key.decode()
                if key not in self.__data:
                    self.__data[key] = raw_value.decode()
                    self.__changes_pending = True

        # filter loaded data by prefix
        filtered_data: dict[str, str] = {
            k: v for k, v in self.__data.items() if k.startswith(prefix)
        }

        return LevelDB.parse_flat_dict(filtered_data)

    def set_section(self, prefix: str, data: dict[str, Any]) -> None:
        """
        Sets the data of a prefixed section. This operation is performed in-memory and an
        explicit call to `save()` is required to persist the changes to the database.

        Args:
            prefix (str): The prefix of the section.
            data (dict[str, Any]): The data to set.
        """

        raw_data: dict[str, str] = LevelDB.flatten_nested_dict(data, prefix=prefix)
        self.__data.update(raw_data)
        self.__changes_pending = True

    def get_key(self, key: str) -> Optional[Any]:
        """
        Returns the deserialized value of a specified key. If the key is not in the
        loaded in-memory data, it is attempted to load it from the database.

        Args:
            key (str): The key to get.

        Returns:
            Optional[Any]: The value of the key or None if the key does not exist.
        """

        if key not in self.__data:
            self.load(prefix=key)

        if key in self.__data:
            return json.loads(self.__data.get(key))

    def set_key(self, key: str, value: Any) -> None:
        """
        Sets the value of a specified key in the in-memory data.

        Args:
            key (str): The key to set.
            value (Any): The value to set.
        """

        self.__data[key] = json.dumps(value)
        self.__changes_pending = True

    @staticmethod
    def flatten_nested_dict(
        nested_dict: dict, prefix: Optional[str] = None
    ) -> dict[str, str]:
        """
        This function takes a nested dictionary
        and converts it back to a flat dictionary in this format:
        ```
        {'key1###subkey1###subsubkey1###subsubsubkey1': 'subsubsubvalue1'}
        ```

        Args:
            nested_dict (dict): The nested dictionary to flatten.
            prefix (str, optional):
                An optional prefix to add to each key. Defaults to None.

        Returns:
            dict[str, str]: The flattened dictionary.
        """

        flat_dict: dict[str, str] = {}

        def flatten_dict_helper(dictionary: dict, _prefix: str = "") -> None:
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    flatten_dict_helper(value, _prefix + key + "###")
                else:
                    flat_dict[(prefix or "") + _prefix + key] = json.dumps(
                        value, separators=(",", ":")
                    )

        flatten_dict_helper(nested_dict)

        return flat_dict

    @staticmethod
    def parse_flat_dict(data: dict[str, str]) -> dict:
        """
        This function takes a dict in the format of
        ```
        {'key1###subkey1###subsubkey1###subsubsubkey1': 'subsubsubvalue1'}
        ```
        and converts it into a nested dictionary.

        Args:
            data (dict[str, str]): The data to parse.

        Returns:
            dict: The parsed dictionary.
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
                    current: dict[str, dict] = current[key]
                value = json.loads(value)
                current[keys[-1]] = value
            except ValueError:
                LevelDB.log.warning(f"Failed to process key: {keys:20}...")
                continue

        return result

    @staticmethod
    def is_db_readable(path: Path) -> bool:
        """
        Checks if the level database at the specified path is readable.

        Args:
            path (Path): The path to the level database.

        Returns:
            bool: True if the database is readable, False otherwise.
        """

        try:
            with ldb.DB(str(path)) as database:
                # Attempt to read and decode the first key
                for k, v in database.iterator():
                    k.decode()
                    v.decode()
                    return True

        # This means the database is readable, but blocked by Vortex
        except ldb.IOError:
            return True

        except Exception:
            pass

        return False
