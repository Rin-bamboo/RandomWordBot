#===分割ファイルの読み込み
from ast import Constant
from email import header
from multiprocessing import Value
import os
from unittest import result
from xmlrpc.client import boolean
from view_sub import CreateView #import CreateView
from select_sub import SelectCustom #import SelectCustom
from modal_sub import CRUDModal #import CRUDModal
from discord import Button
from bot_setting import BotSetting

import discord

from discord.ui import Button, View,TextInput,Modal,Select
from discord import File

import random

#================テーブル形式で出力
import pandas as pd

#DataFlameをimport matplotlib.pyplot as plt
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
        bot_setting = BotSetting()
        #try:
        button_custom_id = interaction.data["custom_id"]
        #コマンド送信ユーザーの取得
        userId = f"{interaction.user}"
        userName = f"{interaction.user.display_name}"
        #サーバーIDの取得
        guidId = f"{interaction.guild_id}"
        #チャンネルIDの取得
        channnelId = f"{interaction.channel_id}"
        
        bot_setting = BotSetting()
        botseq_id = bot_setting.GetBotSeq(guidId,channnelId)

        select_query = "SELECT * FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s AND start_up_flg = True"
        values = (guidId,channnelId)
        resultData = queryDb.quryexcute(select_query,values)
        
        #メッセージID
        message_id = interaction.message.id
        # target_message = await interaction.channel.fetch_message(message_id)
        #ボタンインスタンス作成
        regist_button = CreateButton(style=discord.ButtonStyle.success, label="登録", custom_id="regist_button")
        update_button = CreateButton(style=discord.ButtonStyle.primary, label="更新", custom_id="update_button")
        delete_button = CreateButton(style=discord.ButtonStyle.danger, label="削除", custom_id="delete_button")
        check_button = CreateButton(style=discord.ButtonStyle.primary, label="確認", custom_id="check_button")
        get_button = CreateButton(style=discord.ButtonStyle.gray, label="ワードゲット！", custom_id="get_button")
        commit_button = CreateButton(style=discord.ButtonStyle.gray, label="登録完了", custom_id="commit_button")  
        re_regist_button = CreateButton(style=discord.ButtonStyle.success, label="再登録", custom_id="re_regist_button")
        join_button = CreateButton(style=discord.ButtonStyle.primary, label="参加", custom_id="join_button")
        end_button = CreateButton(style=discord.ButtonStyle.danger, label="終わる？", custom_id="end_button")
        setting_button = CreateButton(style=discord.ButtonStyle.green, label="設定",custom_id="setting_button")
        setting_confirm_button = CreateButton(style=discord.ButtonStyle.gray, label="設定確認",custom_id="setting_confirm_button")

        try:
            if len(resultData) == 0 and button_custom_id != "start_button" and button_custom_id != "end_button" and button_custom_id != "setting_button":
                logger.info("開始チェック")
                await interaction.response.edit_message(content="終了しているみたい\nまた遊んでね！",view=None,delete_after=2)

            #始めるボタンが押された時の処理
            elif button_custom_id == "start_button":
                logger.info("スタートボタン処理")
                
                values = (guidId,channnelId)
                update_query="UPDATE BOTSEQTABLE SET start_up_flg = True,start_up_flg = True,start_up_time_stamp = cast(now() as datetime) WHERE guild_id = %s AND channel_id = %s"
                queryDb.quryexcute(update_query,values) 
                    
                message_view.add_item(join_button)
                message_view.add_item(end_button)
                message_view.add_item(setting_button)
                message_view.add_item(setting_confirm_button)
                
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
                #embed = discord.Embed(title="登録されているワード", description="(人''▽｀)ありがとう☆！また遊んでね！\n今日の一覧はこちら！", color=0x00ff7f)
                #BOTSEQ
                seqbotid = bot_setting.GetBotSeq(guidId,channnelId)
                
                setting_value = BotSetting().GetSettingValue(seqbotid,"Anonymous Setting")

                if setting_value == "true" :
                    select_columns = " word,create_user,use_user "
                else:
                    select_columns = "word,use_user "

                resultData = ""
                select_query = ""
                select_query = "SELECT " + select_columns + " FROM WORDTABLE WHERE botseq_id = %s AND delete_flg = False AND enable_flg = False"
                values = (botseq_id,)
                resultData = queryDb.quryexcute(select_query,values) 

                if(len(resultData) == 0):
                    await interaction.response.edit_message(content="(人''▽｀)ありがとう☆！また遊んでね\nごめんね。確認する言葉がないよ！" ,view=None)
                else:

                    await interaction.response.defer(thinking=True)

                    img_output_path  = "\output_list\output_table_" + str(seqbotid) + ".png"    #画像ファイル出力先の指定 Linuxの指定じゃないため、変な場所に画像が生成されます。
                    
                    logger.info(f"出力先ファイル：{img_output_path}")
                    
                    if setting_value == "true" :
                        resultData = [(a, b, c if c is not None else '') for a, b, c in resultData]
                        df = pd.DataFrame(resultData, columns=["登録されたワード","作った人","使った人"])
                    else :
                        resultData = [(a, b if b is not None else '') for a, b in resultData]
                        df = pd.DataFrame(resultData, columns=["登録されたワード","使った人"])

                    logger.info("==終了画面生開始==")
                    plt.figure(figsize=(8,6), dpi=150)
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
                    
                    #await target_message.delete()
                    await interaction.followup.send(content="今日のワード一覧だよ！",file=file)
                    #画像ファイルを削除
                    os.remove(img_output_path)
                    
                values = (guidId,channnelId)
                update_query = ""
                update_query = "UPDATE BOTSEQTABLE SET start_up_flg = False, start_up_time_stamp = null WHERE guild_id = %s AND channel_id = %s"
                resultData = queryDb.quryexcute(update_query,values)

                values = (botseq_id,)
                update_query = ""
                update_query = "UPDATE WORDTABLE SET enable_flg = True WHERE botseq_id = %s"
                resultData = queryDb.quryexcute(update_query,values)

                delete_query = ""
                delete_query = "DELETE FROM join_members WHERE botseq_id = %s"
                resultData = queryDb.quryexcute(delete_query,values)
                


            #やめるボタンが押された時の処理
            elif button_custom_id == 'cancel_button':
                logger.info("やめるボタン処理")
                #await interaction.message.delete()    #やめるボタンが押されたらメッセージを削除し、メッセージ表示
                await interaction.response.edit_message(content="終了したよ！",view=None,delete_after=2)

            #参加ボタンが押された時の処理
            elif button_custom_id == "join_button":
                logger.info("参加ボタン処理")
                
                #参加管理DBにデータ登録
                #参加フレーズブレンダーIDの取得
                select_query = "SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s"
                values = (guidId,channnelId)
                resultData = queryDb.quryexcute(select_query,values)
                bot_id = resultData[0][0];

                #参加済みかどうか確認
                select_query = "SELECT id,is_completion FROM join_members WHERE botseq_id = %s AND user_id = %s"
                values = (bot_id,userId)
                resultData = queryDb.quryexcute(select_query,values)
                
                #ボタン表示制御
                output_message = "好きな言葉の「登録」「更新」「削除」ができるよ！"
                if len(resultData) == 0:
                    insert_query = "INSERT INTO join_members(botseq_id,user_id) VALUES(%s,%s); "
                    values = (bot_id,userId)
                    queryDb.quryexcute(insert_query,values)
                    
                    message_view.add_item(regist_button)
                    message_view.add_item(update_button)
                    message_view.add_item(delete_button)
                    message_view.add_item(check_button)
                    #message_view.add_item(get_button)
                    message_view.add_item(commit_button)

                else:
                    if resultData[0][1] == False:
                        message_view.add_item(regist_button)
                        message_view.add_item(update_button)
                        message_view.add_item(delete_button)
                        message_view.add_item(check_button)
                        #message_view.add_item(get_button)
                        message_view.add_item(commit_button)
                        
                    else:
                        output_message = "すでに登録を完了しているよ"

                        message_view.add_item(check_button)
                        message_view.add_item(get_button)
                        message_view.add_item(re_regist_button)

                await interaction.response.send_message(output_message,view=message_view,ephemeral=True)
        
            #登録ボタン
            elif button_custom_id == "regist_button":
                logger.info("登録ボタン処理")
                
                select_query = "SELECT COUNT(*) FROM WORDTABLE WHERE botseq_id = %s AND delete_flg = 0 AND enable_flg = 0 AND create_user_id = %s"
                values = (botseq_id,userId)
                resultData = queryDb.quryexcute(select_query,values) 

                regist_cnt = resultData[0][0]
                limit_cnt = bot_setting.GetSettingValue(botseq_id,"Registration Limit")
                
                if int(regist_cnt) >= int(limit_cnt):
                    
                    await interaction.response.send_message(f'最大登録数 [{limit_cnt}] を越えました。',ephemeral=True,delete_after=2)
                    
                else:
                    regist_modal = CRUDModal(title="好きな言葉を登録しよう！")
                    regist_input = TextInput(label = "好きな言葉を入力してね",style = discord.TextStyle.short ,custom_id = "regist_input",placeholder = "言葉を入力",max_length=25,required  = True)

                    regist_modal.add_item(regist_input)
                    await interaction.response.send_modal(regist_modal)

            #更新ボタン
            elif button_custom_id == "update_button":
                logger.info("更新処理")
                updata_select = SelectCustom(placeholder="登録ワード",custom_id = "update_select")

                select_query = "SELECT id,word FROM WORDTABLE WHERE botseq_id = %s AND create_user_id = %s AND select_flg = False AND delete_flg = False AND enable_flg = False"
                values = (botseq_id,userId)
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
                select_query = "SELECT id,word FROM WORDTABLE WHERE botseq_id = %s AND create_user_id = %s AND select_flg = False AND delete_flg = False AND enable_flg = False"
                values = (botseq_id,userId)
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

                select_query = "SELECT id,word,select_flg FROM WORDTABLE WHERE botseq_id = %s AND create_user_id = %s AND delete_flg = False AND enable_flg = False"
                values = (botseq_id,userId)
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
                
                #ワード登録チェック（参加者全員が登録完了してからワードゲット可能）
                select_query = "SELECT MIN(is_completion) FROM join_members WHERE botseq_id = %s GROUP BY botseq_id"
                values = (botseq_id,)
                resultData = queryDb.quryexcute(select_query,values)
                
                if (resultData[0][0] == 0):
                    await interaction.response.send_message("まだ登録が終わっていないよ",ephemeral=True,delete_after=2)
                    return
                
                #ワードゲット処理
                embed = discord.Embed(title="あなたのワードは・・・", description="あなたのワードはこれだよ！\n面白い言葉が来たかな？", color=0x00bfff)

                select_query = "SELECT id,word FROM WORDTABLE WHERE botseq_id = %s AND select_flg = False AND delete_flg = False AND enable_flg = False"
                values = (botseq_id,)
                resultData = queryDb.quryexcute(select_query,values)

                #サーバーIDを取得
                logger.info("サーバー：" + guidId + "　ユーザー：" + userId + "によって言葉確認処理コマンドが送信されました")

                if(len(resultData) == 0):
                    await interaction.response.send_message("取得する言葉がないよ！",ephemeral=True,delete_after=2)
                    
                else:

                    get_choice = random.choice(resultData)
                    get_id = get_choice[0]
                    get_word = get_choice[1]

                    update_query = "UPDATE WORDTABLE SET select_flg = True, use_user = %s,use_user_id = %s WHERE botseq_id = %s AND id = %s"
                    values = (userName,userId,botseq_id,int(get_choice[0]))
                    resultData = queryDb.quryexcute(update_query,values)

                    embed.add_field(name="あなたのワード", value=get_word,inline=False)

                    cancel_button = CreateButton(style=discord.ButtonStyle.danger, label="閉じる", custom_id="select_cancel_button")
                    message_view.add_item(cancel_button)

                    await interaction.response.send_message(embed = embed,view=message_view ,ephemeral=True)
                    
            elif button_custom_id == "re_regist_button":
                logger.info("再登録ボタン処理")
                
                update_query = "UPDATE join_members SET is_completion = False WHERE botseq_id = %s"
                values = (botseq_id,)
                resultData = queryDb.quryexcute(update_query,values)

                
                message_view.add_item(regist_button)
                message_view.add_item(update_button)
                message_view.add_item(delete_button)
                message_view.add_item(check_button)
                #message_view.add_item(get_button)
                message_view.add_item(commit_button)
                output_message = "好きな言葉の「登録」「更新」「削除」ができるよ！"
                
                await interaction.response.edit_message(content=output_message,embed = None,view = message_view)

            elif button_custom_id == "select_cancel_button":
                logger.info("セレクト選択キャンセル処理")
                await interaction.response.edit_message(content="キャンセルしました",embed = None,view = None,delete_after=2)
                
            elif button_custom_id == "commit_button":
                logger.info("登録完了ボタンの押下")
                
                #登録完了アップデート
                update_query = "UPDATE join_members SET is_completion = True WHERE botseq_id = %s AND user_id = %s"
                values = (botseq_id,userId)
                resultData = queryDb.quryexcute(update_query,values)

                #ボタンインスタンス作成
                check_button = CreateButton(style=discord.ButtonStyle.primary, label="確認", custom_id="check_button")
                get_button = CreateButton(style=discord.ButtonStyle.gray, label="ワードゲット！", custom_id="get_button")
                re_regist_button = CreateButton(style=discord.ButtonStyle.success, label="再登録", custom_id="re_regist_button")
                message_view.add_item(check_button)
                message_view.add_item(get_button)
                message_view.add_item(re_regist_button)
                
                await interaction.response.edit_message(content="登録の完了",view = message_view)
                
            elif button_custom_id == "setting_button":
                logger.info("設定ボタンの押下")
                #BOTSEQ
                botseqId = bot_setting.GetBotSeq(guidId,channnelId)
                
                setting_info_message = bot_setting.GetSettingInfoMessage(botseqId)
                
                if setting_info_message == None:
                    await interaction.response.send_message(content="設定されていません！")
                    return 

                embed = discord.Embed(title="フレーズブレンダー設定", description="設定詳細", color=0x00ff7f)
                embed.add_field(name="設定名称：設定値", value=setting_info_message)

                setting_info = bot_setting.GetSettingInfo(botseqId)
                setting_select = SelectCustom(placeholder="設定情報",custom_id = "setting_select")
                for i in range(len(setting_info)):
                    setting_select.add_option(value=setting_info[i][2],label=setting_info[i][1],description="",)                

                message_view.add_item(setting_select)

                await interaction.response.send_message(embed=embed,view=message_view,content="設定する項目を選択してね！")
                    
                    

            elif button_custom_id == "setting_confirm_button":
                logger.info("設定確認ボタンの押下")
                #BOTSEQ
                botseqId = bot_setting.GetBotSeq(guidId,channnelId)

                setting_info_message = bot_setting.GetSettingInfoMessage(botseqId)
                
                if setting_info_message == None:
                    await interaction.response.send_message(content="設定されていません！")

                embed = discord.Embed(title="フレーズブレンダー設定", description="設定詳細", color=0x00ff7f)

                embed.add_field(name="設定名称：設定値", value=setting_info_message)
                await interaction.response.send_message(embed=embed)
                

                
            #じゃんけんモード
            # elif button_custom_id == "host_janken":
            #     await interaction.response.edit_message(content="誰がじゃんけんをする？",view = None)
                
            # elif button_custom_id == "cpu_janken":
            #     #CPUじゃんけん
            #     rock_janken = CreateButton(style=discord.ButtonStyle.primary, label="\N{Raised Fist} グー", custom_id="rock_janken")
            #     scissors_janken = CreateButton(style=discord.ButtonStyle.success, label="\N{Victory Hand} チョキ", custom_id="scissors_janken")
            #     paper_janken = CreateButton(style=discord.ButtonStyle.danger, label="\N{Raised Hand} パー", custom_id="paper_janken")
                
            #     message_view.add_item(rock_janken)
            #     message_view.add_item(scissors_janken)
            #     message_view.add_item(paper_janken)
                
            #     await interaction.response.edit_message(content="私に勝てるかな！？",view = message_view)
                
            # elif button_custom_id == "random_janken":
            #     rock_janken = CreateButton(style=discord.ButtonStyle.primary, label="\N{Raised Fist} グー", custom_id="rock_janken")
            #     scissors_janken = CreateButton(style=discord.ButtonStyle.success, label="\N{Victory Hand} チョキ", custom_id="scissors_janken")
            #     paper_janken = CreateButton(style=discord.ButtonStyle.danger, label="\N{Raised Hand} パー", custom_id="paper_janken")
                
            #     message_view.add_item(rock_janken)
            #     message_view.add_item(scissors_janken)
            #     message_view.add_item(paper_janken)
            #     await interaction.response.edit_message(content="誰かとランダムでじゃんけんをするよ！",view = message_view)
        
                
            #except Exception as Err:
            #    #print("Error, bot_id : " + bot_id + " channel_id : " + chat_id)
            #    logging.error(Err)
            
        except Exception as ex:
           logger.warning(ex)
           await interaction.response.edit_message(content="ごめんね処理に失敗したよ",embed=None,view=None,delete_after = 5)
       
        finally:
            logger.info("=====================================ボタンコールバック処理終了======================================")

    logger.info("=====================================ボタンクラス処理終了======================================")
 