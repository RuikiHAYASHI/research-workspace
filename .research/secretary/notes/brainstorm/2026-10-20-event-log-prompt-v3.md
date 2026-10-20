---
date: 2026-10-20
project: agentic-streaming-videoqa
topic: イベント記録Agentのプロンプト v3（壁打ちで決めた形）と各部分の役割
status: decided-tentative
tags: [prompt, event-log, recording-agent, qwen3-vl, longvideobench]
---

# イベント記録Agentのプロンプト v3

実装: [記録Agent v3 Workbench spec](../../../lab/projects/agentic-streaming-videoqa/specs/2026-10-20-pre-study-record-workbench-spec.md)（新リポジトリ 2026_10_hayashi_pre_study_agent_system_workbench）。

経緯の詳細は [LongVideoBenchのタスク一覧（T系は当面外す）](2026-10-19-longvideobench-task-table-without-subtitles.md) の「記録プロンプトの設計」以降にある。このメモは、2026-10-19〜20の壁打ちで決まった形をまとめたもの。2026-10-20に実際の動画（約22秒・約3分）で初めて動かした（結果はspecの8.4）。

## 決まったこと

| 項目 | 決定 |
| --- | --- |
| 記録の役割 | **索引**。後で質問文の場面の説明で検索して、何が・いつ・どこにあったかを見つけるためのもの。文字にしきれない細部は残せない前提 |
| 対象タスク | T系（字幕起点）7カテゴリを外した10カテゴリ |
| 予習 | 当面は人が手で書いたプロンプトで代用する（このプロンプト自体が「手書きの予習」） |
| 呼び出し方 | 1区間につき1回の呼び出しで、全種類を出力させる |
| 前の区間の記録 | 見せない（区間ごとに独立） |
| 例 | 1つだけ。評価データと関係のない架空の動画から作る |
| 出力形式 | 1行に1つの事実。`- [start-end] TYPE: description` |
| SCENE | **簡単な場所の説明だけ**（例:「白い壁に囲まれた部屋」）。場所が変わったときだけ新しい行 |
| ENTITY・OBJECT・EVENT・TEXT | **できる限り細かく**書く。物は1つにつき1行、動作は1つにつき1行 |
| 時間 | frameの時刻から写し、事実が見えている範囲を正確に書く |
| 続いている動作 | 同じ動作が複数のframeで続いていたら1行にまとめる。動作が変わったら分ける |
| TEXT | 画面に焼き込まれた字幕も含めてよい |
| 区間の端 | 「区間の最初から続いている／最後まで続いている」は、プロンプトではなく**コードで判定**する（行の時刻が区間の最初・最後のframeと一致するか） |
| 区間の既定値 | 20秒・8枚（約2.5秒に1枚）。ブラウザ上では変えられる |
| `max_new_tokens` | **大きく増やす**（案: 4096）。出力token数・上限に達したか（`hit_max_new_tokens`）・生成時間を区間ごとに記録する |
| 文面 | Qwen専用の言い回しは使わない（研究室の方の意見）。Qwenに合わせるのはコード・設定の側 |

## プロンプト v3

`{{chunk.start}}`, `{{chunk.end}}`, `{{chunk.frame_manifest}}` は、今のWorkbenchのテンプレート変数をそのまま使う想定。

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after. So record as many details as you can, not only the main subject.

You are viewing one window of the video, from {{chunk.start}} s to {{chunk.end}} s. The frames are listed below with their timestamps in seconds from the start of the video:
{{chunk.frame_manifest}}

Write log lines for this window only.

What to record:
- SCENE: one short line about the place only (for example, "room with white walls", "outdoor street at night"). Write a new SCENE line only when the place changes.
- ENTITY: each visible person or animal, one per line, in as much detail as you can: clothing and colors, hair, accessories, and position on the screen.
- OBJECT: each visible object, one per line, in as much detail as you can: color, shape, material, count, and position (for example "on the table to the left of the woman", "upper right corner"). Include small and background objects.
- EVENT: each action, one per line, in as much detail as you can. Write one person or object doing one action.
- CHANGE: a change in how a person or object looks or where it is (color, shape, clothing, position, state).
- TEXT: text that is part of the image (titles, signs, labels, captions, numbers on clocks or screens). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

How to split actions:
- Split a sequence of different actions into separate EVENT lines, each with its own time. For example, "picks up a cup", "drinks from the cup", and "puts the cup down" are three lines, not one.
- Do not summarize several actions into one line such as "has a drink".

How to handle time:
- Look at all frames together, not one by one.
- start and end must be timestamps copied from the frame list. They must cover exactly the frames where the fact is seen.
- If the same person or object keeps doing the same thing across several frames, write one line from the first to the last of those frames. For example, if a person talks to the camera in every frame from 100.0 s to 116.0 s, write one line "[100.0-116.0] EVENT: ... talks to the camera", not one line per frame.
- Start a new line when the action, the person or object, or the place changes.
- If the person or object is not visible in some frames in the middle, end the line before that gap and start a new line after it.
- If a fact is seen in only one frame, use the same timestamp twice.

