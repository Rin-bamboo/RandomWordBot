import os
import re
import unicodedata
from pathlib import Path


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
