# -*- coding: Shift-JIS -*-
import logging
import mysql.connector
import config

db_name=config.DB
user_name=config.USER_NAME
host_name=config.HOST
user_password=config.PASS

# MySQL接続情報
db_config = {
    "host": host_name,  # ホスト名
    "user": user_name,       # ユーザ名
    "password": user_password,  # パスワード
    "database": db_name  # データベース名
}

class DbQuery():
    def quryexcute(self,query,values):
        try:
            # MySQLデータベースに接続
            connection = mysql.connector.connect(**db_config)

            if connection.is_connected():
                # バージョン情報を取得
                cursor = connection.cursor()
                logging.info("Connected to MySQL Server")


                #query="INSERT INTO botseqtable(guild_id,channel_id) VALUES(%s,%s)"
                #values = (1076845818407026758,1076849137007472690)
                cmpleate_query = cursor.execute(query,values)
                logging.info(f"クエリ情報{query}")

                query_value = cursor.fetchall()
                connection.commit();

                return query_value

        except mysql.connector.Error as e:
            print("Error:", e)
            logging.error(e)
            connection.rollback();
            # エラーが発生した場合の処理をここに追加
            # 例: エラーログの出力、エラーメッセージの通知、別のアクションの実行など

        finally:
            # 接続をクローズ
            if connection is not None and connection.is_connected():
                cursor.close()
                connection.close()
                logging.info("Connection closed")
