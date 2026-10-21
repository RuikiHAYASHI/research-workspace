---
date: 2026-10-21
project: agentic-streaming-videoqa
topic: 記録Agentのプロンプトの変遷（旧Workbench → v0〜v5）と、各版の差分・問題点・次の版の目的
status: log
tags: [prompt, event-log, recording-agent, qwen3-vl, longvideobench, prompt-engineering, work-log]
---

# 記録Agentのプロンプトの変遷（2026-10-19〜21）

このメモは作業ログです。各版について **本文 → 差分 → 問題点（実際の出力例） → 次の版の目的** の順に書いた。差分は前の版からの unified diff（`-` が消した行、`+` が足した行）。本文の全文は各節の折りたたみ（「〜の本文（全文）」）にある。

- 出力例・数値は、実際に保存した実行結果（`result.json`、試行スクリプトのJSON）から自動で抜き出した。数値を手で書き換えていない。
- モデルはすべて `Qwen/Qwen3-VL-4B-Instruct`、temperature 0（貪欲生成）、GPU 1台（RTX A4000）。区間は20秒・8枚（約2.5秒に1枚）。
- 関連: [タスク一覧と記録プロンプトの設計の壁打ち](../../../../secretary/notes/brainstorm/2026-10-19-longvideobench-task-table-without-subtitles.md)、[v3](../../../../secretary/notes/brainstorm/2026-10-20-event-log-prompt-v3.md)、[v4](../../../../secretary/notes/brainstorm/2026-10-20-event-log-prompt-v4.md)、[v5](../../../../secretary/notes/brainstorm/2026-10-21-event-log-prompt-v5.md)、[Workbench spec](../specs/2026-10-20-pre-study-record-workbench-spec.md)。
- 新リポジトリ: `RuikiHAYASHI/2026_10_hayashi_pre_study_agent_system_workbench`（本文は `prompts/record/image/v{3,4,5}/prompt.en.txt`）。

## 全体の流れ（一覧）

| 版 | 日付 | どこで作ったか | 実行 | 一番大きな変更 | 何が分かったか |
| --- | --- | --- | --- | --- | --- |
| 旧Workbench | 〜10/08 | 旧Workbench | あり（旧） | — | 「短すぎてモデルを制御できていない」と指摘された |
| v0 | 10/20 | 壁打ち | なし | 目的・入力・観点・呼び方・禁止事項・形式・例を全部書く（約400語） | — |
| v1 | 10/20 | 壁打ち | なし | 続いている動作を1行にまとめる規則 | — |
| v2 | 10/20 | 壁打ち | なし | OBJECTを追加、動作を1つずつ分ける | — |
| v3 | 10/20 | 壁打ち（確定） | あり（22秒・3分） | SCENEは場所だけ、他はできる限り細かく | TEXTのループ、1枚目だけを書く、時刻のずれ |
| v4a | 10/20 | 試行 | 5区間 | 1枚ずつ見る、カット、TEXT 5行まで | ループは止まった。画像と時刻の対応がずれる |
| （入力） | 10/20 | コード | — | 画像の直前に「frame k (t s):」 | v4b以降の前提 |
| v4b | 10/20 | 試行 | 4区間 | ラベルを使う、区間の終わりの時刻を外す | 時刻は一致。1枚ずれが残る |
| v4c | 10/20 | 試行 | 2区間 | 時刻の書き方の例 | 悪化 |
| v4d | 10/20 | 試行 | 2区間 | 範囲をframe番号 `[F3-F5]` で書く | 対応が全frameで正しくなった |
| v4e → **v4** | 10/20 | 確定 | 3分の動画全体 | 続く枚を1範囲にまとめる例 | 14分16秒 → 6分16秒、TEXT 277 → 19 |
| v5a | 10/21 | 試行 | 3本 | 場面の一覧を先に書く2段階 | EVENTが増え、まとめ損ねが減った |
| v5b | 10/21 | 試行 | 3本 | 誤りと正しい例の組 | 複数の人を1行が0に |
| v5c | 10/21 | 試行 | 3本 | 動作はEVENTへ、同じ場所は1場面 | 料理は全基準を満たした |
| v5d | 10/21 | 試行 | 3本 | 各ENTITYの直後にEVENT、行数上限50 | OBJECTのループで悪化 |
| v5e | 10/21 | 試行 | 3本＋2本 | OBJECT 5行まで、上限40に戻す | 3本は良好。追加の2本で文字の多い画面が暴走 |
| v5f | 10/21 | 試行 | 3本 | 「何もない」行の言い換え | ループ再発で悪化 |
| v5g → **v5** | 10/21 | 確定 | 3本＋2本 | 文字の多い画面はタイトルだけ | 3本で最良。スマホの色一覧はまだ暴走 |

## 0. 旧Workbenchのプロンプト（出発点）

旧Workbench（`2026_09_hayashi_longvideoqa_workbench`、`65af089`）の Situation Agent の既定プロンプト。Situation → Summary → Answer の3 Agent構成の1段目で、区間ごとの状況説明を自由な文章で書かせていた。

```text
Original video window: [{{chunk.start}}, {{chunk.end}}) seconds.
The clip timeline starts at 0 seconds and uses the target sample rate. Source-video frame IDs and actual absolute timestamps are authoritative.
Frame manifest:
{{chunk.frame_manifest}}

Describe the visible people, objects, actions, and meaningful state changes across the clip in chronological order.
Do not add facts that are not directly supported by the visible clip.
Do not infer unseen frames or future events, and do not answer any question.
Return only a concise plain text description.
```

### 問題点

- 過去のMTGで「プロンプトの長さが不十分で、モデルを適切に制御できていない」と指摘された（2026-10-20の相談の前提）。
- 中身で決めていないことが多い（2026-10-20の壁打ちで整理）:

| 決めていないこと | 起きる問題 |
| --- | --- |
| 何のために書くのか | 後で質問に答えるための記録だと知らないので、何が大事か判断できない |
| 何を1つのイベントとするか | 粒度が区間ごとにばらばら |
| 人・物をどう呼ぶか | 同じ人が区間ごとに「a woman」「the person」と変わり、再登場を追えない |
| 出力の形式 | 散文になり、時刻と内容の対応が取れない |
| 何も起きないときどうするか | 毎回、無理に何かを書く |

### 次の版の目的

- 目的（索引として後で検索される記録）を伝える。
- 研究室の方の意見「Qwen専用の言い回しは不要、汎用のプロンプトで十分」に従い、文面は汎用にする（Qwenに合わせるのは入力の渡し方・出力の上限などコード側）。
- LongVideoBenchの質問は「見た目の細かい説明で場面を指す」（場面の説明の中央値32語、T系以外のval）ので、記録も同じくらい細かく書かせる。
- 1行1事実の決まった形式にする（後で集約・検索しやすい）。

## 1. v0（壁打ちの最初の案、2026-10-20）

<details><summary>v0 の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will use only this log to answer multiple-choice questions about it. The questions are not known now. They usually point to a moment by describing how it looks (for example, "a man in a black suit standing in front of a white table"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video, from {{chunk.start}} s to {{chunk.end}} s. The frames are listed below with their timestamps in seconds from the start of the video:
{{chunk.frame_manifest}}

Write log lines for this window only.

What to record:
- SCENE: the place and background (location, notable background objects, layout of the screen).
- ENTITY: each visible person, animal, and important object, with its appearance.
- EVENT: each action or happening, in time order.
- CHANGE: a change in how a person or object looks or where it is (color, shape, clothing, position, state).
- TEXT: text that is part of the image (titles, signs, labels). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.


Rules:
- One fact per line. Keep each line short and concrete.
- Include colors, shapes, counts, and left/right positions when they are visible.
- Record only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- If nothing happens in the window, still write the SCENE and ENTITY lines, and write one EVENT line: "no notable action".
- Do not answer any question. Do not write anything other than log lines.

Output format:
Each line is: - [start-end] TYPE: description
start and end are timestamps in seconds copied from the frame list. If a fact is seen in only one frame, use the same timestamp twice. TYPE is one of SCENE, ENTITY, EVENT, CHANGE, TEXT.

Example (from a different video):
- [120.0-137.5] SCENE: kitchen with white wall tiles; wooden table in the center
- [120.0-137.5] ENTITY: woman in a red apron with long black hair
- [120.0-127.5] EVENT: woman in a red apron talks to the camera
- [130.0-137.5] EVENT: woman in a red apron whisks eggs in a glass bowl
- [130.0-137.5] CHANGE: eggs in the glass bowl change from yellow liquid to pale foam
- [120.0-122.5] TEXT: "Easy Omelette"

Now write the log lines for {{chunk.start}} s to {{chunk.end}} s.
```

</details>

### 差分（旧Workbench → v0）

全面的に書き直した（旧版は5行、v0は約400語）。足したもの:
1. 目的: 「この記録だけが残り、動画を見られない人が後で質問に答える」。質問は未知で、見た目の説明で場面を指してくる。
2. 入力: 区間の開始・終了と、frameごとの時刻の一覧。
3. 観点（手書きの予習）: SCENE / ENTITY / EVENT / CHANGE / TEXT。
4. 人・物の呼び方: 見た目の特徴で呼び、同じものは同じ呼び方。
5. 禁止事項: 推測・理由づけ・意見・回答を書かない。何もないときは「no notable action」。
6. 出力形式（最後に置く）: `- [start-end] TYPE: description`、時刻はframe一覧から写す。
7. 例を1つ（架空の料理動画）。

### 決めたこと（林、壁打ち）

- 前の区間の記録はモデルに見せない（区間ごとに独立）。例は短く1つ。出力は1行1事実。
- TEXT（画面上の文字）は含める（焼き込み字幕を含む）。`max_new_tokens` は増やす。区間の既定値は20秒・8枚。

### 問題点（実行前の指摘）

- 林: 「複数frameで同じ人物の同じ動作を観測したときのルールは？ 16秒間話し続けるシーンなら、ずっと話している、としたい」→ v0にはその規則がなく、frameごとに「話している」が8行並ぶおそれがあった（画像は別々に渡される）。

### 次の版の目的

続いている動作を1行にまとめる規則を足す。

## 2. v1（2026-10-20）

<details><summary>v1 の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will use only this log to answer multiple-choice questions about it. The questions are not known now. They usually point to a moment by describing how it looks (for example, "a man in a black suit standing in front of a white table"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video, from {{chunk.start}} s to {{chunk.end}} s. The frames are listed below with their timestamps in seconds from the start of the video:
{{chunk.frame_manifest}}

Write log lines for this window only.

What to record:
- SCENE: the place and background (location, notable background objects, layout of the screen).
- ENTITY: each visible person, animal, and important object, with its appearance.
- EVENT: each action or happening, in time order.
- CHANGE: a change in how a person or object looks or where it is (color, shape, clothing, position, state).
- TEXT: text that is part of the image (titles, signs, labels). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

How to handle several frames:
- Look at all frames together, not one by one.
- If the same person or object keeps doing the same thing across several frames, write one line that spans from the first to the last of those frames. For example, if a person talks to the camera in every frame from 100.0 s to 116.0 s, write one line "[100.0-116.0] EVENT: ... talks to the camera", not one line per frame.
- Start a new line only when the action, the person or object, or the place changes.
- If the person or object is not visible in some frames in the middle, end the line before that gap and start a new line after it.
- SCENE, ENTITY, and TEXT lines also span all consecutive frames where they are seen.

Rules:
- One fact per line. Keep each line short and concrete.
- Include colors, shapes, counts, and left/right positions when they are visible.
- Record only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- If nothing happens in the window, still write the SCENE and ENTITY lines, and write one EVENT line: "no notable action".
- Do not answer any question. Do not write anything other than log lines.

Output format:
Each line is: - [start-end] TYPE: description
start and end are timestamps in seconds copied from the frame list. If a fact is seen in only one frame, use the same timestamp twice. TYPE is one of SCENE, ENTITY, EVENT, CHANGE, TEXT.

Example (from a different video):
- [120.0-137.5] SCENE: kitchen with white wall tiles; wooden table in the center
- [120.0-137.5] ENTITY: woman in a red apron with long black hair
- [120.0-127.5] EVENT: woman in a red apron talks to the camera
- [130.0-137.5] EVENT: woman in a red apron whisks eggs in a glass bowl
- [130.0-137.5] CHANGE: eggs in the glass bowl change from yellow liquid to pale foam
- [120.0-122.5] TEXT: "Easy Omelette"

Now write the log lines for {{chunk.start}} s to {{chunk.end}} s.
```

</details>

### 差分（v0 → v1）

```diff
--- v0
+++ v1
@@ -19,0 +20,6 @@
+How to handle several frames:
+- Look at all frames together, not one by one.
+- If the same person or object keeps doing the same thing across several frames, write one line that spans from the first to the last of those frames. For example, if a person talks to the camera in every frame from 100.0 s to 116.0 s, write one line "[100.0-116.0] EVENT: ... talks to the camera", not one line per frame.
+- Start a new line only when the action, the person or object, or the place changes.
+- If the person or object is not visible in some frames in the middle, end the line before that gap and start a new line after it.
+- SCENE, ENTITY, and TEXT lines also span all consecutive frames where they are seen.
```

### なぜこの変更か

- 同じ人・同じ動作が複数frameで続くなら、最初のframeから最後のframeまでの1行にする（例: 100.0〜116.0秒ずっと話す → 1行）。
- 動作・人・場所が変わったときだけ新しい行。途中で見えなくなったら分ける。
- 区間の端で続いているかは、プロンプトではなくコードで判定する（行の時刻が区間の最初・最後のframeと一致するか）と決めた（林）。

### 問題点（実行前の指摘）

- 林: 「1行程度で出力させると、『女性の隣の机に花瓶』『右上の時計の時刻』のような細かい情景が削れる。LongVideoBenchでは細かい情景が必要なケースがある」。
  - 場面の説明は中央値32語、上位10%で57語。S2O・S2A・SAAは細かい物や見た目を問う。
- 林: 「動作も1行単位に分けるのか？（コップを取って水を飲む）」。E3E（〜の後に何をしたか）は数秒の小さな動作の前後を問うので、分けないと前後関係が消える。

### 次の版の目的

- 細かさは「長い1行」ではなく「行を増やす」ことで残す（物1つにつき1行、OBJECTを追加）。
- 動作は1つにつき1行。まとめた要約は後の集約で作る。
- 記録は「索引」と位置づける（決定）。文字にしきれない細部は残せない前提。

## 3. v2（2026-10-20）

<details><summary>v2 の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after. So record details, not only the main subject.

You are viewing one window of the video, from {{chunk.start}} s to {{chunk.end}} s. The frames are listed below with their timestamps in seconds from the start of the video:
{{chunk.frame_manifest}}

Write log lines for this window only.

What to record:
- SCENE: the place and background (location, lighting, layout of the screen).
- ENTITY: each visible person or animal, with appearance (clothing colors, hair, accessories) and position.
- OBJECT: each visible object, one object per line, with color, shape, count, and position (for example "on the table to the left of the woman", "upper right corner"). List as many visible objects as you can, including small and background objects.
- EVENT: each action, one action per line. Write one person or object doing one action.
- CHANGE: a change in how a person or object looks or where it is (color, shape, clothing, position, state).
- TEXT: text that is part of the image (titles, signs, labels, captions, numbers on clocks or screens). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

How to split actions:
- Split a sequence of different actions into separate EVENT lines, each with its own time. For example, "picks up a cup", "drinks from the cup", and "puts the cup down" are three lines, not one.
- Do not summarize several actions into one line such as "has a drink".

How to handle several frames:
- Look at all frames together, not one by one.
- If the same person or object keeps doing the same thing across several frames, write one line that spans from the first to the last of those frames. For example, if a person talks to the camera in every frame from 100.0 s to 116.0 s, write one line "[100.0-116.0] EVENT: ... talks to the camera", not one line per frame.
- Start a new line only when the action, the person or object, or the place changes.
- If the person or object is not visible in some frames in the middle, end the line before that gap and start a new line after it.
- SCENE, ENTITY, OBJECT, and TEXT lines also span all consecutive frames where they are seen.

Rules:
- One fact per line. Keep each line short and concrete.
- Record only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- If nothing happens in the window, still write the SCENE, ENTITY, and OBJECT lines, and write one EVENT line: "no notable action".
- Do not answer any question. Do not write anything other than log lines.

Output format:
Each line is: - [start-end] TYPE: description
start and end are timestamps in seconds copied from the frame list. If a fact is seen in only one frame, use the same timestamp twice. TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video):
- [120.0-137.5] SCENE: bright kitchen with white wall tiles
- [120.0-137.5] ENTITY: woman in a red apron with long black hair, standing behind the table
- [120.0-137.5] OBJECT: wooden table in the center
- [120.0-137.5] OBJECT: glass bowl on the table in front of the woman
- [120.0-137.5] OBJECT: round white wall clock in the upper right, hands at about 3:15
- [120.0-125.0] EVENT: woman in a red apron talks to the camera
- [127.5-127.5] EVENT: woman in a red apron picks up an egg
- [130.0-130.0] EVENT: woman in a red apron cracks the egg into the glass bowl
- [132.5-137.5] EVENT: woman in a red apron whisks the egg in the glass bowl
- [120.0-122.5] TEXT: "Easy Omelette"

