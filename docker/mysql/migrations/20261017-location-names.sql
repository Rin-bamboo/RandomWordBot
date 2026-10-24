-- 適用前にバックアップし、名前列がない既存DBへ一度だけ適用する。
-- 不明な名前はNULLのまま保持し、Botが確認できた実際の名前を保存する。
ALTER TABLE BOTSEQTABLE
    ADD COLUMN guild_name VARCHAR(255) NULL,
    ADD COLUMN channel_name VARCHAR(255) NULL;
