from Entity.RWBEntity import InteractionContext


def location_names(interaction):
    """取得できない名前はNoneとし、既存DBの名前を消さない。"""
    names = {}
    for field, target in (("guild_name", getattr(interaction,"guild",None)),
                          ("channel_name", getattr(interaction,"channel",None))):
        name = getattr(target, "name", None)
        names[field] = name if isinstance(name, str) and 0 < len(name) <= 255 else None
    return names


def interaction_context(interaction, selected_value=None):
    """Discord固有のオブジェクトから処理に必要な値だけを取り出す。"""

    return InteractionContext(
        guild_id=str(interaction.guild_id),
        channel_id=str(interaction.channel_id),
        user_id=str(interaction.user),
        user_name=str(interaction.user.display_name),
        selected_value=None if selected_value is None else str(selected_value),
        **location_names(interaction),
    )
