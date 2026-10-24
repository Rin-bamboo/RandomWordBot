"""自鯖で合成ID・一時ワードだけを使い、HTTPS更新とBotの共有設定を往復検証する。"""
import base64
import json
from pathlib import Path
import ssl
import subprocess
import urllib.request

settings = dict(line.split('=', 1) for line in Path('.env.admin').read_text().splitlines() if '=' in line)
origin = settings['ADMIN_ORIGIN']
context = ssl._create_unverified_context()
headers = {'Authorization': 'Basic ' + base64.b64encode((settings['ADMIN_USER'] + ':' + settings['ADMIN_PASSWORD']).encode()).decode()}


def request(path, payload=None):
    current = dict(headers)
    if payload is not None:
        current.update({'Content-Type': 'application/json', 'Origin': origin, 'X-CSRF-Token': token})
    request = urllib.request.Request(origin + path, headers=current,
                                     data=json.dumps(payload).encode() if payload is not None else None)
    with urllib.request.urlopen(request, context=context, timeout=30) as response:
        return json.load(response)


token = request('/api/csrf')['token']
before = request('/api/moderation')
identifier = '18446744073709551615'  # 現在のDiscordでは発行されていない将来日時のSnowflake。
word = 'phraseblendertesttemporaryng20261022'
assert all(entry['id'] != identifier for entry in before['blocked_users'] + before['blocked_guilds'])
assert word not in before['ng_words']
try:
    for target, value in [('user', identifier), ('guild', identifier), ('word', word)]:
        request('/api/moderation', dict(target=target, action='block', value=value))
    code = ("from access_control import load_policy; from ng_word_filter import is_ng_word; "
            "p=load_policy(); assert 18446744073709551615 in p['blocked_user_ids']; "
            "assert 18446744073709551615 in p['blocked_guild_ids']; "
            "assert is_ng_word('phraseblendertesttemporaryng20261022'); print('Bot reads all three Web settings: OK')")
    subprocess.run(['docker', 'exec', 'phraseblender-linux-discord-bot-1', 'python', '-c', code], check=True)
finally:
    for target, value in [('user', identifier), ('guild', identifier), ('word', word)]:
        request('/api/moderation', dict(target=target, action='unblock', value=value))
after = request('/api/moderation')
for key in ('blocked_users', 'blocked_guilds', 'ng_words'):
    assert before[key] == after[key], key
print('HTTPS add/remove roundtrip: OK; original NG settings restored')
