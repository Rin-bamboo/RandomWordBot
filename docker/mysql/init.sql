-- Fresh installations only. Existing databases must be backed up and migrated separately.
SET NAMES utf8mb4;

CREATE TABLE BOTSEQTABLE (
    id INT PRIMARY KEY AUTO_INCREMENT,
    guild_id BIGINT,
    channel_id BIGINT,
    start_up_flg BOOLEAN DEFAULT FALSE,
    start_up_time_stamp TIMESTAMP NULL,
    guild_name VARCHAR(255) NULL,
    channel_name VARCHAR(255) NULL
);

CREATE TABLE WORDTABLE (
    id INT PRIMARY KEY AUTO_INCREMENT,
    botseq_id INT,
    word TEXT,
    create_user TEXT,
    create_user_id TEXT,
    use_user TEXT,
    use_user_id TEXT,
    select_flg BOOLEAN DEFAULT FALSE,
    delete_flg BOOLEAN DEFAULT FALSE,
    enable_flg BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP(6) NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP(6)
);

CREATE TABLE settings (
    setting_id INT PRIMARY KEY AUTO_INCREMENT,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    setting_name VARCHAR(100) NOT NULL UNIQUE,
    setting_explanation TEXT NOT NULL
);

CREATE TABLE settings_value (
    setting_id INT NOT NULL,
    botseq_id INT NOT NULL,
    setting_value TEXT NOT NULL,
    PRIMARY KEY (setting_id, botseq_id)
);

CREATE TABLE join_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    botseq_id INT NOT NULL,
    user_id BIGINT NOT NULL,
    is_completion BOOLEAN DEFAULT FALSE,
    user_name VARCHAR(255) NULL,
    display_name VARCHAR(255) NULL,
    UNIQUE KEY member_per_channel (botseq_id, user_id)
);

INSERT INTO settings (setting_name, setting_explanation) VALUES
    ('Anonymous Setting', '終了時の名前表示'),
    ('Registration Limit', '登録できる言葉の上限');



CREATE TABLE word_reports (
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
