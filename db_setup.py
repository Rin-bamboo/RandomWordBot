import mysql.connector
from time import perf_counter
from operation_log import log_event

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
        started_at = perf_counter()
        operation = query.lstrip().split(None, 1)[0].upper()
        log_event(logger, "db_started", operation=operation, query=" ".join(query.split()))
        try:
            # MySQLデータベースに接続
            connection = mysql.connector.connect(**db_config)

            if connection.is_connected():
                # バージョン情報を取得
                cursor = connection.cursor()
                log_event(logger, "db_connected", operation=operation)
                
                cursor.execute(query,values)

                query_value = cursor.fetchall()
                connection.commit();
                log_event(logger, "db_committed", operation=operation, affected_rows=cursor.rowcount,
                          returned_rows=len(query_value),
                          elapsed_ms=round((perf_counter() - started_at) * 1000, 2))

                return query_value

        except mysql.connector.Error as e:
            log_event(logger, "db_failed", outcome="failed", operation=operation,
                      error_number=e.errno, error_type=type(e).__name__,
                      elapsed_ms=round((perf_counter() - started_at) * 1000, 2))
            logger.error(e)
            if connection is not None and connection.is_connected():
                try:
                    connection.rollback()
                    log_event(logger, "db_rolled_back", operation=operation)
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
                log_event(logger, "db_closed", operation=operation)
