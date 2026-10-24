

#BOTURL
#https://discord.com/api/oauth2/authorize?client_id=1132298647288168519&permissions=8&scope=bot%20applications.commands
#https://onl.bz/Q3wpVaV

#半角英数の記号を入れるとSQLエラー

#設定ファイルの読み込み import
import os
from dotenv import load_dotenv
from bot_setting import BotSetting
load_dotenv()

#=========テキストファイルの読み込み============
import text_input

#=========discord.pyの読み込み=================
import discord
#スラッシュコマンドライブラリの読み込み
from discord import app_commands
from discord.ext import tasks
from access_control import allow_interaction, enforce_blocked_guilds, leave_if_blocked, restricted_interaction
#DB MYSQL
#import mysql.connector

#=======================ログ出力設定============================
from log_setting import getLogger
from operation_log import log_event, trace_interaction
from Model.DiscordInfo import location_names
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

class RestrictedCommandTree(app_commands.CommandTree):
    async def interaction_check(self, interaction):
        return await allow_interaction(interaction)


client = discord.Client(intents=intents)
tree = RestrictedCommandTree(client)
from word_reporting import register_report_commands
register_report_commands(tree)
    
logger.info("=====================================各種設定読み込み終了======================================")


@tasks.loop(seconds=60)
async def access_sweep():
    await enforce_blocked_guilds(client)

@client.event
async def on_ready():
    logger.info("=====================================ボット開始処理======================================")
    try:
        view = CreateView()
        logger.info(f'We have logged in as {client.user}')
        await enforce_blocked_guilds(client)
        if not access_sweep.is_running():
            access_sweep.start()
        await tree.sync()
        BotSetting().SyncInstalledGuilds(client)
        BotSetting().SyncLocationNames(client)
        BotSetting().SyncMemberNames(client)
    except Exception as ex:
       logger.warning("BOT起動でエラーが発生しました")
       logger.warning(f"エラー情報：{ex}")
    finally:
        logger.info("=====================================ボット開始処理終了======================================")

@client.event
async def on_guild_join(guild):
    log_event(logger,"guild_join_received",guild_id=guild.id,guild_name=guild.name)
    try:
        if await leave_if_blocked(guild):
            return
        registered = BotSetting().RegisterInstalledGuild(guild)
        log_event(logger,"guild_join_processed",guild_id=guild.id,guild_name=guild.name,
                  registered=registered)
    except Exception:
        # イベント時に失敗しても、次回起動時の一覧同期で補完する。
        logger.exception("導入時のサーバー登録失敗 guild_id=%s",guild.id)


