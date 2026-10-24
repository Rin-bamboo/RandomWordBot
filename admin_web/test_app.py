from pathlib import Path
import base64
import os
import unittest
from unittest.mock import patch

from aiohttp.test_utils import TestClient, TestServer
from admin_web.app import authorized, create_app, fetch_guild_count, load_statistics, read_ng_configuration


class AuthenticationTests(unittest.TestCase):
    def test_authentication_rejects_missing_malformed_and_wrong_password(self):
        for header in ('', 'Bearer token', 'Basic !!!', 'Basic ' + base64.b64encode(b'admin:wrong').decode()):
            self.assertFalse(authorized(header, 'admin', 'password'))
        self.assertTrue(authorized('Basic ' + base64.b64encode(b'admin:password').decode(), 'admin', 'password'))


class PolicyTests(unittest.TestCase):
    def test_shared_settings_and_word_roundtrip(self):
        import tempfile, json
        from access_control import update_policy
        from ng_word_filter import update_ng_word, load_ng_words
        with tempfile.TemporaryDirectory() as directory:
            policy = Path(directory) / 'policy.json'; words = Path(directory) / 'words.txt'
            policy.write_text(json.dumps({'blocked_guild_ids': [], 'blocked_user_ids': []}))
            words.write_text('# words\nexisting\n', encoding='utf-8')
            with patch.dict(os.environ, {'ACCESS_POLICY_FILE':str(policy), 'NG_WORD_FILE':str(words)}):
                update_policy('block', 'user', '18446744073709551615', policy)
                update_ng_word('block', 'ＢＡＤ word'); update_ng_word('block', 'BADWORD')
                result = read_ng_configuration()
                self.assertEqual(result['policy']['blocked_user_ids'], ['18446744073709551615'])
                self.assertEqual(result['ng_words'], ['badword', 'existing'])
                update_ng_word('unblock', 'badword')
                self.assertEqual(load_ng_words(words, ''), ('existing',))
                for value in ('', '#comment', 'x\ny', 'x' * 101):
                    with self.assertRaises(ValueError):
                        update_ng_word('block', value)



class WebTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.calls = 0
        def loader():
            self.calls += 1
            return {'counts': {'words': 0}, 'users': [], 'guilds': []}
        async def guild_loader(session, token):
            return 0
        self.client = TestClient(TestServer(create_app('admin', 'a' * 32, loader, guild_loader)))
        await self.client.start_server()
        self.headers = {'Authorization': 'Basic ' + base64.b64encode(('admin:' + 'a' * 32).encode()).decode()}

    async def asyncTearDown(self):
        await self.client.close()

    async def test_private_assets_and_api(self):
        for path in ('/', '/assets/app.js', '/api/statistics', '/api/moderation'):
            response = await self.client.get(path)
            self.assertEqual(response.status, 401)
            self.assertEqual(response.headers['Cache-Control'], 'no-store')

    async def test_empty_statistics_and_cache(self):
        with patch.dict(os.environ, {'BOT_TOKEN': 'test'}):
            for _ in range(2):
                response = await self.client.get('/api/statistics', headers=self.headers)
                self.assertEqual(response.status, 200)
                data = await response.json()
                self.assertEqual(data['current_guilds'], 0)
        self.assertEqual(self.calls, 1)

    async def test_database_error_is_not_exposed(self):
        def fail():
            raise RuntimeError('secret connection string')
        client = TestClient(TestServer(create_app('admin', 'a' * 32, fail)))
        await client.start_server()
        try:
            response = await client.get('/api/statistics', headers=self.headers)
            self.assertEqual(response.status, 503)
            self.assertNotIn('secret', await response.text())
        finally:
            await client.close()

    async def test_discord_error_is_unknown_not_zero(self):
        async def fail(session, token):
            raise RuntimeError('token')
        client = TestClient(TestServer(create_app('admin', 'a' * 32, lambda: {}, fail)))
        await client.start_server()
        try:
            with patch.dict(os.environ, {'BOT_TOKEN': 'test'}):
                response = await client.get('/api/statistics', headers=self.headers)
                data = await response.json()
                self.assertIsNone(data['current_guilds'])
                self.assertEqual(data['discord_status'], 'unavailable')
        finally:
            await client.close()

    async def test_moderation_and_no_write_endpoint(self):
        payload = {'blocked_users': [{'id': '18446744073709551615', 'name': '<script>'}], 'blocked_guilds': [], 'reports': []}
        client = TestClient(TestServer(create_app('admin', 'a' * 32, moderation_loader=lambda: payload)))
        await client.start_server()
        try:
            response = await client.get('/api/moderation', headers=self.headers)
            self.assertEqual(await response.json(), payload)
            response = await client.post('/api/moderation', headers=self.headers, json={})
            self.assertEqual(response.status, 403)
        finally:
            await client.close()

    async def test_moderation_failure_is_not_empty_policy(self):
        def fail():
            raise ValueError('private file path')
        client = TestClient(TestServer(create_app('admin', 'a' * 32, moderation_loader=fail)))
        await client.start_server()
        try:
            response = await client.get('/api/moderation', headers=self.headers)
            self.assertEqual(response.status, 503)
            self.assertNotIn('private', await response.text())
        finally:
            await client.close()

    async def test_mutation_requires_origin_and_token(self):
        calls = []
        client = TestClient(TestServer(create_app('admin', 'a' * 32, mutation_handler=lambda *args: calls.append(args))))
        await client.start_server()
        try:
            response = await client.get('/api/csrf', headers=self.headers)
            token = (await response.json())['token']
            payload = {'target':'word', 'action':'block', 'value':'testword'}
            headers = dict(self.headers, **{'X-CSRF-Token': token, 'Origin':'https://evil.example'})
            response = await client.post('/api/moderation', headers=headers, json=payload)
            self.assertEqual(response.status, 403)
            self.assertEqual(calls, [])
            headers['Origin'] = 'https://192.168.40.175:8084'
            response = await client.post('/api/moderation', headers=headers, json=payload)
            self.assertEqual(response.status, 200)
            self.assertEqual(calls, [('word', 'block', 'testword')])
            payload['target'] = 'other'
            response = await client.post('/api/moderation', headers=headers, json=payload)
            self.assertEqual(response.status, 400)
            self.assertEqual(len(calls), 1)
        finally:
            await client.close()

    async def test_operator_guild_and_bot_are_protected(self):
        from admin_web.app import change_moderation
        with patch.dict(os.environ, {'OPERATOR_GUILD_ID':'123', 'BOT_USER_ID':'456'}):
            for target, value in [('guild','123'), ('user','456')]:
                with self.assertRaises(ValueError):
                    change_moderation(target, 'block', value)

    async def test_discord_pagination(self):
        pages = [[{'id': str(i)} for i in range(1, 201)], [{'id': '201'}]]
        class Response:
            status = 200
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def json(self):
                return pages.pop(0)
        class Session:
            def get(self, url, **kwargs):
                return Response()
        self.assertEqual(await fetch_guild_count(Session(), 'test'), 201)


if __name__ == '__main__':
    unittest.main()
