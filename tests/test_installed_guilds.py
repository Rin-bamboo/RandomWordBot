import os
import re
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import mysql.connector
from bot_setting import BotSetting


class InstalledGuildTests(unittest.TestCase):
    @patch("bot_setting.DbQuery")
    def test_join_event_registers_new_guild(self, query_type):
        query=query_type.return_value.quryexcute
        query.side_effect=[[],[]]
        self.assertTrue(BotSetting().RegisterInstalledGuild(SimpleNamespace(id=2,name="導入先🍎")))
        self.assertEqual((2,"導入先🍎"),query.call_args.args[1])

    @patch("bot_setting.DbQuery")
    def test_reintroduction_does_not_modify_existing_guild(self, query_type):
        query=query_type.return_value.quryexcute
        query.return_value=[(7,)]
        self.assertFalse(BotSetting().RegisterInstalledGuild(SimpleNamespace(id=2,name="導入先")))
        query.assert_called_once()

    @patch("bot_setting.DbQuery")
    def test_failed_insert_does_not_report_registration(self, query_type):
        query=query_type.return_value.quryexcute
        query.side_effect=[[],mysql.connector.Error("test failure")]
        with self.assertRaises(mysql.connector.Error):
            BotSetting().RegisterInstalledGuild(SimpleNamespace(id=2,name="導入先"))

    @patch("bot_setting.DbQuery")
    def test_registers_only_missing_guilds_without_channel(self, query_type):
        query=query_type.return_value.quryexcute
        query.side_effect=[[(1,)],[]]
        client=SimpleNamespace(guilds=[SimpleNamespace(id=1,name="既存"),SimpleNamespace(id=2,name="未使用")])
        BotSetting().SyncInstalledGuilds(client)
        self.assertEqual(2,query.call_count)
        self.assertIn("NULL,FALSE",query.call_args.args[0])
        self.assertEqual((2,"未使用"),query.call_args.args[1])

    @patch("bot_setting.DbQuery")
    def test_empty_guild_list_does_not_delete_existing_records(self, query_type):
        query=query_type.return_value.quryexcute
        query.return_value=[(1,)]
        BotSetting().SyncInstalledGuilds(SimpleNamespace(guilds=[]))
        query.assert_called_once()

    @patch("bot_setting.DbQuery")
    def test_first_start_uses_existing_inventory_row(self, query_type):
        query=query_type.return_value.quryexcute
        query.side_effect=[[(7,)],[]]
        BotSetting().RegisterChannel(1,2,"サーバー","チャンネル")
        sql,parameters=query.call_args.args
        self.assertTrue(sql.startswith("UPDATE"))
        self.assertIn("AND channel_id IS NULL",sql)
        self.assertEqual((2,"サーバー","チャンネル",7),parameters)

    @patch("bot_setting.DbQuery")
    def test_new_channel_in_used_guild_creates_new_row(self, query_type):
        query=query_type.return_value.quryexcute
        query.side_effect=[[],[]]
        BotSetting().RegisterChannel(1,2,"サーバー","チャンネル")
        self.assertTrue(query.call_args.args[0].startswith("INSERT"))
        self.assertEqual((1,2,"サーバー","チャンネル"),query.call_args.args[1])

    @patch("bot_setting.DbQuery")
    def test_guild_only_row_rename_does_not_require_channel(self, query_type):
        query=query_type.return_value.quryexcute
        query.side_effect=[[(7,1,None,"旧名称",None)],[]]
        client=MagicMock()
        client.get_guild.return_value=SimpleNamespace(name="新名称")
        BotSetting().SyncLocationNames(client)
        self.assertEqual(("新名称",None,7),query.call_args.args[1])
        client.get_channel.assert_not_called()

    @unittest.skipUnless(os.getenv("RUN_MYSQL_TESTS")=="1", "MySQL結合テストは明示的に有効化する")
    def test_repeated_sync_and_channel_registration_preserve_existing_data(self):
        connection=mysql.connector.connect(host=os.environ["HOST"],user=os.environ["USER_NAME"],
                                           password=os.environ["PASS"],database=os.environ["DB"])
        cursor=connection.cursor()
        try:
            schema=(Path(__file__).resolve().parents[1]/"docker/mysql/init.sql").read_text(encoding="utf-8")
            ddl=re.search(r"CREATE TABLE BOTSEQTABLE \(.*?\);",schema,re.S).group()
            cursor.execute(ddl.replace("CREATE TABLE BOTSEQTABLE","CREATE TEMPORARY TABLE installed_guilds_test",1))
            cursor.execute("INSERT INTO installed_guilds_test (id,guild_id,channel_id,guild_name,channel_name,start_up_flg) VALUES (7,1,10,'既存','利用中',TRUE)")

            def query(sql,parameters):
                cursor.execute(sql.replace("BOTSEQTABLE","installed_guilds_test"),parameters)
                return cursor.fetchall()

            with patch("bot_setting.DbQuery") as query_type:
                query_type.return_value.quryexcute.side_effect=query
                settings=BotSetting()
                client=SimpleNamespace(guilds=[SimpleNamespace(id=1,name="既存"),SimpleNamespace(id=2,name="新規🍎")])
                settings.SyncInstalledGuilds(client)
                settings.SyncInstalledGuilds(client)
                self.assertFalse(settings.RegisterInstalledGuild(SimpleNamespace(id=2,name="既存")))
                self.assertTrue(settings.RegisterInstalledGuild(SimpleNamespace(id=3,name="導入イベント")))
                self.assertFalse(settings.RegisterInstalledGuild(SimpleNamespace(id=3,name="再導入イベント")))
                cursor.execute("SELECT id,channel_id,start_up_flg FROM installed_guilds_test WHERE guild_id=2")
                inventory=cursor.fetchall()
                self.assertEqual(1,len(inventory))
                self.assertEqual((None,0),inventory[0][1:])
                settings.RegisterChannel(2,20,"新規🍎","最初のチャンネル")
                cursor.execute("SELECT id FROM installed_guilds_test WHERE guild_id=2 AND channel_id=20")
                self.assertEqual(inventory[0][0],cursor.fetchone()[0])
                settings.RegisterChannel(2,21,"新規🍎","別のチャンネル")
                cursor.execute("SELECT channel_id FROM installed_guilds_test WHERE guild_id=2 ORDER BY channel_id")
                self.assertEqual([(20,),(21,)],cursor.fetchall())
                cursor.execute("SELECT channel_id,guild_name,channel_name,start_up_flg FROM installed_guilds_test WHERE id=7")
                self.assertEqual((10,"既存","利用中",1),cursor.fetchone())
        finally:
            connection.rollback()
            cursor.close()
            connection.close()