Now write the log lines for {{chunk.start}} s to {{chunk.end}} s.
```

</details>

### 差分（v1 → v2）

```diff
--- v1
+++ v2
@@ -1 +1 @@
-You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will use only this log to answer multiple-choice questions about it. The questions are not known now. They usually point to a moment by describing how it looks (for example, "a man in a black suit standing in front of a white table"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.
+You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after. So record details, not only the main subject.
@@ -9,3 +9,4 @@
-- SCENE: the place and background (location, notable background objects, layout of the screen).
-- ENTITY: each visible person, animal, and important object, with its appearance.
-- EVENT: each action or happening, in time order.
+- SCENE: the place and background (location, lighting, layout of the screen).
+- ENTITY: each visible person or animal, with appearance (clothing colors, hair, accessories) and position.
+- OBJECT: each visible object, one object per line, with color, shape, count, and position (for example "on the table to the left of the woman", "upper right corner"). List as many visible objects as you can, including small and background objects.
+- EVENT: each action, one action per line. Write one person or object doing one action.
@@ -13 +14 @@
-- TEXT: text that is part of the image (titles, signs, labels). Copy it exactly.
+- TEXT: text that is part of the image (titles, signs, labels, captions, numbers on clocks or screens). Copy it exactly.
@@ -19,0 +21,4 @@
+How to split actions:
+- Split a sequence of different actions into separate EVENT lines, each with its own time. For example, "picks up a cup", "drinks from the cup", and "puts the cup down" are three lines, not one.
+- Do not summarize several actions into one line such as "has a drink".
+
@@ -25 +30 @@
-- SCENE, ENTITY, and TEXT lines also span all consecutive frames where they are seen.
+- SCENE, ENTITY, OBJECT, and TEXT lines also span all consecutive frames where they are seen.
@@ -29 +33,0 @@
-- Include colors, shapes, counts, and left/right positions when they are visible.
@@ -31 +35 @@
-- If nothing happens in the window, still write the SCENE and ENTITY lines, and write one EVENT line: "no notable action".
+- If nothing happens in the window, still write the SCENE, ENTITY, and OBJECT lines, and write one EVENT line: "no notable action".
@@ -36 +40 @@
-start and end are timestamps in seconds copied from the frame list. If a fact is seen in only one frame, use the same timestamp twice. TYPE is one of SCENE, ENTITY, EVENT, CHANGE, TEXT.
+start and end are timestamps in seconds copied from the frame list. If a fact is seen in only one frame, use the same timestamp twice. TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.
@@ -39,5 +43,9 @@
-- [120.0-137.5] SCENE: kitchen with white wall tiles; wooden table in the center
-- [120.0-137.5] ENTITY: woman in a red apron with long black hair
-- [120.0-127.5] EVENT: woman in a red apron talks to the camera
-- [130.0-137.5] EVENT: woman in a red apron whisks eggs in a glass bowl
-- [130.0-137.5] CHANGE: eggs in the glass bowl change from yellow liquid to pale foam
+- [120.0-137.5] SCENE: bright kitchen with white wall tiles
+- [120.0-137.5] ENTITY: woman in a red apron with long black hair, standing behind the table
+- [120.0-137.5] OBJECT: wooden table in the center
+- [120.0-137.5] OBJECT: glass bowl on the table in front of the woman
+- [120.0-137.5] OBJECT: round white wall clock in the upper right, hands at about 3:15
+- [120.0-125.0] EVENT: woman in a red apron talks to the camera
+- [127.5-127.5] EVENT: woman in a red apron picks up an egg
+- [130.0-130.0] EVENT: woman in a red apron cracks the egg into the glass bowl
+- [132.5-137.5] EVENT: woman in a red apron whisks the egg in the glass bowl
```

### なぜこの変更か

- OBJECT: 見える物をできるだけ、物1つにつき1行（色・形・数・位置）。
- EVENT: 1行に1つの動作。「How to split actions」で「picks up a cup / drinks / puts down は3行」と示す。
- 冒頭に「記録は検索される」「主役以外の細部も書く」と追記。

### 問題点（実行前の指摘）

- 林: 「SCENEは簡単な状況説明（白い壁に囲まれた部屋など）にして、物・人・イベント・テキストをできる限り細かく。時間の間隔もしっかり」。v2ではSCENEに細部を書く余地があり、細部の置き場所が重複していた。

### 次の版の目的

SCENEは場所だけ、他の種類はできる限り細かく。時間の扱いを1つの節にまとめて強調する。

## 4. v3（壁打ちで確定、2026-10-20）

<details><summary>v3 の本文（全文）</summary>

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

</details>

### 差分（v2 → v3）

```diff
--- v2
+++ v3
@@ -1 +1 @@
-You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after. So record details, not only the main subject.
+You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after. So record as many details as you can, not only the main subject.
@@ -9,4 +9,4 @@
-- SCENE: the place and background (location, lighting, layout of the screen).
-- ENTITY: each visible person or animal, with appearance (clothing colors, hair, accessories) and position.
-- OBJECT: each visible object, one object per line, with color, shape, count, and position (for example "on the table to the left of the woman", "upper right corner"). List as many visible objects as you can, including small and background objects.
-- EVENT: each action, one action per line. Write one person or object doing one action.
+- SCENE: one short line about the place only (for example, "room with white walls", "outdoor street at night"). Write a new SCENE line only when the place changes.
+- ENTITY: each visible person or animal, one per line, in as much detail as you can: clothing and colors, hair, accessories, and position on the screen.
+- OBJECT: each visible object, one per line, in as much detail as you can: color, shape, material, count, and position (for example "on the table to the left of the woman", "upper right corner"). Include small and background objects.
+- EVENT: each action, one per line, in as much detail as you can. Write one person or object doing one action.
@@ -25 +25 @@
-How to handle several frames:
+How to handle time:
@@ -27,2 +27,3 @@
-- If the same person or object keeps doing the same thing across several frames, write one line that spans from the first to the last of those frames. For example, if a person talks to the camera in every frame from 100.0 s to 116.0 s, write one line "[100.0-116.0] EVENT: ... talks to the camera", not one line per frame.
-- Start a new line only when the action, the person or object, or the place changes.
+- start and end must be timestamps copied from the frame list. They must cover exactly the frames where the fact is seen.
+- If the same person or object keeps doing the same thing across several frames, write one line from the first to the last of those frames. For example, if a person talks to the camera in every frame from 100.0 s to 116.0 s, write one line "[100.0-116.0] EVENT: ... talks to the camera", not one line per frame.
+- Start a new line when the action, the person or object, or the place changes.
@@ -30 +31 @@
-- SCENE, ENTITY, OBJECT, and TEXT lines also span all consecutive frames where they are seen.
+- If a fact is seen in only one frame, use the same timestamp twice.
@@ -33 +34 @@
-- One fact per line. Keep each line short and concrete.
+- One fact per line. Each line must be concrete.
@@ -40 +41 @@
-start and end are timestamps in seconds copied from the frame list. If a fact is seen in only one frame, use the same timestamp twice. TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.
+TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.
@@ -43,4 +44,4 @@
-- [120.0-137.5] SCENE: bright kitchen with white wall tiles
-- [120.0-137.5] ENTITY: woman in a red apron with long black hair, standing behind the table
-- [120.0-137.5] OBJECT: wooden table in the center
-- [120.0-137.5] OBJECT: glass bowl on the table in front of the woman
+- [120.0-137.5] SCENE: kitchen with white wall tiles
+- [120.0-137.5] ENTITY: woman in a red apron over a white shirt, long black hair tied back, standing behind the table
+- [120.0-137.5] OBJECT: rectangular wooden table in the center
+- [120.0-137.5] OBJECT: clear glass bowl on the table in front of the woman
@@ -49 +50 @@
-- [127.5-127.5] EVENT: woman in a red apron picks up an egg
+- [127.5-127.5] EVENT: woman in a red apron picks up a brown egg
@@ -51 +52 @@
-- [132.5-137.5] EVENT: woman in a red apron whisks the egg in the glass bowl
+- [132.5-137.5] EVENT: woman in a red apron whisks the egg in the glass bowl with a metal whisk
```

### なぜこの変更か

- SCENEは「場所だけ・場所が変わったら新しい行」。ENTITY・OBJECT・EVENTに「in as much detail as you can」。
- 「How to handle time」を独立させ、時刻はframe一覧から写す・見えている範囲を正確に、と明示。
- 設定: `max_new_tokens` 4096。入力は image_list（画像を別々に並べる）。

### 問題点（実データで初めて実行）

**(a) 約22秒の動画 `I2Fyzav8MxE`（2区間）**: 最後まで成功（1区間目 入力8,332 token・生成484 token・48秒）。ただし:
- 時刻を最後のframe（17.5秒）ではなく区間の終わり（20.0秒）で書いた（15行中9行が「時刻がframeと不一致」）。
- 同じ動作をframeごとに別の行で繰り返した。
- 何もないときに `TEXT: none`、`CHANGE: no notable change` を書いた。

```text
- [0.0-20.0] EVENT: man in a black T-shirt holds an orange plastic bowl with a spoon in his right hand and leans over the table
- [2.5-2.5] EVENT: man in a black T-shirt holds an orange plastic bowl with a spoon in his right hand and a white enamel tray with blue paint in his left hand
- [5.0-5.0] EVENT: man in a black T-shirt holds an orange plastic bowl with a spoon in his right hand and a white enamel tray with blue paint in his left hand
- [7.5-7.5] EVENT: man in a black T-shirt holds an orange plastic bowl with a spoon in his right hand and a white enamel tray with blue paint in his left hand
- [10.0-12.5] EVENT: man in a black T-shirt uses a paintbrush to apply blue paint to a white paper or canvas
- [15.0-15.0] EVENT: man in a black T-shirt places the paintbrush down on the table
```

**(b) 約3分の動画 `66dwcQ1Y048`（10区間）**: 成功したが全体14分16秒。
- 2区間で同じTEXT行を延々と繰り返し、`max_new_tokens` 4096に達して各265秒。区間6は146行中136行が同じ行:

```text
- [100.0-120.0] EVENT: man gestures with both hands toward the camera while speaking
- [100.0-120.0] TEXT: "The BROADWAY HOLLYWOOD" on the billboard
- [100.0-120.0] TEXT: "BROADWAY" on the billboard
- [100.0-120.0] TEXT: "HOLLYWOOD" on the billboard
- [100.0-120.0] TEXT: "BROADWAY HOLLYWOOD" on the billboard
- [100.0-120.0] TEXT: "BROADWAY HOLLYWOOD" on the billboard
- [100.0-120.0] TEXT: "BROADWAY HOLLYWOOD" on the billboard
- [100.0-120.0] TEXT: "BROADWAY HOLLYWOOD" on the billboard
```
- 区間8も「Send message」「jordandemo 47m」を交互に60回ずつ。
- 8枚とも場面が違う区間でも、すべての行を区間全体 `[140.0-160.0]` にして、1枚目の場面だけを書いた:

```text
- [140.0-160.0] SCENE: indoor room with a gray patterned rug and a dark-colored coffee table to the left
- [140.0-160.0] ENTITY: man in a red hoodie and blue jeans, holding a smartphone with both hands, sitting on a couch
- [140.0-160.0] OBJECT: smartphone with a black case, displaying a video of a person in a dark room, held in the man's hands
- [140.0-160.0] OBJECT: white dresser with two drawers in the background, partially visible behind the man's legs
- [140.0-160.0] EVENT: man in a red hoodie watches a video on his smartphone
```
- 動画全体で416行中、TEXTが277行（ほぼ繰り返し）、EVENTは17行、時刻がframeと一致しない行は372行。

### 次の版の目的（林の指示）

- 「コード上で同じ行を削除させるのは綺麗じゃない」→ **プロンプトで** TEXTの大量発生を止める。
- 「時間の問題も解決できるように」→ 実行時間（ループ）と、時刻のずれの両方を対象にした。
- 進め方: 問題の区間だけを試す小さなスクリプトを作り、案を比べる。

## 5. v4a（2026-10-20）

<details><summary>v4a の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video, from {{chunk.start}} s to {{chunk.end}} s. You are given these frames, in time order:
{{chunk.frame_manifest}}

Look at every frame, from the first to the last. The frames may come from different shots: the video can cut to a different place, person, or screen between two frames. Do not describe only the first frame.

What to record:
- SCENE: one short line about the place only (for example, "room with white walls", "airport curb", "phone screen held in a hand"). Write a new SCENE line each time the place or shot changes.
- ENTITY: each visible person or animal, one per line, with clothing and colors, hair, accessories, and position on the screen.
- OBJECT: each important visible object, one per line, with color, shape, count, and position. Include small and background objects that someone could ask about.
- EVENT: each action, one per line. Write one person or object doing one action.
- CHANGE: a change in how a person or object looks or where it is.
- TEXT: large or important text in the image (titles, captions, signs, names). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

How to split actions:
- Split a sequence of different actions into separate EVENT lines, each with its own time. For example, "picks up a cup", "drinks from the cup", and "puts the cup down" are three lines, not one.
- Do not summarize several actions into one line such as "has a drink".

How to write times:
- start and end must both be times from the frame list above. Never use a time that is not in the list (for example, never use {{chunk.end}} unless it is in the list).
- A line covers exactly the frames where the fact is seen: start is the first of those frames and end is the last of those frames. If something is seen in only one frame, use that frame's time twice.
- If the same person or object keeps doing the same thing across several frames, write one line from the first to the last of those frames, not one line per frame.
- If the person or object is not visible in some frames in the middle, end the line before that gap and start a new line after it.

Rules:
- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the time range of all frames where it is seen.
- Write at most 5 TEXT lines. Skip small interface text on phone or computer screens (buttons, usernames, timestamps) and repeated watermarks.
- Write only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- Skip a type when there is nothing to write for it. Do not write lines such as "none" or "no change".
- A window usually needs 10 to 40 lines. When every frame is covered, stop.
- Do not answer any question. Do not write anything other than log lines.

Output format:
Each line is: - [start-end] TYPE: description
TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video whose frames are at 120.0, 122.5, ..., 137.5 s; the shot cuts after 127.5 s):
- [120.0-127.5] SCENE: kitchen with white wall tiles
- [120.0-127.5] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
- [120.0-127.5] OBJECT: clear glass bowl on the wooden table in front of the woman
- [120.0-122.5] EVENT: woman in a red apron talks to the camera
- [125.0-125.0] EVENT: woman in a red apron cracks an egg into the glass bowl
- [120.0-122.5] TEXT: "Easy Omelette"
- [130.0-137.5] SCENE: close-up of a frying pan on a gas stove
- [130.0-137.5] OBJECT: black frying pan with melted butter
- [132.5-137.5] EVENT: beaten egg is poured into the frying pan
- [135.0-137.5] CHANGE: egg in the pan turns from liquid to solid at the edges

Now write the log lines for {{chunk.start}} s to {{chunk.end}} s.
```

</details>

### 差分（v3 → v4a）

```diff
--- v3
+++ v4a
@@ -1 +1 @@
-You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after. So record as many details as you can, not only the main subject.
+You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.
@@ -3 +3 @@
-You are viewing one window of the video, from {{chunk.start}} s to {{chunk.end}} s. The frames are listed below with their timestamps in seconds from the start of the video:
+You are viewing one window of the video, from {{chunk.start}} s to {{chunk.end}} s. You are given these frames, in time order:
@@ -6 +6 @@
-Write log lines for this window only.
+Look at every frame, from the first to the last. The frames may come from different shots: the video can cut to a different place, person, or screen between two frames. Do not describe only the first frame.
@@ -9,6 +9,6 @@
-- SCENE: one short line about the place only (for example, "room with white walls", "outdoor street at night"). Write a new SCENE line only when the place changes.
-- ENTITY: each visible person or animal, one per line, in as much detail as you can: clothing and colors, hair, accessories, and position on the screen.
-- OBJECT: each visible object, one per line, in as much detail as you can: color, shape, material, count, and position (for example "on the table to the left of the woman", "upper right corner"). Include small and background objects.
-- EVENT: each action, one per line, in as much detail as you can. Write one person or object doing one action.
-- CHANGE: a change in how a person or object looks or where it is (color, shape, clothing, position, state).
-- TEXT: text that is part of the image (titles, signs, labels, captions, numbers on clocks or screens). Copy it exactly.
+- SCENE: one short line about the place only (for example, "room with white walls", "airport curb", "phone screen held in a hand"). Write a new SCENE line each time the place or shot changes.
+- ENTITY: each visible person or animal, one per line, with clothing and colors, hair, accessories, and position on the screen.
+- OBJECT: each important visible object, one per line, with color, shape, count, and position. Include small and background objects that someone could ask about.
+- EVENT: each action, one per line. Write one person or object doing one action.
+- CHANGE: a change in how a person or object looks or where it is.
+- TEXT: large or important text in the image (titles, captions, signs, names). Copy it exactly.
@@ -25,5 +25,4 @@
-How to handle time:
-- Look at all frames together, not one by one.
-- start and end must be timestamps copied from the frame list. They must cover exactly the frames where the fact is seen.
-- If the same person or object keeps doing the same thing across several frames, write one line from the first to the last of those frames. For example, if a person talks to the camera in every frame from 100.0 s to 116.0 s, write one line "[100.0-116.0] EVENT: ... talks to the camera", not one line per frame.
-- Start a new line when the action, the person or object, or the place changes.
+How to write times:
+- start and end must both be times from the frame list above. Never use a time that is not in the list (for example, never use {{chunk.end}} unless it is in the list).
+- A line covers exactly the frames where the fact is seen: start is the first of those frames and end is the last of those frames. If something is seen in only one frame, use that frame's time twice.
+- If the same person or object keeps doing the same thing across several frames, write one line from the first to the last of those frames, not one line per frame.
@@ -31 +29,0 @@
-- If a fact is seen in only one frame, use the same timestamp twice.
@@ -34,3 +32,5 @@
-- One fact per line. Each line must be concrete.
-- Record only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
-- If nothing happens in the window, still write the SCENE, ENTITY, and OBJECT lines, and write one EVENT line: "no notable action".
+- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the time range of all frames where it is seen.
+- Write at most 5 TEXT lines. Skip small interface text on phone or computer screens (buttons, usernames, timestamps) and repeated watermarks.
+- Write only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
+- Skip a type when there is nothing to write for it. Do not write lines such as "none" or "no change".
+- A window usually needs 10 to 40 lines. When every frame is covered, stop.
@@ -43,10 +43,6 @@
-Example (from a different video):
-- [120.0-137.5] SCENE: kitchen with white wall tiles
-- [120.0-137.5] ENTITY: woman in a red apron over a white shirt, long black hair tied back, standing behind the table
-- [120.0-137.5] OBJECT: rectangular wooden table in the center
-- [120.0-137.5] OBJECT: clear glass bowl on the table in front of the woman
-- [120.0-137.5] OBJECT: round white wall clock in the upper right, hands at about 3:15
-- [120.0-125.0] EVENT: woman in a red apron talks to the camera
-- [127.5-127.5] EVENT: woman in a red apron picks up a brown egg
-- [130.0-130.0] EVENT: woman in a red apron cracks the egg into the glass bowl
-- [132.5-137.5] EVENT: woman in a red apron whisks the egg in the glass bowl with a metal whisk
+Example (from a different video whose frames are at 120.0, 122.5, ..., 137.5 s; the shot cuts after 127.5 s):
+- [120.0-127.5] SCENE: kitchen with white wall tiles
+- [120.0-127.5] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
+- [120.0-127.5] OBJECT: clear glass bowl on the wooden table in front of the woman
+- [120.0-122.5] EVENT: woman in a red apron talks to the camera
+- [125.0-125.0] EVENT: woman in a red apron cracks an egg into the glass bowl
@@ -53,0 +50,4 @@
+- [130.0-137.5] SCENE: close-up of a frying pan on a gas stove
+- [130.0-137.5] OBJECT: black frying pan with melted butter
+- [132.5-137.5] EVENT: beaten egg is poured into the frying pan
+- [135.0-137.5] CHANGE: egg in the pan turns from liquid to solid at the edges
```

### なぜこの変更か

- 「Look at every frame… The frames may come from different shots… Do not describe only the first frame」: 1枚目だけを書く問題への対策。
- SCENEは「場所かショットが変わるたびに新しい行」。
- TEXTを「大きく重要な文字」に限定し、1区間5行まで。スマホ画面の小さな文字（ボタン・ユーザー名・時刻）と透かしは書かない。
- 「すべての行は互いに違う」「同じ文字は1回だけ」: ループ対策。
- 「書くことがない種類は書かない」「10〜40行、全frameを書いたら止める」: none行と長すぎる出力の対策。
- 時刻: 「start/end はframe一覧の時刻だけ、{{chunk.end}} は使わない」。

### 結果（`66dwcQ1Y048` の5区間）

| 区間 | 時間(秒) | 生成token | 行数 | TEXT | 重複最大 | 時刻一致 |
| --- | --: | --: | --: | --: | --: | --: |
| 0 | 68.7 | 868 | 29 | 1 | 3 | 24/29 |
| 1 | 72.4 | 1102 | 40 | 1 | 2 | 36/40 |
| 5 | 44.3 | 656 | 22 | 0 | 2 | 19/22 |
| 7 | 57.1 | 855 | 28 | 4 | 4 | 25/28 |
| 9 | 37.2 | 569 | 17 | 1 | 1 | 0/17 |

TEXTのループは止まった（各区間0〜4行、最大1,102 token）。

### 問題点

- **画像と時刻の対応がずれている**。区間2（20〜40秒）の実際の画像は「部屋で騒ぐ人たち → 渦巻きの壁の男性×3 → 路地 → 式典 → スノーボード → 崖」なのに、記録は20秒に路地、30秒に渦巻きの男性:

```text
- [20.0-22.5] SCENE: narrow alley between brick buildings
- [22.5-25.0] SCENE: stage with dark curtain background
- [25.0-27.5] SCENE: snowy mountain slope with pine trees
- [27.5-30.0] SCENE: rocky cliff overlooking ocean
- [30.0-32.5] SCENE: indoor room with white walls
- [32.5-35.0] SCENE: narrow alley between brick buildings
- [35.0-37.5] SCENE: stage with dark curtain background
- [37.5-40.0] SCENE: snowy mountain slope with pine trees
```
- 原因は入力の形: 画像はラベルなしで並び、時刻の一覧は文章の後ろにまとめて書いてあるだけ。モデルにはどの画像が何秒か分からない。**プロンプトの文章だけでは直せない**。
- 1枚だけの区間（区間10、180.0秒の1枚）で、区間の終わり `[180.0-186.8]` を書いた（17行すべて時刻不一致）。
- 同じ場面（渦巻きの壁の男性）を1枚ずつ別の行に書いた。

### 次の版の目的

- 入力を変える: 各画像の直前に「frame k (t s):」のラベルを置く（コードの変更、commit `c6d1d4c`）。
- 区間の終わりの時刻をプロンプトから外す。同じ場面はまとめる。

## 6. 入力の変更: 画像の直前にラベルを置く（コード、commit `c6d1d4c`）

チャットの内容を「`frame 1 (20.0 s):` → 画像 → `frame 2 (22.5 s):` → 画像 … → プロンプト本文」の順に組み立てるようにした（Qwen3-VLは文章と画像の交互の入力を受け取れる）。プロンプトの文章ではなくモデルへの見せ方の変更で、v4b以降すべての前提。


## 7. v4b（2026-10-20）

<details><summary>v4b の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video that starts at {{chunk.start}} s. Each image above is shown right after its label, such as "frame 1 (120.0 s):". The frames of this window are:
{{chunk.frame_manifest}}

Look at every frame, from the first to the last, and use its label to know its time. The frames may come from different shots: the video can cut to a different place, person, or screen between two frames. Do not describe only the first frame.
Group consecutive frames that show the same shot, and describe each group once. Do not repeat the same SCENE, ENTITY, or OBJECT line for every frame of a group; give it one time range that covers the whole group.

What to record:
- SCENE: one short line about the place only (for example, "room with white walls", "airport curb", "phone screen held in a hand"). Write a new SCENE line each time the place or shot changes.
- ENTITY: each visible person or animal, one per line, with clothing and colors, hair, accessories, and position on the screen.
- OBJECT: each important visible object, one per line, with color, shape, count, and position. Include small and background objects that someone could ask about.
- EVENT: each action, one per line. Write one person or object doing one action.
- CHANGE: a change in how a person or object looks or where it is.
- TEXT: large or important text in the image (titles, captions, signs, names). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

How to split actions:
- Split a sequence of different actions into separate EVENT lines, each with its own time. For example, "picks up a cup", "drinks from the cup", and "puts the cup down" are three lines, not one.
- Do not summarize several actions into one line such as "has a drink".

How to write times:
- First decide which frames show the fact. start is the time of the first of those frames, and end is the time of the last of those frames. Both must be times from the frame list above.
- A frame's time is a single moment, not a period. Something seen only in frame 3 (125.0 s) is written [125.0-125.0], not [125.0-127.5].
- If the same person or object keeps doing the same thing across several frames, write one line from the first to the last of those frames, not one line per frame.
- If the person or object is not visible in some frames in the middle, end the line before that gap and start a new line after it.

Rules:
- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the time range of all frames where it is seen.
- Write at most 5 TEXT lines. Skip small interface text on phone or computer screens (buttons, usernames, timestamps) and repeated watermarks.
- Write only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- Skip a type when there is nothing to write for it. Do not write lines such as "none" or "no change".
- A window usually needs 10 to 40 lines. When every frame is covered, stop.
- Do not answer any question. Do not write anything other than log lines.

Output format:
Each line is: - [start-end] TYPE: description
TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video whose frames are at 120.0, 122.5, ..., 137.5 s; the shot cuts after 127.5 s):
- [120.0-127.5] SCENE: kitchen with white wall tiles
- [120.0-127.5] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
- [120.0-127.5] OBJECT: clear glass bowl on the wooden table in front of the woman
- [120.0-122.5] EVENT: woman in a red apron talks to the camera
- [125.0-125.0] EVENT: woman in a red apron cracks an egg into the glass bowl
- [120.0-122.5] TEXT: "Easy Omelette"
- [130.0-137.5] SCENE: close-up of a frying pan on a gas stove
- [130.0-137.5] OBJECT: black frying pan with melted butter
- [132.5-137.5] EVENT: beaten egg is poured into the frying pan
- [135.0-137.5] CHANGE: egg in the pan turns from liquid to solid at the edges

