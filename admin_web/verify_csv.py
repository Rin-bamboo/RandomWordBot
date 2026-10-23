"""自鯖で既存ワードをダウンロード・再取込し、NG設定を変えず往復検証する。"""
import base64
import json
from pathlib import Path
import ssl
import urllib.request

settings = dict(line.split('=', 1) for line in Path('.env.admin').read_text().splitlines() if '=' in line)
origin = settings['ADMIN_ORIGIN']
context = ssl._create_unverified_context()
headers = {'Authorization': 'Basic ' + base64.b64encode((settings['ADMIN_USER'] + ':' + settings['ADMIN_PASSWORD']).encode()).decode()}


def fetch(path, body=None, extra=None):
    request = urllib.request.Request(origin + path, data=body, headers={**headers, **(extra or {})})
    return urllib.request.urlopen(request, context=context, timeout=30)


with fetch('/api/moderation') as response:
    before = json.load(response)['ng_words']
with fetch('/api/csrf') as response:
    token = json.load(response)['token']
with fetch('/api/ng-words/csv') as response:
    assert 'attachment' in response.headers['Content-Disposition']
    csv_bytes = response.read()
    assert csv_bytes.startswith(b'\xef\xbb\xbf')
extra = {'Content-Type':'text/csv', 'Origin':origin, 'X-CSRF-Token':token, 'X-Upload-Filename':'ng-words.csv'}
with fetch('/api/ng-words/csv/preview', csv_bytes, extra) as response:
    preview = json.load(response)
    assert preview['added'] == 0
    assert preview['unique'] == len(before)
with fetch('/api/ng-words/csv/import', csv_bytes, extra) as response:
    result = json.load(response)
    assert result['added'] == 0
    assert result['total'] == len(before)
with fetch('/api/moderation') as response:
    assert json.load(response)['ng_words'] == before
print(f'HTTPS CSV download/preview/import: OK; existing {len(before)} words preserved')
