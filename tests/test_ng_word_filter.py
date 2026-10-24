import tempfile
import unittest
from pathlib import Path

from ng_word_filter import find_ng_word, is_ng_word, load_ng_words


class NgWordFilterTests(unittest.TestCase):
    def test_loads_file_and_environment_words(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ng_words.txt"
            path.write_text("# comment\n禁止語\n\n", encoding="utf-8")

            words = load_ng_words(path, "追加語,")

        self.assertEqual(("禁止語", "追加語"), words)

    def test_matches_case_width_and_whitespace_variants(self):
        words = ("badword",)

        self.assertTrue(is_ng_word("ＢＡＤ word", words))

    def test_returns_none_for_allowed_word(self):
        self.assertIsNone(find_ng_word("好きな言葉", ("禁止語",)))

    def test_default_list_rejects_explicit_abuse_and_variants(self):
        words = load_ng_words(environment_value="")
        for text in ("死 ね", "ぶっ殺すぞ", "自殺しろ", "児童ポルノ", "フェラチオ", "ＫＩＬＬ ＹＯＵＲＳＥＬＦ"):
            with self.subTest(text=text):
                self.assertTrue(is_ng_word(text, words))

    def test_default_list_preserves_ordinary_words(self):
        words = load_ng_words(environment_value="")
        for text in ("好きな言葉", "パチンコ", "ぱちんこ", "ロマンコメディ", "中国料理", "韓国旅行", "障害者支援", "自殺予防", "性教育", "池沼の生態系"):
            with self.subTest(text=text):
                self.assertFalse(is_ng_word(text, words))


if __name__ == "__main__":
    unittest.main()
