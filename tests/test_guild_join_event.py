import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class GuildJoinEventTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # Discordへ接続せず、実際のエントリーポイントのイベント登録を読み込む。
        spec=importlib.util.spec_from_file_location("guild_event_test_bot",Path(__file__).resolve().parents[1]/"RandomWordBot.py")
        cls.bot=importlib.util.module_from_spec(spec)
        with patch("discord.Client.run"):
            spec.loader.exec_module(cls.bot)

    async def test_registered_event_calls_single_guild_registration(self):
        guild=SimpleNamespace(id=123,name="導入先")
        self.assertIs(self.bot.client.on_guild_join,self.bot.on_guild_join)
        with patch.object(self.bot,"BotSetting") as settings:
            settings.return_value.RegisterInstalledGuild.return_value=True
            await self.bot.on_guild_join(guild)
            settings.return_value.RegisterInstalledGuild.assert_called_once_with(guild)

    async def test_registration_failure_is_logged_without_escaping_event(self):
        guild=SimpleNamespace(id=123,name="導入先")
        with patch.object(self.bot,"BotSetting") as settings:
            settings.return_value.RegisterInstalledGuild.side_effect=RuntimeError("test failure")
            with self.assertLogs(self.bot.logger,level="ERROR") as captured:
                await self.bot.on_guild_join(guild)
            self.assertIn("guild_id=123",captured.output[0])
