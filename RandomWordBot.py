
# -*- coding: Shift-JIS -*-

#BOTURL
#https://discord.com/api/oauth2/authorize?client_id=1132298647288168519&permissions=8&scope=bot%20applications.commands
#https://onl.bz/Q3wpVaV

#���p�p���̋L���������SQL�G���[

#�ݒ�t�@�C���̓ǂݍ��� import

from importlib.abc import TraversableResources
from operator import truediv
from pickle import NONE
from tarfile import RECORDSIZE
import config
import logging
import logging.handlers
#=========discord.py�̓ǂݍ���=================
from discord.ext import commands
from db_setup import DbQuery
from discord.ui import Button, View,TextInput,Modal,Select
from discord import Message,SelectOption,Guild
import discord
#�X���b�V���R�}���h���C�u�����̓ǂݍ���
from discord import app_commands
#DB MYSQL
#from datetime import datetime, timedelta, timezone
#from db_setup import DB
import mysql.connector

#==============================================
# ������Bot�̃A�N�Z�X�g�[�N���ɒu�������Ă��������i�R���t�B�O�t�@�C���ɑޔ������Ă��܂��j
TOKEN = config.TOKEN_dev    #�e�X�g�g�[�N��
#TOKEN = config.TOKEN        #�{�ԃg�[�N��
#=======================���O�o�͐ݒ�============================
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.DEBUG)

FORMAT = '%(levelname)s %(asctime)s %(name)s�F %(message)s'
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
#sqllite�̓ǂݍ���
import sqlite3
import random
connection = sqlite3.connect(':memory:')
cursor = connection.cursor()

#table�쐬
#���ʃN�G��
#=====================MYSQL�ݒ�
db_name=config.DB
user_name=config.USER_NAME
host_name=config.HOST
user_password=config.PASS
# MySQL�ڑ����
db_config = {
    "host": host_name,  # �z�X�g��
    "user": user_name,       # ���[�U��
    "password": user_password,  # �p�X���[�h
    "database": db_name  # �f�[�^�x�[�X��
}
db = NONE
connection = mysql.connector.connect(**db_config)
#==============================================================
#intents�I�u�W�F�N�g�i���ׂĎ擾�j�𐶐�
intents = discord.Intents.all()

client = discord.Client(intents=intents)
class Client_bot(discord.Client):
    def __init__(self,intents=intents):
        intents = discord.Intents.default()
        intents.message_content = True

        self.add_view(CreateView())

#client = Client_bot(intents=intents)
tree = app_commands.CommandTree(client)
    
logger.info("=====================================�e��ݒ�ǂݍ��ݏI��======================================")

#View���p�������N���X���쐬
class CreateView(View):
    logger.info("=====================================View�N���X����======================================")

    def __init__(self):
        logger.info("=====================================view�R���X�g���N�^����======================================")
        super().__init__(timeout=None)
        logger.info("=====================================view�R���X�g���N�^�����I��======================================")
    
    logger.info("=====================================View�N���X�����I��======================================")