Now write the log lines for this window.
```

</details>

### 差分（v4a → v4b）

```diff
--- v4a
+++ v4b
@@ -3 +3 @@
-You are viewing one window of the video, from {{chunk.start}} s to {{chunk.end}} s. You are given these frames, in time order:
+You are viewing one window of the video that starts at {{chunk.start}} s. Each image above is shown right after its label, such as "frame 1 (120.0 s):". The frames of this window are:
@@ -6 +6,2 @@
-Look at every frame, from the first to the last. The frames may come from different shots: the video can cut to a different place, person, or screen between two frames. Do not describe only the first frame.
+Look at every frame, from the first to the last, and use its label to know its time. The frames may come from different shots: the video can cut to a different place, person, or screen between two frames. Do not describe only the first frame.
+Group consecutive frames that show the same shot, and describe each group once. Do not repeat the same SCENE, ENTITY, or OBJECT line for every frame of a group; give it one time range that covers the whole group.
@@ -26,2 +27,2 @@
-- start and end must both be times from the frame list above. Never use a time that is not in the list (for example, never use {{chunk.end}} unless it is in the list).
-- A line covers exactly the frames where the fact is seen: start is the first of those frames and end is the last of those frames. If something is seen in only one frame, use that frame's time twice.
+- First decide which frames show the fact. start is the time of the first of those frames, and end is the time of the last of those frames. Both must be times from the frame list above.
+- A frame's time is a single moment, not a period. Something seen only in frame 3 (125.0 s) is written [125.0-125.0], not [125.0-127.5].
@@ -55 +56 @@
-Now write the log lines for {{chunk.start}} s to {{chunk.end}} s.
+Now write the log lines for this window.
```

### なぜこの変更か

- 「Each image above is shown right after its label」: 新しい入力の形を伝える。
- 区間の終わり（`{{chunk.end}}`）をプロンプトから削除（1枚だけの区間で区間の終わりを書く原因）。
- 「同じショットが続く枚をまとめ、1回だけ書く」。
- 時刻: 「まずどのframeに写っているか決める」「frameの時刻は1点で期間ではない。frame 3 だけなら [125.0-125.0]」。

### 結果（4区間）

- 区間1: 82.9秒、31行、時刻一致 31/31、TEXT 1
- 区間5: 63.9秒、23行、時刻一致 23/23、TEXT 0
- 区間7: 64.5秒、26行、時刻一致 26/26、TEXT 4
- 区間9: 48.4秒、17行、時刻一致 17/17、TEXT 4

時刻はすべてframe一覧と一致。区間2の対応もほぼ正しくなった。

### 問題点

- 1枚だけの場面を「その枚から次の枚まで」と書く（路地はframe 5＝30.0秒だけなのに `[30.0-32.5]`）。
- 区間8で、場面の始まりが1枚ずれる（空港はframe 5＝150.0秒なのに 147.5秒から）:

```text
- [140.0-142.5] SCENE: dimly lit room with a person lying on a couch
- [142.5-145.0] SCENE: room with a television and a white dresser in the background
- [145.0-147.5] SCENE: room with a gray patterned blanket on a bed
- [147.5-150.0] SCENE: airport terminal with a bus and cars in the background
- [150.0-152.5] SCENE: mountain road with a rocky cliff on the left
- [152.5-157.5] SCENE: room with a black and white spiral graffiti wall
```

### 次の版の目的

frameと時刻の対応を、具体例でさらに強調する。

## 8. v4c（2026-10-20）

<details><summary>v4c の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video that starts at {{chunk.start}} s. Each image above is shown right after its label, such as "frame 1 (120.0 s):". The frames of this window are:
{{chunk.frame_manifest}}

Look at every frame, from the first to the last, and use its label to know its time. The frames may come from different shots: the video can cut to a different place, person, or screen between two frames. Do not describe only the first frame.
Before writing, go through the labels one by one (frame 1, frame 2, ...) and note which shot each frame shows. Every frame must belong to exactly one shot; do not skip a frame.
Group consecutive frames that show the same shot, and describe each group once. Do not repeat the same SCENE, ENTITY, or OBJECT line for every frame of a group; give it one time range that covers the whole group.

What to record:
- SCENE: one short line about the place only (for example, "room with white walls", "airport curb", "phone screen held in a hand"). Write a new SCENE line each time the place or shot changes.
- ENTITY: each visible person or animal, one per line, with clothing and colors, hair, accessories, and position on the screen.
- OBJECT: each important visible object, one per line, with color, shape, count, and position. Include small and background objects that someone could ask about.
- EVENT: each action, one per line. Write one person or object doing one action.
- CHANGE: a change in how a person or object looks or where it is.
- TEXT: large or important text in the image (titles, captions, signs, names). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

How to split actions:
- Split a sequence of different actions into separate EVENT lines, each with its own time. For example, "picks up a cup", "drinks from the cup", and "puts the cup down" are three lines, not one.
- Do not summarize several actions into one line such as "has a drink".

How to write times:
- First decide which frames show the fact. start is the time of the first of those frames, and end is the time of the last of those frames. Both must be times from the frame list above.
- A frame's time is a single moment, not a period. end is never the time of a frame that does not show the fact.
  - Seen in frames 1 to 3 (120.0, 122.5, 125.0 s): [120.0-125.0]
  - Seen only in frame 5 (130.0 s): [130.0-130.0], not [130.0-132.5]
  - A new shot that starts at frame 6 (132.5 s) starts at 132.5, not at 130.0.
- If the same person or object keeps doing the same thing across several frames, write one line from the first to the last of those frames, not one line per frame.
- If the person or object is not visible in some frames in the middle, end the line before that gap and start a new line after it.

Rules:
- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the time range of all frames where it is seen.
- Write at most 5 TEXT lines. Skip small interface text on phone or computer screens (buttons, usernames, timestamps) and repeated watermarks.
- Write only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- Skip a type when there is nothing to write for it. Do not write lines such as "none" or "no change".
- A window usually needs 10 to 40 lines. When every frame is covered, stop.
- Do not answer any question. Do not write anything other than log lines.

Output format:
Each line is: - [start-end] TYPE: description
TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video whose frames are at 120.0, 122.5, ..., 137.5 s; the shot cuts after 127.5 s):
- [120.0-127.5] SCENE: kitchen with white wall tiles
- [120.0-127.5] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
- [120.0-127.5] OBJECT: clear glass bowl on the wooden table in front of the woman
- [120.0-122.5] EVENT: woman in a red apron talks to the camera
- [125.0-125.0] EVENT: woman in a red apron cracks an egg into the glass bowl
- [120.0-122.5] TEXT: "Easy Omelette"
- [130.0-137.5] SCENE: close-up of a frying pan on a gas stove
- [130.0-137.5] OBJECT: black frying pan with melted butter
- [132.5-137.5] EVENT: beaten egg is poured into the frying pan
- [135.0-137.5] CHANGE: egg in the pan turns from liquid to solid at the edges

Now write the log lines for this window.
```

</details>

### 差分（v4b → v4c）

