import os
import re
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import mysql.connector
from bot_setting import BotSetting
from button_sub import CreateButton


class MemberNameSyncTests(unittest.TestCase):
    @patch("bot_setting.DbQuery")
    def test_guild_specific_display_names_and_unavailable_members(self, query_type):
        query = query_type.return_value.quryexcute
        query.side_effect = [
            [(1,10,123,None,None),(2,20,123,None,None),(3,30,456,"保存済み","退出済み")], [], [],
        ]
        first = MagicMock()
        first.get_member.return_value=SimpleNamespace(name="username",display_name="サーバーAの名前")
        second = MagicMock()
        second.get_member.return_value=SimpleNamespace(name="username",display_name="サーバーBの名前")
        client = MagicMock()
        client.get_guild.side_effect=[first,second,None]
        BotSetting().SyncMemberNames(client)
        self.assertEqual(3,query.call_count)
        self.assertEqual(("username","サーバーAの名前",1),query.call_args_list[1].args[1])
        self.assertEqual(("username","サーバーBの名前",2),query.call_args_list[2].args[1])

    @patch("bot_setting.DbQuery")
    def test_unchanged_or_invalid_names_do_not_write(self, query_type):
        query = query_type.return_value.quryexcute
        query.return_value=[(1,10,123,"username","表示名"),(2,10,456,"保存済み","表示名")]
        client=MagicMock()
        client.get_guild.return_value.get_member.side_effect=[
            SimpleNamespace(name="username",display_name="表示名"),
            SimpleNamespace(name="",display_name="あ"*256),
        ]
        BotSetting().SyncMemberNames(client)
        query.assert_called_once()


@unittest.skipUnless(os.getenv("RUN_MYSQL_TESTS")=="1", "MySQL結合テストは明示的に有効化する")
class MemberNameMySqlTests(unittest.IsolatedAsyncioTestCase):
    async def test_join_complete_and_rejoin_preserve_identity_and_other_rows(self):
        connection=mysql.connector.connect(host=os.environ["HOST"],user=os.environ["USER_NAME"],
                                           password=os.environ["PASS"],database=os.environ["DB"])
        cursor=connection.cursor()
        try:
            schema=(Path(__file__).resolve().parents[1]/"docker/mysql/init.sql").read_text(encoding="utf-8")
            ddl=re.search(r"CREATE TABLE join_members \(.*?\);",schema,re.S).group()
            cursor.execute(ddl.replace("CREATE TABLE join_members","CREATE TEMPORARY TABLE member_names_test",1))
            cursor.execute("INSERT INTO member_names_test (botseq_id,user_id,user_name,display_name) "
                           "VALUES (7,999,'other','別の人'),(8,123,'other-session','別の回')")

            def query(sql,parameters):
                if "FROM BOTSEQTABLE" in sql:
                    return [(7,)]
                cursor.execute(sql.replace("join_members","member_names_test"),parameters)
                return cursor.fetchall()

            interaction=MagicMock()
            interaction.user.id=123
            interaction.user.name="original_user"
            interaction.user.display_name="元の表示名"
            interaction.user.__str__.return_value="original_user"
            interaction.response.send_message=AsyncMock()
            interaction.response.edit_message=AsyncMock()
            interaction.response.is_done.return_value=False
            with patch("button_sub.DbQuery") as query_type,patch("button_sub.BotSetting") as settings:
                query_type.return_value.quryexcute.side_effect=query
                settings.return_value.GetBotSeq.return_value=7
                for custom_id in ["join_button","commit_button"]:
                    interaction.data={"custom_id":custom_id}
                    await CreateButton(label="確認",custom_id=custom_id).callback(interaction)
                interaction.user.name="renamed_user"
                interaction.user.display_name="表示名'🍎"
                interaction.data={"custom_id":"join_button"}
                await CreateButton(label="参加",custom_id="join_button").callback(interaction)
                cursor.execute("SELECT user_id,user_name,display_name,is_completion FROM member_names_test WHERE botseq_id=7 AND user_id=123")
                self.assertEqual([(123,"renamed_user","表示名'🍎",1)],cursor.fetchall())
                cursor.execute("SELECT user_name FROM member_names_test WHERE user_id=999 OR botseq_id=8 ORDER BY id")
                self.assertEqual([("other",),("other-session",)],cursor.fetchall())
                self.assertEqual("すでに登録を完了しているよ",interaction.response.send_message.call_args.args[0])
        finally:
            connection.rollback()
            cursor.close()
            connection.close()
