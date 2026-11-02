---
date: 2026-10-30
project: agentic-streaming-videoqa
type: meeting-materials
topic: 中間発表の付録用：予習で追記した節・記録Agent・回答Agentのプロンプト全文と日本語訳
status: draft
target_meeting: 2026-10-30
tags: [meeting-materials, interim-presentation, prompt, record-agent, answer-agent, pre-study]
---

# プロンプト全文と日本語訳（2026-10-30）

- 出典（Workbench `2026_10_hayashi_pre_study_agent_system_workbench`）
  - 記録Agent: `prompts/history/record/v6g-lvb.txt`（予習の1節あり。予習なしの `v6g.txt` は、この1節がないだけで残りは同じ）
  - 回答Agent: `prompts/history/answer/a3.txt`。差し込みは `experiments/2026-10-22-lvb-duration-groups/scripts/answer.py`
- 日本語訳は Claude による。モデルに渡しているのは英語の原文だけ。
- `{{...}}` は実行時に差し込む部分。

## 1. 予習で追記した節（Claude が作成。記録Agentのプロンプトの2段落目に入る）

### 原文

```text
What the questions will ask (known in advance):
The questions are multiple-choice. Each question first points to one or more moments of the video by describing how they look (the place, the people and their clothes, the objects that are visible), and then asks one of these:
- what a person or animal does at that moment;
- which objects are there at that moment, or which person or object takes part in an event;
- what an object looks like at that moment (its color, shape, or number);
- what happens just before or just after an event, or which object appears just before or after another object;
- in which order several scenes happen;
- in which other scene the same object or person appears again, or how its look changes between two scenes.
So write the log so that each moment can be found again from how it looks: name people by how they look, name the objects that people use, hold, or point at with their color, and name the new place by what is easy to see there when the view changes (at most two features, as written below).
```

### 日本語訳

```text
来る質問の内容（事前に分かっていること）：
質問は多肢選択式です。どの質問も，まず動画の1つまたは複数の瞬間を，その見た目（場所，人とその服，見えている物）で指し示し，そのうえで次のどれかを問います。
- その瞬間に，人や動物が何をしているか
- その瞬間に何の物があるか，またはある出来事にどの人・物が関わっているか
- その瞬間に，ある物がどう見えるか（色，形，数）
- ある出来事の直前・直後に何が起きるか，またはある物の直前・直後にどの物が現れるか
- いくつかの場面がどの順に起きるか
- 同じ物や人が別のどの場面に再び現れるか，または2つの場面の間でその見た目がどう変わるか
だから，それぞれの瞬間を見た目から探し直せるように記録を書いてください：人は見た目で呼び，人が使う・持つ・指さす物は色付きで書き，画面が変わったときは，新しい場所をそこで見て分かりやすいもので呼んでください（下に書いたとおり，特徴は2つまで）。
```

## 2. 記録Agent（Qwen3-VL-4B）のプロンプト全文（v6g-lvb）

- chunk の8枚の画像（それぞれ「frame 1 (120.0 s):」のようなラベルの直後に置く）の後に，このテキストを続けて渡す。
- `{{chunk.frame_manifest}}` には，この chunk の各画像の番号と時刻の一覧が入る。

### 原文

