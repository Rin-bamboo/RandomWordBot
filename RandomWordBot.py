
# -*- coding: Shift-JIS -*-

#BOTURL
#https://discord.com/api/oauth2/authorize?client_id=1132298647288168519&permissions=8&scope=bot%20applications.commands
#https://onl.bz/Q3wpVaV

#半角英数の記号を入れるとSQLエラー

#設定ファイルの読み込み import

from importlib.abc import TraversableResources
from operator import truediv
from pickle import NONE
from tarfile import RECORDSIZE
import config
import logging
import logging.handlers
#=========discord.pyの読み込み=================
from discord.ext import commands
from db_setup import DbQuery
from discord.ui import Button, View,TextInput,Modal,Select
from discord import Message,SelectOption,Guild
import discord
#スラッシュコマンドライブラリの読み込み
from discord import app_commands
#DB MYSQL
#from datetime import datetime, timedelta, timezone
#from db_setup import DB
import mysql.connector

#==============================================
# 自分のBotのアクセストークンに置き換えてください（コンフィグファイルに退避させています）
TOKEN = config.TOKEN_dev    #テストトークン
#TOKEN = config.TOKEN        #本番トークン
#=======================ログ出力設定============================
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.DEBUG)

FORMAT = '%(levelname)s %(asctime)s %(name)s： %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

#==============================================================
#sqlliteの読み込み
import sqlite3
import random
connection = sqlite3.connect(':memory:')
cursor = connection.cursor()

#table作成
#共通クエリ
#=====================MYSQL設定
db_name=config.DB
user_name=config.USER_NAME
host_name=config.HOST
user_password=config.PASS
# MySQL接続情報
db_config = {
    "host": host_name,  # ホスト名
    "user": user_name,       # ユーザ名
    "password": user_password,  # パスワード
    "database": db_name  # データベース名
}
db = NONE
connection = mysql.connector.connect(**db_config)
#==============================================================
#intentsオブジェクト（すべて取得）を生成
intents = discord.Intents.all()

client = discord.Client(intents=intents)
class Client_bot(discord.Client):
    def __init__(self,intents=intents):
        intents = discord.Intents.default()
        intents.message_content = True

        self.add_view(CreateView())

#client = Client_bot(intents=intents)
tree = app_commands.CommandTree(client)
    
logger.info("=====================================各種設定読み込み終了======================================")

#Viewを継承したクラスを作成
class CreateView(View):
    logger.info("=====================================Viewクラス処理======================================")

    def __init__(self):
        logger.info("=====================================viewコンストラクタ処理======================================")
        super().__init__(timeout=None)
        logger.info("=====================================viewコンストラクタ処理終了======================================")
    
    logger.info("=====================================Viewクラス処理終了======================================")

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

        select_query = "SELECT * FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s AND start_up_flg = True"
        values = (guidId,channnelId)
        resultData = queryDb.quryexcute(select_query,values)

        try:
            if len(resultData) == 0 and button_custom_id != "start_button" and button_custom_id != "end_button":
                logger.info("開始チェｋック")
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
                logger.info("修了確認ボタン処理")
                embed = discord.Embed(title="登録されているワード", description="(人''▽｀)ありがとう☆！また遊んでね！\n今日の一覧はこちら！", color=0x00ff7f)

                select_query = ""
                select_query = "SELECT word,create_user,use_user FROM WORDTABLE WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND delete_flg = False AND enable_flg = False"
                values = (guidId,channnelId)
                resultData = queryDb.quryexcute(select_query,values)       


                if(len(resultData) == 0):
                    await interaction.response.edit_message(content="(人''▽｀)ありがとう☆！また遊んでね\nごめんね。確認する言葉がないよ！" ,view=None)
                else:
                    value = ["","",""]
                    for data in resultData:
                        value[0] = value[0] + data[0] +"\n"
                        value[1] = value[1] + data[1] +"\n"
                        if data[2] == None:
                            value[2] = value[2] + "\n"
                        else:
                            value[2] = value[2] + data[2] +"\n"

                    embed.add_field(name="登録されたワード", value=value[0],inline=True)
                    embed.add_field(name="登録した人", value=value[1],inline=True)
                    embed.add_field(name="ワードを使った人", value=value[2],inline=True)
                    await interaction.response.edit_message(content="",embed=embed,view=None)

                update_query = ""
                update_query = "UPDATE BOTSEQTABLE SET start_up_flg = False, start_up_time_stamp = null WHERE guild_id = %s AND channel_id = %s"
                resultData = queryDb.quryexcute(update_query,values)

                update_query = ""
                update_query = "UPDATE WORDTABLE SET enable_flg = True WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s)"
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
                regist_input = TextInput(label = "好きな言葉を入力してね",style = discord.TextStyle.short ,custom_id = "regist_input",placeholder = "言葉を入力",required  = True)

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
                    await interaction.response.send_message("削除するする言葉がないよ！",ephemeral=True,delete_after=2)
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
                logging.info("サーバー：" + guidId + "　ユーザー：" + userId + "によって言葉確認処理コマンドが送信されました")

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

            #except Exception as Err:
            #    #print("Error, bot_id : " + bot_id + " channel_id : " + chat_id)
            #    logging.error(Err)
            logger.info("=====================================ボタンコールバック処理終了======================================")
        except Exception as ex:
           logging.warning(ex)
           await interaction.response.edit_message(content="処理に失敗しました。一度終了します。",embed=None,view=None,delete_after = 5)
       
        finally:
            logger.info("=====================================ボタンクラス処理終了======================================")
 
