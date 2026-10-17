# Linux Dockerへの展開（192.168.40.175）

Docker EngineとDocker Compose v2を導入したLinuxホストで実行します。
これは新規DBでの展開手順です。既存環境のDBや設定は自動移行しません。
既存ボットと同じトークンを使う場合は、動作確認直前に旧ボットを停止してください。

## 配置と設定

このプロジェクトをホストの任意の専用ディレクトリ（例: `~/phraseblender`）へ配置します。
Windowsの `venv`、`.git`、`.env`、ログ、ビルド成果物は転送不要です。
`Dockerfile`、`requirements.txt`、Pythonソース、`text/`、`docker/`、
`docker-compose.linux.yml`、`.env.linux.example`を含めてください。

サーバー上で配置先へ移動して実行します。

```sh
cp .env.linux.example .env.linux
chmod 600 .env.linux
nano .env.linux
```

`BOT_TOKEN`をDiscordボットのトークンに、`PASS`と`MYSQL_ROOT_PASSWORD`を
それぞれ異なる十分に長いパスワードに変更します。
Discord Developer PortalでServer Members IntentとMessage Content Intentを有効にし、
ボットを対象サーバーへ `bot` と `applications.commands` のスコープで招待してください。

## 起動と確認

```sh
docker compose --env-file .env.linux -f docker-compose.linux.yml config --quiet
docker compose --env-file .env.linux -f docker-compose.linux.yml up -d --build
docker compose --env-file .env.linux -f docker-compose.linux.yml ps
docker compose --env-file .env.linux -f docker-compose.linux.yml logs --tail=100 discord-bot
```

DBがhealthy、ボットがUpになり、ログに `We have logged in as` が出ることを確認します。
Discordのテスト用チャンネルで `/start` →「始める！」→「参加」→「登録」と操作し、
言葉を1件登録して「確認」「ワードゲット」を試します。
最後に「終わる？」で一覧画像が表示されることを確認してください。

ボットはDiscordへ発信接続するため、ホストのHTTPポート公開は不要です。
DBはホストのLANアドレス `192.168.40.175:3307` で公開します。別ホストへ配置する場合は `MYSQL_BIND_ADDRESS` を変更してください。`http://192.168.40.175` に管理画面はありません。
ホストからコンテナイメージ、Pythonパッケージ、Discordへのインターネット接続が必要です。

## 停止・更新・保存

```sh
docker compose --env-file .env.linux -f docker-compose.linux.yml down
# ソース更新後
docker compose --env-file .env.linux -f docker-compose.linux.yml up -d --build
```

DBとログは専用のDockerボリュームに保存され、通常のdownや再ビルドで保持されます。
`down -v` はDBも削除するため実行しないでください。
初期化SQLとDBユーザー作成は空のDBボリュームに対して初回だけ実行されます。
運用開始後のパスワード変更やスキーマ更新は、バックアップのうえ別途実施してください。
既存の `docker-compose.yml` と開発用Composeは従来どおり利用できます。

初期化方式: https://hub.docker.com/_/mysql

起動待ち: https://docs.docker.com/compose/how-tos/startup-order/

## A5:SQL Mk-2からの接続

A5でMySQL接続を作成し、ホスト `192.168.40.175`、ポート `3307`、
ユーザー `botapp`、データベース `botapp` を指定します。
パスワードはサーバー上の `/home/bamboo/phraseblender/.env.linux` の `PASS` です。
SSHトンネルは不要です。LAN内から接続してください。

## ホスト再起動後の起動待機

DockerがLANアドレスの割当より先に起動すると、DBのポート確保が失敗する場合があります。
以下のユーザーサービスは公開用IPを最大120秒待ち、DBのネットワークを作り直してからBotを起動します。
失敗時の再実行は30分間で最大3回に制限します。

配置先が `~/phraseblender` の場合、bambooユーザーで以下を実行します。

```sh
loginctl enable-linger "$USER"
mkdir -p ~/.config/systemd/user
cp docker/phraseblender-start.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now phraseblender-start.service
```

状態は `systemctl --user status phraseblender-start.service`、
起動ログは `journalctl --user -u phraseblender-start.service` で確認できます。
配置先を変更する場合はサービス内のパスも変更してください。
サービスを手動で再実行するとDBコンテナが再作成され、一時的にDB接続が切れます。ボリュームのデータは保持されます。

## 2026-10-17: 最新取得ワード確認用のDB更新

`WORDTABLE.updated_at` がない既存DBは、バックアップ後に
`docker/mysql/migrations/20261017-word-updated-at.sql` を一度だけ適用します。
新規DBは初期化SQLに含まれているため適用不要です。
既存の取得日時は不明なのでNULLとし、以後のワード取得から日時を保存します。
日時のない過去データはID降順を代替として使用し、過去の取得順序は復元しません。

2026-10-17の稼働DBへの適用前バックアップは、サーバーの
`~/phraseblender/backups/before-updated-at-20261017-145029.sql` に保存しています。
バックアップはGitおよびDockerイメージに含めません。

MySQLを使う結合テストは、稼働データに触れない一時テーブルで実行します。

```sh
docker compose --env-file .env.linux -f docker-compose.linux.yml run --rm --no-deps -e RUN_MYSQL_TESTS=1 --entrypoint python discord-bot -m unittest discover -s tests -v
```
