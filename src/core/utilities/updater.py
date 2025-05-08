"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional

import jstyleson as json
import requests
import semantic_version as semver
from PySide6.QtCore import QObject

from ui.widgets.updater_dialog import UpdaterDialog


class Updater(QObject):
    """
    Class for updating application.
    """

    log: logging.Logger = logging.getLogger("Updater")

    REPO_NAME: str = "Mod-Manager-Migrator"
    REPO_BRANCH: str = "main"
    REPO_OWNER: str = "Cutleast"
    CHANGELOG_URL: str = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{REPO_BRANCH}/Changelog.md"
    UPDATE_URL: str = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{REPO_BRANCH}/update.json"

    installed_version: semver.Version
    latest_version: Optional[semver.Version] = None
    download_url: str

    def __init__(self, installed_version: str) -> None:
        super().__init__()

        self.installed_version = semver.Version(installed_version)

    def run(self) -> None:
        """
        Checks for updates and runs dialog.
        """

        self.log.info("Checking for update...")

        if self.update_available():
            self.log.info(
                f"Update available: Installed: {self.installed_version} - Latest: {self.latest_version}"
            )

            UpdaterDialog(
                self.installed_version,
                self.latest_version,  # type: ignore
                self.get_changelog(),
                self.download_url,
            )
        else:
            self.log.info("No update available.")

    def update_available(self) -> bool:
        """
        Checks if update is available and returns True or False.

        Returns False if requested version is invalid.
        """

        self.request_update()

        if self.latest_version is None:
            return False

        update_available: bool = self.installed_version < self.latest_version
        return update_available

    def request_update(self) -> None:
        """
        Requests latest available version and download url
        from GitHub repository.
        """

        try:
            response = requests.get(Updater.UPDATE_URL, timeout=1)

            if response.status_code == 200:
                latest_version_json = response.content.decode(
                    encoding="utf8", errors="ignore"
                )
                latest_version_data = json.loads(latest_version_json)
                latest_version = latest_version_data["version"]
                self.latest_version = semver.Version(latest_version)
                self.download_url = latest_version_data["download_url"]

            else:
                self.log.error(
                    f"Failed to request update. Status Code: {response.status_code}"
                )
                self.log.debug(f"Request URL: {Updater.UPDATE_URL}")

        except requests.exceptions.RequestException as ex:
            self.log.error(f"Failed to request update: {ex}")
            self.log.debug(f"Request URL: {Updater.UPDATE_URL}")

    def get_changelog(self) -> str:
        """
        Gets changelog from repository.

        Returns it as string with markdown.
        """

        try:
            response = requests.get(Updater.CHANGELOG_URL, timeout=3)

            if response.status_code == 200:
                changelog: str = response.content.decode(
                    encoding="utf8", errors="ignore"
                )

                return changelog
            else:
                self.log.error(
                    f"Failed to request changelog. Status Code: {response.status_code}"
                )
                self.log.debug(f"Request URL: {Updater.CHANGELOG_URL}")

                return f"Status Code: {response.status_code}"
        except requests.exceptions.RequestException as ex:
            self.log.error(f"Failed to request changelog: {ex}")
            self.log.debug(f"Request URL: {Updater.CHANGELOG_URL}")

            return str(ex)
