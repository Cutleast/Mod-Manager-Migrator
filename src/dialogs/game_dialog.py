"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import json
import logging

import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import games
import main
import utilities as utils


class GameDialog(qtw.QDialog):
    """
    Dialog for game selection.
    """

    def __init__(self, parent: qtw.QWidget, app: main.MainApp):
        super().__init__(parent)

        self.app = app
        self.game: str = None
        self.game_instance: games.GameInstance = None

        # Initialize class specific logger
        self.log = logging.getLogger("GameDialog")

        # Configure dialog
        self.setWindowTitle(self.app.lang['select_game'])
        self.setModal(True)
        self.setObjectName("root")
        self.setFixedSize(720, 350)

        # Create main layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # Add label with instruction
        label = qtw.QLabel()
        label.setText(self.app.lang["select_game_text"])
        label.setObjectName("titlelabel")
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(label)

        # Add listbox for games
        self.games_box = qtw.QListWidget()
        self.games_box.setSelectionMode(qtw.QListWidget.SelectionMode.SingleSelection)
        self.games_box.doubleClicked.connect(self.finish)
        self.games_box.setMinimumHeight(200)
        layout.addWidget(self.games_box, 1)

        # Add games to listbox
        for game in games.GAMES:
            game = game(self.app)
            text = game.name
            # if game.name != "Skyrim Special Edition":
            #    text += " (EXPERIMENTAL)"
            if game.icon_name:
                icon = qtg.QIcon(str(self.app.ico_path / game.icon_name))
                item = qtw.QListWidgetItem(icon, text)
            else:
                item = qtw.QListWidgetItem(text=text)

            self.games_box.addItem(item)
        self.games_box.setCurrentRow(0)

        # Add remember checkbox
        self.rem_checkbox = qtw.QCheckBox(self.app.lang["do_not_ask_again"])
        layout.addWidget(self.rem_checkbox, alignment=qtc.Qt.AlignmentFlag.AlignHCenter)

        # Add cancel and done button
        button_layout = qtw.QHBoxLayout()
        layout.addLayout(button_layout)

        # Cancel button
        cancel_button = qtw.QPushButton(self.app.lang["exit"])
        cancel_button.clicked.connect(self.app.exit)
        button_layout.addWidget(cancel_button)

        # Seperate cancel button with spacing
        button_layout.addSpacing(200)

        # Done button
        done_button = qtw.QPushButton(self.app.lang["done"])
        done_button.clicked.connect(self.finish)
        button_layout.addWidget(done_button)

    def closeEvent(self, event):
        super().closeEvent(event)

        if not self.game_instance:
            self.app.exit()

    def finish(self):
        sel_game = self.games_box.currentItem().text()
        if "(EXPERIMENTAL)" in sel_game:
            sel_game = sel_game.replace("(EXPERIMENTAL)", "").strip()
        for game in games.GAMES:
            if game(self.app).name == sel_game:
                self.game_instance = game(self.app)
                break
        else:
            raise utils.UiException(
                f"[game_not_supported] Game '{sel_game}' not supported."
            )

        dir = self.game_instance.get_install_dir()
        if str(dir).strip() and dir.is_dir():
            self.game = self.game_instance.id
            self.app.game_instance = self.game_instance
            self.app.game = self.game

            # Update game icon
            icon = qtg.QPixmap(self.app.ico_path / self.game_instance.icon_name)
            self.app.game_icon.setPixmap(icon)

            self.log.info(f"Current game: {self.game_instance.name}")

            self.accept()

            # Save game to config if rem checkbox is selected
            if self.rem_checkbox.isChecked():
                self.app.config["default_game"] = self.app.game_instance.name
                with open(self.app.con_path, "w", encoding="utf8") as file:
                    json.dump(self.app.config, file, indent=4)
