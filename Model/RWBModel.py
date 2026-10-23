from db_setup import DbQuery
from log_setting import getLogger
from operation_log import log_event

logger = getLogger(__name__)


class RWBModel:
    """ワードと設定に関するDB操作を集約する。"""

    def __init__(self, query_db=None):
        self.query_db = query_db or DbQuery()

    def _execute_logged(self, event, query, parameters, **fields):
        result = self.query_db.quryexcute(query, parameters)
        log_event(logger, event, **fields)
        return result

    def insert_word(self, botseq_id, word, user_id, user_name):
        query = (
            "INSERT INTO WORDTABLE"
            "(botseq_id,word,create_user_id,create_user) VALUES(%s,%s,%s,%s)"
        )
        return self._execute_logged(
            "word_registered", query, (botseq_id, word, user_id, user_name),
            botseq_id=botseq_id, word=word, owner=user_id, owner_name=user_name,
        )

    def update_word(self, botseq_id, word, user_id, word_id):
        query = (
            "UPDATE WORDTABLE SET word = %s "
            "WHERE botseq_id = %s AND create_user_id = %s AND id = %s"
        )
        return self._execute_logged(
            "word_update_committed", query, (word, botseq_id, user_id, word_id),
            botseq_id=botseq_id, word_id=word_id, word=word, owner=user_id,
        )

    def delete_word(self, botseq_id, user_id, word_id):
        query = (
            "UPDATE WORDTABLE SET delete_flg = True "
            "WHERE botseq_id = %s AND create_user_id = %s AND id = %s"
        )
        return self._execute_logged(
            "word_delete_committed", query, (botseq_id, user_id, word_id),
            botseq_id=botseq_id, word_id=word_id, owner=user_id,
        )

    def update_anonymous_setting(self, botseq_id, setting_value):
        query = (
            "UPDATE settings_value JOIN settings "
            "ON settings_value.setting_id = settings.setting_id "
            "SET settings_value.setting_value = %s "
            "WHERE settings.setting_name = 'Anonymous Setting' "
            "AND botseq_id = %s"
        )
        return self._execute_logged(
            "setting_update_committed", query, (setting_value, botseq_id),
            botseq_id=botseq_id, setting="Anonymous Setting", setting_value=setting_value,
        )

    def update_registration_limit(self, botseq_id, setting_value):
        query = (
            "UPDATE settings_value JOIN settings "
            "ON settings_value.setting_id = settings.setting_id "
            "SET settings_value.setting_value = %s "
            "WHERE settings.setting_name = 'Registration Limit' "
            "AND botseq_id = %s"
        )
        return self._execute_logged(
            "setting_update_committed", query, (setting_value, botseq_id),
            botseq_id=botseq_id, setting="Registration Limit", setting_value=setting_value,
        )
