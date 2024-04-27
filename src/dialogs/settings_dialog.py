"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import json
import logging

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import games
import main
import utilities as utils


class SettingsDialog(qtw.QDialog):
    """
    Shows settings dialog.
    """

    def __init__(self, parent: qtw.QWidget, app: main.MainApp):
        super().__init__(parent)
        self.app = app

        self.stylesheet = self.app._theme.load_stylesheet()

        # initialize class specific logger
        self.log = logging.getLogger("Settings")

        # create popup window
        self.setModal(True)
        self.setWindowTitle(self.app.lang['settings'])
        self.setObjectName("root")
        self.setMinimumWidth(600)
        self.closeEvent = self.cancel_settings
        layout = qtw.QVBoxLayout(self)
        self.setLayout(layout)

        # create detail frame with grid layout
        detail_frame = qtw.QWidget()
        detail_frame.setObjectName("detailframe")
        detail_layout = qtw.QGridLayout()
        detail_frame.setLayout(detail_layout)
        layout.addWidget(detail_frame, stretch=1)
        self.settings_widgets = []
        for r, (config, value) in enumerate(self.app.config.items()):
            label = qtw.QLabel()
            label.setText(self.app.lang.get(config, config))
            detail_layout.addWidget(label, r, 0)
            if isinstance(value, bool):
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems([self.app.lang["true"], self.app.lang["false"]])
                dropdown.setCurrentText(self.app.lang[str(value).lower()])
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(lambda e: self.on_setting_change())
                dropdown.bool = None
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif isinstance(value, int):
                spinbox = qtw.QSpinBox()
                spinbox.setObjectName(config)
                spinbox.setRange(1, 100)
                spinbox.setValue(value)
                spinbox.valueChanged.connect(lambda e: self.on_setting_change())
                self.settings_widgets.append(spinbox)
                detail_layout.addWidget(spinbox, r, 1)
            elif config == "ui_mode":
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems(
                    [self.app.lang["dark"], self.app.lang["light"], "System"]
                )
                dropdown.setCurrentText(self.app.lang.get(value.lower(), value))
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(lambda e: self.on_setting_change())
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif config == "language":
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItem("System")
                loc_path = self.app.res_path / "locales"
                for lang in loc_path.glob("??-??.json"):
                    lang = lang.stem
                    dropdown.addItem(lang)
                dropdown.setCurrentText(self.app.config["language"])
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(lambda e: self.on_setting_change())
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif config == "log_level":
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems(
                    [loglevel.capitalize() for loglevel in utils.LOG_LEVELS.values()]
                )
                dropdown.setCurrentText(value.capitalize())
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(lambda e: self.on_setting_change())
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)
            elif config == "accent_color":
                button = qtw.QPushButton()
                button.setObjectName(config)
                button.color = self.app.config["accent_color"]

                def choose_color():
                    colordialog = qtw.QColorDialog(self)
                    colordialog.setOption(
                        colordialog.ColorDialogOption.DontUseNativeDialog, on=True
                    )
                    colordialog.setCustomColor(0, qtg.QColor("#d78f46"))
                    color = button.color
                    if qtg.QColor.isValidColor(color):
                        colordialog.setCurrentColor(qtg.QColor(color))
                    if colordialog.exec():
                        button.color = colordialog.currentColor().name(
                            qtg.QColor.NameFormat.HexRgb
                        )
                        button.setIcon(
                            qta.icon("mdi6.square-rounded", color=button.color)
                        )
                        self.on_setting_change()

                button.setText(self.app.lang["select_color"])
                button.setIcon(qta.icon("mdi6.square-rounded", color=button.color))
                button.setIconSize(qtc.QSize(24, 24))
                button.clicked.connect(choose_color)
                self.settings_widgets.append(button)
                detail_layout.addWidget(button, r, 1)
            elif config == "default_game":
                dropdown = qtw.QComboBox()
                dropdown.setObjectName(config)
                dropdown.addItems([game(self.app).name for game in games.GAMES])
                dropdown.addItem(self.app.lang["ask_always"])
                if value is not None:
                    dropdown.setCurrentText(value)
                else:
                    dropdown.setCurrentText(self.app.lang["ask_always"])
                dropdown.setEditable(False)
                dropdown.currentTextChanged.connect(lambda e: self.on_setting_change())
                self.settings_widgets.append(dropdown)
                detail_layout.addWidget(dropdown, r, 1)

        # create frame with cancel and done button
        command_frame = qtw.QWidget()
        command_layout = qtw.QHBoxLayout(command_frame)
        command_frame.setLayout(command_layout)
        layout.addWidget(command_frame)
        # cancel
        cancel_button = qtw.QPushButton(self.app.lang["cancel"])
        cancel_button.clicked.connect(self.cancel_settings)
        command_layout.addWidget(cancel_button)
        # done
        self.settings_done_button = qtw.QPushButton(self.app.lang["done"])
        self.settings_done_button.clicked.connect(self.finish_settings)
        self.settings_done_button.setDisabled(True)
        command_layout.addWidget(self.settings_done_button)

        self.setFixedHeight(self.sizeHint().height())

        # update changes variable
        self.unsaved_settings = False

        # show popup
        self.exec()

    def finish_settings(self):
        """
        Gets user input and saves config to file.
        """

        # Get config
        config = self.app.config.copy()
        for widget in self.settings_widgets:
            name = widget.objectName()
            if isinstance(widget, qtw.QComboBox):
                if hasattr(widget, "bool"):
                    config[name] = widget.currentText() == self.app.lang["true"]
                elif name == "ui_mode":
                    config[name] = (
                        "System"
                        if widget.currentText() == "System"
                        else (
                            "Dark"
                            if widget.currentText() == self.app.lang["dark"]
                            else "Light"
                        )
                    )
                elif name == "language":
                    config[name] = widget.currentText()
                elif name == "log_level":
                    config[name] = widget.currentText().lower()
                elif name == "default_game":
                    value = widget.currentText()
                    if value == self.app.lang["ask_always"]:
                        value = None
                    config[name] = value
            elif isinstance(widget, qtw.QSpinBox):
                config[name] = widget.value()
            elif isinstance(widget, qtw.QPushButton):
                config[name] = widget.color

        # Save config
        if config["ui_mode"] != self.app.config["ui_mode"]:
            self.app._theme.set_mode(config["ui_mode"].lower())
            self.app.theme = self.app._theme.load_theme()
            self.app.stylesheet = self.app._theme.load_stylesheet()
            self.app.root.setStyleSheet(self.app.stylesheet)
            self.app.file_menu.setStyleSheet(self.app.stylesheet)
            self.app.help_menu.setStyleSheet(self.app.stylesheet)
            self.app.theme_change_sign.emit()
        self.app.config = config
        with open(self.app.con_path, "w", encoding="utf8") as file:
            json.dump(self.app.config, file, indent=4)
        self.app.unsaved_settings = False
        self.log.info("Saved config to file.")

        # Update accent color
        self.app.theme["accent_color"] = self.app.config["accent_color"]
        self.stylesheet = self.app._theme.load_stylesheet()
        self.app.root.setStyleSheet(self.app.stylesheet)

        # Update icons
        self.app.mig_button.setIcon(
            qta.icon("fa5s.chevron-right", color=self.app.theme["text_color"])
        )
        if self.app.source and self.app.destination:
            self.app.mig_icon.setPixmap(
                qta.icon(
                    "fa5s.chevron-right", color=self.app.theme["accent_color"]
                ).pixmap(120, 120)
            )
        else:
            self.app.mig_icon.setPixmap(
                qta.icon(
                    "fa5s.chevron-right", color=self.app.theme["text_color"]
                ).pixmap(120, 120)
            )

        # Fix link color
        palette = self.app.palette()
        palette.setColor(
            palette.ColorRole.Link, qtg.QColor(self.app.config["accent_color"])
        )
        self.app.setPalette(palette)

        # Close settings popup
        self.accept()

    def on_setting_change(self):
        """
        Callback for user actions. Triggers unsaved state.
        """

        if (not self.unsaved_settings) and (self is not None):
            self.unsaved_settings = True
            self.settings_done_button.setDisabled(False)
            self.setWindowTitle(f"{self.windowTitle()}*")

    def cancel_settings(self, event=None):
        """
        Closes dialog without saving.
        Asks user to continue if state is unsaved.
        """

        if self.unsaved_settings:
            message_box = qtw.QMessageBox(self)
            message_box.setWindowIcon(self.app.root.windowIcon())
            message_box.setStyleSheet(self.app.stylesheet)
            message_box.setWindowTitle(self.app.lang["cancel"])
            message_box.setText(self.app.lang["unsaved_cancel"])
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.No | qtw.QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.No)
            message_box.button(qtw.QMessageBox.StandardButton.No).setText(
                self.app.lang["no"]
            )
            message_box.button(qtw.QMessageBox.StandardButton.Yes).setText(
                self.app.lang["yes"]
            )
            choice = message_box.exec()

            if choice == qtw.QMessageBox.StandardButton.Yes:
                self.accept()
                del self
            elif event:
                event.ignore()
        else:
            self.accept()
            del self
