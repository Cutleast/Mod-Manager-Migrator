"""
Copyright (c) Cutleast
"""

from core.instance.instance import Instance
from core.instance.mod import Mod

from ..base_test import BaseTest


class TestInstance(BaseTest):
    """
    Tests `core.instance.instance.Instance`.
    """

    def test_loadorder_simple(self, instance: Instance) -> None:
        """
        Tests `core.instance.instance.Instance.loadorder` on a simple conflict between
        two mods.
        """

        # given
        overwritten_mod: Mod = instance.mods[-1]
        overwriting_mod: Mod = instance.mods[0]
        overwritten_mod.mod_conflicts = [overwriting_mod]

        # when
        loadorder: list[Mod] = instance.loadorder

        # then
        assert loadorder.index(overwritten_mod) < loadorder.index(overwriting_mod)

    def test_loadorder_unchanged(self, instance: Instance) -> None:
        """
        Tests `core.instance.instance.Instance.loadorder` with `order_matters=True`.
        """

        # given
        overwritten_mod: Mod = instance.mods[-1]
        overwriting_mod: Mod = instance.mods[0]
        overwritten_mod.mod_conflicts = [overwriting_mod]
        instance.order_matters = True

        # when
        loadorder: list[Mod] = instance.loadorder

        # then
        assert loadorder.index(overwritten_mod) == instance.mods.index(overwritten_mod)
        assert loadorder.index(overwriting_mod) == instance.mods.index(overwriting_mod)