```text
You are transcribing the events of a video into a time-stamped log. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will read it to answer questions about what happened.

What the questions will ask (known in advance):
（第1節の原文と同じ）

You are given one window of the video. Each image above is shown right after its label, such as "frame 1 (120.0 s):". The frames of this window are:
{{chunk.frame_manifest}}

Refer to frames by their numbers: F1 is frame 1, F2 is frame 2, and so on.

What an event is:
An event is a change. Go through the frames in order and write one event each time one of these happens:
1. A person, animal, or object starts an action, stops it, or switches to another action (for example, a man stops talking and holds up a phone). Each repetition of the same action is a new event.
2. Someone starts or stops handling an object (picks it up, puts it down, hands it over, turns it on).
3. A person, animal, or object comes into view or leaves the view.
4. The place or the view changes: a cut to a different place, the camera turning to a new view, or a large change of light or color.
At F1 you cannot see what came before, so start by writing what each visible person or animal is doing at F1.

How to find the events:
1. Compare each frame with the frame before it, and note the frames where something changes. These are the boundaries.
2. Between two boundaries nothing changes, so write one line that covers all those frames, from the first to the last.
3. If the next frame shows the same person doing the same thing in the same place, there is no boundary there: the line just gets longer. This is true even when the camera only moves closer, farther, or to another angle. A change of the person's facial expression or new subtitle text is not a boundary either.
4. Every line must say what changed at its first frame, so that it is different from the line before it. When the place changes, start the line with "view cuts to" and name the new place.

How to write an event:
- One event per line. Write who does what.
- Name each person by three features that stay the same during the whole video, so that the same person can be found again in other parts of the video:
  1. the upper clothing, with its color and type (for example, "black T-shirt", "red plaid shirt", "dark gray suit");
  2. the hair or face (for example, "short brown hair", "long blond hair", "bald", "glasses", "beard");
  3. one more thing that is easy to recognize (for example, text written on the clothing, a hat, a necklace, black gloves, a backpack).
  Example: "man in a black T-shirt with "SEEK" text, short brown hair". Write a feature only when you can see it; if you cannot see a feature, write the features you can see. Use the same three features every time the person appears.
- Write "man" or "woman" only when it is clear. If you are not sure, write "person". Never call the same person "man" in one line and "woman" in another.
- Name animals in the same way (color, size, one distinctive feature). Things that are not people or animals do not need these features.
- You may add one short detail about something that takes part in the event, such as what is shown on a phone screen or what the new place looks like. Add only one short detail: copy at most a few words of a long text, and do not list several objects, texts, signs, or icons. Do not describe things that do not take part in the event.
- For a change of place, name the new place with at most two features, such as "white room with a blue sofa".
- Write events of people in the background too, but only when you can clearly see what they do. Write the main people first.
- Write only what you can see. Do not guess hidden actions, reasons, or feelings.
- An action that continues over several frames is one event: write it once, with the range from its first frame to its last frame. Never write "continues", "still", or "again" for an action that has not stopped.
- Never write the same event twice. When every change in the frames is written, stop.

Do not write lines like these:
- Wrong (one action split into several lines):
  - [F6-F6] EVENT: man in a navy suit with gray hair and glasses speaks outside a building
  - [F7-F8] EVENT: man in a navy suit with gray hair and glasses continues to speak outside a building
  Right: - [F6-F8] EVENT: man in a navy suit with gray hair and glasses speaks outside a building
- Wrong (the same line repeated; the camera only moved closer):
  - [F1-F2] EVENT: woman in a beige coat with long black hair and a pearl necklace speaks outside a building
  - [F3-F4] EVENT: woman in a beige coat with long black hair and a pearl necklace speaks outside a building
  Right: - [F1-F4] EVENT: woman in a beige coat with long black hair and a pearl necklace speaks outside a building
- Wrong (a person named by one feature only, which many people share): - [F2-F2] EVENT: man in a white shirt runs across a street
  Right: - [F2-F2] EVENT: man in a white shirt with short black hair and a blue backpack runs across a street
- Wrong (a list of details): - [F5-F5] EVENT: view cuts to a blue screen with "Subscribe" text, two video thumbnails, and icons for Instagram, Twitter, and Snapchat
  Right: - [F5-F5] EVENT: view cuts to a blue screen with the text "Subscribe"

Output format:
Each line is: - [Ffirst-Flast] EVENT: description
[F3-F5] means the event is seen from frame 3 to frame 5. Use [F4-F4] for a single frame.

Example (from a different video with 8 frames):
- [F1-F3] EVENT: woman in a red apron with long black hair tied back and silver earrings talks to the camera in a kitchen with white tiles
- [F4-F4] EVENT: woman in a red apron with long black hair tied back and silver earrings picks up a brown egg
- [F5-F5] EVENT: woman in a red apron with long black hair tied back and silver earrings cracks the egg into a glass bowl
- [F6-F6] EVENT: view cuts to a close-up of a frying pan on a gas stove
- [F7-F8] EVENT: beaten egg is poured into the frying pan
- [F8-F8] EVENT: boy in a yellow T-shirt with short curly hair and a green cap comes into view from the right

Now write the events of this window.
```

### 日本語訳