#Selectのクラスを継承したクラスでtypeを変更する
class SelectCustom(Select):
    logger.info("=====================================selectクラス処理======================================")
    def __init__(self, placeholder,custom_id):
        logger.info("=====================================selectコンストラクタ処理======================================")
        super().__init__(custom_id=custom_id)
        logger.info("=====================================selectコンストラクタ処理終了======================================")

    async def callback(self, interaction: discord.Interaction):
        logger.info("=====================================Selectコールバッ処理開始======================================")
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
            update_input = TextInput(label = "好きな言葉を入力してね",style = discord.TextStyle.short ,custom_id = "update_input@" + str(chengeid) ,placeholder = "言葉を入力",required  = True)
            update_modal.add_item(update_input)

            await interaction.response.send_modal(update_modal)

        elif select_custom_id == "delete_select":
            update_query = "UPDATE WORDTABLE SET delete_flg = True WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND create_user_id = %s AND id = %s"

            values = (guidId,channnelId,userId,chengeid)
            resultData = queryDb.quryexcute(update_query,values)

            await interaction.response.edit_message(content="データを削除したよ！",view=None,delete_after=2)
        logger.info("=====================================Selectコールバック処理終了======================================")
    logger.info("=====================================selectクラス処理終了======================================")

#モーダルクラスを継承したクラスの作成
class CRUDModal(Modal, title='Questionnaire Response'):
    logger.info("=====================================モーダルクラス処理======================================")
    async def on_submit(self, interaction: discord.Interaction):
        logger.info("=====================================モーダル送信ボタン処理開始======================================")
        #await interaction.response.send_message(f'Thanks for your response, {self.name}!', ephemeral=True)
    #コマンド送信ユーザーの取得

        userId = f"{interaction.user}"
        userName = f"{interaction.user.display_name}"
        #サーバーIDの取得
        guidId = f"{interaction.guild_id}"
        #チャンネルIDの取得
        channnelId = f"{interaction.channel_id}"

        intaraction_data = interaction.data["components"][0]["components"][0]
        regist_word = intaraction_data["value"]
        modal_custom_id = intaraction_data["custom_id"]

        #更新用IDを取得
        split_id = modal_custom_id.split('@')
        modal_custom_id = split_id[0]
        if len(split_id) > 1:
            get_data_id = split_id[1]

        #DB接続のクラスをインスタンス化
        queryDb = DbQuery()

        if len(regist_word) > 100:
            await interaction.response.send_message(f'{regist_word} \nは100文字を超えてるよ！！\n100文字以内で登録してね！', ephemeral=True,delete_after=2)

        else:

            if modal_custom_id == "regist_input":
                #登録モーダルで送信したら
                #登録処理==
                select_query = "SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s"
                values = (guidId,channnelId)
                resultData = queryDb.quryexcute(select_query,values)


                insert_query = "INSERT INTO WORDTABLE(botseq_id,word,create_user_id,create_user) VALUES( %s,%s,%s,%s);"
                values = (int(resultData[0][0]),regist_word,userId,userName);

                queryDb.quryexcute(insert_query,values);

                #==========↑↑====================

                await interaction.response.send_message(f'{regist_word} 登録できたよ！', ephemeral=True,delete_after=2)

            elif modal_custom_id == "update_input":
                #更新が選択されたら
                update_query = "UPDATE WORDTABLE SET word = %s WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND create_user_id = %s AND id = %s"

                values = (regist_word,guidId,channnelId,userId,get_data_id)
                resultData = queryDb.quryexcute(update_query,values)

                await interaction.response.edit_message(content="変更されました",view=None,delete_after=2)
        logger.info("=====================================モーダル送信ボタン処理終了======================================")
    logger.info("=====================================モーダルクラス処理終了======================================")


