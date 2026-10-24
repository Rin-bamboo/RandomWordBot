"""運営者が管理するID単位の利用制限。Discordのサーバー管理権限とは分離する。"""

import argparse
import json
import logging
import os
from pathlib import Path
import tempfile
from functools import wraps
from threading import Lock
from config_store import configuration_lock

logger = logging.getLogger(__name__)
POLICY_PATH = Path(os.environ.get("ACCESS_POLICY_FILE", Path(__file__).resolve().parent / "config" / "access_policy.json"))
_policy_lock = Lock()
MAX_DISCORD_ID = (1 << 64) - 1


def discord_id(value):
    text = str(value)
    if not text.isascii() or not text.isdecimal() or not 0 < int(text) <= MAX_DISCORD_ID:
        raise ValueError("Discord IDには正の整数を指定してください。")
    return int(text)


def load_policy(path=None):
    policy = json.loads(Path(path or POLICY_PATH).read_text(encoding="utf-8"))
    if not isinstance(policy, dict) or set(policy) != {"blocked_guild_ids", "blocked_user_ids"}:
        raise ValueError("NG設定の項目が不正です。")
    for field, entries in policy.items():
        if not isinstance(entries, list):
            raise ValueError("NG設定はIDの配列で指定してください。")
        policy[field] = frozenset(discord_id(entry) for entry in entries)
    return policy


def denial_reason(guild_id, user_id):
    try:
        policy = load_policy()
    except (OSError, ValueError, TypeError) as error:
        # 設定不備で全制限が解除されることを防ぐ。未知の対象を自動退出はさせない。
        logger.error("NG設定読込失敗 error_type=%s", type(error).__name__)
        return "configuration"
    if guild_id in policy["blocked_guild_ids"]:
        return "guild"
    if user_id in policy["blocked_user_ids"]:
        return "user"
    return None


async def allow_interaction(interaction):
    reason = denial_reason(interaction.guild_id, interaction.user.id)
    if reason is None:
        return True
    logger.info("bot_access_denied reason=%s guild_id=%s user_id=%s",
                reason, interaction.guild_id, interaction.user.id)
    # autocompleteは通常メッセージを返せないため、候補を空にする。
    import discord
    if interaction.type == discord.InteractionType.autocomplete:
        await interaction.response.autocomplete([])
    else:
        message = ("現在ボットの利用可否を確認できません。時間をおいて再実行してください。"
                   if reason == "configuration" else "このボットの利用は制限されています。")
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    return False


def restricted_interaction(function):
    @wraps(function)
    async def guarded(*args, **kwargs):
        interaction = kwargs.get("interaction") or args[-1]
        if await allow_interaction(interaction):
            return await function(*args, **kwargs)
    return guarded


async def leave_if_blocked(guild):
    """Trueなら登録処理へ進めない。設定異常時は退出せず登録も保留する。"""
    try:
        policy = load_policy()
    except (OSError, ValueError, TypeError) as error:
        logger.error("NG設定読込失敗 error_type=%s", type(error).__name__)
        return True
    if guild.id not in policy["blocked_guild_ids"]:
        return False
    try:
        await guild.leave()
        logger.info("blocked_guild_left guild_id=%s", guild.id)
    except Exception as error:
        logger.error("NGサーバー退出失敗 guild_id=%s error_type=%s", guild.id, type(error).__name__)
    return True


async def enforce_blocked_guilds(client):
    # 起動時と定期確認で、既存参加先への追加指定も反映する。
    for guild in list(client.guilds):
        await leave_if_blocked(guild)


def update_policy(action, target, target_id, path=None):
    with _policy_lock, configuration_lock(Path(path or POLICY_PATH)):
        _update_policy(action, target, target_id, path)


def _update_policy(action, target, target_id, path=None):
    if target not in ("guild", "user"):
        raise ValueError("対象はguildまたはuserを指定してください。")
    path = Path(path or POLICY_PATH)
    policy = load_policy(path)
    field = "blocked_guild_ids" if target == "guild" else "blocked_user_ids"
    identifier = discord_id(target_id)
    entries = set(policy[field])
    if action == "block":
        entries.add(identifier)
    elif action == "unblock":
        entries.discard(identifier)
    else:
        raise ValueError("操作はblockまたはunblockを指定してください。")
    policy[field] = entries
    payload = {name: [str(entry) for entry in sorted(values)] for name, values in policy.items()}
    # ディレクトリをbind mountするため、原子的な置換後も実行中コンテナから新しい内容が見える。
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".access-policy-", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(payload, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.chmod(temporary_path, path.stat().st_mode & 0o777)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def main():
    parser = argparse.ArgumentParser(description="運営者用：ボットのNGサーバー・NGユーザー管理")
    parser.add_argument("action", choices=("list", "block", "unblock"))
    parser.add_argument("target", nargs="?", choices=("guild", "user"))
    parser.add_argument("target_id", nargs="?")
    args = parser.parse_args()
    try:
        if args.action == "list":
            policy = load_policy()
            print(json.dumps({field: [str(entry) for entry in sorted(entries)]
                              for field, entries in policy.items()}, indent=2))
        else:
            if args.target is None or args.target_id is None:
                parser.error("対象種別とDiscord IDが必要です。")
            update_policy(args.action, args.target, args.target_id)
            print("NG設定を更新しました。")
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f"NG設定の操作に失敗しました: {error}\n")


if __name__ == "__main__":
    main()
