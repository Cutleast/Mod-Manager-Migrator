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
        overwritten_mod: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons", instance
        )
        overwriting_mod: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons - German", instance
        )

        # then
        assert overwritten_mod.mod_conflicts == [overwriting_mod]

        # when
        loadorder: list[Mod] = instance.loadorder

        # then
        assert loadorder.index(overwritten_mod) < loadorder.index(overwriting_mod)

    def test_get_loadorder_without_order_matters(self, instance: Instance) -> None:
        """
        Tests `core.instance.instance.Instance.get_loadorder` with `order_matters=False`.
        """

        # given
        overwritten_mod: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons", instance
        )
        overwriting_mod: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons - German", instance
        )

        # then
        assert overwritten_mod.mod_conflicts == [overwriting_mod]

        # when
        loadorder: list[Mod] = instance.get_loadorder(False)

        # then
        assert loadorder.index(overwritten_mod) < loadorder.index(overwriting_mod)

    def test_loadorder_unchanged(self, instance: Instance) -> None:
        """
        Tests `core.instance.instance.Instance.loadorder` with `order_matters=True`.
        """

        # given
        instance.order_matters = True
        overwritten_mod: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons", instance
        )
        overwriting_mod: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons - German", instance
        )

        # then
        assert overwritten_mod.mod_conflicts == [overwriting_mod]

        # when
        loadorder: list[Mod] = instance.loadorder

        # then
        assert loadorder.index(overwritten_mod) == instance.mods.index(overwritten_mod)
        assert loadorder.index(overwriting_mod) == instance.mods.index(overwriting_mod)