```text
あなたは，動画の出来事を時刻付きの記録に書き起こしています。この記録は，動画について残る唯一の記録です。後で，動画を見られない人がこれを読んで，何が起きたかについての質問に答えます。

来る質問の内容（事前に分かっていること）：
（第1節の訳と同じ）

動画の1つの区間が与えられます。上の各画像は，「frame 1 (120.0 s):」のようなラベルのすぐ後に置かれています。この区間の画像は次のとおりです：
{{chunk.frame_manifest}}

画像は番号で呼んでください：F1 は frame 1，F2 は frame 2，以下同様です。

イベントとは何か：
イベントとは変化です。画像を順に見ていき，次のどれかが起きるたびに，イベントを1つ書いてください。
1. 人・動物・物が，動作を始める，やめる，別の動作に切り替える（例：男性が話すのをやめて電話を掲げる）。同じ動作の繰り返しは，1回ごとに新しいイベントです。
2. 誰かが物を扱い始める，または扱うのをやめる（手に取る，置く，手渡す，スイッチを入れる）。
3. 人・動物・物が画面に入ってくる，または画面から出ていく。
4. 場所や画面が変わる：別の場所への切り替わり，カメラが新しい向きを向く，光や色の大きな変化。
F1 ではそれより前が見えないので，まず F1 で見えている各人・各動物が何をしているかを書いてください。

イベントの見つけ方：
1. 各画像を1つ前の画像と比べ，何かが変わった画像に印を付けます。これが区切りです。
2. 2つの区切りの間では何も変わらないので，それらの画像全部をまとめて，最初から最後までを1行で書きます。
3. 次の画像でも同じ人が同じ場所で同じことをしていれば，そこは区切りではありません。行が長くなるだけです。カメラが近づく，遠ざかる，別の角度になるだけのときも同じです。人の表情の変化や新しい字幕の文字も，区切りではありません。
4. どの行も，その最初の画像で何が変わったかを書き，前の行と違うものにしてください。場所が変わったときは，行を「view cuts to」で始め，新しい場所を書いてください。

イベントの書き方：
- 1行に1つのイベント。誰が何をするかを書きます。
- 人は，動画全体を通して変わらない3つの特徴で呼んでください。動画の別の部分でも同じ人を見つけられるようにするためです：
  1. 上半身の服，その色と種類（例：「黒いTシャツ」「赤いチェックのシャツ」「濃いグレーのスーツ」）
  2. 髪または顔（例：「短い茶髪」「長い金髪」「はげ頭」「眼鏡」「ひげ」）
  3. もう1つ，見分けやすいもの（例：服に書かれた文字，帽子，ネックレス，黒い手袋，リュック）
  例：「"SEEK" の文字が入った黒いTシャツ，短い茶髪の男性」。特徴は見えるときだけ書いてください。見えない特徴があれば，見える特徴を書いてください。その人が出てくるたびに，同じ3つの特徴を使ってください。
- 「男性」「女性」は，はっきりしているときだけ書いてください。確かでなければ「人」と書いてください。同じ人を，ある行では男性，別の行では女性と書かないでください。
- 動物も同じように呼んでください（色，大きさ，目立つ特徴1つ）。人や動物でない物には，これらの特徴は要りません。
- イベントに関わる物について，短い説明を1つ足してもかまいません（例：電話の画面に何が映っているか，新しい場所がどう見えるか）。足すのは短い説明1つだけです：長い文は数語だけ写し，物・文字・看板・アイコンを複数並べないでください。イベントに関わらない物は書かないでください。
- 場所が変わったときは，新しい場所を特徴2つまでで書いてください（例：「青いソファのある白い部屋」）。
- 背景の人のイベントも書いてください。ただし，何をしているかがはっきり見えるときだけです。主な人を先に書いてください。
- 見えることだけを書いてください。隠れた動作，理由，気持ちを推測しないでください。
- 何枚にもわたって続く動作は1つのイベントです：最初の画像から最後の画像までの範囲で，1回だけ書いてください。止まっていない動作に「続ける」「まだ」「再び」と書かないでください。
- 同じイベントを2回書かないでください。画像の中の変化をすべて書いたら，やめてください。

次のような行は書かないでください：
- 誤り（1つの動作が何行にも分かれている）：
  - [F6-F6] EVENT: 紺のスーツ，白髪，眼鏡の男性が建物の外で話す
  - [F7-F8] EVENT: 紺のスーツ，白髪，眼鏡の男性が建物の外で話し続ける
  正しい：- [F6-F8] EVENT: 紺のスーツ，白髪，眼鏡の男性が建物の外で話す
- 誤り（同じ行の繰り返し。カメラが近づいただけ）：
  - [F1-F2] EVENT: ベージュのコート，長い黒髪，真珠のネックレスの女性が建物の外で話す
  - [F3-F4] EVENT: ベージュのコート，長い黒髪，真珠のネックレスの女性が建物の外で話す
  正しい：- [F1-F4] EVENT: ベージュのコート，長い黒髪，真珠のネックレスの女性が建物の外で話す
- 誤り（多くの人に当てはまる特徴1つだけで人を呼んでいる）：- [F2-F2] EVENT: 白いシャツの男性が通りを走って渡る
  正しい：- [F2-F2] EVENT: 白いシャツ，短い黒髪，青いリュックの男性が通りを走って渡る
- 誤り（細かいことを並べている）：- [F5-F5] EVENT: 画面が切り替わり，「Subscribe」の文字，動画のサムネイル2つ，Instagram・Twitter・Snapchat のアイコンがある青い画面
  正しい：- [F5-F5] EVENT: 画面が切り替わり，「Subscribe」の文字がある青い画面

出力の形式：
各行は：- [F最初-F最後] EVENT: 説明
[F3-F5] は，そのイベントが frame 3 から frame 5 まで見えることを表します。1枚だけなら [F4-F4] と書いてください。

例（8枚の別の動画から）：
- [F1-F3] EVENT: 赤いエプロン，後ろで結んだ長い黒髪，銀のイヤリングの女性が，白いタイルの台所でカメラに向かって話す
- [F4-F4] EVENT: 赤いエプロン，後ろで結んだ長い黒髪，銀のイヤリングの女性が茶色い卵を手に取る
- [F5-F5] EVENT: 赤いエプロン，後ろで結んだ長い黒髪，銀のイヤリングの女性が卵をガラスのボウルに割り入れる
- [F6-F6] EVENT: 画面が切り替わり，ガスコンロの上のフライパンのアップ
- [F7-F8] EVENT: 溶き卵がフライパンに注がれる
- [F8-F8] EVENT: 黄色いTシャツ，短い巻き毛，緑の帽子の男の子が右から画面に入ってくる

では，この区間のイベントを書いてください。
```

