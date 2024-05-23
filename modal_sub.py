#===分割ファイルの読み込み
import button_sub #import CreateButton   #ボタン処理の読み込み
import view_sub #import CreateView
import select_sub #import SelectCustom
import modal_sub #import CRUDModal
from bot_setting import BotSetting
from discord.ui import Button, View,TextInput,Modal,Select
import discord

##=====================MYSQL設定
from db_setup import DbQuery

#=======================ログ出力設定============================
from log_setting import getLogger
logger = getLogger(__name__)


#モーダルクラスを継承したクラスの作成
class CRUDModal(Modal, title='Questionnaire Response'):
    logger.info("=====================================モーダルクラス処理======================================")
    async def on_submit(self, interaction: discord.Interaction):
        logger.info("=====================================モーダル送信ボタン処理開始======================================")
        #await interaction.response.send_message(f'Thanks for your response, {self.name}!', ephemeral=True)
    #コマンド送信ユーザーの取得
        try:
            userId = f"{interaction.user}"
            userName = f"{interaction.user.display_name}"
            #サーバーIDの取得
            guidId = f"{interaction.guild_id}"
            #チャンネルIDの取得
            channnelId = f"{interaction.channel_id}"
            
            bot_setting = BotSetting()
            botseq_id = bot_setting.GetBotSeq(guidId,channnelId)

            intaraction_data = interaction.data["components"][0]["components"][0]
            input_value = intaraction_data["value"]
            modal_custom_id = intaraction_data["custom_id"]

            #更新用IDを取得
            split_id = modal_custom_id.split('@')
            modal_custom_id = split_id[0]
            if len(split_id) > 1:
                get_data_id = split_id[1]


            #DB接続のクラスをインスタンス化
            queryDb = DbQuery()

            if len(input_value) > 100:
                await interaction.response.send_message(f'{input_value} \nは100文字を超えてるよ！！\n100文字以内で登録してね！', ephemeral=True,delete_after=2)

            else:

                if modal_custom_id == "regist_input":
                    #登録モーダルで送信したら
                    #登録処理==
                    
                    insert_query = "INSERT INTO WORDTABLE(botseq_id,word,create_user_id,create_user) VALUES( %s,%s,%s,%s);"
                    values = (botseq_id,input_value,userId,userName);

                    queryDb.quryexcute(insert_query,values);

                    #==========↑↑====================

                    await interaction.response.send_message(f'{input_value} 登録できたよ！', ephemeral=True,delete_after=2)

                elif modal_custom_id == "update_input":
                    #更新が選択されたら
                    update_query = "UPDATE WORDTABLE SET word = %s WHERE botseq_id = %s AND create_user_id = %s AND id = %s"

                    values = (input_value,botseq_id,userId,get_data_id)
                    resultData = queryDb.quryexcute(update_query,values)

                    await interaction.response.edit_message(content="変更されました",view=None,delete_after=2)
                    
                elif modal_custom_id == "regist_limit":
                    
                    #文字チェック
                    intcheck = bot_setting.CanConvertToInt(input_value)
                    if intcheck == False:
                        await interaction.response.send_message(f'{input_value} \nは数字じゃないよ！数字を入力してね！', ephemeral=True,delete_after=2)
                    else:
                        if 0 < intcheck & intcheck <= 25:
                            
                            update_query = "UPDATE settings_value JOIN settings ON  settings_value.setting_id = settings.setting_id SET settings_value.setting_value = %s WHERE settings.setting_name = 'Registration Limit' AND  botseq_id = %s ;"
                
                            values = (intcheck,botseq_id)
                            queryDb.quryexcute(update_query,values)
                        
                            await interaction.response.edit_message(content="変更されました",view=None,delete_after=2)
                        else:
                            await interaction.response.send_message(f'{input_value} \n 1 ～ 25の間で設定してね', ephemeral=True,delete_after=2)
                            
        except Exception as ex:
            logger.warning(f"エラー情報：{ex}")
            await interaction.response.edit_message(content="ごめんね処理に失敗したよ",embed=None,view=None,delete_after = 5)
        finally:
            logger.info("=====================================モーダル送信ボタン処理終了======================================")

    logger.info("=====================================モーダルクラス処理終了======================================")