```diff
--- v4b
+++ v4c
@@ -6,0 +7 @@
+Before writing, go through the labels one by one (frame 1, frame 2, ...) and note which shot each frame shows. Every frame must belong to exactly one shot; do not skip a frame.
@@ -28 +29,4 @@
-- A frame's time is a single moment, not a period. Something seen only in frame 3 (125.0 s) is written [125.0-125.0], not [125.0-127.5].
+- A frame's time is a single moment, not a period. end is never the time of a frame that does not show the fact.
+  - Seen in frames 1 to 3 (120.0, 122.5, 125.0 s): [120.0-125.0]
+  - Seen only in frame 5 (130.0 s): [130.0-130.0], not [130.0-132.5]
+  - A new shot that starts at frame 6 (132.5 s) starts at 132.5, not at 130.0.
```

### なぜこの変更か

ラベルを1枚ずつ順に見て各frameの場面を決めさせ、「end は写っていないframeの時刻にしない」「frame 1〜3 なら [120.0-125.0]」「新しい場面がframe 6から始まるなら 132.5から」を例で示した。

### 結果と問題点（2区間）

かえって悪くなった。路地（frame 5＝30.0秒）を `[27.5-30.0]` と1枚前から書き、空港（frame 5＝150.0秒）も `[147.5-150.0]`:

```text
- [20.0-22.5] SCENE: bedroom with white walls, ceiling fan, and framed pictures
- [22.5-27.5] SCENE: outdoor area with a black and white spiral mural on a wall
- [27.5-30.0] SCENE: narrow alleyway between brick buildings with graffiti and a fire escape
- [30.0-32.5] SCENE: indoor stage with a podium and camera equipment
- [32.5-35.0] SCENE: snowy mountain slope with pine trees and distant mountains
- [35.0-37.5] SCENE: rocky cliff overlooking ocean with cloudy sky
```
AIの考え: モデルは「その枚から次の枚まで」という区間の解釈を強く持っていて、例を足しても秒でframeを正確に指せない。4Bのモデルに時刻の計算をさせるのは難しい。

### 次の版の目的

秒の代わりに、画像の直前のラベルと同じ **frame番号** で範囲を書かせる（`[F3-F5]`）。秒への変換はコードで行う。

## 9. v4d（2026-10-20）

<details><summary>v4d の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video that starts at {{chunk.start}} s. Each image above is shown right after its label, such as "frame 1 (120.0 s):". The frames of this window are:
{{chunk.frame_manifest}}

Look at every frame, from the first to the last. Refer to frames by their numbers: F1 is frame 1, F2 is frame 2, and so on. The frames may come from different shots: the video can cut to a different place, person, or screen between two frames. Do not describe only the first frame.
Group consecutive frames that show the same shot, and describe each group once. Do not repeat the same SCENE, ENTITY, or OBJECT line for every frame of a group; give it one time range that covers the whole group.

What to record:
- SCENE: one short line about the place only (for example, "room with white walls", "airport curb", "phone screen held in a hand"). Write a new SCENE line each time the place or shot changes.
- ENTITY: each visible person or animal, one per line, with clothing and colors, hair, accessories, and position on the screen.
- OBJECT: each important visible object, one per line, with color, shape, count, and position. Include small and background objects that someone could ask about.
- EVENT: each action, one per line. Write one person or object doing one action.
- CHANGE: a change in how a person or object looks or where it is.
- TEXT: large or important text in the image (titles, captions, signs, names). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

How to split actions:
- Split a sequence of different actions into separate EVENT lines, each with its own time. For example, "picks up a cup", "drinks from the cup", and "puts the cup down" are three lines, not one.
- Do not summarize several actions into one line such as "has a drink".

How to write which frames a line covers:
- Each line starts with the numbers of the first and last frames that show the fact, such as [F3-F5]. If only one frame shows it, write the same number twice, such as [F4-F4].
- Count the frames carefully: the label right before each image tells its number.
- If the same person or object keeps doing the same thing across several frames, write one line from the first to the last of those frames, not one line per frame.
- If the person or object is not visible in some frames in the middle, end the line before that gap and start a new line after it.

Rules:
- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the time range of all frames where it is seen.
- Write at most 5 TEXT lines. Skip small interface text on phone or computer screens (buttons, usernames, timestamps) and repeated watermarks.
- Write only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- Skip a type when there is nothing to write for it. Do not write lines such as "none" or "no change".
- A window usually needs 10 to 40 lines. When every frame is covered, stop.
- Do not answer any question. Do not write anything other than log lines.

Output format:
Each line is: - [Ffirst-Flast] TYPE: description
TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video with 8 frames; the shot cuts after frame 4):
- [F1-F4] SCENE: kitchen with white wall tiles
- [F1-F4] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
- [F1-F4] OBJECT: clear glass bowl on the wooden table in front of the woman
- [F1-F2] EVENT: woman in a red apron talks to the camera
- [F3-F3] EVENT: woman in a red apron cracks an egg into the glass bowl
- [F1-F2] TEXT: "Easy Omelette"
- [F5-F8] SCENE: close-up of a frying pan on a gas stove
- [F5-F8] OBJECT: black frying pan with melted butter
- [F6-F8] EVENT: beaten egg is poured into the frying pan
- [F7-F8] CHANGE: egg in the pan turns from liquid to solid at the edges

Now write the log lines for this window.
```

</details>

### 差分（v4b → v4d）

※ v4cは採用しなかったので、v4bからの差分。

```diff
--- v4b
+++ v4d
@@ -6 +6 @@
-Look at every frame, from the first to the last, and use its label to know its time. The frames may come from different shots: the video can cut to a different place, person, or screen between two frames. Do not describe only the first frame.
+Look at every frame, from the first to the last. Refer to frames by their numbers: F1 is frame 1, F2 is frame 2, and so on. The frames may come from different shots: the video can cut to a different place, person, or screen between two frames. Do not describe only the first frame.
@@ -26,3 +26,3 @@
-How to write times:
-- First decide which frames show the fact. start is the time of the first of those frames, and end is the time of the last of those frames. Both must be times from the frame list above.
-- A frame's time is a single moment, not a period. Something seen only in frame 3 (125.0 s) is written [125.0-125.0], not [125.0-127.5].
+How to write which frames a line covers:
+- Each line starts with the numbers of the first and last frames that show the fact, such as [F3-F5]. If only one frame shows it, write the same number twice, such as [F4-F4].
+- Count the frames carefully: the label right before each image tells its number.
@@ -41 +41 @@
-Each line is: - [start-end] TYPE: description
+Each line is: - [Ffirst-Flast] TYPE: description
@@ -44,11 +44,11 @@
-Example (from a different video whose frames are at 120.0, 122.5, ..., 137.5 s; the shot cuts after 127.5 s):
-- [120.0-127.5] SCENE: kitchen with white wall tiles
-- [120.0-127.5] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
-- [120.0-127.5] OBJECT: clear glass bowl on the wooden table in front of the woman
-- [120.0-122.5] EVENT: woman in a red apron talks to the camera
-- [125.0-125.0] EVENT: woman in a red apron cracks an egg into the glass bowl
-- [120.0-122.5] TEXT: "Easy Omelette"
-- [130.0-137.5] SCENE: close-up of a frying pan on a gas stove
-- [130.0-137.5] OBJECT: black frying pan with melted butter
-- [132.5-137.5] EVENT: beaten egg is poured into the frying pan
-- [135.0-137.5] CHANGE: egg in the pan turns from liquid to solid at the edges
+Example (from a different video with 8 frames; the shot cuts after frame 4):
+- [F1-F4] SCENE: kitchen with white wall tiles
+- [F1-F4] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
+- [F1-F4] OBJECT: clear glass bowl on the wooden table in front of the woman
+- [F1-F2] EVENT: woman in a red apron talks to the camera
+- [F3-F3] EVENT: woman in a red apron cracks an egg into the glass bowl
+- [F1-F2] TEXT: "Easy Omelette"
+- [F5-F8] SCENE: close-up of a frying pan on a gas stove
+- [F5-F8] OBJECT: black frying pan with melted butter
+- [F6-F8] EVENT: beaten egg is poured into the frying pan
+- [F7-F8] CHANGE: egg in the pan turns from liquid to solid at the edges
```

### なぜこの変更か

- 範囲を `[F3-F5]` のようにframe番号で書かせる（ラベル「frame 3」と同じ番号）。秒での書き方の節を置き換えた。
- 例もframe番号の形に書き直した（8枚、frame 4の後でカット）。

### 結果（2区間）

**画像と記録の対応が全frameで正しくなった**（区間8のスマホ4枚 → 空港 → 山道 → 渦巻きの壁の男性も正確）:

```text
- [F1] SCENE: living room with a couch and a white dresser in the background
- [F2] SCENE: room with a white ceiling, a TV on a dresser, and a green curtain
- [F3] SCENE: room with a gray patterned blanket and a black coffee table
- [F4] SCENE: room with a white ceiling and green curtains
- [F5] SCENE: airport terminal with a bus stop, cars, and an elevator sign
- [F6] SCENE: mountain road with a rocky cliff and a snow-capped mountain in the background
- [F7] SCENE: room with a black and white spiral wall
- [F8] SCENE: room with a black and white spiral wall
```

### 問題点

- 範囲を使わず `[F1]` `[F2]` と1枚ずつ書き、同じ場面を枚ごとに繰り返す（行が増え時間もかかる）。
- `[F1]` 形式は当時の解析処理で読めなかった（→ 解析処理を `[F3-F5]` `[F4]` に対応させた、commit `b2f2a1a`）。

### 次の版の目的

続く枚は1つの範囲にまとめる指示を、具体例で強める。

## 10. v4e → v4（確定、2026-10-20）

<details><summary>v4e の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video that starts at {{chunk.start}} s. Each image above is shown right after its label, such as "frame 1 (120.0 s):". The frames of this window are:
{{chunk.frame_manifest}}

Look at every frame, from the first to the last. Refer to frames by their numbers: F1 is frame 1, F2 is frame 2, and so on. The frames may come from different shots: the video can cut to a different place, person, or screen between two frames. Do not describe only the first frame.
Group consecutive frames that show the same shot, and describe each group once. Do not repeat the same SCENE, ENTITY, or OBJECT line for every frame of a group; give it one time range that covers the whole group.

What to record:
- SCENE: one short line about the place only (for example, "room with white walls", "airport curb", "phone screen held in a hand"). Write a new SCENE line each time the place or shot changes.
- ENTITY: each visible person or animal, one per line, with clothing and colors, hair, accessories, and position on the screen.
- OBJECT: each important visible object, one per line, with color, shape, count, and position. Include small and background objects that someone could ask about.
- EVENT: each action, one per line. Write one person or object doing one action.
- CHANGE: a change in how a person or object looks or where it is.
- TEXT: large or important text in the image (titles, captions, signs, names). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

How to split actions:
- Split a sequence of different actions into separate EVENT lines, each with its own time. For example, "picks up a cup", "drinks from the cup", and "puts the cup down" are three lines, not one.
- Do not summarize several actions into one line such as "has a drink".

How to write which frames a line covers:
- Each line starts with the first and last frame that show the fact, such as [F3-F5]. If only one frame shows it, write the same number twice, such as [F4-F4].
- Use one range for consecutive frames that show the same shot or the same fact. If frames 2, 3, and 4 show the same man in front of the same wall, write [F2-F4] once, not three lines [F2-F2], [F3-F3], [F4-F4].
- Count the frames carefully: the label right before each image tells its number.
- If the same person or object keeps doing the same thing across several frames, write one line from the first to the last of those frames, not one line per frame.
- If the person or object is not visible in some frames in the middle, end the line before that gap and start a new line after it.

Rules:
- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the time range of all frames where it is seen.
- Write at most 5 TEXT lines. Skip small interface text on phone or computer screens (buttons, usernames, timestamps) and repeated watermarks.
- Write only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- Skip a type when there is nothing to write for it. Do not write lines such as "none" or "no change".
- A window usually needs 10 to 40 lines. When every frame is covered, stop.
- Do not answer any question. Do not write anything other than log lines.

Output format:
Each line is: - [Ffirst-Flast] TYPE: description
TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video with 8 frames; the shot cuts after frame 4):
- [F1-F4] SCENE: kitchen with white wall tiles
- [F1-F4] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
- [F1-F4] OBJECT: clear glass bowl on the wooden table in front of the woman
- [F1-F2] EVENT: woman in a red apron talks to the camera
- [F3-F3] EVENT: woman in a red apron cracks an egg into the glass bowl
- [F1-F2] TEXT: "Easy Omelette"
- [F5-F8] SCENE: close-up of a frying pan on a gas stove
- [F5-F8] OBJECT: black frying pan with melted butter
- [F6-F8] EVENT: beaten egg is poured into the frying pan
- [F7-F8] CHANGE: egg in the pan turns from liquid to solid at the edges

Now write the log lines for this window.
```

</details>

### 差分（v4d → v4e）

```diff
--- v4d
+++ v4e
@@ -27 +27,2 @@
-- Each line starts with the numbers of the first and last frames that show the fact, such as [F3-F5]. If only one frame shows it, write the same number twice, such as [F4-F4].
+- Each line starts with the first and last frame that show the fact, such as [F3-F5]. If only one frame shows it, write the same number twice, such as [F4-F4].
+- Use one range for consecutive frames that show the same shot or the same fact. If frames 2, 3, and 4 show the same man in front of the same wall, write [F2-F4] once, not three lines [F2-F2], [F3-F3], [F4-F4].
```

### 差分（v4e → v4、確定時の言い回しの修正）

```diff
--- v4e
+++ v4
@@ -7 +7 @@
-Group consecutive frames that show the same shot, and describe each group once. Do not repeat the same SCENE, ENTITY, or OBJECT line for every frame of a group; give it one time range that covers the whole group.
+Group consecutive frames that show the same shot, and describe each group once. Do not repeat the same SCENE, ENTITY, or OBJECT line for every frame of a group; give it one frame range that covers the whole group.
@@ -34 +34 @@
-- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the time range of all frames where it is seen.
+- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the frame range of all frames where it is seen.
```

### なぜこの変更か

「frame 2・3・4 に同じ男性と同じ壁が写っていれば [F2-F4] を1回、3行に分けない」と具体的に示した。確定時に「time range」を「frame range」に直した。

### 結果

- 3区間: 区間4では `[F1-F3]` とまとめられた。区間2はまだ1枚ずつ。全区間で対応は正しい。
- **同じ3分の動画全体（v3 → v4）**:

| 項目 | v3 | v4 |
| --- | --: | --: |
| 全体の時間 | 14分16秒 | 6分16秒 |
| モデルの時間の合計 | 841秒 | 361秒 |
| max_new_tokensに達した区間 | 2 | 0 |
| 1区間の最大時間 | 265秒 | 48秒 |
| 行数 | 416 | 224 |
| TEXT行（1区間の最大） | 277（140） | 19（6） |
| 時刻がframeと一致しない行 | 372 | 0 |

### 問題点（林の依頼で3本の動画で確認、2026-10-21）

| 版 | 動画 | 全体の時間(秒) | 上限到達 | 行数 | TEXT最大/区間 | 重複行 | 時刻不一致 | 解析不可 | EVENT割合 | 複数の人を1行 | まとめ損ね | EVENTのない場面 |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| v4 | `66dwcQ1Y048_0` | 466 | 0 | 224 | 6 | なし | 0 | 0 | 4.5% | 4 | 14 | — |
| v4 | `NexB4vj8_54_0` | 334 | 0 | 179 | 2 | なし | 0 | 0 | 22.9% | 1 | 41 | — |
| v4 | `BtaVRhoLpC0_0` | 341 | 0 | 146 | 7 | なし | 0 | 0 | 12.3% | 1 | 0 | — |

- VlogでEVENTが4.5%しかない。
- 料理で、同じ台所が8枚続くのに1枚ずつ同じ行を書き、動作をOBJECTの中に書く（`ENTITY: none` まで書く）:

```text
- [F1-F1] SCENE: kitchen with wooden table
- [F1-F1] ENTITY: hand in black glove, pouring sugar
- [F1-F1] OBJECT: clear glass bowl with four egg yolks, 80g sugar being poured into it
- [F1-F1] TEXT: "80g sugar"
- [F2-F2] SCENE: kitchen with wooden table
- [F2-F2] ENTITY: none
- [F2-F2] OBJECT: clear glass bowl with sugar and one egg yolk partially submerged
- [F3-F3] SCENE: kitchen with wooden table
- [F3-F3] ENTITY: hand in black glove holding the bowl
- [F3-F3] OBJECT: clear glass bowl with sugar and one egg yolk partially submerged
- [F4-F4] SCENE: kitchen with wooden table
- [F4-F4] ENTITY: hand in black glove holding the bowl, electric mixer in motion
…
```
- ニュースで発言の字幕を1文ずつTEXTにして7行。

### 次の版の目的（基準を決めた）

