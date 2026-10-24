import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import discord

import access_control
from button_sub import CreateButton
from modal_sub import CRUDModal, ConfirmUpdateButton
from select_sub import SelectCustom, ConfirmDeleteButton
from word_reporting import report_word, report_words


class PolicyFixture:
    def setUp(self):
        super().setUp()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.policy_path = Path(self.directory.name) / "policy.json"
        self.write_policy()
        patcher = patch.object(access_control, "POLICY_PATH", self.policy_path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_policy(self, guilds=(), users=()):
        self.policy_path.write_text(json.dumps({
            "blocked_guild_ids": list(guilds), "blocked_user_ids": list(users),
        }), encoding="utf-8")


class PolicyTests(PolicyFixture, unittest.TestCase):
    def test_add_remove_preserves_other_entries_and_is_idempotent(self):
        self.write_policy(guilds=["11"], users=["44"])
        access_control.update_policy("block", "user", "55")
        access_control.update_policy("block", "user", "55")
        policy = access_control.load_policy()
        self.assertEqual({11}, policy["blocked_guild_ids"])
        self.assertEqual({44, 55}, policy["blocked_user_ids"])
        access_control.update_policy("unblock", "user", "55")
        access_control.update_policy("unblock", "user", "55")
        self.assertEqual({44}, access_control.load_policy()["blocked_user_ids"])
        self.assertEqual([], list(self.policy_path.parent.glob(".access-policy-*")))

    def test_reloads_changes_without_restart(self):
        self.assertIsNone(access_control.denial_reason(11, 44))
        access_control.update_policy("block", "user", 44)
        self.assertEqual("user", access_control.denial_reason(11, 44))
        access_control.update_policy("unblock", "user", 44)
        self.assertIsNone(access_control.denial_reason(11, 44))

    def test_invalid_or_missing_policy_denies_instead_of_clearing_restrictions(self):
        for content in ("invalid", "[]", '{}', '{"blocked_guild_ids":{},"blocked_user_ids":[]}'):
            self.policy_path.write_text(content, encoding="utf-8")
            with self.assertLogs("access_control", level="ERROR"):
                self.assertEqual("configuration", access_control.denial_reason(11, 44))
        self.policy_path.unlink()
        with self.assertLogs("access_control", level="ERROR"):
            self.assertEqual("configuration", access_control.denial_reason(11, 44))

    def test_invalid_ids_are_rejected_without_overwriting_policy(self):
        original = self.policy_path.read_bytes()
        for identifier in (None, True, "", "-1", "0", "１", "1.0", "x", str(1 << 64)):
            with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                access_control.update_policy("block", "guild", identifier)
        self.assertEqual(original, self.policy_path.read_bytes())


class AccessTests(PolicyFixture, unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "access_test_bot", Path(__file__).resolve().parents[1] / "RandomWordBot.py",
        )
        cls.bot = importlib.util.module_from_spec(spec)
        with patch("discord.Client.run"):
            spec.loader.exec_module(cls.bot)

    def interaction(self):
        interaction = MagicMock()
        interaction.guild_id = 11
        interaction.user.id = 44
        interaction.type = discord.InteractionType.component
        interaction.response.is_done.return_value = False
        interaction.response.send_message = AsyncMock()
        interaction.response.autocomplete = AsyncMock()
        interaction.followup.send = AsyncMock()
        return interaction

    async def test_normal_interaction_is_allowed(self):
        interaction = self.interaction()
        self.assertTrue(await access_control.allow_interaction(interaction))
        interaction.response.send_message.assert_not_called()

    async def test_user_is_blocked_across_guilds_and_after_response(self):
        self.write_policy(users=["44"])
        interaction = self.interaction()
        for guild_id in (11, 22, None):
            interaction.guild_id = guild_id
            self.assertFalse(await access_control.allow_interaction(interaction))
        self.assertTrue(interaction.response.send_message.call_args.kwargs["ephemeral"])
        interaction.response.is_done.return_value = True
        self.assertFalse(await access_control.allow_interaction(interaction))
        self.assertTrue(interaction.followup.send.call_args.kwargs["ephemeral"])

    async def test_tree_blocks_command_and_autocomplete(self):
        self.write_policy(guilds=["11"])
        interaction = self.interaction()
        self.assertFalse(await self.bot.tree.interaction_check(interaction))
        interaction.type = discord.InteractionType.autocomplete
        self.assertFalse(await self.bot.tree.interaction_check(interaction))
        interaction.response.autocomplete.assert_awaited_once_with([])

    async def test_all_existing_components_reject_before_database_access(self):
        # 既に開かれた画面・更新削除確認からの操作も対象にする。
        callbacks = [
            CreateButton(label="参加", custom_id="join_button").callback,
            CRUDModal().on_submit,
            ConfirmUpdateButton(1, "44", 2, "対象").callback,
            ConfirmDeleteButton(1, "44", 2).callback,
            SelectCustom(placeholder="選択", custom_id="update_select").callback,
        ]
        self.write_policy(users=["44"])
        for callback in callbacks:
            with self.subTest(callback=callback.__qualname__), patch("mysql.connector.connect") as connect:
                interaction = self.interaction()
                await callback(interaction)
                connect.assert_not_called()
                interaction.response.send_message.assert_awaited_once()

    async def test_report_and_candidates_are_blocked(self):
        self.write_policy(users=["44"])
        interaction = self.interaction()
        with patch("word_reporting.WordReportModel") as model:
            self.assertEqual([], await report_words(interaction, "対象"))
            await report_word.callback(interaction, "33")
            model.assert_not_called()

    async def test_blocked_join_leaves_without_registering(self):
        self.write_policy(guilds=["11"])
        guild = SimpleNamespace(id=11, name="NG", leave=AsyncMock())
        with patch.object(self.bot, "BotSetting") as settings:
            await self.bot.on_guild_join(guild)
            settings.assert_not_called()
        guild.leave.assert_awaited_once()

    async def test_sweep_only_leaves_blocked_guilds_and_retries_failure(self):
        self.write_policy(guilds=["11"])
        blocked = SimpleNamespace(id=11, leave=AsyncMock(side_effect=RuntimeError("temporary")))
        allowed = SimpleNamespace(id=22, leave=AsyncMock())
        client = SimpleNamespace(guilds=[blocked, allowed])
        with self.assertLogs("access_control", level="ERROR"):
            await access_control.enforce_blocked_guilds(client)
        blocked.leave.side_effect = None
        await access_control.enforce_blocked_guilds(client)
        self.assertEqual(2, blocked.leave.await_count)
        allowed.leave.assert_not_called()

    async def test_invalid_policy_does_not_leave_unknown_guilds_or_register(self):
        self.policy_path.write_text("invalid", encoding="utf-8")
        guild = SimpleNamespace(id=11, name="通常", leave=AsyncMock())
        with self.assertLogs("access_control", level="ERROR"), patch.object(self.bot, "BotSetting") as settings:
            await self.bot.on_guild_join(guild)
            settings.assert_not_called()
        guild.leave.assert_not_called()

    async def test_startup_sync_does_not_register_blocked_guild_even_if_leave_is_delayed(self):
        from bot_setting import BotSetting
        self.write_policy(guilds=["11"])
        with patch("bot_setting.DbQuery") as query_type:
            query_type.return_value.quryexcute.return_value = []
            BotSetting().SyncInstalledGuilds(SimpleNamespace(guilds=[SimpleNamespace(id=11, name="NG")]))
            self.assertEqual(1, query_type.return_value.quryexcute.call_count)

    async def test_incomplete_blocked_members_do_not_hold_up_word_draw(self):
        self.write_policy(users=["55"])
        interaction = self.interaction()
        interaction.id = 100
        interaction.data = {"custom_id": "get_button"}
        with patch("button_sub.DbQuery") as query_type, patch("button_sub.BotSetting") as settings:
            settings.return_value.GetBotSeq.return_value = 7
            query = query_type.return_value.quryexcute
            query.side_effect = [[(7,)], [(1,)], []]
            await CreateButton(label="取得", custom_id="get_button").callback(interaction)
        calls = [call.args for call in query.call_args_list if "MIN(is_completion)" in call.args[0]]
        self.assertEqual(1, len(calls))
        self.assertIn("user_id NOT IN (%s)", calls[0][0])
        self.assertEqual((7, 55), calls[0][1])
        self.assertEqual("取得する言葉がないよ！", interaction.response.send_message.call_args.args[0])
