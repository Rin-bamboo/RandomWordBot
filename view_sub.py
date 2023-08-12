from discord.ui import Button, View,TextInput,Modal,Select


#=======================ログ出力設定============================
from log_setting import getLogger
logger = getLogger(__name__)

#Viewを継承したクラスを作成
class CreateView(View):
    logger.info("=====================================Viewクラス処理======================================")

    def __init__(self):
        logger.info("=====================================viewコンストラクタ処理======================================")
        super().__init__(timeout=None)
        logger.info("=====================================viewコンストラクタ処理終了======================================")
    
    logger.info("=====================================Viewクラス処理終了======================================")