| 指標 | 基準 |
| --- | --- |
| 上限到達・時刻不一致・解析不可 | 0 |
| ループ（同じ範囲・同じ本文の重複行） | なし |
| 1行に複数の人や物 | 0 |
| まとめ損ね | 各動画3以下 |
| EVENT | 人が写っている場面にEVENTがある（途中で「全行の15%以上」から変更。1人が話し続けるニュースでは割合が上がらないのが正しいため） |
| TEXT | ループしない |

## 11. v5a（2026-10-21）

<details><summary>v5a の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video that starts at {{chunk.start}} s. Each image above is shown right after its label, such as "frame 1 (120.0 s):". The frames of this window are:
{{chunk.frame_manifest}}

Refer to frames by their numbers: F1 is frame 1, F2 is frame 2, and so on. Count the frames carefully: the label right before each image tells its number.

Write the log in two steps.

Step 1. List the shots.
Look at every frame from the first to the last. A shot is a run of consecutive frames that show the same place from the same camera; the video can cut to a different place, person, or screen between two frames. Write one SCENE line per shot, with the frame range of the whole shot. Every frame belongs to exactly one shot.
- Frames 2, 3, and 4 show the same man in front of the same wall: write one line [F2-F4] SCENE, not three lines.

Step 2. For each shot, in order, describe it with these lines:
- ENTITY: each visible person or animal, one per line. Never put two people in one line. Give clothing and colors, hair, accessories, and position on the screen.
- EVENT: what each person, animal, or moving thing is doing, one action per line. Every shot that shows a person or animal needs at least one EVENT line (talking to the camera, walking, cooking, hugging, jumping, holding something, and so on). If the action changes between frames, write one EVENT line for each action with its own frame range, for example "picks up a cup", then "drinks from the cup", then "puts the cup down".
- OBJECT: each important object, one per line. Never list several objects in one line. Give color, shape, count, and position.
- CHANGE: a change in how a person or object looks or where it is, within the shot.
- TEXT: large or important text in the image (titles, captions, signs, names). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

Frame ranges:
- Each line starts with the first and last frame that show the fact, such as [F3-F5]. If only one frame shows it, write the same number twice, such as [F4-F4].
- A line about a shot that spans several frames uses the range of the frames where the fact is seen, not one line per frame.

Rules:
- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the frame range of all frames where it is seen.
- Write at most 5 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames, timestamps), subtitles of speech that repeat, and watermarks or channel logos.
- Write only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- Skip a type when there is nothing to write for it. Do not write lines such as "none" or "no change".
- A window usually needs 10 to 40 lines. When every shot is described, stop.
- Do not answer any question. Do not write anything other than log lines.

Output format:
Each line is: - [Ffirst-Flast] TYPE: description
TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video with 8 frames; the shot cuts after frame 4):
- [F1-F4] SCENE: kitchen with white wall tiles
- [F5-F8] SCENE: close-up of a frying pan on a gas stove
- [F1-F4] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
- [F1-F2] EVENT: woman in a red apron talks to the camera
- [F3-F3] EVENT: woman in a red apron cracks an egg into the glass bowl
- [F4-F4] EVENT: woman in a red apron whisks the egg with a fork
- [F1-F4] OBJECT: clear glass bowl on the wooden table in front of the woman
- [F1-F2] TEXT: "Easy Omelette"
- [F5-F8] OBJECT: black frying pan with melted butter
- [F6-F8] EVENT: beaten egg is poured into the frying pan
- [F7-F8] CHANGE: egg in the pan turns from liquid to solid at the edges

Now write the log lines for this window.
```

</details>

### 差分（v4 → v5a）

```diff
--- v4
+++ v5a
@@ -6,2 +6 @@
-Look at every frame, from the first to the last. Refer to frames by their numbers: F1 is frame 1, F2 is frame 2, and so on. The frames may come from different shots: the video can cut to a different place, person, or screen between two frames. Do not describe only the first frame.
-Group consecutive frames that show the same shot, and describe each group once. Do not repeat the same SCENE, ENTITY, or OBJECT line for every frame of a group; give it one frame range that covers the whole group.
+Refer to frames by their numbers: F1 is frame 1, F2 is frame 2, and so on. Count the frames carefully: the label right before each image tells its number.
@@ -9,6 +8,11 @@
-What to record:
-- SCENE: one short line about the place only (for example, "room with white walls", "airport curb", "phone screen held in a hand"). Write a new SCENE line each time the place or shot changes.
-- ENTITY: each visible person or animal, one per line, with clothing and colors, hair, accessories, and position on the screen.
-- OBJECT: each important visible object, one per line, with color, shape, count, and position. Include small and background objects that someone could ask about.
-- EVENT: each action, one per line. Write one person or object doing one action.
-- CHANGE: a change in how a person or object looks or where it is.
+Write the log in two steps.
+
+Step 1. List the shots.
+Look at every frame from the first to the last. A shot is a run of consecutive frames that show the same place from the same camera; the video can cut to a different place, person, or screen between two frames. Write one SCENE line per shot, with the frame range of the whole shot. Every frame belongs to exactly one shot.
+- Frames 2, 3, and 4 show the same man in front of the same wall: write one line [F2-F4] SCENE, not three lines.
+
+Step 2. For each shot, in order, describe it with these lines:
+- ENTITY: each visible person or animal, one per line. Never put two people in one line. Give clothing and colors, hair, accessories, and position on the screen.
+- EVENT: what each person, animal, or moving thing is doing, one action per line. Every shot that shows a person or animal needs at least one EVENT line (talking to the camera, walking, cooking, hugging, jumping, holding something, and so on). If the action changes between frames, write one EVENT line for each action with its own frame range, for example "picks up a cup", then "drinks from the cup", then "puts the cup down".
+- OBJECT: each important object, one per line. Never list several objects in one line. Give color, shape, count, and position.
+- CHANGE: a change in how a person or object looks or where it is, within the shot.
@@ -22,5 +26 @@
-How to split actions:
-- Split a sequence of different actions into separate EVENT lines, each with its own time. For example, "picks up a cup", "drinks from the cup", and "puts the cup down" are three lines, not one.
-- Do not summarize several actions into one line such as "has a drink".
-
-How to write which frames a line covers:
+Frame ranges:
@@ -28,4 +28 @@
-- Use one range for consecutive frames that show the same shot or the same fact. If frames 2, 3, and 4 show the same man in front of the same wall, write [F2-F4] once, not three lines [F2-F2], [F3-F3], [F4-F4].
-- Count the frames carefully: the label right before each image tells its number.
-- If the same person or object keeps doing the same thing across several frames, write one line from the first to the last of those frames, not one line per frame.
-- If the person or object is not visible in some frames in the middle, end the line before that gap and start a new line after it.
+- A line about a shot that spans several frames uses the range of the frames where the fact is seen, not one line per frame.
@@ -35 +32 @@
-- Write at most 5 TEXT lines. Skip small interface text on phone or computer screens (buttons, usernames, timestamps) and repeated watermarks.
+- Write at most 5 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames, timestamps), subtitles of speech that repeat, and watermarks or channel logos.
@@ -38 +35 @@
-- A window usually needs 10 to 40 lines. When every frame is covered, stop.
+- A window usually needs 10 to 40 lines. When every shot is described, stop.
@@ -46,0 +44 @@
+- [F5-F8] SCENE: close-up of a frying pan on a gas stove
@@ -48 +45,0 @@
-- [F1-F4] OBJECT: clear glass bowl on the wooden table in front of the woman
@@ -50,0 +48,2 @@
+- [F4-F4] EVENT: woman in a red apron whisks the egg with a fork
+- [F1-F4] OBJECT: clear glass bowl on the wooden table in front of the woman
@@ -52 +50,0 @@
-- [F5-F8] SCENE: close-up of a frying pan on a gas stove
```

### なぜこの変更か

- **2段階**: Step 1で場面（SCENE）の一覧を範囲つきで書かせ、全frameをどれかの場面に入れる。Step 2で場面ごとに人・動作・物を書く。v4で「まとめる」と言っても1枚ずつ書いたのは、先に場面の区切りを決めていないからと考えた。
- 人も物も1行に1つ（「Never put two people in one line」）。
- 人や動物が写る場面には最低1つのEVENT。
- 例を「場面の一覧 → 場面ごとの行」の順に並べ替え、EVENTを3つに増やした。
- TEXTの対象外に「繰り返す発言の字幕」「チャンネルのロゴ」を追加。

### 結果（3本）

| 版 | 動画 | 全体の時間(秒) | 上限到達 | 行数 | TEXT最大/区間 | 重複行 | 時刻不一致 | 解析不可 | EVENT割合 | 複数の人を1行 | まとめ損ね | EVENTのない場面 |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| v5a | `66dwcQ1Y048_0` | 491 | 0 | 264 | 7 | なし | 0 | 0 | 15.5% | 5 | 1 | — |
| v5a | `NexB4vj8_54_0` | 315 | 0 | 192 | 3 | なし | 0 | 0 | 18.8% | 2 | 16 | — |
| v5a | `BtaVRhoLpC0_0` | 273 | 0 | 146 | 5 | なし | 0 | 0 | 13.0% | 0 | 0 | — |

### 問題点

- VlogのEVENTは4.5% → 15.5%、まとめ損ね14 → 1。料理のまとめ損ねも41 → 16。
- 料理で、動かない物（皿・テーブル）を8枚それぞれに書く:

```text
- [F2-F4] OBJECT: yellow cake with powdered sugar on top, round, sitting on a white plate
- [F1] OBJECT: white plate with a yellow cake on it
- [F1] OBJECT: dark wooden table
- [F1] OBJECT: black background
- [F2] OBJECT: white plate with a yellow cake on it
- [F2] OBJECT: dark wooden table
- [F3] OBJECT: white plate with a yellow cake on it
- [F3] OBJECT: dark wooden table
- [F4] OBJECT: white plate with a yellow cake on it
- [F4] OBJECT: dark wooden table
- [F5] OBJECT: white plate with a yellow cake on it
- [F5] OBJECT: dark wooden table
…
```
- Vlogで、1つのENTITY行に2人を「;」でつなぐ（5件）。`TEXT: none` が残る。
- ニュースで「AFP」のロゴをTEXTに書く。

### 次の版の目的

モデルがやりがちな誤りを「Wrong / Right」の組で具体的に示す。

## 12. v5b（2026-10-21）

<details><summary>v5b の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video that starts at {{chunk.start}} s. Each image above is shown right after its label, such as "frame 1 (120.0 s):". The frames of this window are:
{{chunk.frame_manifest}}

Refer to frames by their numbers: F1 is frame 1, F2 is frame 2, and so on. Count the frames carefully: the label right before each image tells its number.

Write the log in two steps.

Step 1. List the shots.
Look at every frame from the first to the last. A shot is a run of consecutive frames that show the same place from the same camera; the video can cut to a different place, person, or screen between two frames. Write one SCENE line per shot, with the frame range of the whole shot. Every frame belongs to exactly one shot.
- Frames 2, 3, and 4 show the same man in front of the same wall: write one line [F2-F4] SCENE, not three lines.

Step 2. For each shot, in order, describe it with these lines:
- ENTITY: each visible person or animal, one per line. If a shot shows two people, write two ENTITY lines. Give clothing and colors, hair, accessories, and position on the screen.
- EVENT: what each person, animal, or moving thing is doing, one action per line. Every shot that shows a person or animal needs at least one EVENT line (talking to the camera, walking, cooking, hugging, jumping, holding something, and so on). If the action changes between frames, write one EVENT line for each action with its own frame range, for example "picks up a cup", then "drinks from the cup", then "puts the cup down".
- OBJECT: each important object, one per line. Give color, shape, count, and position.
- CHANGE: a change in how a person or object looks or where it is, within the shot.
- TEXT: large or important text in the image (titles, captions, signs, names). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

Frame ranges:
- Each line starts with the first and last frame that show the fact, such as [F3-F5]. If only one frame shows it, write the same number twice, such as [F4-F4].
- A person or object that stays in a shot is written once, with the range of all frames where it is seen. Never write the same person or object again for each frame.

Rules:
- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the frame range of all frames where it is seen.
- Write at most 5 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames, timestamps), subtitles of speech that repeat, and watermarks or channel logos (such as "AFP" or a channel name in a corner).
- Write only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- Skip a type when there is nothing to write for it. Do not write lines such as "none" or "no change".
- A window usually needs 10 to 40 lines. When every shot is described, stop.
- Do not answer any question. Do not write anything other than log lines.

Common mistakes. Do not write lines like these:
- Wrong (the same object repeated for each frame):
  - [F2-F2] OBJECT: white plate with a yellow cake
  - [F3-F3] OBJECT: white plate with a yellow cake
  Right: - [F2-F8] OBJECT: white plate with a yellow cake
- Wrong (two people in one line): - [F5-F5] ENTITY: man in a gray sweatshirt waving; woman in a plaid shirt waving
  Right:
  - [F5-F5] ENTITY: man with short blond hair in a gray sweatshirt
  - [F5-F5] ENTITY: woman with long brown hair in a red and black plaid shirt
  - [F5-F5] EVENT: man in a gray sweatshirt and woman in a plaid shirt wave at the camera
- Wrong (nothing to write): - [F3-F3] TEXT: none
  Right: write no TEXT line for that frame.
- Wrong (a channel logo): - [F2-F8] TEXT: "AFP"
  Right: skip logos and watermarks.

Output format:
Each line is: - [Ffirst-Flast] TYPE: description
TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video with 8 frames; the shot cuts after frame 4):
- [F1-F4] SCENE: kitchen with white wall tiles
- [F5-F8] SCENE: close-up of a frying pan on a gas stove
- [F1-F4] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
- [F1-F2] EVENT: woman in a red apron talks to the camera
- [F3-F3] EVENT: woman in a red apron cracks an egg into the glass bowl
- [F4-F4] EVENT: woman in a red apron whisks the egg with a fork
- [F1-F4] OBJECT: clear glass bowl on the wooden table in front of the woman
- [F1-F2] TEXT: "Easy Omelette"
- [F5-F8] OBJECT: black frying pan with melted butter
- [F6-F8] EVENT: beaten egg is poured into the frying pan
- [F7-F8] CHANGE: egg in the pan turns from liquid to solid at the edges

Now write the log lines for this window.
```

</details>

### 差分（v5a → v5b）

```diff
--- v5a
+++ v5b
@@ -15 +15 @@
-- ENTITY: each visible person or animal, one per line. Never put two people in one line. Give clothing and colors, hair, accessories, and position on the screen.
+- ENTITY: each visible person or animal, one per line. If a shot shows two people, write two ENTITY lines. Give clothing and colors, hair, accessories, and position on the screen.
@@ -17 +17 @@
-- OBJECT: each important object, one per line. Never list several objects in one line. Give color, shape, count, and position.
+- OBJECT: each important object, one per line. Give color, shape, count, and position.
@@ -28 +28 @@
-- A line about a shot that spans several frames uses the range of the frames where the fact is seen, not one line per frame.
+- A person or object that stays in a shot is written once, with the range of all frames where it is seen. Never write the same person or object again for each frame.
@@ -32 +32 @@
-- Write at most 5 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames, timestamps), subtitles of speech that repeat, and watermarks or channel logos.
+- Write at most 5 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames, timestamps), subtitles of speech that repeat, and watermarks or channel logos (such as "AFP" or a channel name in a corner).
@@ -36,0 +37,15 @@
+
+Common mistakes. Do not write lines like these:
+- Wrong (the same object repeated for each frame):
+  - [F2-F2] OBJECT: white plate with a yellow cake
+  - [F3-F3] OBJECT: white plate with a yellow cake
+  Right: - [F2-F8] OBJECT: white plate with a yellow cake
+- Wrong (two people in one line): - [F5-F5] ENTITY: man in a gray sweatshirt waving; woman in a plaid shirt waving
+  Right:
+  - [F5-F5] ENTITY: man with short blond hair in a gray sweatshirt
+  - [F5-F5] ENTITY: woman with long brown hair in a red and black plaid shirt
+  - [F5-F5] EVENT: man in a gray sweatshirt and woman in a plaid shirt wave at the camera
+- Wrong (nothing to write): - [F3-F3] TEXT: none
+  Right: write no TEXT line for that frame.
+- Wrong (a channel logo): - [F2-F8] TEXT: "AFP"
+  Right: skip logos and watermarks.
```

### なぜこの変更か

「Common mistakes」の節を足し、誤りと正しい書き方を組で示した: 同じ物を1枚ずつ書く／2人を1行に書く／`TEXT: none`／ロゴ「AFP」。人と物は「一場面に2人いればENTITYを2行」と言い換えた。

### 結果（3本）

