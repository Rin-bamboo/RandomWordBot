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
        logger.info("=============DB処理開始=================")
        try:
            # MySQLデータベースに接続
            connection = mysql.connector.connect(**db_config)

            if connection.is_connected():
                # バージョン情報を取得
                cursor = connection.cursor()
                logger.info("Connected to MySQL Server")
                logger.info(f"クエリ情報：{query}")
                logger.info(f"データ情報：{values}")

                cmpleate_query = cursor.execute(query,values)
                query_value = cursor.fetchall()
                connection.commit();

                return query_value

        except mysql.connector.Error as ex:
            logger.warning(f"エラー情報：{ex}",exc_info=True)
            connection.rollback();
            # エラーが発生した場合の処理をここに追加
            # 例: エラーログの出力、エラーメッセージの通知、別のアクションの実行など

        finally:
            # 接続をクローズ
            if connection is not None and connection.is_connected():
                cursor.close()
                connection.close()
                logger.info("Connection closed")
                logger.info("=============DB処理終了=================")