-- 適用前にバックアップし、名前列がない既存DBへ一度だけ適用する。
-- user_idによる識別は変更しない。不明な名前はNULLのまま保持する。
ALTER TABLE join_members
    ADD COLUMN user_name VARCHAR(255) NULL,
    ADD COLUMN display_name VARCHAR(255) NULL;
