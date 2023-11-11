#データの受け渡しクラス
#=======================ログ出力設定============================
from log_setting import getLogger
logger = getLogger(__name__)

class RWBEntity:
    __botSeqId = 0
    __guidId = 0
    __channnelId = 0
    __userId = 0
    __word = ""
    __wordSeq = 0

    #まとめてセッティング
    def set(self,guidId,channelId,userId,word,botSeqId,wordSeq):
        self.__guidId = guidId
        self.__channelId = channelId
        self.__userId = userId
        self.__word = word
        self.__botSeqId = botSeqId
        self.__wordSeq = wordSeq

    #ギルド（サーバー）IDの取得
    def get_guildId(self):
        return self.__guidId
    
    #チャンネルIDの取得
    def get_channelId(self):
        return self.__channnelId
    
    #ユーザーIDの取得
    def get_userId(self):
        return self.__userId
    
    #ワードの取得
    def get_word(self):
        return self.__word  
    
    #ボットSEQIDの取得
    def get_botSeqId(self):
        return self.__botSeqId
    
    #ワードSEQの取得
    def get_wordSeq(self):
        return self.__wordSeq
    
    #ギルド（サーバー）IDの設定
    def set_guildId(self,guildId):
        self.__guildId = guildId
        
    #チャンネルIDの設定
    def set_channelId(self,channelId):
        self.__channelId = channelId
        
    #ユーザーIDの設定
    def set_userId(self,userId):
        self.__userId = userId
        
    #ワードの設定
    def set_wprd(self,word):
        self.__word = word
        
    #botseqIDの設定
    def set_botSeqId(self,botSeqId):
        self.__botSeqId = botSeqId
        
    #wordSeqの設定
    def set_wordSeq(self,wordSeq):
        self.__wordSeq = wordSeq
        