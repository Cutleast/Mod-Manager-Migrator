"""
Copyright (c) Cutleast
"""

from pathlib import Path

from core.game.game import Game

from ..base_test import BaseTest


class TestGame(BaseTest):
    """
    Tests for `core.game.game.Game`.
    """

    def test_get_games_with_cache(self, qt_resources: None) -> None:
        """
        Tests the cached `core.game.game.Game.get_supported_games()` method.
        """

        # when
        games1: list[Game] = Game.get_supported_games()
        games2: list[Game] = Game.get_supported_games()

        # then
        assert games1 == games2
        assert games1 is games2
        assert all(games1[i] is games2[i] for i in range(len(games1)))

    def test_get_game_by_id_with_cache(self, qt_resources: None) -> None:
        """
        Tests the cached `core.game.game.Game.get_game_by_id()` method.
        """

        # when
        skyrimse: Game = Game.get_game_by_id("skyrimse")

        # then
        skyrimse.installdir = Path()
        cached_skyrimse: Game = Game.get_game_by_id("skyrimse")

        assert skyrimse is cached_skyrimse
        assert skyrimse.installdir == cached_skyrimse.installdir
