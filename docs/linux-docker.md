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
