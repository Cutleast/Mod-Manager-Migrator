"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw

from .mod import Mod


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
