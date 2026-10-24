# 操作と障害調査のログ

BotのINFOログには、Discord上で誰が何を行い、どこまで進んだかを記録します。
Dockerログと `/app/logs/random-word-bot.log` に同じ内容を出力します。
ログファイルは5MiBでローテーションし、バックアップ5世代を保持します。

## 記録内容

- 各コマンド、ボタン、選択メニュー、入力フォーム、更新・削除の確認ボタンの開始と終了。
- 操作ID `interaction_id`、Discord数値ユーザーID、ユーザー名、表示名、サーバーIDと名前、チャンネルIDと名前、メッセージID、操作名、ボタン表示名。
- フォーム入力値、選択値、登録した言葉、更新確認中の言葉と対象ID、DB反映済みの言葉、削除対象ID、設定変更値、取得した言葉。
- 参加・再参加・登録完了時の参加者ID、ユーザー名、そのサーバーでの表示名。起動時の参加者名補完も記録。
- DBの開始、接続、SQL種別とパラメーター化されたSQL、取得件数、影響件数、コミット、ロールバック、終了、所要時間。
- 失敗した工程、例外、入力拒否の理由。

DBへ渡す引数や環境変数の一括出力は行いません。入力値は業務イベントで明示的に記録します。
トークン、接続パスワード、Cookie、Authorization等を汎用イベントのフィールドへ渡した場合は伏せ字にします。
入力の改行はJSONでエスケープし、長い文字列は1024文字で省略します。

ユーザー名・表示名・入力した言葉は運用者が確認できるログに保存されます。
通常の匿名表示設定はDiscord画面の表示設定であり、この障害調査ログの匿名化設定ではありません。

## 読み方

```text
{"event":"interaction_started"} context={"interaction_id":"123", "user_id":"456", "action":"regist_input", ...}
{"event":"input_received", "input_value":"好きな言葉", ...} context={"interaction_id":"123", ...}
{"event":"db_started", "operation":"INSERT", ...} context={"interaction_id":"123", ...}
{"event":"db_committed", "affected_rows":1, ...} context={"interaction_id":"123", ...}
{"event":"word_registered", "word":"好きな言葉", ...} context={"interaction_id":"123", ...}
{"event":"interaction_finished", "outcome":"completed", "elapsed_ms":12.3} context={"interaction_id":"123", ...}
```

`input_received`は入力受付、`word_update_confirmation_requested`は確認待ちです。
`word_registered`や`word_update_committed`はDBの処理が戻った段階です。
更新・削除が実際に何件へ反映されたかは同じ操作IDの`db_committed.affected_rows`を確認します。
`interaction_finished.outcome` は `completed`、`failed`、`rejected` を区別します。
別の操作で同時に処理していても、それぞれの操作IDで追跡できます。

## 確認コマンド

```sh
cd ~/phraseblender
docker compose --env-file .env.linux -f docker-compose.linux.yml logs -f --tail=100 discord-bot
```

特定の操作IDを検索する場合:

```sh
docker compose --env-file .env.linux -f docker-compose.linux.yml logs --no-color discord-bot | grep '"interaction_id": "123"'
```

DB接続失敗があれば `db_failed` と同じ操作IDをたどり、SQL種別・発生工程と利用者の操作を確認します。
ログのテストは `tests/test_operation_log.py` にあり、並行操作の分離、失敗時の結果、改行対策、機密フィールドの伏せ字、ハンドラー重複防止を検証します。
