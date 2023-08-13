#設定ファイルの読み込み import
import os
from dotenv import load_dotenv
load_dotenv()
LOGFILE = os.getenv('LOGFILE')


import logging
import logging.handlers

def getLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logging.getLogger('discord.http').setLevel(logging.DEBUG)

    FORMAT = '%(levelname)s %(asctime)s %(name)s： %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)

    handler = logging.handlers.RotatingFileHandler(
        filename=LOGFILE,
        encoding='utf-8',
        maxBytes= 5 * 1024 * 1024,  # 5 MiB
        backupCount=5,  # Rotate through 5 files
    )
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
