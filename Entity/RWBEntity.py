from dataclasses import dataclass


@dataclass(frozen=True)
class InteractionContext:
    """Discordの操作情報を処理層へ渡すためのデータクラス。"""

    guild_id: str
    channel_id: str
    user_id: str
    user_name: str
    selected_value: str | None = None