#=============================================================テストコマンドです
#コマンド読み取り
@tree.command(name = "start",description="スタートするよ！")
@restricted_interaction
@trace_interaction("command")
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
        
        bot_setting = BotSetting()
        names = location_names(interaction)
        select_query = "SELECT * FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s"
        values = (guidId,channnelId)
        resultData = queryDb.quryexcute(select_query,values)
            
        if (len(resultData) == 0):
            #データがいなかったら
            bot_setting.RegisterChannel(guidId,channnelId,**names)
            
            #設定をデフォルト値で作成
            seqbotid = bot_setting.GetBotSeq(guidId,channnelId,**names)
            
            select_query = "SELECT setting_id FROM settings WHERE setting_name = %s"
            values = ('Anonymous Setting',)
            setting_id = queryDb.quryexcute(select_query,values)
            
            insert_query="INSERT INTO settings_value(setting_id,botseq_id,setting_value) VALUES(%s,%s,%s)"
            values = (setting_id[0][0],seqbotid,"True")
            queryDb.quryexcute(insert_query,values)

            select_query = "SELECT setting_id FROM settings WHERE setting_name = %s"
            values = ('Registration Limit',)
            setting_id = queryDb.quryexcute(select_query,values)
            
            insert_query="INSERT INTO settings_value(setting_id,botseq_id,setting_value) VALUES(%s,%s,%s)"
            values = (setting_id[0][0],seqbotid,10)
            queryDb.quryexcute(insert_query,values)
            

        else:
            select_query = "SELECT * FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s AND start_up_flg = True"
            resultData = queryDb.quryexcute(select_query,values)
            
            seqbotid = bot_setting.GetBotSeq(guidId,channnelId,**names)
            select_query = "SELECT * FROM settings_value WHERE botseq_id = %s"
            values = (seqbotid,)
            settingResultData = queryDb.quryexcute(select_query,values)
            
            if (len(settingResultData) == 0):
                #設定をデフォルト値で作成
            
                select_query = "SELECT setting_id FROM settings WHERE setting_name = %s"
                values = ('Anonymous Setting',)
                setting_id = queryDb.quryexcute(select_query,values)
            
                insert_query="INSERT INTO settings_value(setting_id,botseq_id,setting_value) VALUES(%s,%s,%s)"
                values = (setting_id[0][0],seqbotid,"True")
                queryDb.quryexcute(insert_query,values)

                select_query = "SELECT setting_id FROM settings WHERE setting_name = %s"
                values = ('Registration Limit',)
                setting_id = queryDb.quryexcute(select_query,values)
            
                insert_query="INSERT INTO settings_value(setting_id,botseq_id,setting_value) VALUES(%s,%s,%s)"
                values = (setting_id[0][0],seqbotid,10)
                queryDb.quryexcute(insert_query,values)
        
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

            all_check_button = CreateButton(style=discord.ButtonStyle.gray, label="今日のフレーズ一覧", custom_id="all_check_button")
            label = "すでに開始されているよ！\n参加するを押すと、言葉の「登録」「変更」「削除」ができるよ \n 終わるときは「終わる？」ボタンを押してね！！"
            #viewにボタンを追加
            view.add_item(join_button)
            view.add_item(end_button)

        #設定ボタンの作成
        setting_button = CreateButton(style=discord.ButtonStyle.green, label="設定",custom_id="setting_button")
        setting_confirm_button = CreateButton(style=discord.ButtonStyle.gray, label="設定確認",custom_id="setting_confirm_button")
        view.add_item(setting_button)
        view.add_item(setting_confirm_button)
        client.add_view(view = view)
        # メッセージにボタンを表示します
        await interaction.response.send_message(label, view=view)

    except Exception as ex:
       log_event(logger, "command_failed", outcome="failed", error_type=type(ex).__name__)
       logger.exception("startコマンド処理失敗")
       await interaction.response.send_message(
           "起動に失敗したよ！時間をおいてもう一度試してみて！\n"
           "何度も失敗する場合は、公式サポートサーバーへご連絡ください。\n"
           "https://discord.gg/qsNaRFAbz2"
       )
    finally:
        
        logger.info("=====================================startコマンド処理終了======================================")


@tree.command(name="help",description="ざっくりとした説明だよ！")
@restricted_interaction
@trace_interaction("command")
async def redme_command(interaction: discord.Interaction):
    help_text = text_input.inptfile("help")
    await interaction.response.send_message(help_text)


# @tree.command(name="rps" ,description="じゃんけんするよ")
# async def rockpaperscissors(interaction: discord.Interaction):
#     # ボタンを含むView（ビュー）を作成します
#     #View（土台の作成）
#     view = CreateView()

#     host_janken = CreateButton(style=discord.ButtonStyle.danger, label="メインの人と", custom_id="host_janken")
#     random_janken = CreateButton(style=discord.ButtonStyle.primary, label="参加者の誰かと", custom_id="random_janken")
#     cpu_janken = CreateButton(style=discord.ButtonStyle.green, label="CPUと",custom_id="cpu_janken")
#     view.add_item(host_janken)
#     view.add_item(random_janken)
#     view.add_item(cpu_janken)

#     await interaction.response.send_message("誰とじゃんけんする？",view=view)

logger.info("=====================================run処理開始======================================")
client.run(TOKEN,log_handler=None)
logger.info("=====================================run処理終了======================================")
