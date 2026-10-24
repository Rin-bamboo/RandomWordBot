import logging
import logging.handlers
import os
from threading import Lock

from dotenv import load_dotenv
from operation_log import OperationContextFilter

load_dotenv()
LOGFILE = os.getenv('LOGFILE', 'logs/randombotapp.log').replace(chr(92), os.sep)
_configuration_lock = Lock()


def getLogger(name):
    # ファイルハンドラーを共通化し、重複出力やローテーション競合を防ぐ。
    with _configuration_lock:
        root = logging.getLogger()
        if not any(getattr(handler, "_randomwordbot_handler", False) for handler in root.handlers):
            directory = os.path.dirname(LOGFILE)
            if directory:
                os.makedirs(directory, exist_ok=True)
            formatter = logging.Formatter(
                '%(levelname)s %(asctime)s %(name)s： %(message)s%(operation_context)s'
            )
            console = logging.StreamHandler()
            file_handler = logging.handlers.RotatingFileHandler(
                LOGFILE, encoding='utf-8', maxBytes=5 * 1024 * 1024, backupCount=5,
            )
            for handler in (console, file_handler):
                handler._randomwordbot_handler = True
                handler.setFormatter(formatter)
                handler.addFilter(OperationContextFilter())
                root.addHandler(handler)
            root.setLevel(logging.INFO)
            logging.getLogger('discord').setLevel(logging.INFO)
    return logging.getLogger(name)
