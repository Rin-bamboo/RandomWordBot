# 2026-10-16 依存関係更新

Python 3.14系の修正版と、PyPIで公開済みの最新安定版を適用しました。

| 対象 | 更新前 | 更新後 |
| --- | --- | --- |
| Python | 3.14.6 | 3.14.8 |
| matplotlib | 3.11.0 | 3.11.2 |
| mysql-connector-python | 9.7.0 | 26.7.0 |
| pandas | 3.0.3 | 3.0.6 |
| python-dotenv | 1.2.2 | 1.2.4 |
| setuptools | 80.9.0 | 84.0.0 |

discord.py 2.7.1、japanize-matplotlib 1.1.3、pillow 12.3.0は確認時点の最新安定版です。
Connector/Python 26.7.0は、公式リリースノートによるとバージョン番号の変更のみで機能変更はありません。
MySQLサーバーは稼働中の8.4.11を継続使用します。

## 確認

更新候補イメージで以下を実行しました。

- `python -m unittest discover -s tests -v`: 4件成功。
- `python -m pip check`: 不整合なし。
- 日本語のDataFrameを一覧画像へ変換し、PNGの読込とフォント欠落がないことを確認。
- 稼働DBへの接続、一時テーブルの日本語INSERT/UPDATE/SELECT、ロールバックを確認。検証データは永続テーブルへ保存しません。
- 既存の`DbQuery`による設定マスターのパラメーター付きSELECTを確認。

Discord画面での登録から終了までの操作は別途確認が必要です。

## 切り戻し

サーバー上に更新前イメージを`phraseblender-linux-discord-bot:before-dependency-update-20261016`として保持しています。
必要な場合は、配置先で以下を実行すると更新前のBotへ戻せます。

```sh
docker tag phraseblender-linux-discord-bot:before-dependency-update-20261016 phraseblender-linux-discord-bot:latest
docker compose --env-file .env.linux -f docker-compose.linux.yml up -d --no-build --no-deps discord-bot
```

この操作は稼働イメージのみを切り戻します。再ビルドする場合はソースのDockerfileとrequirements.txtも更新前へ戻す必要があります。

## 参照

- https://pypi.org/
- https://hub.docker.com/_/python
- https://dev.mysql.com/doc/relnotes/connector-python/en/news-26-7-0.html
