import unicodedata

def count_characters(text):
    count = 0
    for char in text:
        char_width = unicodedata.east_asian_width(char)
        if char_width in ('W', 'F'):
            count += 2  # 全角文字
        else:
            count += 1  # 半角文字
    return count