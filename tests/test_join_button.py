import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import mysql.connector
from button_sub import CreateButton


class JoinButtonTests(unittest.IsolatedAsyncioTestCase):
    def make_interaction(self, custom_id):
        interaction = MagicMock()
        interaction.data = {"custom_id": custom_id}
        interaction.user.id = 123456789012345678
        interaction.user.display_name = "参加者"
        interaction.user.name = "example_user"
        interaction.user.__str__.return_value = "example_user"
        interaction.response.send_message = AsyncMock()
        interaction.response.edit_message = AsyncMock()
        interaction.response.is_done.return_value = False
        interaction.edit_original_response = AsyncMock()
        return interaction

    @patch("button_sub.BotSetting")
    @patch("button_sub.DbQuery")
    async def test_drawing_word_records_acquisition_time(self, query_type, setting_type):
        setting_type.return_value.GetBotSeq.return_value = 7
        query = query_type.return_value.quryexcute
        query.side_effect = [[(7,)], [(1,)], [(10, "取得する言葉")], []]
        interaction = self.make_interaction("get_button")
        await CreateButton(label="取得", custom_id="get_button").callback(interaction)
        self.assertIn("updated_at = CURRENT_TIMESTAMP(6)", query.call_args_list[3].args[0])
        interaction.response.send_message.assert_awaited_once()

    @patch("button_sub.BotSetting")
    @patch("button_sub.DbQuery")
    async def test_latest_word_is_scoped_to_user_and_session(self, query_type, setting_type):
        setting_type.return_value.GetBotSeq.return_value = 7
        query = query_type.return_value.quryexcute
        query.side_effect = [[(7,)], [("最後に取得した言葉",)]]
        interaction = self.make_interaction("latest_get_check_button")
        await CreateButton(label="確認", custom_id="latest_get_check_button").callback(interaction)
        sql, parameters = query.call_args_list[1].args
        self.assertEqual((7, "example_user"), parameters)
        self.assertIn("ORDER BY updated_at DESC, id DESC", sql)
        self.assertIn("AND enable_flg = False", sql)
        embed = interaction.response.send_message.call_args.kwargs["embed"]
        self.assertEqual("最後に取得した言葉", embed.fields[0].value)

    @patch("button_sub.BotSetting")
    @patch("button_sub.DbQuery")
    async def test_join_uses_numeric_id_for_lookup_and_insert(self, query_type, setting_type):
        setting_type.return_value.GetBotSeq.return_value = 7
        query = query_type.return_value.quryexcute
        query.side_effect = [[(7,)], [(7,)], [], []]
        interaction = self.make_interaction("join_button")
        await CreateButton(label="参加", custom_id="join_button").callback(interaction)
        self.assertEqual((7, interaction.user.id), query.call_args_list[2].args[1])
        self.assertEqual((7, interaction.user.id,"example_user","参加者"), query.call_args_list[3].args[1])
        interaction.response.send_message.assert_awaited_once()
        self.assertIn("view", interaction.response.send_message.call_args.kwargs)

    @patch("button_sub.BotSetting")
    @patch("button_sub.DbQuery")
    async def test_completion_uses_same_numeric_id(self, query_type, setting_type):
        setting_type.return_value.GetBotSeq.return_value = 7
        query = query_type.return_value.quryexcute
        query.side_effect = [[(7,)], []]
        interaction = self.make_interaction("commit_button")
        await CreateButton(label="登録完了", custom_id="commit_button").callback(interaction)
        self.assertEqual(("example_user","参加者",7, interaction.user.id), query.call_args_list[1].args[1])
        interaction.response.edit_message.assert_awaited_once()

    @patch("button_sub.BotSetting")
    @patch("button_sub.DbQuery")
    async def test_rejoin_refreshes_names_without_resetting_completion(self, query_type, setting_type):
        setting_type.return_value.GetBotSeq.return_value = 7
        query = query_type.return_value.quryexcute
        query.side_effect = [[(7,)], [(7,)], [(10,True)], []]
        interaction = self.make_interaction("join_button")
        interaction.user.name = "renamed_user"
        interaction.user.display_name = "変更後の表示名🍎"
        await CreateButton(label="参加",custom_id="join_button").callback(interaction)
        sql, parameters = query.call_args_list[3].args
        self.assertNotIn("is_completion",sql)
        self.assertEqual(("renamed_user","変更後の表示名🍎",7,interaction.user.id),parameters)
        self.assertEqual("すでに登録を完了しているよ",interaction.response.send_message.call_args.args[0])

    @patch("button_sub.BotSetting")
    @patch("button_sub.DbQuery")
    async def test_db_error_sends_notification_without_none_view(self, query_type, setting_type):
        setting_type.return_value.GetBotSeq.return_value = 7
        query_type.return_value.quryexcute.side_effect = [
            [(7,)], [(7,)], [], mysql.connector.Error("Insert failed")
        ]
        interaction = self.make_interaction("join_button")
        await CreateButton(label="参加", custom_id="join_button").callback(interaction)
        interaction.response.send_message.assert_awaited_once()
        self.assertNotIn("view", interaction.response.send_message.call_args.kwargs)
        self.assertTrue(interaction.response.send_message.call_args.kwargs["ephemeral"])

    @patch("button_sub.BotSetting")
    @patch("button_sub.DbQuery")
    async def test_error_after_response_edits_existing_message(self, query_type, setting_type):
        setting_type.return_value.GetBotSeq.return_value = 7
        query_type.return_value.quryexcute.side_effect = [
            [(7,)], [(7,)], [], mysql.connector.Error("Insert failed")
        ]
        interaction = self.make_interaction("join_button")
        interaction.response.is_done.return_value = True
        await CreateButton(label="参加", custom_id="join_button").callback(interaction)
        interaction.edit_original_response.assert_awaited_once()
        interaction.response.send_message.assert_not_awaited()
