import os
import re
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import mysql.connector
from button_sub import CreateButton


@unittest.skipUnless(os.getenv("RUN_MYSQL_TESTS") == "1", "MySQL結合テストは明示的に有効化する")
class MySqlSchemaTests(unittest.IsolatedAsyncioTestCase):
    async def test_draw_then_latest_uses_acquisition_time_with_fresh_schema(self):
        connection = mysql.connector.connect(
            host=os.environ["HOST"], user=os.environ["USER_NAME"],
            password=os.environ["PASS"], database=os.environ["DB"],
        )
        cursor = connection.cursor()
        try:
            schema = (Path(__file__).resolve().parents[1] / "docker/mysql/init.sql").read_text(encoding="utf-8")
            ddl = re.search(r"CREATE TABLE WORDTABLE \(.*?\);", schema, re.S).group()
            cursor.execute(ddl.replace("CREATE TABLE WORDTABLE", "CREATE TEMPORARY TABLE latest_word_schema_test", 1))
            cursor.execute(
                "INSERT INTO latest_word_schema_test "
                "(id,botseq_id,word,select_flg,use_user_id,updated_at,enable_flg) VALUES "
                "(10,7,'今回取得する言葉',FALSE,NULL,NULL,FALSE),"
                "(20,7,'以前の言葉',TRUE,'example_user','2000-01-01 00:00:00',FALSE),"
                "(30,7,'別の人の言葉',TRUE,'other_user','2030-01-01 00:00:00',FALSE),"
                "(40,7,'終了済みの言葉',TRUE,'example_user','2030-01-01 00:00:00',TRUE)"
            )

            def query(sql, parameters):
                if "FROM BOTSEQTABLE" in sql:
                    return [(7,)]
                if "FROM join_members" in sql:
                    return [(1,)]
                cursor.execute(sql.replace("WORDTABLE", "latest_word_schema_test"), parameters)
                return cursor.fetchall()

            interaction = MagicMock()
            interaction.user.id = 123456789012345678
            interaction.user.__str__.return_value = "example_user"
            interaction.user.display_name = "参加者"
            interaction.response.send_message = AsyncMock()
            interaction.response.is_done.return_value = False
            with patch("button_sub.DbQuery") as query_type, patch("button_sub.BotSetting") as settings:
                query_type.return_value.quryexcute.side_effect = query
                settings.return_value.GetBotSeq.return_value = 7
                for custom_id in ["get_button", "latest_get_check_button"]:
                    interaction.data = {"custom_id": custom_id}
                    await CreateButton(label="確認", custom_id=custom_id).callback(interaction)
                embed = interaction.response.send_message.call_args.kwargs["embed"]
                self.assertEqual("今回取得する言葉", embed.fields[0].value)
                cursor.execute("SELECT updated_at FROM latest_word_schema_test WHERE id=10")
                self.assertIsNotNone(cursor.fetchone()[0])
        finally:
            connection.rollback()
            cursor.close()
            connection.close()
