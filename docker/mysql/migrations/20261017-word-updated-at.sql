-- 適用前にバックアップし、updated_at列がない既存DBへ一度だけ実行する。
-- 過去の取得日時は復元できないためNULLのままとし、既存のid順による代替を使用する。
ALTER TABLE WORDTABLE
    ADD COLUMN updated_at TIMESTAMP(6) NULL DEFAULT NULL
    ON UPDATE CURRENT_TIMESTAMP(6);