| 版 | 動画 | 全体の時間(秒) | 上限到達 | 行数 | TEXT最大/区間 | 重複行 | 時刻不一致 | 解析不可 | EVENT割合 | 複数の人を1行 | まとめ損ね | EVENTのない場面 |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| v5b | `66dwcQ1Y048_0` | 421 | 0 | 257 | 7 | なし | 0 | 0 | 10.1% | 0 | 0 | 17/36 |
| v5b | `NexB4vj8_54_0` | 260 | 0 | 172 | 3 | あり（最大2回） | 0 | 0 | 21.5% | 0 | 4 | 6/21 |
| v5b | `BtaVRhoLpC0_0` | 232 | 0 | 128 | 5 | なし | 0 | 0 | 12.5% | 1 | 0 | 5/21 |

### 問題点

- 1行に複数の人: 5/2/0 → 0/0/1、まとめ損ね 1/16/0 → 0/4/0。3本とも速くなった。
- VlogでEVENTのない場面が17/36。動作がENTITYの説明に入り込んでいる:

```text
- [F1-F1] ENTITY: man in a gray hoodie with short dark hair, mouth open, being pulled by another man
- [F1-F1] ENTITY: man in a red t-shirt with short dark hair, laughing, standing behind the man in the gray hoodie
- [F1-F1] ENTITY: shirtless man with short blond hair, in the foreground, mouth open, pulling the man in the gray hoodie
- [F2-F4] ENTITY: man with short blond hair, wearing a black t-shirt with white text "SEEK DISCOMFORT", sitting in front of the wall
- [F2-F4] EVENT: man in black t-shirt speaks to the camera
- [F2-F4] EVENT: man in black t-shirt gestures with his hands while speaking
- [F5-F5] ENTITY: man in a light green shirt and black pants, walking away from the camera
- [F5-F5] ENTITY: man in a colorful patterned shirt and blue shorts, walking away from the camera
- [F5-F5] ENTITY: man in a colorful patterned shirt and gray shorts, walking away from the camera
- [F6-F6] ENTITY: man in a black graduation gown with a red stole, walking on stage
- [F6-F6] ENTITY: man in a red graduation gown with a black hat, standing behind the man in the black gown
- [F7-F7] ENTITY: snowboarder in a black and gray jacket, black pants, and a helmet, riding down the slope
…
```
- 料理で、同じ場所の場面を細かく分ける（`close-up of a glass bowl on a wooden table` が6回）。

### 次の版の目的

ENTITYは見た目だけ・動作はEVENT、動作が変わっても同じ場所なら同じ場面、と明示する。

## 13. v5c（2026-10-21）

<details><summary>v5c の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video that starts at {{chunk.start}} s. Each image above is shown right after its label, such as "frame 1 (120.0 s):". The frames of this window are:
{{chunk.frame_manifest}}

Refer to frames by their numbers: F1 is frame 1, F2 is frame 2, and so on. Count the frames carefully: the label right before each image tells its number.

Write the log in two steps.

Step 1. List the shots.
Look at every frame from the first to the last. A shot is a run of consecutive frames that show the same place from the same camera; the video can cut to a different place, person, or screen between two frames. Write one SCENE line per shot, with the frame range of the whole shot. Every frame belongs to exactly one shot. A shot does not end when an action changes or the camera moves a little; it ends only when the place or the camera view changes.
- Frames 2, 3, and 4 show the same man in front of the same wall: write one line [F2-F4] SCENE, not three lines.

Step 2. For each shot, in order, describe it with these lines:
- ENTITY: each visible person or animal, one per line. If a shot shows two people, write two ENTITY lines. Describe only how they look: clothing and colors, hair, accessories, and position on the screen. Do not put what they are doing in an ENTITY line; that goes in EVENT.
- EVENT: what each person, animal, or moving thing is doing, one action per line. Every shot that shows a person or animal needs at least one EVENT line (talking to the camera, walking, cooking, hugging, jumping, holding something, and so on). If the action changes between frames, write one EVENT line for each action with its own frame range, for example "picks up a cup", then "drinks from the cup", then "puts the cup down".
- OBJECT: each important object, one per line. Give color, shape, count, and position.
- CHANGE: a change in how a person or object looks or where it is, within the shot.
- TEXT: large or important text in the image (titles, captions, signs, names). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

Frame ranges:
- Each line starts with the first and last frame that show the fact, such as [F3-F5]. If only one frame shows it, write the same number twice, such as [F4-F4].
- A person or object that stays in a shot is written once, with the range of all frames where it is seen. Never write the same person or object again for each frame.

Rules:
- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the frame range of all frames where it is seen.
- Write at most 5 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames and @handles, timestamps), subtitles of speech that repeat, and watermarks or channel logos (such as "AFP" or a channel name in a corner).
- Write only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- Skip a type when there is nothing to write for it. Do not write lines such as "none" or "no change".
- A window usually needs 10 to 40 lines. When every shot is described, stop.
- Do not answer any question. Do not write anything other than log lines.

Common mistakes. Do not write lines like these:
- Wrong (the same object repeated for each frame):
  - [F2-F2] OBJECT: white plate with a yellow cake
  - [F3-F3] OBJECT: white plate with a yellow cake
  Right: - [F2-F8] OBJECT: white plate with a yellow cake
- Wrong (two people in one line): - [F5-F5] ENTITY: man in a gray sweatshirt waving; woman in a plaid shirt waving
  Right:
  - [F5-F5] ENTITY: man with short blond hair in a gray sweatshirt
  - [F5-F5] ENTITY: woman with long brown hair in a red and black plaid shirt
  - [F5-F5] EVENT: man in a gray sweatshirt and woman in a plaid shirt wave at the camera
- Wrong (an action inside an ENTITY line, and no EVENT line): - [F5-F5] ENTITY: man in a light green shirt, walking away from the camera
  Right:
  - [F5-F5] ENTITY: man in a light green shirt and black pants, in the center
  - [F5-F5] EVENT: man in a light green shirt walks away from the camera
- Wrong (one shot split into many SCENE lines with the same place):
  - [F1-F2] SCENE: close-up of a glass bowl on a wooden table
  - [F3-F4] SCENE: close-up of a glass bowl on a wooden table
  Right: - [F1-F4] SCENE: close-up of a glass bowl on a wooden table
- Wrong (nothing to write): - [F3-F3] TEXT: none
  Right: write no TEXT line for that frame.
- Wrong (a channel logo): - [F2-F8] TEXT: "AFP"
  Right: skip logos and watermarks.

Output format:
Each line is: - [Ffirst-Flast] TYPE: description
TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video with 8 frames; the shot cuts after frame 4):
- [F1-F4] SCENE: kitchen with white wall tiles
- [F5-F8] SCENE: close-up of a frying pan on a gas stove
- [F1-F4] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
- [F1-F2] EVENT: woman in a red apron talks to the camera
- [F3-F3] EVENT: woman in a red apron cracks an egg into the glass bowl
- [F4-F4] EVENT: woman in a red apron whisks the egg with a fork
- [F1-F4] OBJECT: clear glass bowl on the wooden table in front of the woman
- [F1-F2] TEXT: "Easy Omelette"
- [F5-F8] OBJECT: black frying pan with melted butter
- [F6-F8] EVENT: beaten egg is poured into the frying pan
- [F7-F8] CHANGE: egg in the pan turns from liquid to solid at the edges

Now write the log lines for this window.
```

</details>

### 差分（v5b → v5c）

```diff
--- v5b
+++ v5c
@@ -11 +11 @@
-Look at every frame from the first to the last. A shot is a run of consecutive frames that show the same place from the same camera; the video can cut to a different place, person, or screen between two frames. Write one SCENE line per shot, with the frame range of the whole shot. Every frame belongs to exactly one shot.
+Look at every frame from the first to the last. A shot is a run of consecutive frames that show the same place from the same camera; the video can cut to a different place, person, or screen between two frames. Write one SCENE line per shot, with the frame range of the whole shot. Every frame belongs to exactly one shot. A shot does not end when an action changes or the camera moves a little; it ends only when the place or the camera view changes.
@@ -15 +15 @@
-- ENTITY: each visible person or animal, one per line. If a shot shows two people, write two ENTITY lines. Give clothing and colors, hair, accessories, and position on the screen.
+- ENTITY: each visible person or animal, one per line. If a shot shows two people, write two ENTITY lines. Describe only how they look: clothing and colors, hair, accessories, and position on the screen. Do not put what they are doing in an ENTITY line; that goes in EVENT.
@@ -32 +32 @@
-- Write at most 5 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames, timestamps), subtitles of speech that repeat, and watermarks or channel logos (such as "AFP" or a channel name in a corner).
+- Write at most 5 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames and @handles, timestamps), subtitles of speech that repeat, and watermarks or channel logos (such as "AFP" or a channel name in a corner).
@@ -47,0 +48,8 @@
+- Wrong (an action inside an ENTITY line, and no EVENT line): - [F5-F5] ENTITY: man in a light green shirt, walking away from the camera
+  Right:
+  - [F5-F5] ENTITY: man in a light green shirt and black pants, in the center
+  - [F5-F5] EVENT: man in a light green shirt walks away from the camera
+- Wrong (one shot split into many SCENE lines with the same place):
+  - [F1-F2] SCENE: close-up of a glass bowl on a wooden table
+  - [F3-F4] SCENE: close-up of a glass bowl on a wooden table
+  Right: - [F1-F4] SCENE: close-up of a glass bowl on a wooden table
```

### なぜこの変更か

- 「A shot does not end when an action changes…; it ends only when the place or the camera view changes」。
- ENTITYは「見た目と位置だけ。動作はEVENTへ」。
- Wrongの例に「動作がENTITYに入っていてEVENTがない」「同じ場所の場面を分ける」を追加。TEXTの対象外に @ハンドル。

### 結果（3本）

| 版 | 動画 | 全体の時間(秒) | 上限到達 | 行数 | TEXT最大/区間 | 重複行 | 時刻不一致 | 解析不可 | EVENT割合 | 複数の人を1行 | まとめ損ね | EVENTのない場面 |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| v5c | `66dwcQ1Y048_0` | 421 | 0 | 272 | 9 | なし | 0 | 0 | 12.5% | 0 | 0 | 13/40 |
| v5c | `NexB4vj8_54_0` | 226 | 0 | 134 | 3 | なし | 0 | 0 | 27.6% | 0 | 0 | 1/14 |
| v5c | `BtaVRhoLpC0_0` | 256 | 0 | 139 | 7 | なし | 0 | 0 | 13.7% | 0 | 0 | 4/20 |

### 問題点

- 料理は全基準を満たした（重複3、まとめ損ね0、EVENTのない場面1/14）。
- TEXTはVlog最大9行・ニュース7行。中身はコラージュに並んだ別々の字幕・発言で、ループではない:

```text
- [F1-F1] TEXT: "Love over"
- [F1-F1] TEXT: "I'm Matt from New York City"
- [F1-F1] TEXT: "I'm Ammar, a Muslim from Egypt"
- [F1-F1] TEXT: "I'm Thomas from Paris"
- [F1-F1] TEXT: "He is my roommate and best friend"
- [F1-F1] TEXT: "These are My Brothers"
- [F1-F1] TEXT: "He's my roommate and best friend"
- [F5-F6] TEXT: "A Love Letter to our Audience:"
- [F5-F6] TEXT: "Thank you for 1 Million Subscribers"
```
- `TEXT: none` が4回（Wrongの例に「none」という語そのものを書いたので、真似している可能性）。
- VlogでEVENTのない場面が13/40。1枚ごとに場面が変わる区間で、動作をENTITYに書いて済ませる。

### 次の版の目的

各ENTITYの直後にEVENTを書かせる。場面の多い区間は行が増えてよいと伝える。TEXTは違う文字を1回ずつ・8行まで。「none」という語をプロンプトから消す。

## 14. v5d（2026-10-21）

<details><summary>v5d の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video that starts at {{chunk.start}} s. Each image above is shown right after its label, such as "frame 1 (120.0 s):". The frames of this window are:
{{chunk.frame_manifest}}

Refer to frames by their numbers: F1 is frame 1, F2 is frame 2, and so on. Count the frames carefully: the label right before each image tells its number.

Write the log in two steps.

Step 1. List the shots.
Look at every frame from the first to the last. A shot is a run of consecutive frames that show the same place from the same camera; the video can cut to a different place, person, or screen between two frames. Write one SCENE line per shot, with the frame range of the whole shot. Every frame belongs to exactly one shot. A shot does not end when an action changes or the camera moves a little; it ends only when the place or the camera view changes.
- Frames 2, 3, and 4 show the same man in front of the same wall: write one line [F2-F4] SCENE, not three lines.

Step 2. For each shot, in order, describe it with these lines. Write each person's EVENT lines right after that person's ENTITY line, so that no person is left without an EVENT line.
- ENTITY: each visible person or animal, one per line. If a shot shows two people, write two ENTITY lines. Describe only how they look: clothing and colors, hair, accessories, and position on the screen. Do not put what they are doing in an ENTITY line; that goes in EVENT.
- EVENT: what each person, animal, or moving thing is doing, one action per line. Every shot that shows a person or animal needs at least one EVENT line (talking to the camera, walking, cooking, hugging, jumping, holding something, and so on). If the action changes between frames, write one EVENT line for each action with its own frame range, for example "picks up a cup", then "drinks from the cup", then "puts the cup down".
- OBJECT: each important object, one per line. Give color, shape, count, and position.
- CHANGE: a change in how a person or object looks or where it is, within the shot.
- TEXT: large or important text in the image (titles, captions, signs, names). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

Frame ranges:
- Each line starts with the first and last frame that show the fact, such as [F3-F5]. If only one frame shows it, write the same number twice, such as [F4-F4].
- A person or object that stays in a shot is written once, with the range of all frames where it is seen. Never write the same person or object again for each frame.

Rules:
- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the frame range of all frames where it is seen.
- Write a TEXT line only when you can copy real words from the image. Write each different text once, and write at most 8 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames and @handles, timestamps), subtitles of speech that repeat, and watermarks or channel logos (such as "AFP" or a channel name in a corner).
- Write only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- Skip a type when there is nothing to write for it; never write a line that only says that nothing is there.
- A window usually needs 10 to 50 lines; a window with many short shots needs more lines than a window with one long shot. When every shot is described, stop.
- Do not answer any question. Do not write anything other than log lines.

Common mistakes. Do not write lines like these:
- Wrong (the same object repeated for each frame):
  - [F2-F2] OBJECT: white plate with a yellow cake
  - [F3-F3] OBJECT: white plate with a yellow cake
  Right: - [F2-F8] OBJECT: white plate with a yellow cake
- Wrong (two people in one line): - [F5-F5] ENTITY: man in a gray sweatshirt waving; woman in a plaid shirt waving
  Right:
  - [F5-F5] ENTITY: man with short blond hair in a gray sweatshirt
  - [F5-F5] ENTITY: woman with long brown hair in a red and black plaid shirt
  - [F5-F5] EVENT: man in a gray sweatshirt and woman in a plaid shirt wave at the camera
- Wrong (an action inside an ENTITY line, and no EVENT line): - [F5-F5] ENTITY: man in a light green shirt, walking away from the camera
  Right:
  - [F5-F5] ENTITY: man in a light green shirt and black pants, in the center
  - [F5-F5] EVENT: man in a light green shirt walks away from the camera
- Wrong (one shot split into many SCENE lines with the same place):
  - [F1-F2] SCENE: close-up of a glass bowl on a wooden table
  - [F3-F4] SCENE: close-up of a glass bowl on a wooden table
  Right: - [F1-F4] SCENE: close-up of a glass bowl on a wooden table
- Wrong (a channel logo): - [F2-F8] TEXT: "AFP"
  Right: skip logos and watermarks.

Output format:
Each line is: - [Ffirst-Flast] TYPE: description
TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video with 8 frames; the shot cuts after frame 4 and after frame 7):
- [F1-F4] SCENE: kitchen with white wall tiles
- [F5-F7] SCENE: close-up of a frying pan on a gas stove
- [F8-F8] SCENE: dining table by a window
- [F1-F4] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
- [F1-F2] EVENT: woman in a red apron talks to the camera
- [F3-F3] EVENT: woman in a red apron cracks an egg into the glass bowl
- [F4-F4] EVENT: woman in a red apron whisks the egg with a fork
- [F1-F4] OBJECT: clear glass bowl on the wooden table in front of the woman
- [F1-F2] TEXT: "Easy Omelette"
- [F5-F8] OBJECT: black frying pan with melted butter
- [F6-F7] EVENT: beaten egg is poured into the frying pan
- [F7-F7] CHANGE: egg in the pan turns from liquid to solid at the edges
- [F8-F8] ENTITY: boy in a yellow T-shirt, sitting at the table
- [F8-F8] EVENT: boy in a yellow T-shirt eats the omelette with a fork
- [F8-F8] OBJECT: white plate with a folded omelette

Now write the log lines for this window.
```

</details>

### 差分（v5c → v5d）