Rules:
- One fact per line. Each line must be concrete.
- Record only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- If nothing happens in the window, still write the SCENE, ENTITY, and OBJECT lines, and write one EVENT line: "no notable action".
- Do not answer any question. Do not write anything other than log lines.

Output format:
Each line is: - [start-end] TYPE: description
TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video):
- [120.0-137.5] SCENE: kitchen with white wall tiles
- [120.0-137.5] ENTITY: woman in a red apron over a white shirt, long black hair tied back, standing behind the table
- [120.0-137.5] OBJECT: rectangular wooden table in the center
- [120.0-137.5] OBJECT: clear glass bowl on the table in front of the woman
- [120.0-137.5] OBJECT: round white wall clock in the upper right, hands at about 3:15
- [120.0-125.0] EVENT: woman in a red apron talks to the camera
- [127.5-127.5] EVENT: woman in a red apron picks up a brown egg
- [130.0-130.0] EVENT: woman in a red apron cracks the egg into the glass bowl
- [132.5-137.5] EVENT: woman in a red apron whisks the egg in the glass bowl with a metal whisk
- [120.0-122.5] TEXT: "Easy Omelette"

Now write the log lines for {{chunk.start}} s to {{chunk.end}} s.
```

## 各部分の役割

| 部分 | 役割 | 背景（壁打ちで出た理由） |
| --- | --- | --- |
| 冒頭（目的） | 「後で、動画を見られない人がこの記録を検索して質問に答える」と伝え、何を残すべきかをモデルに判断させる | 過去のプロンプトは目的を伝えておらず、短すぎて制御できていなかった |
| 冒頭（質問の形） | LongVideoBenchの質問が「見た目の細かい説明で場面を指す」ことを伝える | 質問文の場面の説明は中央値32語（val、T系以外）。記録が同じくらい細かくないと場面を探せない |
| 区間とframeの時刻 | 区間の範囲と、各frameの時刻を渡す | 時刻は計算させずに写させる。小さいモデルは時刻の計算を間違えやすい |
| SCENE | 場所だけを短く書く。場所が変わったら新しい行 | 1区間にSCENEが複数あれば場面が切り替わったと分かる。細部はOBJECT・ENTITYに回す |
| ENTITY | 人・動物を見た目で細かく書く | 質問文は服の色・髪・位置で人を指す |
| OBJECT | 物を1つにつき1行、細かく書く | S2O・S2A・SAAは小さな物や見た目を問う。場面の説明にも背景の物が出る |
| EVENT | 動作を1つにつき1行 | E3E（〜の後に何をしたか）は数秒の間の小さな動作の前後を問う。まとめた要約は後の集約で作る |
| CHANGE | 見た目・位置・状態の変化 | SAA（属性の変化）用 |
| TEXT | 画面の文字をそのまま写す | 質問文は画面の文字で場面を指すことがある。焼き込まれた字幕も含める |
| 呼び方のルール | 人・物を見た目で呼び、同じものは同じ呼び方にする | 前の記録を見せないので、区間をまたいで同じ人・物かを判断する手がかりは呼び方しかない。物体系（O3O, SOS）の正答率に直結する |
| 動作の分け方 | 違う動作は別の行にする | 「コップを取って水を飲む」を1行にすると、前後関係が消える |
| 時間の扱い | 時刻は写す。続いている動作は1行、途中で見えなくなったら分ける | 1枚ずつ書くと「話している」が8行並ぶ。画像は別々に渡される（`image_list`）ので明示が必要 |
| 禁止事項 | 推測・理由づけ・意見・回答を書かない | 見えていないことの作り話を防ぐ |
| 何もないとき | SCENE・ENTITY・OBJECTと「no notable action」だけ書く | 何もない区間で作り話を書くのを防ぐ |
| 出力形式・例（最後に置く） | 形式を1行で示し、架空の料理動画の例を1つ見せる | 小さいモデルでも最後の指示は守りやすい。例で、物の細かさ・動作の分け方・続いている動作のまとめ方を見せる |

## このプロンプトでできること・できないこと（推論）

できること:

- 区間の中での場面の切り替わり（SCENEが複数）
- 人・物の観測と、その見た目の細部
- 一連の動作と、動作の変化（行の並び）
- 画面に焼き込まれた文字

できないこと:

- 区間の境目をまたぐ判断（場面の切り替わり、続いている動作、初登場・再登場）: 集約の段階で行う
- 発話の内容（音声を入れていない）
- frameとframeの間（約2.5秒）に起きた短い出来事
- 別ファイルの字幕（T系の大半）
- 解像度で読めない細部（時計の時刻など）

## 確かめること

- 1本の動画で動かし、次を見る:
  - 形式が守られているか（行の形、TYPE、時刻がframeの時刻と一致するか）
  - 続いている動作が1行にまとまっているか、違う動作が分かれているか
  - 呼び方が区間をまたいで一致するか
  - 出力token数と、上限に達した区間があるか、1区間の生成時間
- 記録が長くなるので、回答の段階では記録を検索して関係する行だけを渡す形が必要になる見込み（回答プロンプトは未設計）。
