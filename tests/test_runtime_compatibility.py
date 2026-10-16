import io
import unittest
import warnings

import matplotlib

matplotlib.use("Agg")

import japanize_matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image


class RuntimeCompatibilityTests(unittest.TestCase):
    def test_word_table_renders_japanese_png(self):
        # 終了一覧で使うpandas、日本語フォント、PNG出力の組み合わせを確認する。
        words = pd.DataFrame([["確認用の言葉", "参加者"]], columns=["言葉", "登録者"])
        figure, axis = plt.subplots()
        try:
            axis.axis("off")
            axis.table(cellText=words.values, colLabels=words.columns, loc="center")
            output = io.BytesIO()
            with warnings.catch_warnings():
                warnings.filterwarnings("error", message="Glyph .* missing from font")
                figure.savefig(output, format="png", transparent=True)
            output.seek(0)
            with Image.open(output) as image:
                self.assertEqual("PNG", image.format)
                self.assertGreater(image.width, 0)
                self.assertGreater(image.height, 0)
                image.verify()
        finally:
            plt.close(figure)
