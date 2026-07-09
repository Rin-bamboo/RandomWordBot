from db_setup import DbQuery


class RWBModel:
    """ワードと設定に関するDB操作を集約する。"""

    def __init__(self, query_db=None):
        self.query_db = query_db or DbQuery()

    def insert_word(self, botseq_id, word, user_id, user_name):
        query = (
            "INSERT INTO WORDTABLE"
            "(botseq_id,word,create_user_id,create_user) VALUES(%s,%s,%s,%s)"
        )
        return self.query_db.quryexcute(
            query, (botseq_id, word, user_id, user_name)
        )

    def update_word(self, botseq_id, word, user_id, word_id):
        query = (
            "UPDATE WORDTABLE SET word = %s "
            "WHERE botseq_id = %s AND create_user_id = %s AND id = %s"
        )
        return self.query_db.quryexcute(
            query, (word, botseq_id, user_id, word_id)
        )

    def delete_word(self, botseq_id, user_id, word_id):
        query = (
            "UPDATE WORDTABLE SET delete_flg = True "
            "WHERE botseq_id = %s AND create_user_id = %s AND id = %s"
        )
        return self.query_db.quryexcute(query, (botseq_id, user_id, word_id))

    def update_anonymous_setting(self, botseq_id, setting_value):
        query = (
            "UPDATE settings_value JOIN settings "
            "ON settings_value.setting_id = settings.setting_id "
            "SET settings_value.setting_value = %s "
            "WHERE settings.setting_name = 'Anonymous Setting' "
            "AND botseq_id = %s"
        )
        return self.query_db.quryexcute(query, (setting_value, botseq_id))

    def update_registration_limit(self, botseq_id, setting_value):
        query = (
            "UPDATE settings_value JOIN settings "
            "ON settings_value.setting_id = settings.setting_id "
            "SET settings_value.setting_value = %s "
            "WHERE settings.setting_name = 'Registration Limit' "
            "AND botseq_id = %s"
        )
        return self.query_db.quryexcute(query, (setting_value, botseq_id))
