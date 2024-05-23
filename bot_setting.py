
##=====================MYSQL設定
from db_setup import DbQuery

#=======================ログ出力設定============================
from log_setting import getLogger
logger = getLogger(__name__)

class BotSetting:
    def GetSettingValue(self,seqbotid,setting_name):
        queryDb = DbQuery()
        logger.info = "設定情報の呼び出し"
        
        select_query = "SELECT sv.setting_id,sv.setting_value, s.setting_explanation FROM settings s JOIN settings_value sv ON  s.setting_id = sv.setting_id WHERE botseq_id = %s AND setting_name = %s ORDER BY sv.setting_id ASC;"
        values = (seqbotid,setting_name)
        resultData = queryDb.quryexcute(select_query,values)
        setting_value = resultData[0][1]

        return setting_value
    
    def GetSettingsData(self,botseq_id,setting_name):
        queryDb = DbQuery()
        logger.info = "設定情報の呼び出し"
        
        select_query = "SELECT s.setting_explanation, sv.setting_value, s.setting_name FROM settings s JOIN settings_value sv ON  s.setting_id = sv.setting_id WHERE setting_name = %s"
        values = (setting_name,)
        setting_value = queryDb.quryexcute(select_query,values)

        return setting_value
    
    def GetBotSeq(self,guidId,channnelId):
        queryDb = DbQuery()
        select_query = "SELECT id FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s"
        values = (guidId,channnelId)
        resultData = queryDb.quryexcute(select_query,values)
        seqbotid = int(resultData[0][0])
        
        return seqbotid
    
    def GetSettingInfoMessage(self,botseqId):
                #BOTSEQ
        queryDb = DbQuery()
        
        select_query = "SELECT sv.botseq_id, s.setting_id, s.is_enabled, s.setting_name, s.setting_explanation, sv.setting_value FROM settings s JOIN settings_value sv ON  s.setting_id = sv.setting_id WHERE botseq_id = %s ORDER BY s.setting_id ASC "
        values = (str(botseqId),)
        resultData = queryDb.quryexcute(select_query,values)
                
        if len(resultData) == 0:
            return None
        else :

            setting_info = ""
            for i in range(len(resultData)):
                setting_name = resultData[i][4]
                setting_value = resultData[i][5]
                
                if resultData[i][3] == "Anonymous Setting":
                    #匿名設定　終了一覧画面に　名前を表示するかしないか
                    if setting_value == "True": setting_value = "表示する"
                    else : setting_value = "表示しない"

                setting_info = setting_info +  setting_name + " ： " + setting_value #resultData[i][3] + "："+
                setting_info = setting_info + "\n"

            return setting_info


    def GetSettingInfo(self,botseqId):
                #BOTSEQ
        queryDb = DbQuery()
        
        select_query = "SELECT s.setting_id, s.setting_explanation, s.setting_name, sv.setting_value FROM settings s JOIN settings_value sv ON  s.setting_id = sv.setting_id WHERE botseq_id = %s ORDER BY s.setting_id ASC "
        values = (str(botseqId),)
        resultData = queryDb.quryexcute(select_query,values)
                
        return resultData
    
    def CanConvertToInt(self,value):
        try:
            int(value)
            return int(value)
        except ValueError:
            return False
