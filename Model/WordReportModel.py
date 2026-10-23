"""通報対象をチャンネルで制限し、通報時点の言葉・登録情報を保持する。"""

from db_setup import DbQuery


class WordReportModel:
    def __init__(self, query_db=None):
        self.query_db = query_db or DbQuery()

    def candidates(self, guild_id, channel_id, search):
        return self.query_db.quryexcute(
            "SELECT w.id, w.word FROM WORDTABLE w "
            "JOIN BOTSEQTABLE b ON b.id = w.botseq_id "
            "WHERE b.guild_id = %s AND b.channel_id = %s "
            "AND w.delete_flg = FALSE "
            "AND LOCATE(%s, w.word) > 0 ORDER BY w.id DESC LIMIT 25",
            (guild_id, channel_id, search),
        )

    def submit(self, report_id, guild_id, channel_id, word_id, reporter_id, reason):
        # INSERT SELECTで対象確認と証跡保存を一体化する。別チャンネルのIDは受理しない。
        # 名前の変更・ワード更新・削除後も通報時点の証跡を残す。
        self.query_db.quryexcute(
            "INSERT INTO word_reports "
            "(report_id, guild_id, channel_id, word_id, reporter_id, "
            "word_snapshot, owner_snapshot, reason) "
            "SELECT %s, b.guild_id, b.channel_id, w.id, %s, w.word, w.create_user_id, %s "
            "FROM WORDTABLE w JOIN BOTSEQTABLE b ON b.id = w.botseq_id "
            "WHERE b.guild_id = %s AND b.channel_id = %s AND w.id = %s "
            "AND w.delete_flg = FALSE "
            "ON DUPLICATE KEY UPDATE report_id = word_reports.report_id",
            (report_id, reporter_id, reason, guild_id, channel_id, word_id),
        )
        rows = self.query_db.quryexcute(
            "SELECT r.report_id, r.word_snapshot, r.reason, r.notification_message_id "
            "FROM word_reports r JOIN WORDTABLE w ON w.id = r.word_id "
            "WHERE r.guild_id = %s AND r.channel_id = %s AND r.word_id = %s "
            "AND r.reporter_id = %s AND BINARY r.word_snapshot = BINARY w.word "
            "AND w.delete_flg = FALSE",
            (guild_id, channel_id, word_id, reporter_id),
        )
        return rows[0] if rows else None

    def mark_notified(self, report_id, message_id):
        self.query_db.quryexcute(
            "UPDATE word_reports SET notification_message_id = %s WHERE report_id = %s",
            (message_id, report_id),
        )
