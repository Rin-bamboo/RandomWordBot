#===分割ファイルの読み込み
import button_sub #import CreateButton   #ボタン処理の読み込み
import view_sub #import CreateView
import select_sub #import SelectCustom

from view_sub import CreateView #import CreateView
from modal_sub import CRUDModal
from bot_setting import BotSetting

from discord.ui import Button, View,TextInput,Modal,Select
import discord

from Model.DiscordInfo import interaction_context
from Model.RWBModel import RWBModel

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
            select_custom_id = interaction.data["custom_id"]
            selected_value = interaction.data["values"][0]
            context = interaction_context(interaction, selected_value)
            model = RWBModel()
            bot_setting = BotSetting()
            botseq_id = bot_setting.GetBotSeq(
                context.guild_id, context.channel_id
            )

            if select_custom_id == "update_select":
                #更新処理
                update_modal = CRUDModal(title="言葉を更新してね")
                update_input = TextInput(label = "好きな言葉を入力してね",style = discord.TextStyle.short ,custom_id = "update_input@" + str(selected_value) ,placeholder = "言葉を入力",max_length=25,required  = True)
                update_modal.add_item(update_input)

                await interaction.response.send_modal(update_modal)

            elif select_custom_id == "delete_select":
                model.delete_word(
                    botseq_id, context.user_id, context.selected_value
                )

                await interaction.response.edit_message(content="データを削除したよ！",view=None,delete_after=2)
                
            elif select_custom_id == "setting_select":
                #設定
                
                
                message_view = CreateView()
                #BOTSEQ
                setting_info_message = bot_setting.GetSettingInfoMessage(botseq_id)
                if setting_info_message == None:
                    await interaction.response.send_message(content="設定されていません！")
                    return

                
                setting_data = bot_setting.GetSettingsData(
                    botseq_id, selected_value
                )
                
                if setting_data[0][2] == "Anonymous Setting":
                    #匿名設定
                    setting_select = SelectCustom(placeholder="設定情報",custom_id = "anonymouse_setting")
                    
                    setting_select.add_option(value="True",label="表示する",description="",)                
                    setting_select.add_option(value="False",label="表示しない",description="",)                

                    message_view.add_item(setting_select)

                    await interaction.response.edit_message(embed=None,view=message_view,content="終了時の名前表示の設定をするよ")
                    
                elif setting_data[0][2] == "Registration Limit":
                    #登録上限設定
                    setting_modal = CRUDModal(title="フレーズブレンダーの設定をするよ！")
                    setting_input = TextInput(label = setting_data[0][0] + "の設定(1～25)",style = discord.TextStyle.short ,custom_id = "regist_limit@" + str(selected_value) ,placeholder = "設定値",required  = True)
                    setting_modal.add_item(setting_input)

                    await interaction.response.send_modal(setting_modal)
                
            elif select_custom_id == "anonymouse_setting":
                model.update_anonymous_setting(botseq_id, selected_value)

                await interaction.response.edit_message(content="変更されました",view=None,delete_after=2)


        except Exception as ex:
           logger.warning(f"エラー情報：{ex}")
           await interaction.response.edit_message(content="ごめんね処理に失敗したよ",embed=None,view=None,delete_after = 5)
        finally:
            logger.info("=====================================Selectコールバック処理終了======================================")

    logger.info("=====================================selectクラス処理終了======================================")
