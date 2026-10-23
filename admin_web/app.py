"""Botと独立して動作する、運営者専用の統計・NG管理画面。"""
import asyncio
import base64
import hmac
import json
import logging
import os
import ssl
import time
from datetime import datetime, timezone
from pathlib import Path

import aiohttp
from aiohttp import web
import mysql.connector

logger = logging.getLogger(__name__)
ROOT = Path(__file__).parent


def read_ng_configuration():
    """稼働Botと共有する設定を毎回読む。読込失敗をNGなしと扱わない。"""
    from access_control import load_policy
    from ng_word_filter import load_ng_words
    policy = load_policy(os.environ['ACCESS_POLICY_FILE'])
    words_path = Path(os.environ['NG_WORD_FILE'])
    return dict(policy={field: [str(entry) for entry in sorted(entries)] for field, entries in policy.items()},
                ng_words=sorted(set(load_ng_words(words_path, environment_value=''))),
                words_captured_at=datetime.fromtimestamp(words_path.stat().st_mtime, timezone.utc).isoformat())


def change_moderation(target, action, value):
    from access_control import discord_id, update_policy
    from ng_word_filter import update_ng_word
    if target == 'word':
        update_ng_word(action, value)
    else:
        identifier = discord_id(value)
        if action == 'block' and ((target == 'guild' and str(identifier) == os.environ['OPERATOR_GUILD_ID'])
                                 or (target == 'user' and str(identifier) == os.environ['BOT_USER_ID'])):
            raise ValueError('Protected target')
        update_policy(action, target, identifier, os.environ['ACCESS_POLICY_FILE'])
    # Basic認証は共通の管理者アカウント。個人のDiscord IDを操作者とはみなさない。
    record = dict(at=datetime.now(timezone.utc).isoformat(), operator=os.environ.get('ADMIN_USER', 'admin'),
                  target=target, action=action, value=value)
    with open(os.environ['MODERATION_AUDIT_FILE'], 'a', encoding='utf-8') as audit:
        audit.write(json.dumps(record, ensure_ascii=False) + '\n')
        audit.flush()
        os.fsync(audit.fileno())


def load_moderation():
    configuration = read_ng_configuration()
    connection = mysql.connector.connect(host=os.environ['HOST'], user=os.environ['USER_NAME'],
                                        password=os.environ['PASS'], database=os.environ['DB'], connection_timeout=5)
    try:
        connection.start_transaction(readonly=True, consistent_snapshot=True)
        cursor = connection.cursor(dictionary=True)
        try:
            # NG一覧は通常少数だが、大量指定にも一括取得で対応する。
            cursor.execute('SELECT CAST(guild_id AS CHAR) AS id, MAX(guild_name) AS name FROM BOTSEQTABLE GROUP BY guild_id')
            guild_names = {row['id']: row['name'] for row in cursor.fetchall()}
            cursor.execute('SELECT CAST(user_id AS CHAR) AS id, MAX(COALESCE(display_name,user_name)) AS name FROM join_members GROUP BY user_id')
            user_names = {row['id']: row['name'] for row in cursor.fetchall()}
            configuration['guild_candidates'] = [dict(id=identifier, name=name) for identifier, name in guild_names.items() if identifier]
            configuration['user_candidates'] = [dict(id=identifier, name=name) for identifier, name in user_names.items() if identifier]
            cursor.execute("SELECT DISTINCT word FROM WORDTABLE WHERE delete_flg=FALSE AND CHAR_LENGTH(word) BETWEEN 1 AND 100 ORDER BY word LIMIT 1000")
            configuration['word_candidates'] = [row['word'] for row in cursor.fetchall()]
            policy = configuration.pop('policy')
            configuration['blocked_guilds'] = [dict(id=identifier, name=guild_names.get(identifier)) for identifier in policy['blocked_guild_ids']]
            configuration['blocked_users'] = [dict(id=identifier, name=user_names.get(identifier)) for identifier in policy['blocked_user_ids']]
            cursor.execute('SELECT COUNT(*) AS total, COALESCE(SUM(notification_message_id IS NULL),0) AS unnotified FROM word_reports')
            configuration['report_counts'] = {key: int(value) for key, value in cursor.fetchone().items()}
            cursor.execute("""SELECT CAST(r.report_id AS CHAR) AS report_id, CAST(r.guild_id AS CHAR) AS guild_id,
                CAST(r.channel_id AS CHAR) AS channel_id, r.word_id, CAST(r.reporter_id AS CHAR) AS reporter_id,
                r.word_snapshot, r.owner_snapshot, r.reason,
                DATE_FORMAT(r.created_at,'%Y-%m-%d %H:%i:%s') AS created_at,
                r.notification_message_id IS NOT NULL AS notified,
                (SELECT MAX(b.guild_name) FROM BOTSEQTABLE b WHERE b.guild_id=r.guild_id) AS guild_name
                FROM word_reports r ORDER BY r.created_at DESC, r.report_id DESC LIMIT 50""")
            configuration['reports'] = cursor.fetchall()
            configuration['updated_at'] = datetime.now(timezone.utc).isoformat()
            return configuration
        finally:
            cursor.close()
    finally:
        connection.rollback()
        connection.close()


