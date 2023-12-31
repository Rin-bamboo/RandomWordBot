

#BOTURL
#https://discord.com/api/oauth2/authorize?client_id=1132298647288168519&permissions=8&scope=bot%20applications.commands
#https://onl.bz/Q3wpVaV

#半角英数の記号を入れるとSQLエラー

#設定ファイルの読み込み import
import os
from pickle import NONE
from dotenv import load_dotenv
load_dotenv()

#=========テキストファイルの読み込み============
import text_input

#=========discord.pyの読み込み=================
import discord
#スラッシュコマンドライブラリの読み込み
from discord import app_commands
#DB MYSQL
#import mysql.connector

#=======================ログ出力設定============================
from log_setting import getLogger
#import logging
logger = getLogger(__name__)

#==============================================
# 自分のBotのアクセストークンに置き換えてください（コンフィグファイルに退避させています）
TOKEN = os.getenv('BOT_TOKEN')        #トークン

##=====================MYSQL設定
from db_setup import DbQuery

#==============================================================
#===分割ファイルの読み込み
from button_sub import CreateButton #import CreateButton   #ボタン処理の読み込み
from view_sub import CreateView #import CreateView


#intentsオブジェクト（すべて取得）を生成
intents = discord.Intents.default()
intents.message_content = True  #メッセージインテンツの取得
intents.typing = False          #タイピングインテンツは無視
intents.presences = False       #プレゼンス(状態)インテンツは無視
intents.guilds=True             #Guild(サーバー)のインテンツの取得
intents.members = True          #メンバーインテンツの取得

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
    
logger.info("=====================================各種設定読み込み終了======================================")

@client.event
async def on_ready():
    logger.info("=====================================ボット開始処理======================================")
    try:
        view = CreateView()
        logger.info(f'We have logged in as {client.user}')
        await tree.sync()
    except Exception as ex:
       logger.warning("BOT起動でエラーが発生しました")
       logger.warning(f"エラー情報：{ex}")
    finally:
        logger.info("=====================================ボット開始処理終了======================================")

#=============================================================テストコマンドです
#コマンド読み取り
@tree.command(name = "start",description="スタートするよ！")
async def start(interaction: discord.Interaction):  
    logger.info("=====================================startコマンド取得処理======================================")
    try:
        logger.info("=====================================ＤＢ接続・各種開始ボタン表示処理開始======================================")
 
        #コマンド送信ユーザーの取得
        userId = f"{interaction.user}"
        #サーバーIDの取得
        guidId = f"{interaction.guild_id}"
        #チャンネルIDの取得
        channnelId = f"{interaction.channel_id}"
        #=====DBの準備
        queryDb = DbQuery()

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

        client.add_view(view = view)
        # メッセージにボタンを表示します
        await interaction.response.send_message(label, view=view)

    except Exception as ex:
       logger.warning(f"エラー情報：{ex}")
       await interaction.response.send_message("起動に失敗したよ！時間をおいてもう一度試してみて！")
    finally:
        
        logger.info("=====================================startコマンド処理終了======================================")


@tree.command(name="help",description="ざっくりとした説明だよ！")
async def redme_command(interaction: discord.Interaction):
    help_text = text_input.inptfile("help")
    await interaction.response.send_message(help_text)

logger.info("=====================================run処理開始======================================")
client.run(TOKEN,log_handler=None)
logger.info("=====================================run処理終了======================================")