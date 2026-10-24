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

運用中のログ項目と障害調査の方法は [操作ログ](operation-logging.md) を参照してください。

`BOTSEQTABLE.guild_name` と `channel_name` に、問い合わせ時に確認するサーバー名・チャンネル名を保存します。
Bot起動時にDiscord上の導入済みサーバー一覧を取得し、未登録サーバーを `channel_id=NULL`、`start_up_flg=FALSE` で登録します。
新しくサーバーへ導入された際も `on_guild_join` イベントで同じ初期状態を即時登録します。
再導入時は既存行を維持します。イベントでDB登録に失敗した場合はログを残し、次回起動時の一覧同期で補完します。
既存のチャンネル行があるサーバーは重複登録しません。最初の `/start` で未使用サーバーの行へチャンネルを設定し、
別チャンネルでの利用時は従来どおり別行を登録します。退出済みサーバーの履歴を自動削除することはありません。
Bot起動時に確認できる既存行を補完し、`/start`やボタン・フォーム・選択メニューの操作時に名前変更を反映します。
取得できない名前は既存値を維持し、未取得の場合はNULLです。履歴ではなく最後に確認した名前を保存します。

名前列がない既存DBはバックアップ後に `docker/mysql/migrations/20261017-location-names.sql` を一度だけ適用します。
導入済みサーバー同期自体に追加のDBスキーマ変更は不要です。
新規DBでは初期化SQLに含まれるため不要です。2026-10-17の適用前バックアップは
`~/phraseblender/backups/before-location-names-20261017-161754.sql` に保存しています。

A5等では以下で確認できます。

```sql
SELECT id, guild_id, guild_name, channel_id, channel_name
FROM BOTSEQTABLE
ORDER BY id;
```

`join_members.user_name` にはDiscordユーザー名、`display_name` にはそのサーバーでの表示名を保存します。
数値の `user_id` による識別は維持し、参加・再参加・登録完了時に名前を更新します。
起動時にも、Botのキャッシュで確認できる既存参加者の名前を補完します。
退出済み・確認できない参加者の名前は既存値を維持し、未取得の場合はNULLです。
登録完了状態を名前変更によってリセットすることはありません。
ゲーム終了時に参加者行を削除する既存動作は変更しません。

名前列がない既存DBには、バックアップ後に `docker/mysql/migrations/20261017-member-names.sql` を一度だけ適用します。
適用前バックアップは `~/phraseblender/backups/before-member-names-20261017-163440.sql` です。

```sql
SELECT id, botseq_id, user_id, user_name, display_name, is_completion
FROM join_members
ORDER BY botseq_id, id;
```

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
