"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import sys

from main import MainApp


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
