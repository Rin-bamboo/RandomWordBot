"""コンテナ内で実行し、資格情報を出力せず実DBとHTTPSを確認する。"""
import base64
import json
import os
import ssl
import urllib.error
import urllib.request

import mysql.connector
from admin_web.app import load_statistics, load_moderation

context = ssl._create_unverified_context()
url = 'https://192.168.40.175:8084/'
try:
    urllib.request.urlopen(url, context=context)
    raise AssertionError('Unauthenticated access was allowed')
except urllib.error.HTTPError as error:
    assert error.code == 401
header = base64.b64encode((os.environ['ADMIN_USER'] + ':' + os.environ['ADMIN_PASSWORD']).encode()).decode()
request = urllib.request.Request(url + 'api/statistics', headers={'Authorization': 'Basic ' + header})
with urllib.request.urlopen(request, context=context) as response:
    result = json.load(response)
    assert result['counts'] == load_statistics()['counts']
    assert result['discord_status'] == 'ok'
    print(json.dumps({'authentication': 'OK', 'database_counts': result['counts'],
                      'current_guilds': result['current_guilds'],
                      'user_ranking_rows': len(result['users']),
                      'guild_ranking_rows': len(result['guilds'])}))
request = urllib.request.Request(url + 'api/moderation', headers={'Authorization': 'Basic ' + header})
with urllib.request.urlopen(request, context=context) as response:
    result = json.load(response)
    expected = load_moderation()
    for key in ('blocked_users', 'blocked_guilds', 'ng_words', 'report_counts', 'reports'):
        assert result[key] == expected[key]
    print('Moderation HTTPS API matches live settings and database: OK')
connection = mysql.connector.connect(host=os.environ['HOST'], user=os.environ['USER_NAME'],
                                    password=os.environ['PASS'], database=os.environ['DB'])
try:
    cursor = connection.cursor()
    try:
        cursor.execute('UPDATE WORDTABLE SET id=id WHERE 1=0')
        raise AssertionError('Unexpected UPDATE permission')
    except mysql.connector.Error as error:
        assert error.errno == 1142, error.errno
        print('Database UPDATE denied: OK')
    finally:
        cursor.close()
finally:
    connection.rollback()
    connection.close()
