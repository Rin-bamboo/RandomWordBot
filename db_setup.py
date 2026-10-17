import mysql.connector

#設定ファイルの読み込み import
import os
from dotenv import load_dotenv
load_dotenv()


db_name = os.getenv('DB')
user_name = os.getenv('USER_NAME')
host_name = os.getenv('HOST')
user_password = os.getenv('PASS')

#=======================ログ出力設定============================
from log_setting import getLogger
logger = getLogger(__name__)

# MySQL接続情報
db_config = {
    "host": host_name,  # ホスト名
    "user": user_name,       # ユーザ名
    "password": user_password,  # パスワード
    "database": db_name  # データベース名
}

class DbQuery():
    def quryexcute(self,query,values):
        connection = None
        cursor = None
        try:
            # MySQLデータベースに接続
            connection = mysql.connector.connect(**db_config)

            if connection.is_connected():
                # バージョン情報を取得
                cursor = connection.cursor()
                logger.info("Connected to MySQL Server")
                
                cursor.execute(query,values)

                query_value = cursor.fetchall()
                connection.commit();

                return query_value

        except mysql.connector.Error as e:
            logger.error(e)
            if connection is not None and connection.is_connected():
                try:
                    connection.rollback()
                except mysql.connector.Error:
                    logger.warning("DBロールバックに失敗しました", exc_info=True)
            raise

        finally:
            # 接続をクローズ
            # 接続・カーソル作成の途中で失敗しても、元の例外を保持する。
            if cursor is not None:
                try:
                    cursor.close()
                except mysql.connector.Error:
                    logger.warning("DBカーソルの終了に失敗しました", exc_info=True)
            if connection is not None:
                try:
                    connection.close()
                except mysql.connector.Error:
                    logger.warning("DB接続の終了に失敗しました", exc_info=True)
                logger.info("Connection closed")
