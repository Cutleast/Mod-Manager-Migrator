"""
Copyright (c) Cutleast
"""

import logging
import os
import re
import sys
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path
from typing import Callable, Optional, TextIO, override

from .datetime import datetime_format_to_regex


class Logger(logging.Logger):
    """
    Class for application logging. Copies all logging messages from
    `sys.stdout` and `sys.stderr` to a file and executes a callback with the new message.
    """

    __lines: list[str]
    __root_logger: logging.Logger
    __log_handler: logging.StreamHandler

    __stdout: Optional[TextIO] = None
    __stderr: Optional[TextIO] = None

    __log_file_path: Path
    __log_file: TextIOWrapper

    __callback: Callable[[str], None] | None = None

    def __init__(
        self, log_file: Path, fmt: str | None = None, date_fmt: str | None = None
    ) -> None:
        super().__init__("Logger")

        # Create log folder if it doesn't exist
        os.makedirs(log_file.parent, exist_ok=True)

        self.__log_file_path = log_file
        self.__log_file = log_file.open("a", encoding="utf8")

        self.__root_logger = logging.getLogger()
        formatter = logging.Formatter(fmt, date_fmt)
        self.__log_handler = logging.StreamHandler(self)
        self.__log_handler.setFormatter(formatter)
        self.__root_logger.addHandler(self.__log_handler)
        self.addHandler(self.__log_handler)
        self.__lines = []

        self.open()

    def open(self) -> None:
        self.__stdout = sys.stdout
        self.__stderr = sys.stderr

        sys.stdout = self
        sys.stderr = self

    @override
    def setLevel(self, level: int | str) -> None:
        """
        Sets logging level.

        Args:
            level (int | str): New logging level.
        """

        self.__root_logger.setLevel(level)
        self.__log_handler.setLevel(level)

        super().setLevel(level)

    def set_callback(self, callback: Callable[[str], None] | None) -> None:
        """
        Sets callback that is called everytime something is written stdout.

        Args:
            callback (Callable[[str], None] | None):
                A method or function taking a string as argument.
                Existing callback is removed if None.
        """

        self.__callback = callback

    @staticmethod
    def clean_log_folder(folder: Path, basename: str, num_of_files: int) -> None:
        """
        Deletes old log files from log folder matching until there is
        a specified number of files left.

        Args:
            folder (Path): Path to log folder.
            basename (str): Basename of log files.
            num_of_files (int): Number of newest log files to keep.
                Keeps all log files if it is negative.
        """

        if num_of_files < 0:
            return

        log_filename_pattern: str = datetime_format_to_regex(basename)
        log_files: list[Path] = [
            file
            for file in folder.glob("*")
            if file.is_file()
            and re.match(log_filename_pattern, file.name, re.IGNORECASE)
        ]
        log_files.sort(key=lambda name: datetime.strptime(name.name, basename))

        while len(log_files) > num_of_files:
            os.remove(log_files.pop(0))

    def close(self) -> None:
        sys.stdout = self.__stdout
        sys.stderr = self.__stderr
        self.__log_file.close()

    def write(self, string: str) -> None:
        """
        Writes a string to stdout and calls callback with string as argument

        Args:
            string (str): Message.
        """

        try:
            self.__lines.append(string)
            self.__log_file.write(string)
            if self.__stdout is not None:
                self.__stdout.write(string)
        except Exception as ex:
            if self.__stdout is not None:
                self.__stdout.write(f"Logging error occured: {str(ex)}")

        if self.__callback is not None:
            self.__callback(string)

    def flush(self) -> None:
        """
        Flushes file.
        """

        self.__log_file.flush()

    def get_content(self) -> str:
        """
        Returns content of current log as string.

        Returns:
            str: Content of current log.
        """

        return "".join(self.__lines)

    def get_file_path(self) -> Path:
        """
        Returns path to current log file.

        Returns:
            Path: Path to current log file.
        """

        return self.__log_file_path
