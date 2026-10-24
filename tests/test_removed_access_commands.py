import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

import discord


class RemovedAccessCommandTests(unittest.TestCase):
    def test_ng_management_commands_are_not_registered_but_access_checks_remain(self):
        spec = importlib.util.spec_from_file_location(
            "removed_access_commands_test_bot", Path(__file__).resolve().parents[1] / "RandomWordBot.py",
        )
        bot = importlib.util.module_from_spec(spec)
        with patch("discord.Client.run"):
            spec.loader.exec_module(bot)
        self.assertEqual({"start", "help", "report"}, {command.name for command in bot.tree.get_commands()})
        self.assertEqual([], bot.tree.get_commands(guild=discord.Object(id=1509544644143480872)))
        self.assertIsInstance(bot.tree, bot.RestrictedCommandTree)