#discord.ui.button���p���� callback���I�[�o�[���C�h�I
class CreateButton(Button):
    logger.info("=====================================�{�^���쐬�N���X����======================================")

    async def callback(self, interaction: discord.Interaction):
        logger.info("=====================================�{�^���R�[���o�b�N����======================================")
        #DB�ڑ��̃N���X���C���X�^���X��
        queryDb = DbQuery()
        message_view = CreateView()
        #try:
        button_custom_id = interaction.data["custom_id"]
        #�R�}���h���M���[�U�[�̎擾
        userId = f"{interaction.user}"
        userName = f"{interaction.user.display_name}"
        #�T�[�o�[ID�̎擾
        guidId = f"{interaction.guild_id}"
        #�`�����l��ID�̎擾
        channnelId = f"{interaction.channel_id}"

        select_query = "SELECT * FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s AND start_up_flg = True"
        values = (guidId,channnelId)
        resultData = queryDb.quryexcute(select_query,values)

        try:
            if len(resultData) == 0 and button_custom_id != "start_button" and button_custom_id != "end_button":
                logger.info("�J�n�`�F���b�N")
                await interaction.response.edit_message(content="�I�����Ă���݂���\n�܂��V��łˁI",view=None,delete_after=2)

            #�n�߂�{�^���������ꂽ���̏���
            elif button_custom_id == "start_button":
                logger.info("�X�^�[�g�{�^������")
                select_query = "SELECT * FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s"
                values = (guidId,channnelId)
                resultData = queryDb.quryexcute(select_query,values)
            
                if (len(resultData) == 0):
                    #�f�[�^�����Ȃ�������
                    insert_query="INSERT INTO BOTSEQTABLE(guild_id,channel_id,start_up_flg,start_up_time_stamp) VALUES(%s,%s,True,cast(now() as datetime))"
                    queryDb.quryexcute(insert_query,values)

                else:
                    update_query="UPDATE BOTSEQTABLE SET start_up_flg = True,start_up_flg = True,start_up_time_stamp = cast(now() as datetime) WHERE guild_id = %s AND channel_id = %s"
                    queryDb.quryexcute(update_query,values) 
    
                join_button = CreateButton(style=discord.ButtonStyle.primary, label="�Q��", custom_id="join_button")
                end_button = CreateButton(style=discord.ButtonStyle.danger, label="�I���H", custom_id="end_button")

                message_view.add_item(join_button)
                message_view.add_item(end_button)
                await interaction.response.edit_message(content="�Q������������ƁA���t�́u�o�^�v�u�ύX�v�u�폜�v���ł���� \n �I���Ƃ��́u�I���H�v�{�^���������ĂˁI�I",view=message_view)
                #await message.edit("�Q������������ƁA���t�́u�o�^�v�u�ύX�v�u�폜�v���ł����",view=start_view)

            elif button_custom_id == "end_button":
                logger.info("�I���{�^������")
                #�X�^�[�g��̊m�F
                start_button = CreateButton(style=discord.ButtonStyle.primary, label="�܂��I���Ȃ��I", custom_id="start_button")
                final_end_button = CreateButton(style=discord.ButtonStyle.danger, label="�I����I", custom_id="final_end_button")
            
                message_view.add_item(start_button)
                message_view.add_item(final_end_button)

                await interaction.response.edit_message(content="�{���ɏI���H",view=message_view)

            #�ŏI�I���{�^���������ꂽ��
            elif button_custom_id == "final_end_button":
                #await interaction.message.delete()    #��߂�{�^���������ꂽ�烁�b�Z�[�W���폜���A���b�Z�[�W�\��
                logger.info("�C���m�F�{�^������")
                embed = discord.Embed(title="�o�^����Ă��郏�[�h", description="(�l''���M)���肪�Ƃ����I�܂��V��łˁI\n�����̈ꗗ�͂�����I", color=0x00ff7f)

                select_query = ""
                select_query = "SELECT word,create_user,use_user FROM WORDTABLE WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND delete_flg = False AND enable_flg = False"
                values = (guidId,channnelId)
                resultData = queryDb.quryexcute(select_query,values)       


                if(len(resultData) == 0):
                    await interaction.response.edit_message(content="(�l''���M)���肪�Ƃ����I�܂��V��ł�\n���߂�ˁB�m�F���錾�t���Ȃ���I" ,view=None)
                else:
                    value = ["","",""]
                    for data in resultData:
                        value[0] = value[0] + data[0] +"\n"
                        value[1] = value[1] + data[1] +"\n"
                        if data[2] == None:
                            value[2] = value[2] + "\n"
                        else:
                            value[2] = value[2] + data[2] +"\n"

                    embed.add_field(name="�o�^���ꂽ���[�h", value=value[0],inline=True)
                    embed.add_field(name="�o�^�����l", value=value[1],inline=True)
                    embed.add_field(name="���[�h���g�����l", value=value[2],inline=True)
                    await interaction.response.edit_message(content="",embed=embed,view=None)

                update_query = ""
                update_query = "UPDATE BOTSEQTABLE SET start_up_flg = False, start_up_time_stamp = null WHERE guild_id = %s AND channel_id = %s"
                resultData = queryDb.quryexcute(update_query,values)

                update_query = ""
                update_query = "UPDATE WORDTABLE SET enable_flg = True WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s)"
                resultData = queryDb.quryexcute(update_query,values)

            #��߂�{�^���������ꂽ���̏���
            elif button_custom_id == 'cancel_button':
                logger.info("��߂�{�^������")
                #await interaction.message.delete()    #��߂�{�^���������ꂽ�烁�b�Z�[�W���폜���A���b�Z�[�W�\��
                await interaction.response.edit_message(content="�I��������I",view=None,delete_after=2)

            #�Q���{�^���������ꂽ���̏���
            elif button_custom_id == "join_button":
                logger.info("�Q���{�^������")
                regist_button = CreateButton(style=discord.ButtonStyle.success, label="�o�^", custom_id="regist_button")
                update_button = CreateButton(style=discord.ButtonStyle.primary, label="�X�V", custom_id="update_button")
                delete_button = CreateButton(style=discord.ButtonStyle.danger, label="�폜", custom_id="delete_button")
                check_button = CreateButton(style=discord.ButtonStyle.primary, label="�m�F", custom_id="check_button")
                get_button = CreateButton(style=discord.ButtonStyle.gray, label="���[�h�Q�b�g�I", custom_id="get_button")
                exit_button = CreateButton(style=discord.ButtonStyle.gray, label="�o�^���I���", custom_id="exit_button")
            
                message_view.add_item(regist_button)
                message_view.add_item(update_button)
                message_view.add_item(delete_button)
                message_view.add_item(check_button)
                message_view.add_item(get_button)

                await interaction.response.send_message("�D���Ȍ��t�́u�o�^�v�u�X�V�v�u�폜�v���ł����I",view=message_view,ephemeral=True)
        
            #�o�^�{�^��
            elif button_custom_id == "regist_button":
                logger.info("�o�^�{�^������")
                regist_modal = CRUDModal(title="�D���Ȍ��t��o�^���悤�I")
                regist_input = TextInput(label = "�D���Ȍ��t����͂��Ă�",style = discord.TextStyle.short ,custom_id = "regist_input",placeholder = "���t�����",required  = True)

                regist_modal.add_item(regist_input)
                await interaction.response.send_modal(regist_modal)

            #�X�V�{�^��
            elif button_custom_id == "update_button":
                logger.info("�X�V����")
                updata_select = SelectCustom(placeholder="�o�^���[�h",custom_id = "update_select")

                select_query = "SELECT id,word FROM WORDTABLE WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND create_user_id = %s AND select_flg = False AND delete_flg = False AND enable_flg = False"
                values = (guidId,channnelId,userId)
                resultData = queryDb.quryexcute(select_query,values)
                if(len(resultData) == 0):
                    await interaction.response.send_message("�X�V���錾�t���Ȃ���I",ephemeral=True,delete_after=2)
                else:
                    output_message = ""
                    for i in range(len(resultData)):

                        updata_select.add_option(value=resultData[i][0],label=resultData[i][1],description="",)

                    cancel_button = CreateButton(style=discord.ButtonStyle.danger, label="�L�����Z��", custom_id="select_cancel_button")
                    message_view.add_item(updata_select)
                    message_view.add_item(cancel_button)

                    await interaction.response.send_message("�X�V���錾�t��I��łˁI", view=message_view,ephemeral  = True)

            #�폜�{�^��
            elif button_custom_id == "delete_button":
                logger.info("�폜�{�^������")
                delete_select = SelectCustom(placeholder="�o�^���[�h",custom_id = "delete_select")
                #===============
                select_query = "SELECT id,word FROM WORDTABLE WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND create_user_id = %s AND select_flg = False AND delete_flg = False AND enable_flg = False"
                values = (guidId,channnelId,userId)
                resultData = queryDb.quryexcute(select_query,values)

                if(len(resultData) == 0):
                    await interaction.response.send_message("�폜���邷�錾�t���Ȃ���I",ephemeral=True,delete_after=2)
                else:
                    output_message = ""
                    for i in range(len(resultData)):

                        delete_select.add_option(value=resultData[i][0],label=resultData[i][1],description="",)
                #================================================
                    cancel_button = CreateButton(style=discord.ButtonStyle.danger, label="�L�����Z��", custom_id="select_cancel_button")
                    message_view.add_item(delete_select)
                    message_view.add_item(cancel_button)

                    await interaction.response.send_message("�폜���錾�t��I��łˁI", view=message_view,ephemeral  = True)


            #�m�F�{�^���������ꂽ��
            elif button_custom_id == "check_button":
                logger.info("�m�F�{�^������")
                embed = discord.Embed(title="���Ȃ��̓o�^�������[�h", description="���Ȃ��̓o�^�������[�h���m�F�����I", color=0xd2691e)

                select_query = "SELECT id,word,select_flg FROM WORDTABLE WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND create_user_id = %s AND delete_flg = False AND enable_flg = False"
                values = (guidId,channnelId,userId)
                resultData = queryDb.quryexcute(select_query,values)

                if(len(resultData) == 0):
                    await interaction.response.send_message("�m�F���錾�t���Ȃ���I",ephemeral=True,delete_after=2)
                else:
                    output_message = ""
                    for i in range(len(resultData)):
                        output_message = output_message + str(i + 1) + "�F" + resultData[i][1] + "�@"
                        if resultData[i][2] == 1:
                            output_message = output_message + "���łɒN�����g�����݂����I"
                        output_message = output_message + "\n"

                    embed.add_field(name="�o�^�������[�h", value=output_message)
                
                    cancel_button = CreateButton(style=discord.ButtonStyle.danger, label="����", custom_id="select_cancel_button")
                    message_view.add_item(cancel_button)
                    await interaction.response.send_message(embed=embed,view=message_view,ephemeral  = True)

            #���t�Q�b�g�I�I
            elif button_custom_id == "get_button":
                logger.info("���[�h�Q�b�g�{�^������")
                embed = discord.Embed(title="���Ȃ��̃��[�h�́E�E�E", description="���Ȃ��̃��[�h�͂��ꂾ��I\n�ʔ������t���������ȁH", color=0x00bfff)

                select_query = "SELECT id,word FROM WORDTABLE WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND select_flg = False AND delete_flg = False AND enable_flg = False"
                values = (guidId,channnelId)
                resultData = queryDb.quryexcute(select_query,values)

                #�T�[�o�[ID���擾
                logging.info("�T�[�o�[�F" + guidId + "�@���[�U�[�F" + userId + "�ɂ���Č��t�m�F�����R�}���h�����M����܂���")

                if(len(resultData) == 0):
                    await interaction.response.send_message("�擾���錾�t���Ȃ���I",ephemeral=True,delete_after=2)
                else:

                    get_choice = random.choice(resultData)
                    get_id = get_choice[0]
                    get_word = get_choice[1]

                    update_query = "UPDATE WORDTABLE SET select_flg = True, use_user = %s,use_user_id = %s WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND id = %s"
                    values = (userName,userId,guidId,channnelId,int(get_choice[0]))
                    resultData = queryDb.quryexcute(update_query,values)

                    embed.add_field(name="���Ȃ��̃��[�h", value=get_word,inline=False)

                    cancel_button = CreateButton(style=discord.ButtonStyle.danger, label="����", custom_id="select_cancel_button")
                    message_view.add_item(cancel_button)

                    await interaction.response.send_message(embed = embed,view=message_view ,ephemeral=True)

            elif button_custom_id == "select_cancel_button":
                logger.info("�Z���N�g�I���L�����Z������")
                await interaction.response.edit_message(content="�L�����Z�����܂���",embed = None,view = None,delete_after=2)

            #except Exception as Err:
            #    #print("Error, bot_id : " + bot_id + " channel_id : " + chat_id)
            #    logging.error(Err)
            logger.info("=====================================�{�^���R�[���o�b�N�����I��======================================")
        except Exception as ex:
           logging.warning(ex)
           await interaction.response.edit_message(content="�����Ɏ��s���܂����B��x�I�����܂��B",embed=None,view=None,delete_after = 5)
       
        finally:
            logger.info("=====================================�{�^���N���X�����I��======================================")
 
