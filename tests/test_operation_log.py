import asyncio
import io
import json
import logging
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from log_setting import getLogger
from Model.RWBModel import RWBModel
from operation_log import OperationContextFilter, log_event, operation_context, trace_interaction


class OperationLogTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.output = io.StringIO()
        self.handler = logging.StreamHandler(self.output)
        self.handler.addFilter(OperationContextFilter())
        self.handler.setFormatter(logging.Formatter("%(message)s%(operation_context)s"))
        self.root = logging.getLogger()
        self.root.addHandler(self.handler)
        self.addCleanup(self.root.removeHandler, self.handler)

    def interaction(self, interaction_id="audit-test-1"):
        return SimpleNamespace(
            id=interaction_id, data={"custom_id": "regist_input"},
            user=SimpleNamespace(id=123, display_name="確認用ユーザー"),
            guild_id=456, channel_id=789,
        )

    async def test_input_and_commit_are_correlated_with_actor(self):
        query = MagicMock()
        query.quryexcute.return_value = []

        @trace_interaction("modal")
        async def submit(interaction):
            log_event(getLogger(__name__), "input_received", input_value="確認用の言葉")
            RWBModel(query).insert_word(7, "確認用の言葉", "test-user", "確認用ユーザー")

        await submit(self.interaction())
        output = self.output.getvalue()
        self.assertIn('"event": "interaction_started"', output)
        self.assertIn('"event": "word_registered"', output)
        self.assertIn('"word": "確認用の言葉"', output)
        self.assertIn('"user_id": "123"', output)
        self.assertIn('"interaction_id": "audit-test-1"', output)
        self.assertIn('"outcome": "completed"', output)
        self.assertIsNone(operation_context.get())

    async def test_failed_write_has_no_committed_event_and_context_resets(self):
        query = MagicMock()
        query.quryexcute.side_effect = RuntimeError("test failure")

        @trace_interaction("modal")
        async def submit(interaction):
            RWBModel(query).insert_word(7, "確認用の言葉", "test-user", "確認用ユーザー")

        with self.assertRaises(RuntimeError):
            await submit(self.interaction())
        output = self.output.getvalue()
        self.assertNotIn('"event": "word_registered"', output)
        self.assertIn('"outcome": "failed"', output)
        self.assertIsNone(operation_context.get())

    async def test_concurrent_interactions_keep_separate_contexts(self):
        observed = []

        @trace_interaction("button")
        async def press(interaction):
            await asyncio.sleep(0)
            observed.append((interaction.id, operation_context.get()["interaction_id"]))

        await asyncio.gather(press(self.interaction("first")), press(self.interaction("second")))
        self.assertEqual([("first", "first"), ("second", "second")], observed)
        self.assertIsNone(operation_context.get())

    async def test_handled_failure_is_not_reported_as_completed(self):
        @trace_interaction("modal")
        async def submit(interaction):
            log_event(getLogger(__name__), "input_rejected", outcome="rejected", reason="length")

        await submit(self.interaction())
        self.assertIn('"outcome": "rejected"', self.output.getvalue())
        self.assertNotIn('"outcome": "completed"', self.output.getvalue())

    def test_input_newlines_are_escaped_and_secrets_redacted(self):
        log_event(getLogger(__name__), "input_received", input_value="一行目\n二行目",
                  password="never-log-password", extra={"BOT_TOKEN": "never-log-token"})
        output = self.output.getvalue()
        self.assertEqual(1, len(output.splitlines()))
        self.assertNotIn("never-log-password", output)
        self.assertNotIn("never-log-token", output)
        self.assertEqual("一行目\n二行目", json.loads(output)["input_value"])

    def test_repeated_get_logger_does_not_add_handlers(self):
        before = len([h for h in self.root.handlers if getattr(h, "_randomwordbot_handler", False)])
        getLogger("audit.repeat")
        getLogger("audit.repeat")
        after = len([h for h in self.root.handlers if getattr(h, "_randomwordbot_handler", False)])
        self.assertEqual(before, after)