## 3. 回答Agent（Qwen3-VL-4B，テキストだけ）のプロンプト全文（a3）

- `{{duration}}`: 動画の長さ（例：`6 min 45 s`）
- `{{log}}`: 記録の全行。1行は `- [分:秒-分:秒] 文`。記録なしの対照では空
- `{{log_note}}`: Stage B の後の記録のときだけ，次の1文が入る（それ以外は空）
  - 原文: ` A tag such as P04 before the event names a person or animal: lines with the same tag show the same one (people who change clothes may get a new tag).`
  - 訳: 「出来事の前の P04 のような札は，人や動物を表します。同じ札の行は同じ人・動物です（服を着替えた人には新しい札が付くことがあります）。」
- `{{question}}`: 質問文（英語のまま），`{{options}}`: 選択肢（`A. …` の形で1行に1つ）

### 原文

```text
You will answer a multiple-choice question about a video. You cannot watch the video. Instead, you are given a log of the events in the video, written by someone who watched it. The video is {{duration}} long.

Each line of the log is: - [start-end] event. The times are minutes:seconds from the start of the video, and the lines are in time order.{{log_note}}

<log>
{{log}}
</log>

Question: {{question}}

Options:
{{options}}

How to answer:
1. The question first describes one or more moments of the video by how they look. Find the lines of the log that best match that description (the place, the people and their clothes, the objects).
2. Read those lines and the lines just before and after them, and choose the option that the log supports best.
3. The log may miss the moment or describe it in other words. Then guess: choose the option that fits the log best. You must always choose one option. Do not explain and do not say that the log does not mention it.

Answer with the option's letter from the given choices directly.
The best answer is:
```

### 日本語訳

```text
動画についての多肢選択式の質問に答えてください。あなたは動画を見られません。代わりに，動画を見た人が書いた，動画の出来事の記録が与えられます。動画の長さは {{duration}} です。

記録の各行は「- [開始-終了] 出来事」です。時刻は動画の先頭からの分:秒で，行は時刻の順に並んでいます。{{log_note}}

<log>
{{log}}
</log>

質問：{{question}}

選択肢：
{{options}}

答え方：
1. 質問は，まず動画の1つまたは複数の瞬間を，その見た目で説明しています。その説明（場所，人とその服，物）にいちばん合う記録の行を探してください。
2. それらの行と，そのすぐ前後の行を読み，記録がいちばん支持する選択肢を選んでください。
3. 記録がその瞬間を書き漏らしていたり，別の言葉で書いていたりすることがあります。そのときは推測してください：記録にいちばん合う選択肢を選んでください。必ず1つ選ばなければなりません。説明はせず，記録に書かれていないとも言わないでください。

与えられた選択肢から，その記号だけで直接答えてください。
最も良い答えは：
```
