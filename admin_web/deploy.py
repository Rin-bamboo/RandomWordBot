"""自鯖上で実行。既存Bot/DBを再起動せず、管理画面だけを起動する。"""
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import shutil


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def deploy():
    os.umask(0o077)
    root = Path('/home/bamboo/phraseblender')
    os.chdir(root)
    bot = json.loads(subprocess.check_output(['docker', 'inspect', 'phraseblender-linux-discord-bot-1']))[0]
    env = dict(entry.split('=', 1) for entry in bot['Config']['Env'] if '=' in entry)
    database = env['DB']
    if not re.fullmatch(r'[A-Za-z0-9_]+', database):
        raise ValueError('Unsupported database name')
    password_file = root / '.env.admin'
    words = json.loads(subprocess.check_output([
        'docker', 'exec', 'phraseblender-linux-discord-bot-1', 'python', '-c',
        'import json,ng_word_filter; print(json.dumps(sorted(set(ng_word_filter.load_ng_words()))))',
    ]))
    # 初回だけ既存のファイル・環境変数の有効ワードを共有設定へ移行する。
    seed = "import os,pathlib,sys; p=pathlib.Path('/app/access-policy/ng_words.txt'); exists=p.exists(); content=sys.stdin.read(); p.write_text(content,encoding='utf-8') if not exists else None; os.chown(p,100,101); os.chmod(p,0o600)"
    run('docker', 'exec', '-i', '-u', '0', 'phraseblender-linux-discord-bot-1', 'python', '-c', seed,
        input='# 管理画面で管理するNGワード\n' + '\n'.join(words) + '\n', text=True)
    bot_user_id = subprocess.check_output([
        'docker', 'exec', 'phraseblender-linux-discord-bot-1', 'python', '-c',
        "import os,json,urllib.request; r=urllib.request.Request('https://discord.com/api/v10/users/@me',headers={'Authorization':'Bot '+os.environ['BOT_TOKEN'], 'User-Agent':'PhraseBlenderAdmin/1.0'}); print(json.load(urllib.request.urlopen(r,timeout=15))['id'])",
    ], text=True).strip()
    operator = json.loads((root / 'config/report_destination.json').read_text())
    runtime = root / 'admin_web/runtime'
    runtime.mkdir(exist_ok=True)
    for filename in ('access_control.py', 'ng_word_filter.py', 'config_store.py'):
        shutil.copyfile(root / filename, runtime / filename)
        (runtime / filename).chmod(0o644)
    runtime.chmod(0o755)
    if password_file.exists():
        values = dict(line.split('=', 1) for line in password_file.read_text().splitlines() if '=' in line)
        db_password, admin_password = values['PASS'], values['ADMIN_PASSWORD']
    else:
        db_password, admin_password = secrets.token_hex(32), secrets.token_urlsafe(32)
    # アプリ側のreadonly transactionに加えて、DB権限でも更新を禁止する。
    sql = (f"CREATE USER IF NOT EXISTS 'phrase_stats'@'%' IDENTIFIED BY '{db_password}';"
           f"ALTER USER 'phrase_stats'@'%' IDENTIFIED BY '{db_password}';"
           f"GRANT SELECT ON `{database}`.* TO 'phrase_stats'@'%';")
    run('docker', 'exec', '-i', 'phraseblender-linux-db-1', 'sh', '-c',
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot', input=sql, text=True)
    tls = root / 'admin-tls'
    tls.mkdir(exist_ok=True)
    if not (tls / 'cert.pem').exists():
        run('openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-nodes', '-days', '365',
            '-keyout', str(tls / 'key.pem'), '-out', str(tls / 'cert.pem'),
            '-subj', '/CN=192.168.40.175', '-addext', 'subjectAltName=IP:192.168.40.175',
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # ホスト上では配置ディレクトリを700にし、コンテナの非root UIDから読めるようにする。
    tls.chmod(0o700)
    (tls / 'key.pem').chmod(0o644)
    (tls / 'cert.pem').chmod(0o644)
    values = dict(HOST='db', USER_NAME='phrase_stats', PASS=db_password, DB=database,
                  BOT_TOKEN=env['BOT_TOKEN'], ADMIN_USER='admin', ADMIN_PASSWORD=admin_password,
                  TLS_CERT='/run/cert.pem', TLS_KEY='/run/key.pem')
    values.update(ACCESS_POLICY_FILE='/run/access-policy/policy.json', NG_WORD_FILE='/run/access-policy/ng_words.txt',
                  MODERATION_AUDIT_FILE='/run/access-policy/web-audit.jsonl',
                  OPERATOR_GUILD_ID=str(operator['guild_id']), BOT_USER_ID=bot_user_id,
                  ADMIN_ORIGIN='https://192.168.40.175:8084')
    if any('\n' in value or '\r' in value or '$' in value or '#' in value for value in values.values()):
        raise ValueError('Unsupported environment value')
    password_file.write_text(''.join(f'{key}={value}\n' for key, value in values.items()))
    password_file.chmod(0o600)
    run('docker', 'compose', '--env-file', '.env.linux', '-f', 'docker-compose.linux.yml', 'up', '-d', '--build', '--no-deps', 'discord-bot')
    run('docker', 'compose', '-f', 'docker-compose.admin.yml', 'up', '-d', '--build', 'admin-web')
    print('Admin dashboard deployed. Credentials: /home/bamboo/phraseblender/.env.admin')


if __name__ == '__main__':
    deploy()
