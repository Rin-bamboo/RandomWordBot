import base64
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aiohttp.test_utils import TestClient, TestServer
from admin_web.app import create_app
from admin_web.ng_csv import export_csv, parse_csv


class CsvTests(unittest.TestCase):
    def test_encodings_headers_and_duplicates(self):
        for encoding in ('utf-8-sig', 'cp932'):
            words, rows = parse_csv('ng_word\r\n禁止語\r\nＢＡＤ word\r\nbadword\r\n'.encode(encoding))
            self.assertEqual(words, ['badword', '禁止語'])
            self.assertEqual(rows, 3)

    def test_export_is_excel_safe_and_roundtrips_quotes_and_commas(self):
        words = ['=1+1', '+command', '-1', '@text', "'quoted", '引用"符', 'a,b', '禁止語']
        exported = export_csv(words)
        self.assertTrue(exported.startswith(b'\xef\xbb\xbf'))
        self.assertIn("'=1+1", exported.decode('utf-8-sig'))
        self.assertEqual(parse_csv(exported)[0], sorted(words))

    def test_rejects_invalid_csv_entirely(self):
        for payload in (b'', b'ng_word\n', b'a,b\n', b'valid\n"broken', b'valid\n"line\nbreak"', b'valid\n#comment', b'\x00', b'a' * 101, b'a' * (1024 * 1024 + 1), b'a\n' * 10001):
            with self.subTest(payload=payload[:30]), self.assertRaises(ValueError):
                parse_csv(payload)


class CsvApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.words = root / 'words.txt'
        self.words.write_text('existing\n', encoding='utf-8')
        policy = root / 'policy.json'
        policy.write_text(json.dumps({'blocked_guild_ids': [], 'blocked_user_ids': []}))
        self.environment = patch.dict(os.environ, {'NG_WORD_FILE':str(self.words), 'ACCESS_POLICY_FILE':str(policy), 'MODERATION_AUDIT_FILE':str(root / 'audit.jsonl')})
        self.environment.start()
        self.client = TestClient(TestServer(create_app('admin', 'a' * 32)))
        await self.client.start_server()
        self.headers = {'Authorization':'Basic ' + base64.b64encode(('admin:' + 'a' * 32).encode()).decode()}
        response = await self.client.get('/api/csrf', headers=self.headers)
        self.headers.update({'X-CSRF-Token':(await response.json())['token'], 'Origin':'https://192.168.40.175:8084', 'Content-Type':'text/csv', 'X-Upload-Filename':'words.csv'})

    async def asyncTearDown(self):
        await self.client.close()
        self.environment.stop()
        self.directory.cleanup()

    async def test_preview_import_and_download(self):
        payload = b'ng_word\nexisting\nnewword\nnewword\n'
        response = await self.client.post('/api/ng-words/csv/preview', headers=self.headers, data=payload)
        self.assertEqual(response.status, 200)
        self.assertEqual((await response.json())['added'], 1)
        self.assertEqual(self.words.read_text(), 'existing\n')
        response = await self.client.post('/api/ng-words/csv/import', headers=self.headers, data=payload)
        self.assertEqual((await response.json())['total'], 2)
        response = await self.client.get('/api/ng-words/csv', headers=self.headers)
        self.assertIn('attachment', response.headers['Content-Disposition'])
        self.assertEqual(parse_csv(await response.read())[0], ['existing', 'newword'])
        response = await self.client.post('/api/ng-words/csv/import', headers=self.headers, data=payload)
        self.assertEqual((await response.json())['added'], 0)

    async def test_invalid_file_does_not_partially_import(self):
        response = await self.client.post('/api/ng-words/csv/import', headers=self.headers, data=b'newword\n"bad\nword"\n')
        self.assertEqual(response.status, 400)
        self.assertEqual(self.words.read_text(), 'existing\n')

    async def test_auth_csrf_extension_and_size(self):
        response = await self.client.get('/api/ng-words/csv')
        self.assertEqual(response.status, 401)
        headers = dict(self.headers, Origin='https://evil.example')
        response = await self.client.post('/api/ng-words/csv/import', headers=headers, data=b'newword')
        self.assertEqual(response.status, 403)
        headers = dict(self.headers, **{'X-Upload-Filename':'words.exe'})
        response = await self.client.post('/api/ng-words/csv/import', headers=headers, data=b'newword')
        self.assertEqual(response.status, 400)
        response = await self.client.post('/api/ng-words/csv/import', headers=self.headers, data=b'a' * (1024 * 1024 + 1))
        self.assertEqual(response.status, 413)


if __name__ == '__main__':
    unittest.main()
