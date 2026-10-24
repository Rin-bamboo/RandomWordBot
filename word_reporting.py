"""登録者を公開せず、ワード単位で管理用チャンネルへ通報する。"""

import asyncio
import json
from pathlib import Path

import discord
from discord import app_commands

from Model.WordReportModel import WordReportModel
from log_setting import getLogger
from access_control import allow_interaction, denial_reason

logger = getLogger(__name__)
MAX_WORD_ID = 2147483647


def can_report(interaction):
    return (
        interaction.guild is not None
        and interaction.channel_id is not None
        and interaction.permissions.view_channel
        and denial_reason(interaction.guild_id, interaction.user.id) is None
    )


def destination_ready(channel, guild_id):
    if not isinstance(channel, discord.TextChannel) or channel.guild.id != guild_id:
        return False
    guild = channel.guild
    # 通報内容を誰でも見られるチャンネルへの誤設定を防ぐ。
    if channel.permissions_for(guild.default_role).view_channel:
        return False
    permissions = channel.permissions_for(guild.me)
    return permissions.view_channel and permissions.send_messages and permissions.embed_links


async def operator_destination(client):
    # 利用先サーバーの設定を参照せず、運営者の配置設定だけを使う。
    path = Path(__file__).resolve().parent / "config" / "report_destination.json"
    settings = json.loads(path.read_text(encoding="utf-8"))
    guild_id = int(settings["guild_id"])
    channel_id = int(settings["channel_id"])
    channel = client.get_channel(channel_id)
    if channel is None:
        channel = await client.fetch_channel(channel_id)
    return channel if destination_ready(channel, guild_id) else None


async def report_words(interaction: discord.Interaction, current: str):
    if not can_report(interaction):
        return []
    try:
        rows = await asyncio.to_thread(
            WordReportModel().candidates, interaction.guild_id, interaction.channel_id, current[:100]
        )
        # 候補に登録者を含めない。同じ言葉は記録番号で区別する。
        return [app_commands.Choice(name=f"{word_id}: {word}"[:100], value=str(word_id))
                for word_id, word in rows]
    except Exception as error:
        logger.error("通報候補取得失敗 error_type=%s", type(error).__name__)
        return []


@app_commands.command(name="report", description="このチャンネルの問題のある言葉を通報します")
@app_commands.guild_only()
@app_commands.describe(word="言葉を入力して候補から選択してください", reason="通報理由（任意・500文字以内）")
@app_commands.autocomplete(word=report_words)
@app_commands.checks.cooldown(1, 30, key=lambda interaction: (interaction.guild_id, interaction.user.id))
async def report_word(interaction: discord.Interaction, word: str, reason: str = ""):
    if not await allow_interaction(interaction):
        return
    if not can_report(interaction):
        await interaction.response.send_message("対象のサーバーチャンネルで実行してください。", ephemeral=True)
        return
    if not word.isascii() or not word.isdecimal() or len(word) > 10 or not 0 < int(word) <= MAX_WORD_ID:
        await interaction.response.send_message("言葉を入力し、表示される候補から選んでください。", ephemeral=True)
        return
    if len(reason) > 500:
        await interaction.response.send_message("通報理由は500文字以内で入力してください。", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    model = WordReportModel()
    saved = False
    try:
        channel = await operator_destination(interaction.client)
        if channel is None:
            await interaction.followup.send("ボット運営者への通知先を利用できません。時間をおいて再実行してください。", ephemeral=True)
            return
        report = await asyncio.to_thread(
            model.submit, interaction.id, interaction.guild_id, interaction.channel_id,
            int(word), interaction.user.id, reason.strip(),
        )
        if report is None:
            await interaction.followup.send("対象の言葉が見つかりません。候補を選び直してください。", ephemeral=True)
            return
        saved = True
        report_id, snapshot, stored_reason, notification_id = report
        if notification_id is not None:
            await interaction.followup.send("この言葉はすでに通報済みです。", ephemeral=True)
            return
        embed = discord.Embed(title="ワードの通報", color=discord.Color.orange())
        embed.add_field(name="対象ワード", value=discord.utils.escape_markdown(snapshot)[:1024], inline=False)
        embed.add_field(name="理由", value=discord.utils.escape_markdown(stored_reason or "未記入"), inline=False)
        embed.add_field(name="対象チャンネル", value=str(interaction.channel_id))
        embed.add_field(name="対象サーバー", value=str(interaction.guild_id))
        embed.add_field(name="ワード記録番号", value=word)
        embed.add_field(name="通報者ID", value=str(interaction.user.id))
        embed.set_footer(text=f"通報番号: {report_id} / 登録者情報はDBの通報記録で確認できます")
        message = await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        await asyncio.to_thread(model.mark_notified, report_id, message.id)
        logger.info("通報通知完了 report_id=%s", report_id)
        await interaction.followup.send("通報を受け付け、ボット運営者に通知しました。", ephemeral=True)
    except Exception as error:
        # ワード・理由・登録者情報を例外ログへ展開しない。
        logger.error("通報処理失敗 saved=%s error_type=%s", saved, type(error).__name__)
        text = ("通報は保存しましたが、通知の完了を確認できませんでした。30秒後に再実行してください。"
                if saved else "通報に失敗しました。時間をおいて再実行してください。")
        await interaction.followup.send(text, ephemeral=True)


@report_word.error
async def report_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message("通報は30秒以上あけて実行してください。", ephemeral=True)
    else:
        logger.error("通報コマンド失敗 error_type=%s", type(error).__name__)
        if not interaction.response.is_done():
            await interaction.response.send_message("通報を実行できませんでした。", ephemeral=True)


def register_report_commands(tree):
    tree.add_command(report_word)
