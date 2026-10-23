"""NGワードCSVの全件検証と、Excel向けの安全なCSV出力。"""
import csv
import io
from ng_word_filter import normalize_word

MAX_CSV_BYTES = 1024 * 1024
MAX_CSV_ROWS = 10000
FORMULA_PREFIXES = ("'", '=', '+', '-', '@')


def parse_csv(payload):
    if len(payload) > MAX_CSV_BYTES:
        raise ValueError('CSVは1MB以下にしてください。')
    try:
        text = payload.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            text = payload.decode('cp932')
        except UnicodeDecodeError as error:
            raise ValueError('UTF-8またはShift_JISのCSVを指定してください。') from error
    if '\x00' in text:
        raise ValueError('CSVに不正な文字が含まれています。')
    words, rows, first = set(), 0, True
    try:
        for line, row in enumerate(csv.reader(io.StringIO(text, newline=''), strict=True), 1):
            if not row or row == ['']:
                continue
            if len(row) != 1:
                raise ValueError(f'{line}行目：NGワード1列のCSVにしてください。')
            value = row[0].strip()
            if first and value in ('ng_word', 'word', 'NGワード'):
                first = False
                continue
            first = False
            rows += 1
            if rows > MAX_CSV_ROWS:
                raise ValueError('CSVのデータは10,000行以下にしてください。')
            # ダウンロード時の数式無効化用の接頭辞を復元する。
            if len(value) > 1 and value[0] == "'" and value[1] in FORMULA_PREFIXES:
                value = value[1:]
            if not 1 <= len(value) <= 100 or any(ord(char) < 32 or ord(char) == 127 for char in value):
                raise ValueError(f'{line}行目：ワードは改行・制御文字を含まない1～100文字にしてください。')
            normalized = normalize_word(value)
            if not normalized or normalized.startswith('#'):
                raise ValueError(f'{line}行目：空白のみ、または#で始まるワードは登録できません。')
            words.add(normalized)
    except csv.Error as error:
        raise ValueError('CSV形式が不正です。引用符と区切りを確認してください。') from error
    if not words:
        raise ValueError('登録できるNGワードがありません。')
    return sorted(words), rows


def export_csv(words):
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\r\n')
    writer.writerow(['ng_word'])
    for word in sorted(set(words)):
        # Excel等が数式として評価しないようにする。parse_csvで元の値へ戻す。
        writer.writerow(["'" + word if word.startswith(FORMULA_PREFIXES) else word])
    return output.getvalue().encode('utf-8-sig')