#Select�̃N���X���p�������N���X��type��ύX����
class SelectCustom(Select):
    logger.info("=====================================select�N���X����======================================")
    def __init__(self, placeholder,custom_id):
        logger.info("=====================================select�R���X�g���N�^����======================================")
        super().__init__(custom_id=custom_id)
        logger.info("=====================================select�R���X�g���N�^�����I��======================================")

    async def callback(self, interaction: discord.Interaction):
        logger.info("=====================================Select�R�[���o�b�����J�n======================================")
        #DB�ڑ��̃N���X���C���X�^���X��
        queryDb = DbQuery()

        select_custom_id = interaction.data["custom_id"]
        #�R�}���h���M���[�U�[�̎擾
        userId = f"{interaction.user}"
        #�T�[�o�[ID�̎擾
        guidId = f"{interaction.guild_id}"
        #�`�����l��ID�̎擾
        channnelId = f"{interaction.channel_id}"

        chengeid = interaction.data["values"][0]

        if select_custom_id == "update_select":
            
            update_modal = CRUDModal(title="���t���X�V���Ă�")
            update_input = TextInput(label = "�D���Ȍ��t����͂��Ă�",style = discord.TextStyle.short ,custom_id = "update_input@" + str(chengeid) ,placeholder = "���t�����",required  = True)
            update_modal.add_item(update_input)

            await interaction.response.send_modal(update_modal)

        elif select_custom_id == "delete_select":
            update_query = "UPDATE WORDTABLE SET delete_flg = True WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND create_user_id = %s AND id = %s"

            values = (guidId,channnelId,userId,chengeid)
            resultData = queryDb.quryexcute(update_query,values)

            await interaction.response.edit_message(content="�f�[�^���폜������I",view=None,delete_after=2)
        logger.info("=====================================Select�R�[���o�b�N�����I��======================================")
    logger.info("=====================================select�N���X�����I��======================================")

