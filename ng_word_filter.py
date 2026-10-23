import os
import re
import unicodedata
from pathlib import Path
from config_store import configuration_lock, atomic_save


DEFAULT_NG_WORD_FILE = Path(__file__).parent / "text" / "ng_words.txt"


def normalize_word(value):
    """表記揺れと空白によるNGワード回避を抑止する。"""

    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", "", normalized)


def load_ng_words(file_path=None, environment_value=None):
    """設定ファイルと環境変数からNGワードを読み込む。"""

    path = Path(file_path or os.getenv("NG_WORD_FILE", DEFAULT_NG_WORD_FILE))
    configured_words = []

    if path.exists():
        configured_words.extend(
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )

    raw_environment_value = (
        os.getenv("NG_WORDS", "")
        if environment_value is None
        else environment_value
    )
    configured_words.extend(raw_environment_value.split(","))

    return tuple(
        normalized
        for word in configured_words
        if (normalized := normalize_word(word.strip()))
    )


def find_ng_word(value, ng_words=None):
    """入力に含まれる最初のNGワードを返す。該当しない場合はNone。"""

    normalized_value = normalize_word(value)
    words = load_ng_words() if ng_words is None else ng_words
    return next((word for word in words if word in normalized_value), None)


def is_ng_word(value, ng_words=None):
    return find_ng_word(value, ng_words) is not None


def update_ng_word(action, word, file_path=None):
    if action not in ('block', 'unblock'):
        raise ValueError('不正な操作です。')
    if not isinstance(word, str) or not 1 <= len(word.strip()) <= 100 or any(ord(char) < 32 for char in word):
        raise ValueError('NGワードは改行を含まない1～100文字で入力してください。')
    normalized = normalize_word(word.strip())
    if not normalized or normalized.startswith('#'):
        raise ValueError('空白のみ、または#で始まるワードは指定できません。')
    path = Path(file_path or os.environ['NG_WORD_FILE'])
    with configuration_lock(path):
        if not path.is_file():
            raise OSError('NGワード設定ファイルがありません。')
        words = set(load_ng_words(path, environment_value=''))
        if action == 'block':
            words.add(normalized)
        else:
            words.discard(normalized)
        atomic_save(path, '# 管理画面で管理するNGワード\n' + '\n'.join(sorted(words)) + '\n')


def add_ng_words(words, file_path=None):
    """検証済みCSVの全件を、一度の原子的保存で追加する。"""
    path = Path(file_path or os.environ['NG_WORD_FILE'])
    with configuration_lock(path):
        if not path.is_file():
            raise OSError('NGワード設定ファイルがありません。')
        existing = set(load_ng_words(path, environment_value=''))
        merged = existing | set(words)
        atomic_save(path, '# 管理画面で管理するNGワード\n' + '\n'.join(sorted(merged)) + '\n')
        return dict(added=len(merged - existing), existing=len(set(words) & existing), total=len(merged))