def load_statistics():
    connection = mysql.connector.connect(
        host=os.environ['HOST'], user=os.environ['USER_NAME'],
        password=os.environ['PASS'], database=os.environ['DB'],
        connection_timeout=5,
    )
    try:
        connection.start_transaction(readonly=True, consistent_snapshot=True)
        cursor = connection.cursor(dictionary=True)
        try:
            def query(sql):
                cursor.execute(sql)
                return cursor.fetchall()

            counts = query("""SELECT
                (SELECT COUNT(*) FROM WORDTABLE WHERE delete_flg=FALSE) AS words,
                (SELECT COUNT(*) FROM WORDTABLE WHERE delete_flg=TRUE) AS deleted_words,
                (SELECT COUNT(DISTINCT guild_id) FROM BOTSEQTABLE) AS historical_guilds,
                (SELECT COUNT(DISTINCT guild_id) FROM BOTSEQTABLE WHERE start_up_flg=TRUE) AS playing_guilds,
                (SELECT COUNT(DISTINCT user_id) FROM join_members) AS participants,
                (SELECT COUNT(DISTINCT create_user_id) FROM WORDTABLE
                 WHERE delete_flg=FALSE AND create_user_id IS NOT NULL AND create_user_id<>'') AS contributors
            """)[0]
            users = query("""SELECT create_user_id AS user_id,
                COALESCE(NULLIF(MAX(create_user),''),create_user_id) AS name, COUNT(*) AS count
                FROM WORDTABLE WHERE delete_flg=FALSE
                AND create_user_id IS NOT NULL AND create_user_id<>''
                GROUP BY create_user_id ORDER BY count DESC, create_user_id LIMIT 20""")
            guilds = query("""SELECT CAST(b.guild_id AS CHAR) AS guild_id,
                COALESCE(NULLIF(MAX(b.guild_name),''),CAST(b.guild_id AS CHAR)) AS name,
                COUNT(w.id) AS count
                FROM BOTSEQTABLE b LEFT JOIN WORDTABLE w ON w.botseq_id=b.id AND w.delete_flg=FALSE
                WHERE b.guild_id IS NOT NULL GROUP BY b.guild_id
                ORDER BY count DESC, b.guild_id LIMIT 20""")
            return dict(counts=counts, users=users, guilds=guilds,
                        updated_at=datetime.now(timezone.utc).isoformat())
        finally:
            cursor.close()
    finally:
        connection.rollback()
        connection.close()


