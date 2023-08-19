
import os
#===分割ファイルの読み込み
from unittest import result
from view_sub import CreateView #import CreateView
from select_sub import SelectCustom #import SelectCustom
from modal_sub import CRUDModal #import CRUDModal
from discord import Button
import discord

from discord.ui import Button, View,TextInput,Modal,Select
from discord import File

import random

#================テーブル形式で出力
import pandas as pd
#pip install pandas

#pip install matplotlib
#pip install japanize-matplotlib

import japanize_matplotlib
import matplotlib.pyplot as plt
##=====================MYSQL設定
from db_setup import DbQuery

#=======================ログ出力設定============================
from log_setting import getLogger
logger = getLogger(__name__)

#discord.ui.buttonを継承し callbackをオーバーライド！
class CreateButton(Button):
    logger.info("=====================================ボタン作成クラス処理======================================")

    async def callback(self, interaction: discord.Interaction):
        logger.info("=====================================ボタンコールバック処理======================================")
        #DB接続のクラスをインスタンス化
        queryDb = DbQuery()
        message_view = CreateView()
        #try:
        button_custom_id = interaction.data["custom_id"]
        #コマンド送信ユーザーの取得
        userId = f"{interaction.user}"
        userName = f"{interaction.user.display_name}"
        #サーバーIDの取得
        guidId = f"{interaction.guild_id}"
        #チャンネルIDの取得
        channnelId = f"{interaction.channel_id}"


        try:

            select_query = "SELECT * FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s AND start_up_flg = True"
            values = (guidId,channnelId)
            resultData = queryDb.quryexcute(select_query,values)

            if len(resultData) == 0 and button_custom_id != "start_button" and button_custom_id != "end_button":
                logger.info("開始チェック")
                await interaction.response.edit_message(content="終了しているみたい\nまた遊んでね！",view=None,delete_after=2)

            #始めるボタンが押された時の処理
            elif button_custom_id == "start_button":
                logger.info("スタートボタン処理")
                select_query = "SELECT * FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s"
                values = (guidId,channnelId)
                resultData = queryDb.quryexcute(select_query,values)
            
                if (len(resultData) == 0):
                    #データがいなかったら
                    insert_query="INSERT INTO BOTSEQTABLE(guild_id,channel_id,start_up_flg,start_up_time_stamp) VALUES(%s,%s,True,cast(now() as datetime))"
                    queryDb.quryexcute(insert_query,values)

                else:
                    update_query="UPDATE BOTSEQTABLE SET start_up_flg = True,start_up_flg = True,start_up_time_stamp = cast(now() as datetime) WHERE guild_id = %s AND channel_id = %s"
                    queryDb.quryexcute(update_query,values) 
    
                join_button = CreateButton(style=discord.ButtonStyle.primary, label="参加", custom_id="join_button")
                end_button = CreateButton(style=discord.ButtonStyle.danger, label="終わる？", custom_id="end_button")

                message_view.add_item(join_button)
                message_view.add_item(end_button)
                await interaction.response.edit_message(content="参加するを押すと、言葉の「登録」「変更」「削除」ができるよ \n 終わるときは「終わる？」ボタンを押してね！！",view=message_view)
                #await message.edit("参加するを押すと、言葉の「登録」「変更」「削除」ができるよ",view=start_view)

            elif button_custom_id == "end_button":
                logger.info("終了ボタン処理")
                #スタート後の確認
                start_button = CreateButton(style=discord.ButtonStyle.primary, label="まだ終わらない！", custom_id="start_button")
                final_end_button = CreateButton(style=discord.ButtonStyle.danger, label="終わるよ！", custom_id="final_end_button")
            
                message_view.add_item(start_button)
                message_view.add_item(final_end_button)

                await interaction.response.edit_message(content="本当に終わる？",view=message_view)

            #最終終了ボタンが押されたら
            elif button_custom_id == "final_end_button":
                #await interaction.message.delete()    #やめるボタンが押されたらメッセージを削除し、メッセージ表示
                logger.info("終了確認ボタン処理")
                embed = discord.Embed(title="登録されているワード", description="(人''▽｀)ありがとう☆！また遊んでね！\n今日の一覧はこちら！", color=0x00ff7f)
                
                select_query = "SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s"
                values = (guidId,channnelId)
                resultData = queryDb.quryexcute(select_query,values)   
                seqbotid = int(resultData[0][0])

                values = (seqbotid,)
                select_query = ""
                select_query = "SELECT word,create_user,use_user FROM WORDTABLE WHERE botseq_id = %s AND delete_flg = False AND enable_flg = False"
                resultData = queryDb.quryexcute(select_query,values)

                logger.info("==終了画面生成==")
                if(len(resultData) == 0):
                    await interaction.response.edit_message(content="(人''▽｀)ありがとう☆！また遊んでね\nごめんね。確認する言葉がないよ！" ,view=None)
                else:
                    #メッセージID
                    message_id = interaction.message.id
                    target_message = await interaction.channel.fetch_message(message_id)
                    await interaction.response.defer(thinking=True)

                    #Noneを空白に変換
                    img_output_path  = f"output_list\\output_table_{seqbotid}.png"   #画像ファイル出力先の指定

                    resultData = [(a, b, c if c is not None else '') for a, b, c in resultData]
                    df = pd.DataFrame(resultData, columns=["登録されたワード","作った人","使った人"])

                    plt.figure(figsize=(8,6), dpi=1000)
                    ax = plt.gca()
                    ax.axis('off')

                    ## DataFrameをテーブルとして描画
                    table_data = []
                    for row in df.itertuples(index=False):
                        table_data.append(list(row))
                    #表のフォントサイズを指定
                    font_size = 16
                    table = ax.table(cellText=table_data, colLabels=df.columns, cellLoc='center', loc='center', colColours=['lightgray'] * len(df.columns),fontsize=font_size)

                    # 画像を保存
                    plt.savefig(img_output_path, bbox_inches='tight', pad_inches=0.1, transparent=True)

                    file = File(img_output_path)
                    logger.info("==終了画面生成終了==")
                    await target_message.delete()
                    await interaction.followup.send(content="今日のワード一覧だよ！",file=file)
                    os.remove(img_output_path)
                    #await interaction.response.send_message(content=df)

                update_query = ""
                update_query = "UPDATE BOTSEQTABLE SET start_up_flg = False, start_up_time_stamp = null WHERE id = %s"
                resultData = queryDb.quryexcute(update_query,values)

                update_query = ""
                update_query = "UPDATE WORDTABLE SET enable_flg = True WHERE botseq_id = %s"
                resultData = queryDb.quryexcute(update_query,values)

                

            #やめるボタンが押された時の処理
            elif button_custom_id == 'cancel_button':
                logger.info("やめるボタン処理")
                #await interaction.message.delete()    #やめるボタンが押されたらメッセージを削除し、メッセージ表示
                await interaction.response.edit_message(content="終了したよ！",view=None,delete_after=2)

            #参加ボタンが押された時の処理
            elif button_custom_id == "join_button":
                logger.info("参加ボタン処理")
                regist_button = CreateButton(style=discord.ButtonStyle.success, label="登録", custom_id="regist_button")
                update_button = CreateButton(style=discord.ButtonStyle.primary, label="更新", custom_id="update_button")
                delete_button = CreateButton(style=discord.ButtonStyle.danger, label="削除", custom_id="delete_button")
                check_button = CreateButton(style=discord.ButtonStyle.primary, label="確認", custom_id="check_button")
                get_button = CreateButton(style=discord.ButtonStyle.gray, label="ワードゲット！", custom_id="get_button")
                exit_button = CreateButton(style=discord.ButtonStyle.gray, label="登録を終わる", custom_id="exit_button")
            
                message_view.add_item(regist_button)
                message_view.add_item(update_button)
                message_view.add_item(delete_button)
                message_view.add_item(check_button)
                message_view.add_item(get_button)

                await interaction.response.send_message("好きな言葉の「登録」「更新」「削除」ができるよ！",view=message_view,ephemeral=True)
        
            #登録ボタン
            elif button_custom_id == "regist_button":
                logger.info("登録ボタン処理")
                regist_modal = CRUDModal(title="好きな言葉を登録しよう！")
                regist_input = TextInput(label = "好きな言葉を入力してね",style = discord.TextStyle.short ,custom_id = "regist_input",placeholder = "言葉を入力",max_length=25,required  = True)

                regist_modal.add_item(regist_input)
                await interaction.response.send_modal(regist_modal)

            #更新ボタン
            elif button_custom_id == "update_button":
                logger.info("更新処理")
                updata_select = SelectCustom(placeholder="登録ワード",custom_id = "update_select")

                select_query = "SELECT id,word FROM WORDTABLE WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND create_user_id = %s AND select_flg = False AND delete_flg = False AND enable_flg = False"
                values = (guidId,channnelId,userId)
                resultData = queryDb.quryexcute(select_query,values)
                if(len(resultData) == 0):
                    await interaction.response.send_message("更新する言葉がないよ！",ephemeral=True,delete_after=2)
                else:
                    output_message = ""
                    for i in range(len(resultData)):

                        updata_select.add_option(value=resultData[i][0],label=resultData[i][1],description="",)

                    cancel_button = CreateButton(style=discord.ButtonStyle.danger, label="キャンセル", custom_id="select_cancel_button")
                    message_view.add_item(updata_select)
                    message_view.add_item(cancel_button)

                    await interaction.response.send_message("更新する言葉を選んでね！", view=message_view,ephemeral  = True)

            #削除ボタン
            elif button_custom_id == "delete_button":
                logger.info("削除ボタン処理")
                delete_select = SelectCustom(placeholder="登録ワード",custom_id = "delete_select")
                #===============
                select_query = "SELECT id,word FROM WORDTABLE WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND create_user_id = %s AND select_flg = False AND delete_flg = False AND enable_flg = False"
                values = (guidId,channnelId,userId)
                resultData = queryDb.quryexcute(select_query,values)

                if(len(resultData) == 0):
                    await interaction.response.send_message("削除する言葉がないよ！",ephemeral=True,delete_after=2)
                else:
                    output_message = ""
                    for i in range(len(resultData)):

                        delete_select.add_option(value=resultData[i][0],label=resultData[i][1],description="",)
                #================================================
                    cancel_button = CreateButton(style=discord.ButtonStyle.danger, label="キャンセル", custom_id="select_cancel_button")
                    message_view.add_item(delete_select)
                    message_view.add_item(cancel_button)

                    await interaction.response.send_message("削除する言葉を選んでね！", view=message_view,ephemeral  = True)


            #確認ボタンが押されたら
            elif button_custom_id == "check_button":
                logger.info("確認ボタン処理")
                embed = discord.Embed(title="あなたの登録したワード", description="あなたの登録したワードを確認するよ！", color=0xd2691e)

                select_query = "SELECT id,word,select_flg FROM WORDTABLE WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND create_user_id = %s AND delete_flg = False AND enable_flg = False"
                values = (guidId,channnelId,userId)
                resultData = queryDb.quryexcute(select_query,values)

                if(len(resultData) == 0):
                    await interaction.response.send_message("確認する言葉がないよ！",ephemeral=True,delete_after=2)
                else:
                    output_message = ""
                    for i in range(len(resultData)):
                        output_message = output_message + str(i + 1) + "：" + resultData[i][1] + "　"
                        if resultData[i][2] == 1:
                            output_message = output_message + "すでに誰かが使ったみたい！"
                        output_message = output_message + "\n"

                    embed.add_field(name="登録したワード", value=output_message)
                
                    cancel_button = CreateButton(style=discord.ButtonStyle.danger, label="閉じる", custom_id="select_cancel_button")
                    message_view.add_item(cancel_button)
                    await interaction.response.send_message(embed=embed,view=message_view,ephemeral  = True)

            #言葉ゲット！！
            elif button_custom_id == "get_button":
                logger.info("ワードゲットボタン処理")
                embed = discord.Embed(title="あなたのワードは・・・", description="あなたのワードはこれだよ！\n面白い言葉が来たかな？", color=0x00bfff)

                select_query = "SELECT id,word FROM WORDTABLE WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND select_flg = False AND delete_flg = False AND enable_flg = False"
                values = (guidId,channnelId)
                resultData = queryDb.quryexcute(select_query,values)

                #サーバーIDを取得
                logger.info("サーバー：" + guidId + "　ユーザー：" + userId + "によって言葉確認処理コマンドが送信されました")

                if(len(resultData) == 0):
                    await interaction.response.send_message("取得する言葉がないよ！",ephemeral=True,delete_after=2)
                else:

                    get_choice = random.choice(resultData)
                    get_id = get_choice[0]
                    get_word = get_choice[1]

                    update_query = "UPDATE WORDTABLE SET select_flg = True, use_user = %s,use_user_id = %s WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND id = %s"
                    values = (userName,userId,guidId,channnelId,int(get_choice[0]))
                    resultData = queryDb.quryexcute(update_query,values)

                    embed.add_field(name="あなたのワード", value=get_word,inline=False)

                    cancel_button = CreateButton(style=discord.ButtonStyle.danger, label="閉じる", custom_id="select_cancel_button")
                    message_view.add_item(cancel_button)

                    await interaction.response.send_message(embed = embed,view=message_view ,ephemeral=True)

            elif button_custom_id == "select_cancel_button":
                logger.info("セレクト選択キャンセル処理")
                await interaction.response.edit_message(content="キャンセルしました",embed = None,view = None,delete_after=2)
            
        except discord.DiscordException as ex:
           logger.warning(f"DiscordException：{ex}",exc_info=True)
        except discord.ClientException as ex:
           logger.warning(f"ClientException：{ex}",exc_info=True)
        except discord.HTTPException as ex:
            logger.warning(f"HTTPException：{ex}",exc_info=True)
        except Exception as ex:
           logger.warning(f"エラー情報：{ex}",exc_info=True)
           await interaction.response.edit_message(content="ごめんね処理に失敗したよ",embed=None,view=None,delete_after = 5)


        finally:
            logger.info("=====================================ボタンコールバック処理終了======================================")

    logger.info("=====================================ボタンクラス処理終了======================================")
 