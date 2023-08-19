#===分割ファイルの読み込み
import button_sub #import CreateButton   #ボタン処理の読み込み
import view_sub #import CreateView
import select_sub #import SelectCustom
from modal_sub import CRUDModal

from discord.ui import Button, View,TextInput,Modal,Select
import discord

##=====================MYSQL設定
from db_setup import DbQuery

#=======================ログ出力設定============================
from log_setting import getLogger
logger = getLogger(__name__)

#Selectのクラスを継承したクラスでtypeを変更する
class SelectCustom(Select):
    logger.info("=====================================selectクラス処理======================================")
    def __init__(self, placeholder,custom_id):
        logger.info("=====================================selectコンストラクタ処理======================================")
        super().__init__(custom_id=custom_id)
        logger.info("=====================================selectコンストラクタ処理終了======================================")

    async def callback(self, interaction: discord.Interaction):
        logger.info("=====================================Selectコールバッ処理開始======================================")
        try:
            #DB接続のクラスをインスタンス化
            queryDb = DbQuery()

            select_custom_id = interaction.data["custom_id"]
            #コマンド送信ユーザーの取得
            userId = f"{interaction.user}"
            #サーバーIDの取得
            guidId = f"{interaction.guild_id}"
            #チャンネルIDの取得
            channnelId = f"{interaction.channel_id}"

            chengeid = interaction.data["values"][0]

            if select_custom_id == "update_select":
            
                update_modal = CRUDModal(title="言葉を更新してね")
                update_input = TextInput(label = "好きな言葉を入力してね",style = discord.TextStyle.short ,custom_id = "update_input@" + str(chengeid) ,placeholder = "言葉を入力",max_length=25,required  = True)
                update_modal.add_item(update_input)

                await interaction.response.send_modal(update_modal)

            elif select_custom_id == "delete_select":
                update_query = "UPDATE WORDTABLE SET delete_flg = True WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND create_user_id = %s AND id = %s"

                values = (guidId,channnelId,userId,chengeid)
                resultData = queryDb.quryexcute(update_query,values)

                await interaction.response.edit_message(content="データを削除したよ！",view=None,delete_after=2)
        except Exception as ex:
           logger.warning(f"エラー情報：{ex}",exc_info=True)
           await interaction.response.edit_message(content="ごめんね処理に失敗したよ",embed=None,view=None,delete_after = 5)
        finally:
            logger.info("=====================================Selectコールバック処理終了======================================")

    logger.info("=====================================selectクラス処理終了======================================")