async def fetch_guild_count(session, token):
    """100件超もページ送りし、退出済みのDB行を現在数へ含めない。"""
    count, after = 0, '0'
    for _ in range(1000):
        async with session.get('https://discord.com/api/v10/users/@me/guilds',
                               headers={'Authorization': 'Bot ' + token},
                               params={'limit': '200', 'after': after}) as response:
            if response.status != 200:
                raise RuntimeError('Discord guild request failed: ' + str(response.status))
            guilds = await response.json()
        count += len(guilds)
        if len(guilds) < 200:
            return count
        next_after = str(max(int(guild['id']) for guild in guilds))
        if int(next_after) <= int(after):
            raise RuntimeError('Discord pagination did not advance')
        after = next_after
    raise RuntimeError('Discord pagination limit reached')


def authorized(header, username, password):
    try:
        scheme, encoded = header.split(' ', 1)
        if scheme.lower() != 'basic':
            return False
        supplied = base64.b64decode(encoded, validate=True)
        expected = (username + ':' + password).encode()
        return hmac.compare_digest(supplied, expected)
    except (ValueError, UnicodeError):
        return False


def create_app(username, password, loader=load_statistics, guild_loader=fetch_guild_count, moderation_loader=load_moderation, mutation_handler=None):
    if not username or len(password) < 20:
        raise ValueError('A username and a password of at least 20 characters are required')

    csrf_token = hmac.new(password.encode(), b'phraseblender-csrf-v1', 'sha256').hexdigest()

    @web.middleware
    async def protect(request, handler):
        if not authorized(request.headers.get('Authorization', ''), username, password):
            response = web.Response(status=401, text='管理者の認証が必要です',
                                    headers={'WWW-Authenticate': 'Basic realm="Phrase Blender", charset="UTF-8"'})
        else:
            if request.method not in ('GET', 'HEAD', 'OPTIONS'):
                expected_origin = os.environ.get('ADMIN_ORIGIN', 'https://192.168.40.175:8084')
                if (request.headers.get('Origin') != expected_origin
                        or not hmac.compare_digest(request.headers.get('X-CSRF-Token', ''), csrf_token)):
                    return web.json_response({'error': '操作の有効性を確認できません。画面を再読み込みしてください。'}, status=403)
            try:
                response = await handler(request)
            except web.HTTPRequestEntityTooLarge:
                response = web.json_response({'error': 'CSVは1MB以下にしてください。'}, status=413)
        response.headers.update({
            'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY', 'Referrer-Policy': 'no-referrer',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'",
        })
        return response

    app = web.Application(middlewares=[protect], client_max_size=1024 * 1024)
    cache = {'data': None, 'expires': 0}
    lock = asyncio.Lock()

    async def statistics(request):
        async with lock:
            if time.monotonic() >= cache['expires']:
                try:
                    result = await asyncio.to_thread(loader)
                except Exception as error:
                    logger.error('Statistics database unavailable: %s', type(error).__name__)
                    return web.json_response({'error': '統計を取得できませんでした。時間をおいて再試行してください。'}, status=503)
                result['current_guilds'] = None
                result['discord_status'] = 'unavailable'
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                        result['current_guilds'] = await guild_loader(session, os.environ['BOT_TOKEN'])
                    result['discord_status'] = 'ok'
                except Exception as error:
                    logger.warning('Discord statistics unavailable: %s', type(error).__name__)
                cache.update(data=result, expires=time.monotonic() + 60)
            return web.json_response(cache['data'])

    async def index(request):
        return web.Response(text=(ROOT / 'index.html').read_text(encoding='utf-8'), content_type='text/html')

    moderation_lock = asyncio.Lock()

    async def moderation(request):
        async with moderation_lock:
            try:
                return web.json_response(await asyncio.to_thread(moderation_loader))
            except Exception as error:
                logger.error('Moderation information unavailable: %s', type(error).__name__)
                return web.json_response({'error': 'NG情報を取得できませんでした。設定・DBの状態を確認してください。'}, status=503)

    async def csrf(request):
        return web.json_response({'token': csrf_token})

    async def mutate(request):
        if request.content_type != 'application/json':
            return web.json_response({'error': 'JSON形式で指定してください。'}, status=415)
        try:
            payload = await request.json()
            if not isinstance(payload, dict) or set(payload) != {'target', 'action', 'value'}:
                raise ValueError('対象・操作・値を指定してください。')
            target, action, value = payload['target'], payload['action'], payload['value']
            if target not in ('guild', 'user', 'word') or action not in ('block', 'unblock') or not isinstance(value, str):
                raise ValueError('不正な対象・操作・値です。')
            handler = mutation_handler or change_moderation
            async with moderation_lock:
                await asyncio.to_thread(handler, target, action, value)
            logger.info('moderation_changed operator=%s target=%s action=%s', username, target, action)
            return web.json_response({'message': 'NG設定を更新しました。'})
        except (ValueError, TypeError):
            return web.json_response({'error': '入力が不正です。IDまたはワードを確認してください。運営サーバーとBot自身はNG追加できません。'}, status=400)
        except OSError as error:
            logger.error('Moderation update failed: %s', type(error).__name__)
            return web.json_response({'error': '設定を更新できませんでした。再読み込みして状態を確認してください。'}, status=503)

    async def download_csv(request):
        from admin_web.ng_csv import export_csv
        try:
            configuration = await asyncio.to_thread(read_ng_configuration)
            return web.Response(body=export_csv(configuration['ng_words']), content_type='text/csv',
                                headers={'Content-Disposition': 'attachment; filename="ng-words.csv"'})
        except (OSError, ValueError):
            return web.json_response({'error': 'NGワードを読み取れませんでした。'}, status=503)

    async def upload_csv(request):
        from admin_web.ng_csv import parse_csv
        from ng_word_filter import add_ng_words
        from urllib.parse import unquote
        if request.content_type != 'text/csv':
            return web.json_response({'error': 'CSVファイルを指定してください。'}, status=415)
        filename = unquote(request.headers.get('X-Upload-Filename', ''))
        if not filename.lower().endswith('.csv') or len(filename) > 255:
            return web.json_response({'error': '拡張子が.csvのファイルを指定してください。'}, status=400)
        try:
            words, rows = parse_csv(await request.read())
            async with moderation_lock:
                if request.path.endswith('/preview'):
                    configuration = await asyncio.to_thread(read_ng_configuration)
                    existing = set(configuration['ng_words'])
                    return web.json_response(dict(rows=rows, unique=len(words), duplicates=rows-len(words),
                                                  added=len(set(words)-existing), existing=len(set(words)&existing),
                                                  preview=words[:20]))
                result = await asyncio.to_thread(add_ng_words, words)
                def audit_import():
                    record = dict(at=datetime.now(timezone.utc).isoformat(), operator=username,
                                  target='word', action='csv_import', words=words, **result)
                    with open(os.environ['MODERATION_AUDIT_FILE'], 'a', encoding='utf-8') as audit:
                        audit.write(json.dumps(record, ensure_ascii=False) + '\n')
                        audit.flush()
                        os.fsync(audit.fileno())
                await asyncio.to_thread(audit_import)
                return web.json_response(dict(message='CSVからNGワードを追加しました。', **result))
        except ValueError as error:
            return web.json_response({'error': str(error)}, status=400)
        except OSError as error:
            logger.error('CSV operation failed: %s', type(error).__name__)
            return web.json_response({'error': 'CSVを反映できませんでした。再読み込みして設定を確認してください。'}, status=503)

    app.router.add_get('/api/ng-words/csv', download_csv)
    app.router.add_post('/api/ng-words/csv/preview', upload_csv)
    app.router.add_post('/api/ng-words/csv/import', upload_csv)
    app.router.add_get('/api/csrf', csrf)
    app.router.add_post('/api/moderation', mutate)
    app.router.add_get('/', index)
    app.router.add_get('/api/statistics', statistics)
    app.router.add_get('/api/moderation', moderation)
    app.router.add_static('/assets/', ROOT / 'assets')
    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(os.environ['TLS_CERT'], os.environ['TLS_KEY'])
    web.run_app(create_app(os.environ['ADMIN_USER'], os.environ['ADMIN_PASSWORD']),
                host='0.0.0.0', port=8080, ssl_context=context, access_log=None)