@client.event
async def on_ready():
    logger.info("=====================================ボット開始処理======================================")
    view = CreateView()
    logger.info(f'We have logged in as {client.user}')
    await tree.sync()
    logger.info("=====================================開始処理終了======================================")

#=============================================================テストコマンドです
#コマンド読み取り
@tree.command(name = "start",description="スタートするよ！")
async def start(interaction: discord.Interaction):  
    logger.info("=====================================startコマンド取得処理======================================")

    #コマンド送信ユーザーの取得
    userId = f"{interaction.user}"
    #サーバーIDの取得
    guidId = f"{interaction.guild_id}"
    #チャンネルIDの取得
    channnelId = f"{interaction.channel_id}"
    #=====DBの準備
    queryDb = DbQuery()

    try:
        logger.info("=====================================ＤＢ接続・各種開始ボタン表示処理開始======================================")
        #DBへ接続します。
        select_query = "SELECT * FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s AND start_up_flg = True"
        values = (guidId,channnelId)
        resultData = queryDb.quryexcute(select_query,values)
        
        # ボタンを含むView（ビュー）を作成します
        #View（土台の作成）
        view = CreateView()

        #ボットが起動しているか確認 起動していなかったら
        if len(resultData) == 0:
            #ボタンの作成 style:ボタンの種類 label:ボタンの名前 custom_id：ボタンのID
            okbutton = CreateButton(style=discord.ButtonStyle.primary, label="始める！", custom_id="start_button")
            cancelbutton = CreateButton(style=discord.ButtonStyle.danger, label="やっぱりやめる！", custom_id="cancel_button")
            #viewにボタンを追加
            view.add_item(okbutton)
            view.add_item(cancelbutton)
           
            label = "楽しい遊びを始めますか？"
            #view.start_message()

        else:
            join_button = CreateButton(style=discord.ButtonStyle.primary, label="参加", custom_id="join_button")
            end_button = CreateButton(style=discord.ButtonStyle.danger, label="終わる？", custom_id="end_button")
            all_check_button = CreateButton(style=discord.ButtonStyle.gray, label="今日のワード一覧", custom_id="all_check_button")
            label = "すでに開始されているよ！\n参加するを押すと、言葉の「登録」「変更」「削除」ができるよ \n 終わるときは「終わる？」ボタンを押してね！！"
            #viewにボタンを追加
            view.add_item(join_button)
            view.add_item(end_button)

        # メッセージにボタンを表示します
        await interaction.response.send_message(label, view=view)

    except Exception as ex:
       logging.warning(f"エラー情報：{ex}")
       await interaction.response.send_message("起動に失敗したよ！時間をおいてもう一度試してみて！")
    finally:
        client.add_view(view = view)
        logger.info("=====================================startコマンド処理終了======================================")


@tree.command(name="help",description="ざっくりとした説明だよ！")
async def redme_command(interaction: discord.Interaction):
        await interaction.response.send_message("""
/start：好きな言葉を登録開始コマンドだよ！
開始したらボタンをポチポチ押して登録したり更新したり削除したりしてね！
みんながワードの登録が終わったらワードを取得してね！
終了すると登録された誰がどのワードを登録したのか。
だれがどのワードを使ったのがが見れる一覧が表示されるよ。
削除されたデータも見れるから、気を付けてね(;'∀')
何かわからないことがあったら、リンゴまで連絡してね！
""")

logger.info("=====================================run処理開始======================================")
client.run(TOKEN,log_handler=None, log_level=logging.DEBUG)
logger.info("=====================================run処理終了======================================")