#���[�_���N���X���p�������N���X�̍쐬
class CRUDModal(Modal, title='Questionnaire Response'):
    logger.info("=====================================���[�_���N���X����======================================")
    async def on_submit(self, interaction: discord.Interaction):
        logger.info("=====================================���[�_�����M�{�^�������J�n======================================")
        #await interaction.response.send_message(f'Thanks for your response, {self.name}!', ephemeral=True)
    #�R�}���h���M���[�U�[�̎擾

        userId = f"{interaction.user}"
        userName = f"{interaction.user.display_name}"
        #�T�[�o�[ID�̎擾
        guidId = f"{interaction.guild_id}"
        #�`�����l��ID�̎擾
        channnelId = f"{interaction.channel_id}"

        intaraction_data = interaction.data["components"][0]["components"][0]
        regist_word = intaraction_data["value"]
        modal_custom_id = intaraction_data["custom_id"]

        #�X�V�pID���擾
        split_id = modal_custom_id.split('@')
        modal_custom_id = split_id[0]
        if len(split_id) > 1:
            get_data_id = split_id[1]

        #DB�ڑ��̃N���X���C���X�^���X��
        queryDb = DbQuery()

        if len(regist_word) > 100:
            await interaction.response.send_message(f'{regist_word} \n��100�����𒴂��Ă��I�I\n100�����ȓ��œo�^���ĂˁI', ephemeral=True,delete_after=2)

        else:

            if modal_custom_id == "regist_input":
                #�o�^���[�_���ő��M������
                #�o�^����==
                select_query = "SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s"
                values = (guidId,channnelId)
                resultData = queryDb.quryexcute(select_query,values)


                insert_query = "INSERT INTO WORDTABLE(botseq_id,word,create_user_id,create_user) VALUES( %s,%s,%s,%s);"
                values = (int(resultData[0][0]),regist_word,userId,userName);

                queryDb.quryexcute(insert_query,values);

                #==========����====================

                await interaction.response.send_message(f'{regist_word} �o�^�ł�����I', ephemeral=True,delete_after=2)

            elif modal_custom_id == "update_input":
                #�X�V���I�����ꂽ��
                update_query = "UPDATE WORDTABLE SET word = %s WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND create_user_id = %s AND id = %s"

                values = (regist_word,guidId,channnelId,userId,get_data_id)
                resultData = queryDb.quryexcute(update_query,values)

                await interaction.response.edit_message(content="�ύX����܂���",view=None,delete_after=2)
        logger.info("=====================================���[�_�����M�{�^�������I��======================================")
    logger.info("=====================================���[�_���N���X�����I��======================================")


