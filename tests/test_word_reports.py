import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from Model.WordReportModel import WordReportModel
from word_reporting import (
    destination_ready, operator_destination, register_report_commands, report_word, report_words,
)


class WordReportModelTests(unittest.TestCase):
    def test_candidates_are_channel_scoped_without_owners_and_search_is_parameterized(self):
        query_db = MagicMock()
        model = WordReportModel(query_db)
        model.candidates(11, 22, "' OR 1=1 --")
        sql, parameters = query_db.quryexcute.call_args.args
        self.assertEqual((11, 22, "' OR 1=1 --"), parameters)
        self.assertNotIn("' OR", sql)
        self.assertIn("b.guild_id = %s AND b.channel_id = %s", sql)
        self.assertIn("w.delete_flg = FALSE", sql)
        self.assertNotIn("enable_flg", sql)
        self.assertIn("LIMIT 25", sql)
        self.assertNotIn("create_user", sql)

    def test_submit_snapshots_atomically_and_reuses_duplicate(self):
        query_db = MagicMock()
        query_db.quryexcute.side_effect = [[], [(100, "対象", "理由", None)]]
        result = WordReportModel(query_db).submit(100, 11, 22, 33, 44, "理由")
        self.assertEqual((100, "対象", "理由", None), result)
        insert, lookup = query_db.quryexcute.call_args_list
        sql, parameters = insert.args
        self.assertIn("INSERT INTO word_reports", sql)
        self.assertIn("w.create_user_id", sql)
        self.assertIn("b.guild_id = %s AND b.channel_id = %s AND w.id = %s", sql)
        self.assertIn("ON DUPLICATE KEY UPDATE", sql)
        self.assertEqual((100, 44, "理由", 11, 22, 33), parameters)
        self.assertIn("BINARY r.word_snapshot = BINARY w.word", lookup.args[0])


