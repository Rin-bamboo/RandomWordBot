import unicodedata

def count_characters(text):
    count = 0
    for char in text:
        char_width = unicodedata.east_asian_width(char)
        if char_width in ('W', 'F'):
            count += 2  # �S�p����
        else:
            count += 1  # ���p����
    return count