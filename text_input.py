from log_setting import getLogger
logger = getLogger(__name__)


def inptfile(name):
    logger.info("=========テキストファイルの読み込み============")

    path = f"text/{name}.txt"  #ヘルプファイルの読み込み
    try:
        f = open(path,encoding='utf-8')
        logger.info(f)
        input_value = f.read()
        logger.info("読み込みデータ：" + input_value)
        f.close()
    except Exception as ex:
        logger.warning(f"エラー情報：{ex}")
        input_value = "テキストが読み込めませんでした"
    finally:
        return input_value