class WordReportCommandTests(unittest.IsolatedAsyncioTestCase):
    def interaction(self):
        interaction = MagicMock()
        interaction.id = 100
        interaction.guild_id = 11
        interaction.guild.id = 11
        interaction.channel_id = 22
        interaction.user.id = 44
        interaction.permissions.view_channel = True
        interaction.permissions.manage_guild = False
        interaction.response.send_message = AsyncMock()
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()
        interaction.client.get_channel.return_value.send = AsyncMock(return_value=SimpleNamespace(id=500))
        return interaction

    async def test_commands_register_and_report_is_guild_only_with_cooldown(self):
        tree = discord.app_commands.CommandTree(discord.Client(intents=discord.Intents.none()))
        register_report_commands(tree)
        self.assertIs(tree.get_command("report"), report_word)
        self.assertTrue(report_word.guild_only)
        self.assertTrue(report_word.checks)
        self.assertIsNone(tree.get_command("report-channel"))

    async def test_report_notifies_without_owner_or_mentions_and_receipt_is_private(self):
        interaction = self.interaction()
        with patch("word_reporting.WordReportModel") as model_type, patch("word_reporting.operator_destination", new=AsyncMock(return_value=interaction.client.get_channel.return_value)):
            model = model_type.return_value
            model.submit.return_value = (100, "@everyone **対象**", "<@123> 理由", None)
            await report_word.callback(interaction, "33", "理由")
            model.submit.assert_called_once_with(100, 11, 22, 33, 44, "理由")
            model.mark_notified.assert_called_once_with(100, 500)
        notification = interaction.client.get_channel.return_value.send.call_args.kwargs
        interaction.guild.get_channel.assert_not_called()
        self.assertFalse(notification["allowed_mentions"].everyone)
        self.assertFalse(notification["allowed_mentions"].users)
        fields = notification["embed"].to_dict()["fields"]
        self.assertFalse(any("登録者" in field["name"] for field in fields))
        self.assertTrue(interaction.response.defer.call_args.kwargs["ephemeral"])
        self.assertTrue(interaction.followup.send.call_args.kwargs["ephemeral"])

    async def test_cross_channel_or_removed_word_is_rejected_without_notification(self):
        interaction = self.interaction()
        with patch("word_reporting.WordReportModel") as model_type, patch("word_reporting.operator_destination", new=AsyncMock(return_value=interaction.client.get_channel.return_value)):
            model_type.return_value.submit.return_value = None
            await report_word.callback(interaction, "33")
        interaction.client.get_channel.return_value.send.assert_not_called()
        self.assertIn("見つかりません", interaction.followup.send.call_args.args[0])

    async def test_duplicate_notification_is_not_sent(self):
        interaction = self.interaction()
        with patch("word_reporting.WordReportModel") as model_type, patch("word_reporting.operator_destination", new=AsyncMock(return_value=interaction.client.get_channel.return_value)):
            model_type.return_value.submit.return_value = (99, "対象", "元の理由", 500)
            await report_word.callback(interaction, "33", "別の理由")
        interaction.client.get_channel.return_value.send.assert_not_called()
        self.assertIn("通報済み", interaction.followup.send.call_args.args[0])

    async def test_notification_failure_preserves_record_for_retry(self):
        interaction = self.interaction()
        interaction.client.get_channel.return_value.send.side_effect = RuntimeError("通知失敗")
        with patch("word_reporting.WordReportModel") as model_type, patch("word_reporting.operator_destination", new=AsyncMock(return_value=interaction.client.get_channel.return_value)):
            model = model_type.return_value
            model.submit.return_value = (99, "対象", "理由", None)
            with self.assertLogs("word_reporting", level="ERROR"):
                await report_word.callback(interaction, "33")
            model.mark_notified.assert_not_called()
        self.assertIn("保存しました", interaction.followup.send.call_args.args[0])

    async def test_unconfigured_destination_does_not_accept_report(self):
        interaction = self.interaction()
        with patch("word_reporting.WordReportModel") as model_type, patch("word_reporting.operator_destination", new=AsyncMock(return_value=None)):
            await report_word.callback(interaction, "33")
            model_type.return_value.submit.assert_not_called()
        self.assertIn("利用できません", interaction.followup.send.call_args.args[0])

    async def test_invalid_inputs_do_not_access_database(self):
        for word, reason in [("対象", ""), ("-1", ""), ("０１", ""), ("0", ""),
                             ("2147483648", ""), ("33", "a" * 501)]:
            with self.subTest(word=word, reason_length=len(reason)):
                interaction = self.interaction()
                with patch("word_reporting.WordReportModel") as model_type:
                    await report_word.callback(interaction, word, reason)
                    model_type.assert_not_called()
                self.assertTrue(interaction.response.send_message.call_args.kwargs["ephemeral"])

    async def test_dm_has_no_candidates_and_cannot_submit(self):
        interaction = self.interaction()
        interaction.guild = None
        with patch("word_reporting.WordReportModel") as model_type:
            self.assertEqual([], await report_words(interaction, "対象"))
            await report_word.callback(interaction, "33")
            model_type.assert_not_called()

    async def test_candidates_only_show_record_number_and_word(self):
        interaction = self.interaction()
        with patch("word_reporting.WordReportModel") as model_type:
            model_type.return_value.candidates.return_value = [(33, "あ" * 100)]
            choices = await report_words(interaction, "あ")
        self.assertEqual("33", choices[0].value)
        self.assertLessEqual(len(choices[0].name), 100)

    async def test_database_failure_does_not_claim_saved(self):
        interaction = self.interaction()
        with patch("word_reporting.WordReportModel") as model_type, patch("word_reporting.operator_destination", new=AsyncMock(return_value=interaction.client.get_channel.return_value)):
            model_type.return_value.submit.side_effect = RuntimeError("失敗")
            with self.assertLogs("word_reporting", level="ERROR"):
                await report_word.callback(interaction, "33")
        interaction.client.get_channel.return_value.send.assert_not_called()
        self.assertNotIn("保存しました", interaction.followup.send.call_args.args[0])

    async def test_reason_boundary_and_unsent_existing_report_retry(self):
        interaction = self.interaction()
        with patch("word_reporting.WordReportModel") as model_type, patch("word_reporting.operator_destination", new=AsyncMock(return_value=interaction.client.get_channel.return_value)):
            model = model_type.return_value
            model.submit.return_value = (99, "対象", "元の理由", None)
            await report_word.callback(interaction, "33", "あ" * 500)
            model.mark_notified.assert_called_once_with(99, 500)
        fields = interaction.client.get_channel.return_value.send.call_args.kwargs["embed"].fields
        self.assertEqual("元の理由", fields[1].value)

    async def test_destination_must_be_private_same_guild_and_bot_can_send(self):
        interaction = self.interaction()
        channel = MagicMock(spec=discord.TextChannel)
        channel.guild.id = 11
        channel.guild.default_role = interaction.guild.default_role
        channel.guild.me = interaction.guild.me
        channel.permissions_for.return_value = SimpleNamespace(
            view_channel=True, send_messages=True, embed_links=True,
        )
        self.assertFalse(destination_ready(channel, 11))
        channel.permissions_for.side_effect = [SimpleNamespace(view_channel=False),
            SimpleNamespace(view_channel=True, send_messages=True, embed_links=True)]
        self.assertTrue(destination_ready(channel, 11))
        channel.guild.id = 12
        self.assertFalse(destination_ready(channel, 11))

    async def test_operator_destination_uses_only_configured_channel_and_checks_guild(self):
        client = MagicMock()
        with patch("word_reporting.destination_ready", return_value=True) as ready:
            result = await operator_destination(client)
        client.get_channel.assert_called_once_with(1562756569412673616)
        ready.assert_called_once_with(client.get_channel.return_value, 1509544644143480872)
        self.assertIs(result, client.get_channel.return_value)

    async def test_operator_destination_fetches_uncached_channel(self):
        client = MagicMock()
        client.get_channel.return_value = None
        client.fetch_channel = AsyncMock()
        with patch("word_reporting.destination_ready", return_value=True):
            result = await operator_destination(client)
        client.fetch_channel.assert_awaited_once_with(1562756569412673616)
        self.assertIs(result, client.fetch_channel.return_value)

    async def test_wrong_operator_guild_never_falls_back_to_origin(self):
        client = MagicMock()
        with patch("word_reporting.destination_ready", return_value=False):
            self.assertIsNone(await operator_destination(client))
        client.get_channel.return_value.send.assert_not_called()
