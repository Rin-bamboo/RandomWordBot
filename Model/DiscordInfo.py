from Entity.RWBEntity import InteractionContext


def interaction_context(interaction, selected_value=None):
    """Discord固有のオブジェクトから処理に必要な値だけを取り出す。"""

    return InteractionContext(
        guild_id=str(interaction.guild_id),
        channel_id=str(interaction.channel_id),
        user_id=str(interaction.user),
        user_name=str(interaction.user.display_name),
        selected_value=None if selected_value is None else str(selected_value),
    )
