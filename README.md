# フレーズブレンダー

## このボットについて
このボットは、サーバー参加メンバーで好きな言葉を入れてもらい、
くじ引きのようにランダムで言葉を取り出すボットです

[Discord](https://discord.gg/vtT9S4DnVP)


### 製作者使用想定(検索に引っかかるかテスト中)
1. AmongUs：おふざけアモアス・ゴビングアス・語尾ングアス・ごびんぐあす
1. 抽選機能：当たりはずれを入れて置きランダムに当たりはずれを取得

### 開発環境
OS：Windows 11 <br/>
IED：Microsoft Visual Studio 2022<br/>
言語：Python 3.11.4<br/>
DB：MySQL<br/>

## 使用方法
セルフホストを考えている方は設定ファイルをを作成し、MySQLを導入してください<br/>
※各種Pytho・MySQLの導入・BOTの起動方法等は先駆者の解説を参考にお願いします。こちらでは割愛させていただきます。


~~`config.py` を作成し、RandomWordBot.pyと同じディレクトリ(フォルダ)に保存してください~~
.envに変更しました

### .envの準備
作成する設定ファイルの中身
```python:config.py
BOT_TOKEN = "自分のbotのトークン"
PASS="MySQLのパスワード"
USER_NAME="MySQLのユーザー名"
HOST="MySQLのホスト名"
DB="MySQLのDB名"
``` 


作成するDBの中身
```SQL:create.sql
--ボットを起動しているサーバーとチャンネルを管理するTBL
CREATE TABLE BOTSEQTABLE (
	id INT PRIMARY KEY AUTO_INCREMENT,
	guild_id BIGINT,
	channel_id BIGINT,
	start_up_flg bool default False,
	start_up_time_stamp TIMESTAMP
);

--登録された言葉を管理するTBL
CREATE TABLE WORDTABLE(
	id INT PRIMARY KEY AUTO_INCREMENT,
	botseq_id INT,
	word TEXT,
	create_user TEXT,
	create_user_id TEXT,
	use_user TEXT,
	use_user_id TEXT,
	select_flg bool default False ,
	delete_flg bool default False,
	enable_flg bool default False
);
```

## BOTの使い方
すぐに使って遊びたい方は、[こちら](https://onl.la/9P2VAZN)からサーバーへ追加をお願いします。

### コマンドの説明
このボットにコマンドは2つしかありません

`/start`と`/help`の二つになります。

`/start`　ボットを起動します。この時、起動した同じサーバー同じチャンネルのみで言葉を共有します。

`/help`　大まかな使い方を記載しております。

`/start`コマンドでボットを開始したら、下記のような画面が出てきます。

![スタート画面](/img/start.png "スタート画面")

「始める！」ボタンでボットの処理を開始し、「やっぱりやめるで」処理を終了します。<br/>
始めるボタンを押すと下のような画面になり、ボットへの参加が可能になります。<br/>
終了する際には「終わる？」ボタンを押してください<br/>
終了時に登録されたワード・登録したユーザー・使ったユーザーが表示されます

![参加画面](/img/join.png "参加画面")

「参加」ボタンを押すと下記のような「登録」「更新」「削除」「確認」「ワードゲット」<br/>
のボタンが表示されます。

![参加中画面](/img/game.png "参加中画面")

`登録`：好きな言葉が登録するモーダルが表示されます。
![登録画面](/img/regist_word_modal.png "登録画面")

ここで好きな言葉を登録できます。「言葉を入力」に好きな言葉を入力したら「送信」ボタンを押してください


`更新`：一度登録した言葉を変更したいときに押します。
![登録画面](/img/update_select.png "変更画面")

選択リストから変更したいワードを選択すると、登録画面と同じモーダル画面が表示されます。<br/>
変更したいを入力して送信を押すと変更ができます。

`削除`：登録した言葉を削除したいときに押します。

更新画面と同じような画面が表示され、削除したい言葉を選択すると削除が完了します。

**※更新と削除は、すでに選ばれた言葉はできません（選択画面に表示されません）**

`確認`：自分が登録した言葉を確認することができます。

![確認画面](/img/kakuin.png "確認画面")

ここで、すでに使用されているワードには横に「誰かがすでに使っているみたい」<br/>
の言葉が表示されます。

`ワードゲット`：ランダムで登録された言葉を取得します。

![ワードゲット画面](/img/getword.png "ワードゲット画面")

ここで参加者が登録した言葉がランダムで選ばれます。

**参加ボタン以降の画面は本人にしか見えないメッセージとなっています** <br/>
**メッセージが邪魔で削除したいときなどは「閉じる」ボタンや「これらのメッセージを削除する」を押して対応してください。**





※現在FAQのDiscordサーバーを構築中です。開設時にはこちらにリンクを張りますので、ぜひよろしくお願いします。


