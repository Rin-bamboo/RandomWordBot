-- 既存DB向け。バックアップ後、ボットの更新前に適用する。
SET NAMES utf8mb4;



CREATE TABLE IF NOT EXISTS word_reports (
    report_id BIGINT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    word_id INT NOT NULL,
    reporter_id BIGINT NOT NULL,
    word_snapshot VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin NOT NULL,
    owner_snapshot TEXT NULL,
    reason VARCHAR(500) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notification_message_id BIGINT NULL,
    UNIQUE KEY reporter_per_word (word_id, reporter_id, word_snapshot)
);
