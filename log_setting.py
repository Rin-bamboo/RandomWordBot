#設定ファイルの読み込み import
import os
from dotenv import load_dotenv
load_dotenv()
LOGFILE = os.getenv('LOGFILE', 'logs/randombotapp.log').replace('\\', os.sep)
log_directory = os.path.dirname(LOGFILE)
if log_directory:
    os.makedirs(log_directory, exist_ok=True)


import logging
import logging.handlers

def getLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logging.getLogger('discord').setLevel(logging.INFO)

    FORMAT = '%(levelname)s %(asctime)s %(name)s： %(message)s'
    logging.basicConfig(level=logging.INFO, format=FORMAT)

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
