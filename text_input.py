
def inptfile(name):
    #=========テキストファイルの読み込み============
    path = 'text/'+ name +'.txt'  #ヘルプファイルの読み込み
    try:
        f = open(path,encoding='utf-8')
        input_value = f.read()
        f.close()
    except:
        input_value = "テキストが読み込めませんでした"
    finally:
        return input_value