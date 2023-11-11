from pandas.io import sql
import Entity
from Entity.RWBEntity import RWBEntity


##=====================MYSQL設定
from db_setup import DbQuery
#=======================ログ出力設定============================
from log_setting import getLogger
logger = getLogger(__name__)

#DB接続のクラスをインスタンス化
queryDb = DbQuery()

class RWBModel:
    
    botSeqId = 0
    guildId = 0
    channel_id = 0
    userId = ""
    regist_word = ""
    userName = ""

    #サーバーとチャンネルIDを取得
    def guildInfo(self,RWBEntity):
        data = RWBEntity
        select_query = "SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s"
        guildId = data.get_guildId
        channnelId = data.getchannnelId
        
        values = (guildId,channnelId)
        resultData = queryDb.quryexcute(select_query,values)
        
        if not resultData:
            #データがなければ、Falseを返却
            return False
        
        return resultData[0][0] #IDの返却
        
    #ワード登録
    def WordInsert(self,RWBEntity):
        data = RWBEntity
        insert_query = "INSERT INTO WORDTABLE(botseq_id,word,create_user_id,create_user) VALUES( %s,%s,%s,%s);"
        botSeqId = data.get_botSeqId
        word = data.get_word
        userId = data.get_userId
        userName = data.get_userName
        
        values = (botSeqId,word,userId,userName)
        queryDb.quryexcute(insert_query,values);
        
    #ワード更新 
    def WordUpdate(self,RWBEntity):
        data = RWBEntity
        #更新が選択されたら
        update_query = "UPDATE WORDTABLE SET word = %s WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND create_user_id = %s AND id = %s"
        word = data.get_word
        guildId = data.get_guildId
        channnelId = data.get_channnelId
        userId = data.get_userId
        wordSeq = data.get_wordSeq

        values = (word,guildId,channnelId,userId,wordSeq)
        resultData = queryDb.quryexcute(update_query,values)

    #ワード論理削除
    def WordDelete(self,RWBEntity):
        data = RWBEntity
        update_query = "UPDATE WORDTABLE SET delete_flg = True WHERE botseq_id = (SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s) AND create_user_id = %s AND id = %s"
        guidId = data.get_guildId
        channnelId = data.get_channelId
        userId = data.get_userId
        wordSeq = data.get_wordSeq

        values = (guidId,channnelId,userId,wordSeq)
        resultData = queryDb.quryexcute(update_query,values)