```diff
--- v5c
+++ v5d
@@ -14 +14 @@
-Step 2. For each shot, in order, describe it with these lines:
+Step 2. For each shot, in order, describe it with these lines. Write each person's EVENT lines right after that person's ENTITY line, so that no person is left without an EVENT line.
@@ -32 +32 @@
-- Write at most 5 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames and @handles, timestamps), subtitles of speech that repeat, and watermarks or channel logos (such as "AFP" or a channel name in a corner).
+- Write a TEXT line only when you can copy real words from the image. Write each different text once, and write at most 8 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames and @handles, timestamps), subtitles of speech that repeat, and watermarks or channel logos (such as "AFP" or a channel name in a corner).
@@ -34,2 +34,2 @@
-- Skip a type when there is nothing to write for it. Do not write lines such as "none" or "no change".
-- A window usually needs 10 to 40 lines. When every shot is described, stop.
+- Skip a type when there is nothing to write for it; never write a line that only says that nothing is there.
+- A window usually needs 10 to 50 lines; a window with many short shots needs more lines than a window with one long shot. When every shot is described, stop.
@@ -56,2 +55,0 @@
-- Wrong (nothing to write): - [F3-F3] TEXT: none
-  Right: write no TEXT line for that frame.
@@ -65 +63 @@
-Example (from a different video with 8 frames; the shot cuts after frame 4):
+Example (from a different video with 8 frames; the shot cuts after frame 4 and after frame 7):
@@ -67 +65,2 @@
-- [F5-F8] SCENE: close-up of a frying pan on a gas stove
+- [F5-F7] SCENE: close-up of a frying pan on a gas stove
+- [F8-F8] SCENE: dining table by a window
@@ -75,2 +74,5 @@
-- [F6-F8] EVENT: beaten egg is poured into the frying pan
-- [F7-F8] CHANGE: egg in the pan turns from liquid to solid at the edges
+- [F6-F7] EVENT: beaten egg is poured into the frying pan
+- [F7-F7] CHANGE: egg in the pan turns from liquid to solid at the edges
+- [F8-F8] ENTITY: boy in a yellow T-shirt, sitting at the table
+- [F8-F8] EVENT: boy in a yellow T-shirt eats the omelette with a fork
+- [F8-F8] OBJECT: white plate with a folded omelette
```

### なぜこの変更か

- 「Write each person's EVENT lines right after that person's ENTITY line」。
- TEXT: 「本物の語を写せるときだけ」「違う文字は1回ずつ、8行まで」。5行は情報を捨てすぎると判断（ループではない字幕も意味がある）。
- 「none」の語を含む行・例を削除し、「何もないことを言うだけの行は書かない」に言い換え。
- 行数を10〜50に増やし「場面の多い区間はもっと行が要る」。例を3場面にした。

### 結果（3本）

| 版 | 動画 | 全体の時間(秒) | 上限到達 | 行数 | TEXT最大/区間 | 重複行 | 時刻不一致 | 解析不可 | EVENT割合 | 複数の人を1行 | まとめ損ね | EVENTのない場面 |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| v5d | `66dwcQ1Y048_0` | 679 | 1 | 490 | 9 | あり（最大185回） | 0 | 0 | 9.8% | 0 | 0 | 8/42 |
| v5d | `NexB4vj8_54_0` | 489 | 1 | 322 | 2 | あり（最大32回） | 0 | 1 | 11.2% | 0 | 1 | 0/16 |
| v5d | `BtaVRhoLpC0_0` | 272 | 0 | 148 | 8 | なし | 0 | 0 | 16.9% | 0 | 0 | 0/20 |

### 問題点

- EVENTのない場面は 8/42、0/16、0/20 と減った。
- しかし **OBJECTのループ** が起き、2本で上限到達（同じ行が最大185回）。Vlogの区間6の出力の最後:

```text
（236行のうち最後の6行）
- [F7-F7] OBJECT: protest sign with text "TIT"
- [F7-F7] OBJECT: protest sign with text "TIT"
- [F7-F7] OBJECT: protest sign with text "TIT"
- [F7-F7] OBJECT: protest sign with text "TIT"
- [F7-F7] OBJECT: protest sign with text "TIT"
- [F7-F7] OBJECT: protest sign with text "TIT"
```
- 料理でもボウル・ミキサー・テーブルを延々と並べ直した。
- AIの考え: 行数の上限を緩めたことと、もともとの「小さな物や背景の物も書く」が重なり、止まれなくなった。

### 次の版の目的

行数を10〜40に戻し、OBJECTは1場面5行まで（質問されそうな物を選ぶ）にする。

## 15. v5e（2026-10-21）

<details><summary>v5e の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video that starts at {{chunk.start}} s. Each image above is shown right after its label, such as "frame 1 (120.0 s):". The frames of this window are:
{{chunk.frame_manifest}}

Refer to frames by their numbers: F1 is frame 1, F2 is frame 2, and so on. Count the frames carefully: the label right before each image tells its number.

Write the log in two steps.

Step 1. List the shots.
Look at every frame from the first to the last. A shot is a run of consecutive frames that show the same place from the same camera; the video can cut to a different place, person, or screen between two frames. Write one SCENE line per shot, with the frame range of the whole shot. Every frame belongs to exactly one shot. A shot does not end when an action changes or the camera moves a little; it ends only when the place or the camera view changes.
- Frames 2, 3, and 4 show the same man in front of the same wall: write one line [F2-F4] SCENE, not three lines.

Step 2. For each shot, in order, describe it with these lines. Write each person's EVENT lines right after that person's ENTITY line, so that no person is left without an EVENT line.
- ENTITY: each visible person or animal, one per line. If a shot shows two people, write two ENTITY lines. Describe only how they look: clothing and colors, hair, accessories, and position on the screen. Do not put what they are doing in an ENTITY line; that goes in EVENT.
- EVENT: what each person, animal, or moving thing is doing, one action per line. Every shot that shows a person or animal needs at least one EVENT line (talking to the camera, walking, cooking, hugging, jumping, holding something, and so on). If the action changes between frames, write one EVENT line for each action with its own frame range, for example "picks up a cup", then "drinks from the cup", then "puts the cup down".
- OBJECT: the most important objects, one per line, at most 5 OBJECT lines per shot. Choose objects that someone could ask about (things people use or hold, large or colorful things, signs). Give color, shape, count, and position. Each object is written once per shot.
- CHANGE: a change in how a person or object looks or where it is, within the shot.
- TEXT: large or important text in the image (titles, captions, signs, names). Copy it exactly.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

Frame ranges:
- Each line starts with the first and last frame that show the fact, such as [F3-F5]. If only one frame shows it, write the same number twice, such as [F4-F4].
- A person or object that stays in a shot is written once, with the range of all frames where it is seen. Never write the same person or object again for each frame.

Rules:
- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the frame range of all frames where it is seen.
- Write a TEXT line only when you can copy real words from the image. Write each different text once, and write at most 8 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames and @handles, timestamps), subtitles of speech that repeat, and watermarks or channel logos (such as "AFP" or a channel name in a corner).
- Write only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- Skip a type when there is nothing to write for it; never write a line that only says that nothing is there.
- A window usually needs 10 to 40 lines. When every shot is described, stop.
- Do not answer any question. Do not write anything other than log lines.

Common mistakes. Do not write lines like these:
- Wrong (the same object repeated for each frame):
  - [F2-F2] OBJECT: white plate with a yellow cake
  - [F3-F3] OBJECT: white plate with a yellow cake
  Right: - [F2-F8] OBJECT: white plate with a yellow cake
- Wrong (two people in one line): - [F5-F5] ENTITY: man in a gray sweatshirt waving; woman in a plaid shirt waving
  Right:
  - [F5-F5] ENTITY: man with short blond hair in a gray sweatshirt
  - [F5-F5] ENTITY: woman with long brown hair in a red and black plaid shirt
  - [F5-F5] EVENT: man in a gray sweatshirt and woman in a plaid shirt wave at the camera
- Wrong (an action inside an ENTITY line, and no EVENT line): - [F5-F5] ENTITY: man in a light green shirt, walking away from the camera
  Right:
  - [F5-F5] ENTITY: man in a light green shirt and black pants, in the center
  - [F5-F5] EVENT: man in a light green shirt walks away from the camera
- Wrong (one shot split into many SCENE lines with the same place):
  - [F1-F2] SCENE: close-up of a glass bowl on a wooden table
  - [F3-F4] SCENE: close-up of a glass bowl on a wooden table
  Right: - [F1-F4] SCENE: close-up of a glass bowl on a wooden table
- Wrong (a channel logo): - [F2-F8] TEXT: "AFP"
  Right: skip logos and watermarks.

Output format:
Each line is: - [Ffirst-Flast] TYPE: description
TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video with 8 frames; the shot cuts after frame 4 and after frame 7):
- [F1-F4] SCENE: kitchen with white wall tiles
- [F5-F7] SCENE: close-up of a frying pan on a gas stove
- [F8-F8] SCENE: dining table by a window
- [F1-F4] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
- [F1-F2] EVENT: woman in a red apron talks to the camera
- [F3-F3] EVENT: woman in a red apron cracks an egg into the glass bowl
- [F4-F4] EVENT: woman in a red apron whisks the egg with a fork
- [F1-F4] OBJECT: clear glass bowl on the wooden table in front of the woman
- [F1-F2] TEXT: "Easy Omelette"
- [F5-F8] OBJECT: black frying pan with melted butter
- [F6-F7] EVENT: beaten egg is poured into the frying pan
- [F7-F7] CHANGE: egg in the pan turns from liquid to solid at the edges
- [F8-F8] ENTITY: boy in a yellow T-shirt, sitting at the table
- [F8-F8] EVENT: boy in a yellow T-shirt eats the omelette with a fork
- [F8-F8] OBJECT: white plate with a folded omelette

Now write the log lines for this window.
```

</details>

### 差分（v5d → v5e）

```diff
--- v5d
+++ v5e
@@ -17 +17 @@
-- OBJECT: each important object, one per line. Give color, shape, count, and position.
+- OBJECT: the most important objects, one per line, at most 5 OBJECT lines per shot. Choose objects that someone could ask about (things people use or hold, large or colorful things, signs). Give color, shape, count, and position. Each object is written once per shot.
@@ -35 +35 @@
-- A window usually needs 10 to 50 lines; a window with many short shots needs more lines than a window with one long shot. When every shot is described, stop.
+- A window usually needs 10 to 40 lines. When every shot is described, stop.
```

### なぜこの変更か

OBJECTを「最も重要な物、1場面5行まで、質問されそうな物（人が使う・持つ物、大きい・色の目立つ物、看板）」にし、「小さな物や背景の物も」を消した。行数を10〜40に戻した。

### 結果（3本）

| 版 | 動画 | 全体の時間(秒) | 上限到達 | 行数 | TEXT最大/区間 | 重複行 | 時刻不一致 | 解析不可 | EVENT割合 | 複数の人を1行 | まとめ損ね | EVENTのない場面 |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| v5e | `66dwcQ1Y048_0` | 473 | 0 | 314 | 9 | なし | 0 | 0 | 16.9% | 0 | 1 | 9/44 |
| v5e | `NexB4vj8_54_0` | 254 | 0 | 149 | 2 | なし | 0 | 0 | 22.1% | 0 | 0 | 2/18 |
| v5e | `BtaVRhoLpC0_0` | 264 | 0 | 145 | 9 | なし | 0 | 0 | 15.2% | 0 | 0 | 0/20 |

### 問題点

- 3本ともループなし。上限到達・時刻不一致・解析不可・複数の人を1行が0。同じ範囲・同じ本文の重複は3本とも最大1回（「3〜4回」は別の場面に同じ物が写っていたもの）。
- 「何もない」行がまだ数件:

```text
- [F8-F8] OBJECT: space, black background with no visible stars or objects
- [F1-F2] TEXT: none
- [F1-F1] TEXT: (none)
- [F1-F5] CHANGE: no visible change in the logo or text position or appearance across frames
```
- **追加の2本で問題が見つかった**（下の表）。日常Vlog `gtX_oRpLClY` の区間4で、スマホの設定画面の項目を書き続けTEXTが297行・上限到達。理系解説 `22iOyzE8Ec0` でエンドクレジットのスタッフ名を19行。

### 次の版の目的

「何もない」行の禁止を言い換え、1枚だけの場面にもEVENTを書かせる。

## 16. v5f（2026-10-21）

<details><summary>v5f の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video that starts at {{chunk.start}} s. Each image above is shown right after its label, such as "frame 1 (120.0 s):". The frames of this window are:
{{chunk.frame_manifest}}

Refer to frames by their numbers: F1 is frame 1, F2 is frame 2, and so on. Count the frames carefully: the label right before each image tells its number.

Write the log in two steps.

Step 1. List the shots.
Look at every frame from the first to the last. A shot is a run of consecutive frames that show the same place from the same camera; the video can cut to a different place, person, or screen between two frames. Write one SCENE line per shot, with the frame range of the whole shot. Every frame belongs to exactly one shot. A shot does not end when an action changes or the camera moves a little; it ends only when the place or the camera view changes.
- Frames 2, 3, and 4 show the same man in front of the same wall: write one line [F2-F4] SCENE, not three lines.

Step 2. For each shot, in order, describe it with these lines. Write each person's EVENT lines right after that person's ENTITY line, so that no person is left without an EVENT line.
- ENTITY: each visible person or animal, one per line. If a shot shows two people, write two ENTITY lines. Describe only how they look: clothing and colors, hair, accessories, and position on the screen. Do not put what they are doing in an ENTITY line; that goes in EVENT.
- EVENT: what each person, animal, or moving thing is doing, one action per line. Every shot that shows a person or animal needs at least one EVENT line, even a shot of only one frame (talking to the camera, walking, cooking, hugging, jumping, holding something, and so on). If the action changes between frames, write one EVENT line for each action with its own frame range, for example "picks up a cup", then "drinks from the cup", then "puts the cup down".
- OBJECT: the most important objects, one per line, at most 5 OBJECT lines per shot. Choose objects that someone could ask about (things people use or hold, large or colorful things, signs). Give color, shape, count, and position. Each object is written once per shot.
- CHANGE: a change that you can see between two frames of the same shot, in how a person or object looks or where it is. If nothing changes, write no CHANGE line.
- TEXT: large or important text in the image (titles, captions, signs, names), copied exactly inside quotation marks. If no words can be read, write no TEXT line.

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

Frame ranges:
- Each line starts with the first and last frame that show the fact, such as [F3-F5]. If only one frame shows it, write the same number twice, such as [F4-F4].
- A person or object that stays in a shot is written once, with the range of all frames where it is seen. Never write the same person or object again for each frame.

Rules:
- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the frame range of all frames where it is seen.
- Write a TEXT line only when you can copy real words from the image. Write each different text once, and write at most 8 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames and @handles, timestamps), subtitles of speech that repeat, and watermarks or channel logos (such as "AFP" or a channel name in a corner).
- Write only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- Skip a type when there is nothing to write for it; never write a line that only says that nothing is there.
- A window usually needs 10 to 40 lines. When every shot is described, stop.
- Do not answer any question. Do not write anything other than log lines.

Common mistakes. Do not write lines like these:
- Wrong (the same object repeated for each frame):
  - [F2-F2] OBJECT: white plate with a yellow cake
  - [F3-F3] OBJECT: white plate with a yellow cake
  Right: - [F2-F8] OBJECT: white plate with a yellow cake
- Wrong (two people in one line): - [F5-F5] ENTITY: man in a gray sweatshirt waving; woman in a plaid shirt waving
  Right:
  - [F5-F5] ENTITY: man with short blond hair in a gray sweatshirt
  - [F5-F5] ENTITY: woman with long brown hair in a red and black plaid shirt
  - [F5-F5] EVENT: man in a gray sweatshirt and woman in a plaid shirt wave at the camera
- Wrong (an action inside an ENTITY line, and no EVENT line): - [F5-F5] ENTITY: man in a light green shirt, walking away from the camera
  Right:
  - [F5-F5] ENTITY: man in a light green shirt and black pants, in the center
  - [F5-F5] EVENT: man in a light green shirt walks away from the camera
- Wrong (one shot split into many SCENE lines with the same place):
  - [F1-F2] SCENE: close-up of a glass bowl on a wooden table
  - [F3-F4] SCENE: close-up of a glass bowl on a wooden table
  Right: - [F1-F4] SCENE: close-up of a glass bowl on a wooden table
- Wrong (a channel logo): - [F2-F8] TEXT: "AFP"
  Right: skip logos and watermarks.

Output format:
Each line is: - [Ffirst-Flast] TYPE: description
TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video with 8 frames; the shot cuts after frame 4 and after frame 7):
- [F1-F4] SCENE: kitchen with white wall tiles
- [F5-F7] SCENE: close-up of a frying pan on a gas stove
- [F8-F8] SCENE: dining table by a window
- [F1-F4] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
- [F1-F2] EVENT: woman in a red apron talks to the camera
- [F3-F3] EVENT: woman in a red apron cracks an egg into the glass bowl
- [F4-F4] EVENT: woman in a red apron whisks the egg with a fork
- [F1-F4] OBJECT: clear glass bowl on the wooden table in front of the woman
- [F1-F2] TEXT: "Easy Omelette"
- [F5-F8] OBJECT: black frying pan with melted butter
- [F6-F7] EVENT: beaten egg is poured into the frying pan
- [F7-F7] CHANGE: egg in the pan turns from liquid to solid at the edges
- [F8-F8] ENTITY: boy in a yellow T-shirt, sitting at the table
- [F8-F8] EVENT: boy in a yellow T-shirt eats the omelette with a fork
- [F8-F8] OBJECT: white plate with a folded omelette

Now write the log lines for this window.
```

