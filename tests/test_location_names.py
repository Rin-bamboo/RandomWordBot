import unittest
import os
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import mysql.connector

from bot_setting import BotSetting
from Model.DiscordInfo import location_names


class LocationNameTests(unittest.TestCase):
    @patch("bot_setting.DbQuery")
    def test_missing_names_are_filled_using_parameters(self, query_type):
        query = query_type.return_value.quryexcute
        query.side_effect = [[(7,None,None)], []]
        self.assertEqual(7,BotSetting().GetBotSeq(1,2,"問い合わせ用のサーバー","雑談'チャンネル"))
        sql, parameters = query.call_args.args
        self.assertIn("WHERE id=%s", sql)
        self.assertNotIn("雑談", sql)
        self.assertEqual(("問い合わせ用のサーバー","雑談'チャンネル",7),parameters)

    @patch("bot_setting.DbQuery")
    def test_rename_updates_existing_row(self, query_type):
        query = query_type.return_value.quryexcute
        query.side_effect = [[(7,"旧サーバー","旧チャンネル")], []]
        BotSetting().GetBotSeq(1,2,"新サーバー","新チャンネル")
        self.assertEqual(("新サーバー","新チャンネル",7),query.call_args.args[1])

    @patch("bot_setting.DbQuery")
    def test_unavailable_names_preserve_saved_names(self, query_type):
        query = query_type.return_value.quryexcute
        query.return_value = [(7,"保存済みサーバー","保存済みチャンネル")]
        BotSetting().GetBotSeq(1,2)
        query.assert_called_once()

    @patch("bot_setting.DbQuery")
    def test_unchanged_names_do_not_write(self, query_type):
        query = query_type.return_value.quryexcute
        query.return_value = [(7,"サーバー","チャンネル")]
        BotSetting().GetBotSeq(1,2,"サーバー","チャンネル")
        query.assert_called_once()

    @patch("bot_setting.DbQuery")
    def test_invalid_and_empty_names_do_not_overwrite_saved_names(self, query_type):
        query = query_type.return_value.quryexcute
        query.return_value = [(7,"サーバー","チャンネル")]
        BotSetting().GetBotSeq(1,2,"", "あ"*256)
        query.assert_called_once()

    @patch("bot_setting.DbQuery")
    def test_maximum_length_and_partly_available_names(self, query_type):
        query = query_type.return_value.quryexcute
        query.side_effect = [[(7,"旧サーバー","保存済みチャンネル")], []]
        BotSetting().GetBotSeq(1,2,"あ"*255,None)
        self.assertEqual(("あ"*255,"保存済みチャンネル",7),query.call_args.args[1])

    @patch("bot_setting.DbQuery")
    def test_startup_sync_uses_cached_names_and_preserves_unavailable_rows(self, query_type):
        query = query_type.return_value.quryexcute
        query.side_effect = [[(7,1,2,None,None),(8,3,4,"退会済み","削除済み")], []]
        client = MagicMock()
        client.get_guild.side_effect = [SimpleNamespace(name="サーバー"),None]
        client.get_channel.side_effect = [SimpleNamespace(name="チャンネル",guild=SimpleNamespace(id=1)),None]
        BotSetting().SyncLocationNames(client)
        self.assertEqual(2,query.call_count)
        self.assertEqual(("サーバー","チャンネル",7),query.call_args.args[1])

    def test_missing_discord_objects_return_none(self):
        self.assertEqual({"guild_name":None,"channel_name":None},location_names(SimpleNamespace()))

    @unittest.skipUnless(os.getenv("RUN_MYSQL_TESTS")=="1", "MySQL結合テストは明示的に有効化する")
    def test_names_round_trip_and_rename_with_real_mysql_schema(self):
        connection = mysql.connector.connect(
            host=os.environ["HOST"],user=os.environ["USER_NAME"],
            password=os.environ["PASS"],database=os.environ["DB"],
        )
        cursor = connection.cursor()
        try:
            schema = (Path(__file__).resolve().parents[1]/"docker/mysql/init.sql").read_text(encoding="utf-8")
            ddl = re.search(r"CREATE TABLE BOTSEQTABLE \(.*?\);",schema,re.S).group()
            cursor.execute(ddl.replace("CREATE TABLE BOTSEQTABLE","CREATE TEMPORARY TABLE location_names_test",1))
            cursor.execute("INSERT INTO location_names_test (id,guild_id,channel_id) VALUES (7,1,2),(8,1,3)")

            def query(sql,parameters):
                cursor.execute(sql.replace("BOTSEQTABLE","location_names_test"),parameters)
                return cursor.fetchall()

            with patch("bot_setting.DbQuery") as query_type:
                query_type.return_value.quryexcute.side_effect=query
                settings = BotSetting()
                settings.GetBotSeq(1,2,"問い合わせサーバー","雑談'🍎")
                settings.GetBotSeq(1,2,"名前変更後",None)
            cursor.execute("SELECT guild_name,channel_name FROM location_names_test ORDER BY id")
            self.assertEqual([("名前変更後","雑談'🍎"),(None,None)],cursor.fetchall())
        finally:
            connection.rollback()
            cursor.close()
            connection.close()
