
#pip install Pillow

from PIL import Image, ImageDraw, ImageFont

# テキストと画像のサイズを設定
text = "文字画像"
image_size = (1024, 704) # これはピクセル単位です

# フォントのパスとサイズを設定
font_path = "C:\\Windows\\Fonts\\msgothic.ttc"  # 例として MS ゴシックを指定
font_size = 18

# 画像を作成
image = Image.new("RGBA", image_size, (0, 0, 0, 255))

# フォントを設定
font = ImageFont.truetype(font_path, font_size)

# テキストのサイズを計算（固定のフォントサイズを使用）
text_width, text_height = len(text) * font_size, font_size

# テキストを描画
draw = ImageDraw.Draw(image)
x = (image_size[0] - text_width) // 2
y = (image_size[1] - text_height) // 2
draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

# 画像を保存
image.save("output_img\\text_image.png")