</details>

### 差分（v5e → v5f）

```diff
--- v5e
+++ v5f
@@ -16 +16 @@
-- EVENT: what each person, animal, or moving thing is doing, one action per line. Every shot that shows a person or animal needs at least one EVENT line (talking to the camera, walking, cooking, hugging, jumping, holding something, and so on). If the action changes between frames, write one EVENT line for each action with its own frame range, for example "picks up a cup", then "drinks from the cup", then "puts the cup down".
+- EVENT: what each person, animal, or moving thing is doing, one action per line. Every shot that shows a person or animal needs at least one EVENT line, even a shot of only one frame (talking to the camera, walking, cooking, hugging, jumping, holding something, and so on). If the action changes between frames, write one EVENT line for each action with its own frame range, for example "picks up a cup", then "drinks from the cup", then "puts the cup down".
@@ -18,2 +18,2 @@
-- CHANGE: a change in how a person or object looks or where it is, within the shot.
-- TEXT: large or important text in the image (titles, captions, signs, names). Copy it exactly.
+- CHANGE: a change that you can see between two frames of the same shot, in how a person or object looks or where it is. If nothing changes, write no CHANGE line.
+- TEXT: large or important text in the image (titles, captions, signs, names), copied exactly inside quotation marks. If no words can be read, write no TEXT line.
```

### なぜこの変更か

- CHANGE: 「同じ場面の2枚の間で見える変化だけ。変化がなければCHANGEを書かない」。
- TEXT: 「引用符の中に正確に写す。読める語がなければTEXTを書かない」。
- 「1枚だけの場面でもEVENTを書く」。

### 結果（3本）

| 版 | 動画 | 全体の時間(秒) | 上限到達 | 行数 | TEXT最大/区間 | 重複行 | 時刻不一致 | 解析不可 | EVENT割合 | 複数の人を1行 | まとめ損ね | EVENTのない場面 |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| v5f | `66dwcQ1Y048_0` | 692 | 1 | 477 | 9 | あり（最大156回） | 0 | 1 | 11.7% | 0 | 1 | 3/44 |
| v5f | `NexB4vj8_54_0` | 524 | 1 | 338 | 4 | あり（最大165回） | 0 | 0 | 13.6% | 0 | 1 | 0/20 |
| v5f | `BtaVRhoLpC0_0` | 260 | 0 | 145 | 8 | あり（最大2回） | 0 | 0 | 16.6% | 0 | 0 | 0/19 |

### 問題点

- **ループが再発**。VlogでOBJECTが156回、料理でCHANGEが165回、2本で上限到達。
- AIの考え: v5dでもv5fでも、プロンプトを少し変えただけでループが出たり消えたりした。ループは指示の中身より、temperature 0の貪欲生成が一度同じ行に入ると抜けられない性質によるもので、プロンプトの小さな違いで起きたり起きなかったりする。



### 次の版の目的

v5fは採用しない。v5eに戻り、追加の2本で見つかった「文字の多い画面」への規則を足す。

## 17. v5g（2026-10-21）

<details><summary>v5g の本文（全文）</summary>

```text
You are writing a visual log of a long video. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will search this log to find moments and answer multiple-choice questions about them. The questions are not known now. They usually point to a moment by describing how it looks in detail (for example, "a man in a black suit standing in front of a white table, with a vase on the left"), and then ask what happened, what was there, what something looked like, what changed, or what came before or after.

You are viewing one window of the video that starts at {{chunk.start}} s. Each image above is shown right after its label, such as "frame 1 (120.0 s):". The frames of this window are:
{{chunk.frame_manifest}}

Refer to frames by their numbers: F1 is frame 1, F2 is frame 2, and so on. Count the frames carefully: the label right before each image tells its number.

Write the log in two steps.

Step 1. List the shots.
Look at every frame from the first to the last. A shot is a run of consecutive frames that show the same place from the same camera; the video can cut to a different place, person, or screen between two frames. Write one SCENE line per shot, with the frame range of the whole shot. Every frame belongs to exactly one shot. A shot does not end when an action changes or the camera moves a little; it ends only when the place or the camera view changes.
- Frames 2, 3, and 4 show the same man in front of the same wall: write one line [F2-F4] SCENE, not three lines.

Step 2. For each shot, in order, describe it with these lines. Write each person's EVENT lines right after that person's ENTITY line, so that no person is left without an EVENT line.
- ENTITY: each visible person or animal, one per line. If a shot shows two people, write two ENTITY lines. Describe only how they look: clothing and colors, hair, accessories, and position on the screen. Do not put what they are doing in an ENTITY line; that goes in EVENT.
- EVENT: what each person, animal, or moving thing is doing, one action per line. Every shot that shows a person or animal needs at least one EVENT line (talking to the camera, walking, cooking, hugging, jumping, holding something, and so on). If the action changes between frames, write one EVENT line for each action with its own frame range, for example "picks up a cup", then "drinks from the cup", then "puts the cup down".
- OBJECT: the most important objects, one per line, at most 5 OBJECT lines per shot. Choose objects that someone could ask about (things people use or hold, large or colorful things, signs). Give color, shape, count, and position. Each object is written once per shot.
- CHANGE: a change in how a person or object looks or where it is, within the shot.
- TEXT: large or important text in the image (titles, captions, signs, names). Copy it exactly.
  When a frame shows a lot of text at once (a menu, a settings screen, a list, a document, or the credits at the end of a video), do not copy the items one by one. Write one TEXT line with only its title or first line, and describe the rest in an OBJECT line, for example "phone screen showing a settings menu" or "end credits listing names and roles".

How to name people and objects:
- Always name them by how they look: clothing colors, hair, distinctive items, and position. Example: "man in a black T-shirt with short gray hair", not "a man" or "the speaker".
- Use the same name for the same person or object in every line.
- Do not use real names unless they are written on screen.

Frame ranges:
- Each line starts with the first and last frame that show the fact, such as [F3-F5]. If only one frame shows it, write the same number twice, such as [F4-F4].
- A person or object that stays in a shot is written once, with the range of all frames where it is seen. Never write the same person or object again for each frame.

Rules:
- Every line must be different from every other line. Never write the same fact twice. Each distinct text is written once, with the frame range of all frames where it is seen.
- Write a TEXT line only when you can copy real words from the image. Write each different text once, and write at most 8 TEXT lines in the whole window. Skip small interface text on phone or computer screens (buttons, usernames and @handles, timestamps), subtitles of speech that repeat, and watermarks or channel logos (such as "AFP" or a channel name in a corner).
- Write only what is visible in these frames. Do not guess what happens between or after the frames, do not explain why, and do not give opinions.
- Skip a type when there is nothing to write for it; never write a line that only says that nothing is there.
- A window usually needs 10 to 40 lines. When every shot is described, stop.
- Do not answer any question. Do not write anything other than log lines.

Common mistakes. Do not write lines like these:
- Wrong (the same object repeated for each frame):
  - [F2-F2] OBJECT: white plate with a yellow cake
  - [F3-F3] OBJECT: white plate with a yellow cake
  Right: - [F2-F8] OBJECT: white plate with a yellow cake
- Wrong (two people in one line): - [F5-F5] ENTITY: man in a gray sweatshirt waving; woman in a plaid shirt waving
  Right:
  - [F5-F5] ENTITY: man with short blond hair in a gray sweatshirt
  - [F5-F5] ENTITY: woman with long brown hair in a red and black plaid shirt
  - [F5-F5] EVENT: man in a gray sweatshirt and woman in a plaid shirt wave at the camera
- Wrong (an action inside an ENTITY line, and no EVENT line): - [F5-F5] ENTITY: man in a light green shirt, walking away from the camera
  Right:
  - [F5-F5] ENTITY: man in a light green shirt and black pants, in the center
  - [F5-F5] EVENT: man in a light green shirt walks away from the camera
- Wrong (one shot split into many SCENE lines with the same place):
  - [F1-F2] SCENE: close-up of a glass bowl on a wooden table
  - [F3-F4] SCENE: close-up of a glass bowl on a wooden table
  Right: - [F1-F4] SCENE: close-up of a glass bowl on a wooden table
- Wrong (a channel logo): - [F2-F8] TEXT: "AFP"
  Right: skip logos and watermarks.

Output format:
Each line is: - [Ffirst-Flast] TYPE: description
TYPE is one of SCENE, ENTITY, OBJECT, EVENT, CHANGE, TEXT.

Example (from a different video with 8 frames; the shot cuts after frame 4 and after frame 7):
- [F1-F4] SCENE: kitchen with white wall tiles
- [F5-F7] SCENE: close-up of a frying pan on a gas stove
- [F8-F8] SCENE: dining table by a window
- [F1-F4] ENTITY: woman in a red apron over a white shirt, long black hair tied back, behind the table
- [F1-F2] EVENT: woman in a red apron talks to the camera
- [F3-F3] EVENT: woman in a red apron cracks an egg into the glass bowl
- [F4-F4] EVENT: woman in a red apron whisks the egg with a fork
- [F1-F4] OBJECT: clear glass bowl on the wooden table in front of the woman
- [F1-F2] TEXT: "Easy Omelette"
- [F5-F8] OBJECT: black frying pan with melted butter
- [F6-F7] EVENT: beaten egg is poured into the frying pan
- [F7-F7] CHANGE: egg in the pan turns from liquid to solid at the edges
- [F8-F8] ENTITY: boy in a yellow T-shirt, sitting at the table
- [F8-F8] EVENT: boy in a yellow T-shirt eats the omelette with a fork
- [F8-F8] OBJECT: white plate with a folded omelette

Now write the log lines for this window.
```

</details>

### 差分（v5e → v5g）

```diff
--- v5e
+++ v5g
@@ -19,0 +20 @@
+  When a frame shows a lot of text at once (a menu, a settings screen, a list, a document, or the credits at the end of a video), do not copy the items one by one. Write one TEXT line with only its title or first line, and describe the rest in an OBJECT line, for example "phone screen showing a settings menu" or "end credits listing names and roles".
```

### なぜこの変更か（v5eからの差分）

TEXTに「メニュー・設定画面・一覧・文書・エンドクレジットのように文字の多い画面は、1項目ずつ写さず、タイトルか最初の1行だけをTEXTにして、残りはOBJECTで『設定メニューの画面』『名前と役割が並ぶエンドクレジット』のようにまとめる」を追加。

### 結果（3本）

| 版 | 動画 | 全体の時間(秒) | 上限到達 | 行数 | TEXT最大/区間 | 重複行 | 時刻不一致 | 解析不可 | EVENT割合 | 複数の人を1行 | まとめ損ね | EVENTのない場面 |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| v5g | `66dwcQ1Y048_0` | 480 | 0 | 304 | 9 | なし | 0 | 0 | 18.1% | 0 | 0 | 4/45 |
| v5g | `NexB4vj8_54_0` | 248 | 0 | 144 | 2 | なし | 0 | 0 | 27.8% | 0 | 1 | 0/15 |
| v5g | `BtaVRhoLpC0_0` | 263 | 0 | 148 | 8 | なし | 0 | 0 | 16.2% | 0 | 0 | 1/20 |

### 問題点

- 最初の3本で最良（上限到達0、重複なし、EVENTのない場面 4/45・0/15・1/20、まとめ損ね 0/1/0、複数の人を1行 0）。
- 追加の2本: クレジットは19 → 6行に直った。**スマホの色一覧の画面はまだ暴走**（TEXT 297行、画面にない色の名前まで書き続ける）:

```text
- [F1-F8] TEXT: "Small #7"
- [F1-F8] TEXT: "Default"
- [F1-F8] TEXT: "Style"
…（中略、同じ形の行が続く）
- [F1-F8] TEXT: "Pastel Orange"
- [F1-F8] TEXT: "Cream"
- [F1-F8] TEXT: "Pale Pink"
- [F
```
- 何もない行が料理で2行残る。

### 次の版の目的

（v5として確定。残課題は次節）

## 18. 追加の2本での確認と、repetition_penalty の実験

v5e・v5gを、最初の3本とは別の2本でも試した（`gtX_oRpLClY` 日常Vlog、`22iOyzE8Ec0` 理系解説）。

| 版 | 動画 | 全体の時間(秒) | 上限到達 | 行数 | TEXT最大/区間 | 重複行 | 時刻不一致 | 解析不可 | EVENT割合 | 複数の人を1行 | まとめ損ね | EVENTのない場面 |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| v5e | `gtX_oRpLClY_0` | 608 | 1 | 515 | 297 | あり（最大47回） | 0 | 1 | 13.0% | 0 | 1 | 0/23 |
| v5e | `22iOyzE8Ec0_0` | 316 | 0 | 183 | 19 | なし | 0 | 0 | 12.0% | 0 | 0 | 2/16 |
| v5g | `gtX_oRpLClY_0` | 569 | 1 | 495 | 297 | あり（最大32回） | 0 | 1 | 12.3% | 0 | 1 | 1/13 |
| v5g | `22iOyzE8Ec0_0` | 278 | 0 | 155 | 6 | なし | 0 | 0 | 14.2% | 1 | 0 | 1/16 |

プロンプトでは、文字がぎっしり並んだスマホ画面の暴走を止められなかった。そこで、**行を削除する後処理ではない対策** として、生成設定 `repetition_penalty`（それまでに出た言葉の点数を少し下げ、同じ言葉を選びにくくする設定）を1.05にして試した（実験のみ、Workbenchには入れていない）。

| 版 | 動画 | 全体の時間(秒) | 上限到達 | 行数 | TEXT最大/区間 | 重複行 | 時刻不一致 | 解析不可 | EVENT割合 | 複数の人を1行 | まとめ損ね | EVENTのない場面 |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| v5g + rp1.05 | `gtX_oRpLClY_0` | 446 | 0 | 255 | 22 | なし | 0 | 0 | 24.7% | 0 | 12 | 0/16 |
| v5g + rp1.05 | `66dwcQ1Y048_0` | 536 | 0 | 282 | 7 | なし | 0 | 0 | 16.3% | 0 | 1 | 7/43 |

- 日常Vlog: 上限到達 1 → 0、全体 569 → 446秒、設定画面の区間のTEXT 297 → 7行（どれも画面にある項目）。最初のVlogは悪化なし。
- ウィジェットの説明の区間で、画面に実際にある文字を22行書いた（ループではないが8行の上限は超える）。
- 注意点: 減点はプロンプトや前の行の言葉にもかかるので、「同じ人は同じ呼び方」が守られにくくなるおそれ（1.05は弱め。2本で目に見える崩れはなかったが、全動画では未確認）。
- **採用するかは林と相談中**（2026-10-21、一旦ステイ）。

## 19. 現在の状態と残課題（2026-10-21）

- 既定のプロンプト: **v5**（`record.image.v5`、commit `3b6b90d`）。v3・v4も選べる。
- 入力: 画像の直前に「frame k (t s):」（commit `c6d1d4c`）。範囲はframe番号で書かせ、秒への変換はコード（commit `b2f2a1a`）。

| 課題 | 状態 |
| --- | --- |
| TEXTのループ（v3） | 試した5本中4本で解消。文字がぎっしり並んだスマホ画面では残る |
| 時刻のずれ・1枚目だけを書く（v3） | 解消（時刻不一致0、場面の対応は確認した区間で正しい） |
| 実行時間（v3） | 3分の動画で 14分16秒 → 約8分（v5、Vlog） |
| EVENTが少ない（v4） | 解消（人が写る場面のEVENT抜けは 1割以下） |
| 1行に複数の人（v4） | 解消（0） |
| 同じ場面を1枚ずつ（v4） | 解消（まとめ損ね 0〜1） |
| 何もないことを書く行 | まれに残る（料理で2行） |
| TEXTが8行を少し超える | 実際の字幕・項目で、ループではない |

学んだこと（AIの考え）:
1. 4Bのモデルは、秒でframeを正確に指せない。画像の直前のラベルと同じ番号（frame番号）で指させると対応が取れる。どの画像が何秒かは、文章ではなく入力の並べ方で伝える必要があった。
2. 「まとめる」と指示するより、先に場面の一覧を書かせる（2段階）方が、まとめ損ねが大きく減る。
3. 誤りと正しい例の組は効く。ただし、禁止したい語（none）そのものを例に書くと、かえって真似されることがある。
4. 行数の上限を緩める、指示を少し変える、だけでループが出たり消えたりする。temperature 0の貪欲生成のループは、プロンプトだけでは初めて見る種類の画面まで確実には防げない。
