from gc import callbacks
import Entity.RWBEntity

from discord.ui import Button, View,TextInput,Modal,Select
import discord

class deiscordInfo:
    async def callback(self, interaction: discord.Interaction):
        data = Entity.RWBEntity.RWBEntity

        select_custom_id = interaction.data["custom_id"]
        #コマンド送信ユーザーの取得
        data.get_userId = f"{interaction.user}"
        #サーバーIDの取得
        data.get_guildId = f"{interaction.guild_id}"
        #チャンネルIDの取得
        data.get_channelId = f"{interaction.channel_id}"
            
        data.set_wordSeq = interaction.data["values"][0]    
            