@client.event
async def on_ready():
    logger.info("=====================================�{�b�g�J�n����======================================")
    view = CreateView()
    logger.info(f'We have logged in as {client.user}')
    await tree.sync()
    logger.info("=====================================�J�n�����I��======================================")

#=============================================================�e�X�g�R�}���h�ł�
#�R�}���h�ǂݎ��
@tree.command(name = "start",description="�X�^�[�g�����I")
async def start(interaction: discord.Interaction):  
    logger.info("=====================================start�R�}���h�擾����======================================")

    #�R�}���h���M���[�U�[�̎擾
    userId = f"{interaction.user}"
    #�T�[�o�[ID�̎擾
    guidId = f"{interaction.guild_id}"
    #�`�����l��ID�̎擾
    channnelId = f"{interaction.channel_id}"
    #=====DB�̏���
    queryDb = DbQuery()

    try:
        logger.info("=====================================�c�a�ڑ��E�e��J�n�{�^���\�������J�n======================================")
        #DB�֐ڑ����܂��B
        select_query = "SELECT * FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s AND start_up_flg = True"
        values = (guidId,channnelId)
        resultData = queryDb.quryexcute(select_query,values)
        
        # �{�^�����܂�View�i�r���[�j���쐬���܂�
        #View�i�y��̍쐬�j
        view = CreateView()

        #�{�b�g���N�����Ă��邩�m�F �N�����Ă��Ȃ�������
        if len(resultData) == 0:
            #�{�^���̍쐬 style:�{�^���̎�� label:�{�^���̖��O custom_id�F�{�^����ID
            okbutton = CreateButton(style=discord.ButtonStyle.primary, label="�n�߂�I", custom_id="start_button")
            cancelbutton = CreateButton(style=discord.ButtonStyle.danger, label="����ς��߂�I", custom_id="cancel_button")
            #view�Ƀ{�^����ǉ�
            view.add_item(okbutton)
            view.add_item(cancelbutton)
           
            label = "�y�����V�т��n�߂܂����H"
            #view.start_message()

        else:
            join_button = CreateButton(style=discord.ButtonStyle.primary, label="�Q��", custom_id="join_button")
            end_button = CreateButton(style=discord.ButtonStyle.danger, label="�I���H", custom_id="end_button")
            all_check_button = CreateButton(style=discord.ButtonStyle.gray, label="�����̃��[�h�ꗗ", custom_id="all_check_button")
            label = "���łɊJ�n����Ă����I\n�Q������������ƁA���t�́u�o�^�v�u�ύX�v�u�폜�v���ł���� \n �I���Ƃ��́u�I���H�v�{�^���������ĂˁI�I"
            #view�Ƀ{�^����ǉ�
            view.add_item(join_button)
            view.add_item(end_button)

        # ���b�Z�[�W�Ƀ{�^����\�����܂�
        await interaction.response.send_message(label, view=view)

    except Exception as ex:
       logging.warning(f"�G���[���F{ex}")
       await interaction.response.send_message("�N���Ɏ��s������I���Ԃ������Ă�����x�����Ă݂āI")
    finally:
        client.add_view(view = view)
        logger.info("=====================================start�R�}���h�����I��======================================")


@tree.command(name="help",description="��������Ƃ�����������I")
async def redme_command(interaction: discord.Interaction):
        await interaction.response.send_message("""
/start�F�D���Ȍ��t��o�^�J�n�R�}���h����I
�J�n������{�^�����|�`�|�`�����ēo�^������X�V������폜�����肵�ĂˁI
�݂�Ȃ����[�h�̓o�^���I������烏�[�h���擾���ĂˁI
�I������Ɠo�^���ꂽ�N���ǂ̃��[�h��o�^�����̂��B
���ꂪ�ǂ̃��[�h���g�����̂��������ꗗ���\��������B
�폜���ꂽ�f�[�^������邩��A�C��t���Ă�(;'��')
�����킩��Ȃ����Ƃ���������A�����S�܂ŘA�����ĂˁI
""")

logger.info("=====================================run�����J�n======================================")
client.run(TOKEN,log_handler=None, log_level=logging.DEBUG)
logger.info("=====================================run�����I��======================================")