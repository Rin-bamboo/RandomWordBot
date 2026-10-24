
##=====================MYSQL設定
from db_setup import DbQuery

#=======================ログ出力設定============================
from log_setting import getLogger
from operation_log import log_event
from access_control import load_policy
logger = getLogger(__name__)

class BotSetting:
    def RegisterInstalledGuild(self,guild):
        """導入イベントで1サーバーだけを登録し、再導入時は既存行を維持する。"""
        queryDb = DbQuery()
        rows = queryDb.quryexcute(
            "SELECT id FROM BOTSEQTABLE WHERE guild_id=%s LIMIT 1", (guild.id,),
        )
        if rows:
            return False
        self._insert_installed_guild(queryDb,guild)
        return True

    def _insert_installed_guild(self,queryDb,guild):
        name = getattr(guild,"name",None)
        name = name if isinstance(name,str) and 0 < len(name) <= 255 else None
        queryDb.quryexcute(
            "INSERT INTO BOTSEQTABLE (guild_id,guild_name,channel_id,start_up_flg) "
            "VALUES (%s,%s,NULL,FALSE)", (guild.id,name),
        )
        log_event(logger,"installed_guild_registered",guild_id=guild.id,guild_name=name)

    def SyncInstalledGuilds(self,client):
        """導入済みサーバーを登録する。未使用サーバーの利用チャンネルは推測しない。"""
        blocked_guilds = load_policy()["blocked_guild_ids"]
        queryDb = DbQuery()
        rows = queryDb.quryexcute("SELECT DISTINCT guild_id FROM BOTSEQTABLE", ())
        known_guild_ids = {int(row[0]) for row in rows if row[0] is not None}
        added = 0
        for guild in client.guilds:
            if guild.id in blocked_guilds:
                continue
            if guild.id in known_guild_ids:
                continue
            self._insert_installed_guild(queryDb,guild)
            known_guild_ids.add(guild.id)
            added += 1
        log_event(logger,"installed_guilds_synced",discord_guild_count=len(client.guilds),added=added)

    def RegisterChannel(self,guild_id,channel_id,guild_name=None,channel_name=None):
        """最初の利用時は導入一覧の行を利用し、別チャンネルは新しい行へ登録する。"""
        queryDb = DbQuery()
        rows = queryDb.quryexcute(
            "SELECT id FROM BOTSEQTABLE WHERE guild_id=%s AND channel_id IS NULL ORDER BY id LIMIT 1",
            (guild_id,),
        )
        if rows:
            queryDb.quryexcute(
                "UPDATE BOTSEQTABLE SET channel_id=%s,guild_name=COALESCE(%s,guild_name),"
                "channel_name=%s,start_up_flg=TRUE,start_up_time_stamp=NOW() "
                "WHERE id=%s AND channel_id IS NULL",
                (channel_id,guild_name,channel_name,rows[0][0]),
            )
        else:
            queryDb.quryexcute(
                "INSERT INTO BOTSEQTABLE (guild_id,channel_id,guild_name,channel_name,start_up_flg,start_up_time_stamp) "
                "VALUES (%s,%s,%s,%s,TRUE,NOW())",
                (guild_id,channel_id,guild_name,channel_name),
            )
        log_event(logger,"guild_channel_registered",guild_id=guild_id,channel_id=channel_id,
                  guild_name=guild_name,channel_name=channel_name)

    def GetSettingValue(self,seqbotid,setting_name):
        queryDb = DbQuery()
        logger.info("設定情報の呼び出し")
        
        select_query = "SELECT sv.setting_id,sv.setting_value, s.setting_explanation FROM settings s JOIN settings_value sv ON  s.setting_id = sv.setting_id WHERE botseq_id = %s AND setting_name = %s ORDER BY sv.setting_id ASC;"
        values = (seqbotid,setting_name)
        resultData = queryDb.quryexcute(select_query,values)
        setting_value = resultData[0][1]

        return setting_value
    
    def GetSettingsData(self,botseq_id,setting_name):
        queryDb = DbQuery()
        logger.info("設定情報の呼び出し")
        
        select_query = "SELECT s.setting_explanation, sv.setting_value, s.setting_name FROM settings s JOIN settings_value sv ON  s.setting_id = sv.setting_id WHERE setting_name = %s"
        values = (setting_name,)
        setting_value = queryDb.quryexcute(select_query,values)

        return setting_value
    
    def GetBotSeq(self,guidId,channnelId,guild_name=None,channel_name=None):
        queryDb = DbQuery()
        select_query = "SELECT id,guild_name,channel_name FROM BOTSEQTABLE WHERE guild_id = %s AND channel_id = %s"
        values = (guidId,channnelId)
        resultData = queryDb.quryexcute(select_query,values)
        seqbotid = int(resultData[0][0])
        self._save_location_names(queryDb,seqbotid,resultData[0][1:3],guild_name,channel_name)
        return seqbotid

    def SyncLocationNames(self,client):
        """起動時にキャッシュで確認できた既存サーバー・チャンネルの名前を補完する。"""
        queryDb = DbQuery()
        rows = queryDb.quryexcute(
            "SELECT id,guild_id,channel_id,guild_name,channel_name FROM BOTSEQTABLE", (),
        )
        for seqbotid,guild_id,channel_id,guild_name,channel_name in rows:
            if guild_id is None:
                continue
            guild = client.get_guild(int(guild_id))
            channel = client.get_channel(int(channel_id)) if channel_id is not None else None
            # 退出済み・削除済み・閲覧できない場所の名前は推測しない。
            if getattr(getattr(channel,"guild",None),"id",None) != int(guild_id):
                channel = None
            self._save_location_names(
                queryDb,seqbotid,(guild_name,channel_name),
                getattr(guild,"name",None),getattr(channel,"name",None),
            )

    def _save_location_names(self,queryDb,seqbotid,saved_names,guild_name,channel_name):
        # 一時的に名前が取得できない場合は、問い合わせ用に保存した名前を維持する。
        saved_guild_name, saved_channel_name = saved_names
        next_guild_name = guild_name if isinstance(guild_name, str) and 0 < len(guild_name) <= 255 else saved_guild_name
        next_channel_name = channel_name if isinstance(channel_name, str) and 0 < len(channel_name) <= 255 else saved_channel_name
        if (next_guild_name, next_channel_name) != (saved_guild_name, saved_channel_name):
            queryDb.quryexcute(
                "UPDATE BOTSEQTABLE SET guild_name=%s,channel_name=%s WHERE id=%s",
                (next_guild_name,next_channel_name,seqbotid),
            )
            log_event(logger, "location_names_saved", botseq_id=seqbotid,
                      guild_name=next_guild_name, channel_name=next_channel_name)

    def SyncMemberNames(self,client):
        """表示名はサーバーごとに異なるため、そのサーバーのメンバー情報だけを使う。"""
        queryDb = DbQuery()
        rows = queryDb.quryexcute(
            "SELECT jm.id,bs.guild_id,jm.user_id,jm.user_name,jm.display_name "
            "FROM join_members jm JOIN BOTSEQTABLE bs ON bs.id=jm.botseq_id", (),
        )
        for member_id,guild_id,user_id,saved_user_name,saved_display_name in rows:
            if guild_id is None:
                continue
            guild = client.get_guild(int(guild_id))
            member = guild.get_member(int(user_id)) if guild is not None else None
            if member is None:
                continue
            user_name = getattr(member,"name",None)
            display_name = getattr(member,"display_name",None)
            if not (isinstance(user_name,str) and 0 < len(user_name) <= 255
                    and isinstance(display_name,str) and 0 < len(display_name) <= 255):
                continue
            if (user_name,display_name) != (saved_user_name,saved_display_name):
                queryDb.quryexcute(
                    "UPDATE join_members SET user_name=%s,display_name=%s WHERE id=%s",
                    (user_name,display_name,member_id),
                )
                log_event(logger, "member_names_saved", member_id=member_id, member_user_id=user_id,
                          user_name=user_name, display_name=display_name)

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
