"""Discord操作とDB処理を同じ操作IDで追跡するためのログ。"""

import logging
import json
from contextvars import ContextVar
from functools import wraps
from time import perf_counter
from Model.DiscordInfo import location_names

operation_context = ContextVar("operation_context", default=None)
operation_outcome = ContextVar("operation_outcome", default="completed")
MAX_LOG_TEXT_LENGTH = 1024
SECRET_FIELDS = {"token", "bot_token", "password", "pass", "authorization", "cookie", "secret"}


def safe_fields(fields):
    if isinstance(fields, dict):
        return {name: "[REDACTED]" if str(name).lower() in SECRET_FIELDS else safe_fields(value)
                for name, value in fields.items()}
    if isinstance(fields, (list, tuple)):
        return [safe_fields(value) for value in fields]
    if isinstance(fields, str) and len(fields) > MAX_LOG_TEXT_LENGTH:
        return fields[:MAX_LOG_TEXT_LENGTH] + "[truncated]"
    return fields


def log_event(logger, event, *, level=logging.INFO, **fields):
    if fields.get("outcome") in ("failed", "rejected"):
        operation_outcome.set(fields["outcome"])
    # 改行を含む入力をJSON化し、ログを偽装する別行にはしない。
    logger.log(level, json.dumps(safe_fields({"event": event, **fields}), ensure_ascii=False, default=str))


class OperationContextFilter(logging.Filter):
    def filter(self, record):
        context = operation_context.get()
        record.operation_context = (
            " context=" + json.dumps(context, ensure_ascii=False, default=str) if context else ""
        )
        return True


def trace_interaction(kind):
    """DB読み取り前を含むコールバック全体へ操作者情報を付ける。"""
    def decorate(function):
        @wraps(function)
        async def traced(*args, **kwargs):
            interaction = kwargs.get("interaction") or args[-1]
            component = args[0] if len(args) > 1 else None
            data = interaction.data if isinstance(interaction.data, dict) else {}
            context = {
                "interaction_id": str(interaction.id),
                "user_id": str(interaction.user.id),
                "user_name": str(interaction.user),
                "display_name": str(interaction.user.display_name),
                "guild_id": str(interaction.guild_id),
                "channel_id": str(interaction.channel_id),
                **location_names(interaction),
                "kind": kind,
                "action": data.get("custom_id") or data.get("name") or function.__name__,
            }
            message = getattr(interaction, "message", None)
            if message is not None:
                context["message_id"] = str(message.id)
            if component is not None and isinstance(getattr(component, "label", None), str):
                context["button_label"] = component.label
            context_token = operation_context.set(safe_fields(context))
            outcome_token = operation_outcome.set("completed")
            logger = logging.getLogger(function.__module__)
            started_at = perf_counter()
            try:
                log_event(logger, "interaction_started")
                return await function(*args, **kwargs)
            except Exception:
                operation_outcome.set("failed")
                logger.exception("interaction_failed")
                raise
            finally:
                log_event(logger, "interaction_finished", outcome=operation_outcome.get(),
                          elapsed_ms=round((perf_counter() - started_at) * 1000, 2))
                operation_outcome.reset(outcome_token)
                operation_context.reset(context_token)
        return traced
    return decorate
