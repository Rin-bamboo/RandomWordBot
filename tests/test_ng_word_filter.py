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


if __name__ == "__main__":
    unittest.main()
