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
- **全版の本文（2026-10-22〜）**: 新リポジトリの `prompts/history/`（`record/` に v0〜v6h と動画入力版、`old-workbench-65af089/` に旧Workbenchの一式、`README.md` に版の一覧と本ノートの節）。試行の本文は `experiments/*/prompts/` からここへ移した（branch `exp/qwen-video-input-timestamps`、commit `b0f6fe7`）。
- 実行結果と試行の記録: 新リポジトリの `experiments/2026-10-20-record-prompt-trials/`（Run 4件、試行のJSONと動画ごとのMarkdown、試した案の本文、スクリプト。commit `8cd5c76`）。

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
| v6a | 10/21 | 試行 | 3本（40秒） | EVENTだけを一から（GEBDのイベント＝変化） | v5の約1/3〜1/5の時間。続く動作を別の行に分ける |
| v6b〜v6d | 10/21 | 試行 | 3本（40秒） | 続く動作は1行、付ける情報は1つ、区切りを先に決める、何が変わったか | 第25〜27節 |
| v6e | 10/21 | 試行 | 3本（40秒） | 寄り・引き・角度だけのカットは区切らない | v6系の到達点（第28節） |
| v6f | 10/21 | 試行 | 3本（40秒） | 直前の行との自己チェック、状態だけの行の禁止 | 効かず、v6eとほぼ同じ |
| v6e（20秒） | 10/21 | 試行 | 3本（20秒） | 区間を20秒・8枚に戻す（林の指示） | 時間と行数が約2倍。集約の入力にした |
| v6g | 10/21 | 試行 | 3本（20秒） | 人を3つの特徴で呼ぶ、性別に自信がなければ person、例の呼び方も3つに | 暴走なし。呼び方は詳しくなったが、似た3人を区別できない |
| v6h | 10/21 | 試行 | 3本（20秒） | 髪型とひげの形、似た人は違う特徴を書く、コンマを使わない呼び方の例 | 第32節 |

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

## 20. なぜ SCENE・ENTITY・OBJECT・EVENT・CHANGE・TEXT に分けているのか

記録を6つの種類（TYPE）に分けて1行1事実で書かせている理由を、壁打ちでの決定、LongVideoBenchの質問の形、先行研究Imprintの3つの面から整理した。

### 20.1 出発点: 記録は「索引」で、質問は「見た目で場面を指し、その場面について聞く」

- 記録は、動画を見られない人が後で**検索**して答えるための索引と位置づけた（2026-10-20 決定）。散文の要約では、どこに何が書いてあるかを探せない。
- LongVideoBenchの質問は、ほぼすべて「場面の説明（referring query）」＋「短い質問」の形をしている（T系以外のvalで場面の説明は中央値32語）。
  - 場面の説明は「どこで（場所・背景）」「誰が（服の色・髪）」「何があって（物・位置）」「何が書いてあって（画面の文字）」で場面を指す。
  - 短い質問は「何が起きたか」「何があったか」「どんな見た目か」「何が変わったか」「前後に何があったか」を聞く。
- そこで、**場面を探す手がかり**と**答えの材料**を、それぞれ別の種類として残すことにした。

### 20.2 種類とLongVideoBenchのタスクの対応

| 種類 | 何を書くか | 主に役立つ場面 | 対応するタスク（T系以外） |
| --- | --- | --- | --- |
| SCENE | 場所だけ（1ショットに1行、範囲つき） | 場面の説明の「どこで」。ショットの区切り（いつ場面が変わったか） | 全タスクの場面探し、SSS（場面の順序）、SOS（再び現れる場面） |
| ENTITY | 人・動物の見た目と位置（1人1行） | 場面の説明の「誰が」。区間をまたいで同じ人を照らし合わせる手がかり | E2O（出来事→人）、O3O・SOS（再登場の追跡）、S2A（人の見た目） |
| OBJECT | 物の色・形・数・位置（1つ1行） | 場面の説明の「何があって」、答えの「何があったか・どんな見た目か」 | S2O（その場面にある物）、S2A（物の属性）、O2E・O3O |
| EVENT | 1人が1つの動作をする（1動作1行、範囲つき） | 答えの「何が起きたか」「前後に何をしたか」 | S2E、O2E、E3E（前後の出来事）、SSS |
| CHANGE | 同じショットの中での見た目・位置の変化 | 答えの「何が変わったか」 | SAA（属性の変化） |
| TEXT | 画面に焼き込まれた文字をそのまま | 場面の説明が画面の文字で場面を指すとき、字幕（焼き込み） | 全タスクの場面探し（T系は外したが、焼き込みの文字は残す） |

（タスクとの対応は [タスク一覧表のメモ](../../../../secretary/notes/brainstorm/2026-10-19-longvideobench-task-table-without-subtitles.md) の整理にもとづく。どの種類が実際にどのタスクの正答に効くかは、回答Agentができてから確かめる。）

### 20.3 種類に分けると何がうれしいか（AIの考えを含む）

1. **探しやすい**: 場面の説明を「場所・人・物・文字」に分けて照らし合わせられる。たとえばTEXTだけを文字列検索する、ENTITYだけを見た目で照合する、ができる。
2. **後の処理（集約・回答）に渡しやすい**: 区間をまたいだ集約は種類ごとに違う。ENTITYは同じ人の照合（再登場）、EVENTは時刻順の並べ替え（前後関係）、SCENEはショットのつなぎ合わせ、が必要になる。区間の端で続いているかの印（`from_window_start` / `to_window_end`）も、種類ごとにつなげる。
3. **予習の観点をそのまま表せる**: 予習は当面、手書きのプロンプトで代用している（2026-10-20 決定）。「出来事系・物体系・属性系のタスクが来る」という予習の結果が、「EVENT・ENTITY/OBJECT・CHANGE を書け」という観点になっている。予習Agentを作るときは、この観点（種類と、それぞれに何を書くか）を予習Agentが出す形になる見込み。
4. **抜けと暴走を数えられる**: 種類が決まっているので、「人が写っている場面にEVENTがあるか」「TEXTが何行か」「同じ行の重複」などを自動で数えられた（v4〜v5の試行錯誤はこの指標で進めた）。散文ではこれができない。
5. **小さいモデルを制御しやすい**: 「1行1事実・決まった種類」にすると、書き忘れ（例: EVENTがない）や、1行への詰め込み（例: 2人を1行）を、プロンプトの規則と誤りの例で個別に直せた。

### 20.4 Imprintとの比較（Imprintの内容は本文で確認済み、比較はAIの考え）

[Imprint](https://arxiv.org/abs/2607.00696)（Das & Roy, arXiv 2607.00696, 2026-07）も、見ながらテキストの記録を作り、後で質問に答える。記録を構造化する点は同じで、分け方とその理由が参考になる（詳細は [先行研究の調査メモ](../../../../secretary/notes/brainstorm/2026-10-21-pre-study-and-event-log-prior-work.md)）。

| | Imprint | 私たち（v5） |
| --- | --- | --- |
| 記録の単位 | 1つのやり取りにつき1件の Interaction Record: (person, action, object, start, end)。補助として道具・アプリ・場所・発話・属性 | 1行1事実。6種類（SCENE / ENTITY / OBJECT / EVENT / CHANGE / TEXT）とframe範囲 |
| 作り方 | 2段: EgoGPTが一人称の語り（キャプション）を書く → Qwen2.5-7Bが記録に変換 | 1段: Qwen3-VL-4Bが画像から直接、種類つきの行を書く |
| 構造化する理由（Imprintは本文） | 質問をLLMで (人, 動作, 物体, 意図, 時間の関係) のJSONに分解し、記録の欄と照合して取り出すため。要約（EgoRAG）は繰り返しのやり取りを粗い記述に吸収してしまい、長期の集計に弱い | 質問の「場面の説明」を場所・人・物・文字で照合し、答えの材料（出来事・物・変化）を取り出すため |
| 予習の効かせ方 | 64個のメタ質問を「hidden guidance」としてキャプションのプロンプトに入れる（書き方にだけ効く） | 予習の観点を「どの種類に何を書くか」としてプロンプトに書く（手書き） |
| 時刻 | 抽出の形式（付録B）に時刻の欄がなく、どこから得ているかは本文で明確でない | frame番号で範囲を書かせ、コードで秒に変換する（v4以降） |
| 集約 | 埋め込みの類似度と閾値で、型への割り当て・重要度・まとめ（捨てる・まとめる・足す） | 未実装（種類ごとにつなぐ予定。時間スケールの階層も想定） |

違いの理由（AIの考え）:
- **人・動作・物を1件にまとめるImprintに対し、私たちはENTITYとEVENTとOBJECTを分けている。** Imprintの対象（一人称のライフログ）は、自分や周りの人が物を使うやり取りが中心で、質問も「誰が何をどうしたか」に集中する。LongVideoBenchは第三者視点の編集された動画で、物だけを問う（S2O・S2A）、人の見た目を手がかりに追う（SOS・O3O）、動作の前後を問う（E3E）など、人・物・動作が別々に問われる。そのため別々の行にした。
  - ただし、EVENT行（「man in a light green shirt walks away from the camera」）は、実質的に Imprint の (person, action, object) に近い。
- **SCENEとTEXTがある。** 編集された動画にはカット（ショットの切り替わり）と、画面に焼き込まれた文字（字幕・タイトル）が多い。一人称の連続した映像が対象のImprintには、ショットの区切りの欄がない。v3の失敗（8枚とも違う場面なのに1枚目だけを書く）からも、ショットを先に区切らせることが必要だった（v5の2段階）。
- **CHANGEがある。** SAA（属性の変化）のため。Imprintには属性の欄はあるが、変化の欄はない。
- **1段で書かせている。** 2段（キャプション → 記録）にすると、キャプションの誤りが記録に伝わる（Imprintも限界として挙げている）うえ、モデルを2回呼ぶので時間がかかる。v5は1段で、種類の分け方まで1回の呼び出しで決めさせている。2段にした場合との比較はしていない。

## 21. v5（最終版）の各ブロックで言いたいこと

v5本文を上から順にブロックに分け、それぞれの主旨と、入れた理由（どの問題に対応しているか）、最初に入った版をまとめた。

| # | ブロック（本文の書き出し） | 言いたいこと | なぜ入れたか（対応する問題・経緯） | 入った版 |
| --: | --- | --- | --- | --- |
| 1 | You are writing a visual log… | この記録だけが残る。動画を見られない人が後で検索し、多肢選択の質問に答える。質問は未知で、見た目の細かい説明で場面を指し、何が起きた・何があった・どんな見た目・何が変わった・前後に何があったかを聞く | 旧Workbenchは目的を伝えておらず、何を残すべきかをモデルが判断できなかった。LongVideoBenchの質問の形を伝えて、細部を残させる | v0（「検索」「細部」はv2） |
| 2 | You are viewing one window… starts at {{chunk.start}} s. Each image above is shown right after its label… | 区間の始まりの時刻と、各画像の直前にラベル（frame k (t s)）があること、frame一覧 | v4aまで画像と時刻の対応がずれていた（ラベルなし）。区間の終わりの時刻は、1枚だけの区間で区間の終わりを書く原因になったので外した | v4b |
| 3 | Refer to frames by their numbers: F1 is frame 1… | frameは番号で指す。直前のラベルで番号を数える | 秒で書かせると1枚ずれる（v4b・v4c）。番号なら全frameで対応が取れた（v4d） | v4d |
| 4 | Write the log in two steps. | 2段階で書く | 「まとめて」と頼んでも1枚ずつ書いた（v4）。先に区切りを決めさせる | v5a |
| 5 | Step 1. List the shots. | 全frameを1回ずつ見て、ショット（同じ場所・同じカメラの連続したframe）ごとにSCENEを1行、範囲つきで書く。全frameがどれか1つのショットに入る。動作が変わったり少しカメラが動いたりしただけでは区切らない。例: F2〜F4が同じ男性と同じ壁なら [F2-F4] を1行 | v3で1枚目の場面だけを書いた。v4で同じ場面を1枚ずつ書いた（まとめ損ね 14/41）。v5bで料理の同じ場所を細かく分けた | v4a（カット）→ v5a（一覧）→ v5c（区切りの基準） |
| 6 | Step 2. For each shot, in order… Write each person's EVENT lines right after that person's ENTITY line… | ショットごとに順に書く。各人のENTITY行の直後にその人のEVENT行を書き、EVENTのない人を残さない | v5c までVlogでEVENTのない場面が多かった（13/40） | v5a（ショットごと）→ v5d（直後にEVENT） |
| 7 | - ENTITY: … | 人・動物は1人1行。見た目（服と色、髪、持ち物）と位置だけ。動作はENTITYに書かずEVENTへ | 2人を「;」でつないで1行（v4・v5a）。動作がENTITYに入り込みEVENTがない（v5b） | v0（呼び方）→ v5a（1人1行）→ v5c（見た目だけ） |
| 8 | - EVENT: … | 動いているものの動作を1動作1行。人や動物が写るショットには最低1つ（話す・歩く・料理する・抱き合う・跳ぶ・持つ…）。動作が変わればそれぞれ範囲つきで（取る→飲む→置く） | E3Eは数秒の動作の前後を問う（v2）。v4ではVlogのEVENTが4.5%しかなかった | v2（分け方）→ v5a（最低1つ） |
| 9 | - OBJECT: … | 最も重要な物を1つ1行、1ショット5行まで。質問されそうな物（使う・持つ物、大きい・目立つ物、看板）。色・形・数・位置。1ショットに1回 | S2O・S2Aは物と見た目を問う（v2で追加）。一方「小さな物や背景の物も」と行数上限50が重なるとOBJECTのループ（v5d、185回） | v2 → v5e（5行まで） |
| 10 | - CHANGE: … | 同じショットの中での見た目・位置の変化 | SAA（属性の変化）のため | v0 |
| 11 | - TEXT: …（文字の多い画面の規則を含む） | 大きく重要な文字（タイトル・字幕・看板・名前）をそのまま写す。メニュー・設定画面・一覧・文書・エンドクレジットは1項目ずつ写さず、タイトルだけをTEXTにして、残りはOBJECTで「設定メニューの画面」のようにまとめる | v3のTEXTのループ（136回）。追加の2本で設定画面297行・クレジット19行 | v0 → v4a（大きく重要な文字）→ v5g（文字の多い画面） |
| 12 | How to name people and objects | 見た目で呼ぶ（「a man」でなく「黒いTシャツで短い灰色の髪の男性」）。同じものは同じ呼び方。画面に書かれていない限り実名を使わない | 前の区間の記録を見せないので、区間をまたいで同じ人と分かる手がかりは呼び方だけ。質問も見た目で人を指す | v0 |
| 13 | Frame ranges | 行は写っている最初と最後のframeで始める（[F3-F5]、1枚なら [F4-F4]）。ショットにとどまる人・物は全範囲で1回だけ書き、枚ごとに書き直さない | v1の「続く動作は1行」を範囲の形にしたもの。料理で皿・テーブルを8枚それぞれに書いた（v5a） | v1 → v4d（番号）→ v5b（1回だけ） |
| 14 | Rules: Every line must be different… | すべての行は互いに違う。同じ事実・同じ文字は1回だけ | v3のループ | v4a |
| 15 | Rules: Write a TEXT line only when… at most 8… | 実際に写せる語があるときだけTEXT。違う文字は1回ずつ、1区間8行まで。小さなUIの文字（ボタン・ユーザー名・@・時刻）、繰り返す発言の字幕、透かし・ロゴ（AFPなど）は書かない | 上限5行では意味のある字幕まで捨てる（v5c、コラージュの字幕9行）。スマホのUI・ロゴがTEXTに入った | v4a（5行）→ v5a〜v5d（対象外の追加、8行） |
| 16 | Rules: Write only what is visible… | 見えているものだけ。frameの間や後を推測しない、理由を説明しない、意見を書かない | 作り話を防ぐ | v0 |
| 17 | Rules: Skip a type… never write a line that only says that nothing is there | 書くことのない種類は書かない。「何もない」とだけ言う行を書かない | `TEXT: none`、`CHANGE: no notable change`（v3〜v5）。「none」の語を例に書くと真似されたので、語を使わず言い換えた（v5d） | v4a → v5d |
| 18 | Rules: A window usually needs 10 to 40 lines… stop. | 1区間はふつう10〜40行。全ショットを書いたら止める | ループと長すぎる出力の対策。50行に緩めるとループが起きた（v5d） | v4a（v5dで50 → v5eで40に戻す） |
| 19 | Rules: Do not answer any question… | 質問に答えない。記録の行以外を書かない | 前置きや説明文（解析できない行）を防ぐ | v0 |
| 20 | Common mistakes | 誤りと正しい書き方の組: 同じ物を枚ごとに書く／2人を1行／動作をENTITYに書く／同じ場所の場面を分ける／ロゴをTEXTに | v5a〜v5cで実際に出た誤りそのもの。規則だけより、誤りの例を見せた方が直った（v5bで複数の人を1行が0に） | v5b（v5cで追加） |
| 21 | Output format | `- [Ffirst-Flast] TYPE: description`、TYPEは6種類 | 解析処理が読める決まった形式。最後に置くと小さいモデルでも守りやすい | v0（frame番号はv4d） |
| 22 | Example | 架空の料理動画（8枚、frame 4と7の後でカット）。場面の一覧 → 場面ごとの人・動作・物・文字・変化 | 形式・2段階の順番・動作の分け方・1枚だけの場面のEVENTを見せる。例は評価データから作らない（決定） | v0 → v5a・v5d（場面3つ） |
| 23 | Now write the log lines for this window. | 書き始めの合図 | — | v0（v4bで区間の終わりの時刻を外した） |

### 21.1 この表を作っていて気づいた点（未修正）

- 例（ブロック22）の `- [F5-F8] OBJECT: black frying pan with melted butter` は、F8が別の場面（dining table）なので、ブロック13の規則から見ると [F5-F7] が正しい。v5dで場面を3つに増やしたときに直し忘れた。モデルが範囲を広げて書く原因になりうるので、次の版で直したい。
- ブロック9の「Each object is written once per shot」と、ブロック13の「A person or object that stays in a shot is written once」は同じことを2回言っている（意図的な重ね書きだが、長さを減らすなら1つにまとめられる）。

## 22. 第20節の見直し: 6種類に分けるのは本当によいのか（2026-10-21）

林の問い「20節の分け方が本当にいいのか検討してほしい」への回答。結論から書く。

### 22.1 結論

- **第20節は、分け方を決めた後に理由を並べた「後付けの説明」で、検証されていない主張が混ざっている。** 6種類は、2026-10-20の壁打ち（v0）で、LongVideoBenchのタスク名の文字（S=場面、E=出来事、O=物体、A=属性、T=字幕）から作った観点で、他の分け方と比べて選んだものではない。
- 6種類に分けたことで確かに得られたのは、**小さいモデルを規則で制御し、抜けや暴走を数えられたこと**（20.3の4・5）だけ。**記録を探しやすい・答えやすい（20.3の1・2）は、回答Agentがないので未検証**。
- v5の実際の出力では、**種類の境界がかなり守られていない**（下の22.3）。境界があいまいな種類（ENTITYとEVENT、OBJECTとTEXT、EVENTとCHANGE）は、種類で絞り込んで探す前提を崩す。
- そのため、**今の6種類は「暫定の形」として扱い、探しやすさを確かめる小さな実験をしてから決め直す**のがよいと考える（22.5）。

### 22.2 第20節の主張ごとの検討

| 第20節の主張 | 根拠の強さ | 懸念・反証 |
| --- | --- | --- |
| 質問は「見た目で場面を指し、その場面について聞く」ので、手がかりと答えの材料を分ける | 質問の形は集計で確認済み（場面の説明は中央値32語） | 場面の説明は**1つの長い文章**（場所・人・物・文字が混ざった描写）。種類ごとに分けた短い行より、同じような描写の文章（ショットごとのキャプション）の方が照らし合わせやすい可能性がある。未検証 |
| 種類とタスクの対応表（20.2） | 対応づけはタスクの定義からの推論 | どの種類がどのタスクの正答に効くかは測っていない。表のとおりに効く保証はない |
| 1. 種類ごとに探せる | 未検証 | 境界が守られていない（22.3）ので、「TEXTだけを検索」すると、OBJECTの中に書かれた看板の文字を取りこぼす |
| 2. 集約で種類ごとにつなげる | 未検証（集約は未実装） | ENTITYとEVENTが別の行なので、「誰が何をしたか」をつなぐには、呼び方の文字列の一致に頼るしかない。Imprintは (person, action, object) を1件にまとめていて、つなぐ必要がない |
| 3. 予習の観点をそのまま表せる | 考え方としては成り立つ | 観点がLongVideoBenchのタスク名に合わせて手で作られているので、他のデータセットへの一般化は弱い（議事録の懸念「予習を前提にすると違う種類の質問に対応できない」と同じ） |
| 4. 抜けと暴走を数えられる | v4〜v5の試行錯誤で実際に使えた | 指標の多くが「分け方が守られているか」を測っていて、分け方の良し悪しそのものは測っていない（循環している） |
| 5. 小さいモデルを制御しやすい | 1行に複数の人・まとめ損ねは規則と誤りの例で直った | v5の規則の半分近くは、種類の境界を守らせるためのもの（ENTITYに動作を書かない、TEXTとOBJECTの分け方、など）。分け方そのものが、プロンプトを長く複雑にしている |
| Imprintとの比較（20.4） | Imprintの内容は本文で確認済み | 「LongVideoBenchでは人・物・動作が別々に問われるから分ける」は推論。逆に、人と動作を1件に結びつけるImprintの形の方が、「黒い服の男性は何をしているか」に答えやすい可能性もある |

### 22.3 v5の出力で、種類の境界はどれくらい守られているか（3本のRun、自動集計）

| | Vlog `66dwcQ1Y048` | 料理 `NexB4vj8_54` | ニュース `BtaVRhoLpC0` |
| --- | --: | --: | --: |
| ENTITYに動作・姿勢の語（standing, holding, talking など）が入っている | 49 / 77 | 12 / 16 | 17 / 26 |
| OBJECTの中に、引用符つきの文字（看板の文字など）がある | 18 / 87 | 0 / 41 | 5 / 30 |
| CHANGEに、動作（注ぐ・混ぜる など）が書かれている | 0 / 5 | 6 / 14 | 1 / 1 |
| EVENTが、ENTITYの呼び方（見た目の説明）を言い直している | 30 / 55 | 0 / 40 | 12 / 24 |
| 語数の内訳（多い順） | ENTITY 1071、OBJECT 759、EVENT 579 | EVENT 476、OBJECT 409、SCENE 247 | ENTITY 413、TEXT 389、OBJECT 357 |

例:
- ENTITY: `woman in a black coat with long dark hair, wearing a yellow face mask, holding a closed umbrella`（「holding」は動作か見た目か、境界があいまい）
- OBJECT: `black trash can with the number "3488" on it on the left side`（文字がTEXTではなくOBJECTに入る）
- CHANGE: `yellow liquid is being poured into the bowl`（注ぐ動作がEVENTではなくCHANGEに入る）

読み取れること（AIの考え）:
- 「立っている」「持っている」のような**姿勢・状態は、見た目（ENTITY）と動作（EVENT）のどちらにも入りうる**。境界はモデルの誤りというより、分け方自体があいまい。
- 看板の文字は「物」でも「文字」でもある。v5の「文字の多い画面はOBJECTにまとめる」規則も、TEXTとOBJECTの境界を自分でぼかしている。
- ENTITYとEVENTを分けたことで、**同じ人の見た目を2回書いている**（Vlogで55行中30行）。語数ではENTITYが最も多く、時間の多くを人の見た目の説明に使っている。

### 22.4 ほかの分け方の候補

| 案 | 形 | よい点 | 弱い点 |
| --- | --- | --- | --- |
| 今（6種類） | SCENE / ENTITY / OBJECT / EVENT / CHANGE / TEXT を1行1事実 | 規則で制御でき、数えられる。予習の観点を書きやすい | 境界があいまい。人と動作が別の行で、つなぐのに呼び方の一致が要る。見た目を2回書く |
| A: Imprint型の記録 | ショット（SCENE）＋「誰が・何を・何に（・どこで）」を1行にまとめた出来事の記録＋TEXT。人の見た目は記録の「誰が」に書く | 人と動作が結びつく（「黒い服の男性は何をしているか」に直接答えられる）。見た目を2回書かない。行が減る | 物だけを問う（S2O）・見た目だけを問う（S2A）ための置き場所が弱い。欄が増えると小さいモデルが守れない可能性 |
| B: ショットの説明文＋出来事の行（2層） | ショットごとに、質問の場面の説明と同じような細かい説明文を1つ（場所・人・物・文字をまとめて）＋その下に出来事（EVENT）とCHANGEの行 | 場面を探す部分が、質問の場面の説明と同じ形（長い描写の文章）になり、照らし合わせやすい可能性。種類の境界の問題が「場面の説明」の中では起きない | 説明文の中は数えにくい（抜けや暴走を測りにくい）。説明文が長くなりすぎる可能性 |
| C: 種類なしの説明文だけ | ショットごと・frameごとの自由なキャプション（EgoRAG・Imprintの1段目に近い） | プロンプトが短い。境界の問題がない | 旧Workbenchで「制御できていない」と指摘された形に近い。数えられない。前後関係（E3E）の材料が薄くなりやすい |

AIの考え: いちばん有望なのは **B（ショットの説明文＋出来事の行）**。理由は、LongVideoBenchの質問が「長い描写の文章で場面を指す」形なので、場面を探す部分は種類に分けず、同じ形の文章で持つ方が自然だから。一方、答えの材料（出来事の前後、変化）は行に分けておく方が、E3E・SSS・SAAに使いやすい。ただし、これも未検証。

### 22.5 決めるための小さな実験（案、未実施）

回答Agentを作る前でも、**「記録から、質問が指している場面を見つけられるか」** は測れる。

1. T系以外のvalから、今の3本＋数本の動画の質問を集める（1本あたり1〜3問）。
2. 各質問の場面の説明（`question` から `question_wo_referring_query` を除いた部分）で、記録を検索する（まずは文字列の類似度か、文の埋め込みの類似度）。
3. 正しい区間を引けたかを数える。正解の区間は、valの `position` から決める（ただし `position` をフレーム番号とみなすのは推論で、公式の説明はない。目で確認しながら使う）。
4. 同じ動画を、今の6種類（v5）と、案A・案Bの記録で比べる。

これで「場面を探す」部分については、どの分け方がよいかを数字で比べられる。答えの材料（出来事の前後など）の比較は、回答Agentができてからになる。

### 22.6 当面の扱い

- 第20節は「分け方を選んだ理由」ではなく「今の分け方の狙い（仮説）」として読む。
- v5（6種類）はこのまま既定にしておき、22.5の実験の結果で、6種類を続けるか、案A・Bに変えるかを決める（林と相談）。

## 23. v6系: EVENTだけを書くプロンプトを一から作る（2026-10-21）

### きっかけ（林）

- 「イベントをタイムスタンプ付きで記述するAgentを作ってと言われているのに、イベント以外も記述させている」。2026-10-19 MTGの決定は「予習した観点でイベントをファイル（Markdown、タイムスタンプ付き）に記録」で、v3〜v5はそこから外れて場面の目録になっていた（第22節）。
- 「どのベンチマークでも網羅的にできるようにしたい」。v3〜v5はLongVideoBenchのタスクに寄っていた。
- v5は直さず、EVENTだけを書く版を **v6として一から** 作る（v3〜v5はtxtで保存しており再現でき、比較用に残す）。

### v6の設計（決定の詳細は [イベントの定義](../../../../secretary/notes/brainstorm/2026-10-21-event-definition.md)、先行研究は [イベント書き起こしの出力形式](../../../../secretary/notes/brainstorm/2026-10-21-event-transcription-prior-work-formats.md)）

- **イベント＝変化**（GEBD, ICCV 2021 にならう）: 動作の始まり・終わり・切り替わり（繰り返しの各回も）、物の扱いの始まり・終わり、人・動物・物が見えるようになる・いなくなる、場所や見え方の切り替わり（カット、カメラの向き、明るさや色の大きな変化）。変化のないところには何も書かない。
- 記録の段階は細かい動作。大きなまとまりは集約で作る。
- 付けてよい情報は、イベントに関わるものについての短い情報を一塊だけ。関わらない物は書かない。
- 背景の人の出来事も、何をしているかがはっきり見えるときだけ書く。
- 特定のベンチマークの質問の形を前提にしない（予習は、質問の例だけを渡す別の枠にする予定。v6系ではまだ入れない）。
- **区間は40秒・8枚**（5秒に1枚）。林の指示「実行時間をできる限り半分に」。
- 終了条件（林）: イベントを、重複・無駄なく、しっかり記録できていることが確認できるまで。無駄な情報の付加も解消する。無理そうなら止めて相談。
- 確認の仕方: 同じ3本（Vlog `66dwcQ1Y048`、料理 `NexB4vj8_54`、ニュース `BtaVRhoLpC0`）で、自動の指標と、区間の8枚の画像と記録の目視の見比べ。試行の本文・スクリプトは新リポジトリの `experiments/2026-10-21-event-prompt-v6/`。

## 24. v6a（2026-10-21）

<details><summary>v6a の本文（全文）</summary>

```text
You are transcribing the events of a video into a time-stamped log. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will read it to answer questions about what happened.

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
If nothing changes between frames, write nothing for those frames.

How to write an event:
- One event per line. Write who does what: name people and animals by how they look, such as "man in a black T-shirt", and use the same name every time.
- You may add one short detail about something that takes part in the event, such as what is shown on a phone screen or what the new place looks like. Do not describe things that do not take part in the event.
- For a change of place, name the new place with at most two features, such as "white room with a blue sofa".
- Write events of people in the background too, but only when you can clearly see what they do. Write the main people first.
- Write only what you can see. Do not guess hidden actions, reasons, or feelings.
- An action that continues over several frames is one event, from its first frame to its last frame.
- Never write the same event twice. When every change in the frames is written, stop.

Output format:
Each line is: - [Ffirst-Flast] EVENT: description
[F3-F5] means the event is seen from frame 3 to frame 5. Use [F4-F4] for a single frame.

Example (from a different video with 8 frames):
- [F1-F3] EVENT: woman in a red apron talks to the camera in a kitchen with white tiles
- [F4-F4] EVENT: woman in a red apron picks up a brown egg
- [F5-F5] EVENT: woman in a red apron cracks the egg into a glass bowl
- [F6-F6] EVENT: view cuts to a close-up of a frying pan on a gas stove
- [F7-F8] EVENT: beaten egg is poured into the frying pan
- [F8-F8] EVENT: boy in a yellow T-shirt comes into view from the right

Now write the events of this window.
```

</details>

### 結果（3本、40秒・8枚、自動集計）

| 動画 | 全体の時間(秒) | 区間 | 上限到達 | 行数 | 行/区間 | 語数の平均 | 語数の最大 | 区間内の重複 | 1行に複数の文 | EVENT以外 | 時刻不一致 | 解析不可 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `66dwcQ1Y048_0` | 100 | 5 | 0 | 33 | 6.6 | 17.1 | 34 | 1 | 0 | 0 | 0 | 0 |
| `NexB4vj8_54_0` | 95 | 6 | 0 | 45 | 7.5 | 12.0 | 20 | 0 | 2 | 0 | 0 | 0 |
| `BtaVRhoLpC0_0` | 68 | 5 | 0 | 29 | 5.8 | 12.3 | 22 | 6 | 0 | 0 | 0 | 0 |

### なぜこの形か

v5からの差分ではなく、一から書いた（上の「v6の設計」をそのまま本文にした）。v4までで分かった入力の工夫（画像の直前のラベル、frame番号での範囲）だけは引き継いだ。

### 目視の確認

- 速さ: Vlog 100秒・料理 95秒・ニュース 68秒（v5は 480・248・263秒）。上限到達・EVENT以外の行・時刻不一致・解析不可は0。
- Vlog 区間4（120〜155秒、8枚とも違う場面）: 8枚の画像と記録がほぼ正確に対応した。場面ごとに1行で、関わる情報だけ。

```text
- [F1-F1] EVENT: aerial view shows a street lined with palm trees, with cars driving on it
- [F2-F2] EVENT: blue screen with white text that reads "We can be so much more..."
- [F3-F4] EVENT: man in a black T-shirt with "SEEK" written on it smiles and looks at the camera against a black and white spiral wall
- [F5-F5] EVENT: person in red shirt holds a smartphone displaying a video call with someone in the background
- [F6-F6] EVENT: hand holds a smartphone displaying a social media post with colorful sticky notes and text "Made my mom a basket of reasons I love her"
- [F7-F7] EVENT: man and woman embrace in an airport terminal under an overpass, with cars and buses visible in the background
- [F8-F8] EVENT: man in a black T-shirt with "SEEK DISCOMFORT" written on it speaks to the camera against a black and white spiral wall
```

- 料理 区間2（40〜75秒）: 画像と対応（ヨーグルトを注ぐ → ベーキングパウダーの器に手を伸ばす → 入れる → ミキサーで混ぜる → 止める）。

### 問題点

1. **続いている動作を別の行に分ける**（ニュースの区間内の重複6）。ニュース 区間2:

```text
- [F6-F6] EVENT: man in a dark suit speaks outside a building
- [F7-F7] EVENT: man in a dark suit speaks outside a building
- [F8-F8] EVENT: man in a dark suit speaks outside a building
```
   料理 区間3でも `electric mixer continues to whip the mixture…`、`hand in black glove continues to fold the mixture…` を新しい行として書いた（本来は前の行の範囲を延ばす）。

2. **付ける情報が一塊を超える**（無駄な情報）:

```text
- [F1-F1] EVENT: three men stand side by side, holding hands, with signs in front of them that read "He is my roommate and best friend," "These are My Brothers," and "He's my roommate and best friend"
- [F5-F6] EVENT: view cuts to a blue screen with "Subscribe (please)" text, two video thumbnails, and social media icons for Instagram, Twitter, and Snapchat with the handle "@YesTheory"
```

3. 小さな問題: 画面の文字の時刻のずれ。料理 区間2で「350g yogurt」はF2の画面に出ているのに、F5の行に「5g baking powder」と一緒に書いた。

### 次の版の目的

- 続いている動作は、前の行の範囲を延ばして1行にする（「continues to」で新しい行を書かない）。誤りと正しい例を1組見せる。
- 付ける情報は一塊（1つ）まで。複数の物・文字・アイコンを並べない。誤りと正しい例を1組見せる。

## 25. v6b（2026-10-21）

<details><summary>v6b の本文（全文）</summary>

```text
You are transcribing the events of a video into a time-stamped log. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will read it to answer questions about what happened.

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
If nothing changes between frames, write nothing for those frames.

How to write an event:
- One event per line. Write who does what: name people and animals by how they look, such as "man in a black T-shirt", and use the same name every time.
- You may add one short detail about something that takes part in the event, such as what is shown on a phone screen or what the new place looks like. Add only one detail: do not list several objects, texts, signs, or icons. Do not describe things that do not take part in the event.
- For a change of place, name the new place with at most two features, such as "white room with a blue sofa".
- Write events of people in the background too, but only when you can clearly see what they do. Write the main people first.
- Write only what you can see. Do not guess hidden actions, reasons, or feelings.
- An action that continues over several frames is one event: write it once, with the range from its first frame to its last frame. Do not write a new line for an action that is still going on, and do not write "continues to".
- Never write the same event twice. When every change in the frames is written, stop.

Do not write lines like these:
- Wrong (one action split into several lines):
  - [F6-F6] EVENT: man in a dark suit speaks outside a building
  - [F7-F7] EVENT: man in a dark suit continues to speak outside a building
  Right: - [F6-F8] EVENT: man in a dark suit speaks outside a building
- Wrong (a list of details): - [F5-F5] EVENT: view cuts to a blue screen with "Subscribe" text, two video thumbnails, and icons for Instagram, Twitter, and Snapchat
  Right: - [F5-F5] EVENT: view cuts to a blue screen with the text "Subscribe"

Output format:
Each line is: - [Ffirst-Flast] EVENT: description
[F3-F5] means the event is seen from frame 3 to frame 5. Use [F4-F4] for a single frame.

Example (from a different video with 8 frames):
- [F1-F3] EVENT: woman in a red apron talks to the camera in a kitchen with white tiles
- [F4-F4] EVENT: woman in a red apron picks up a brown egg
- [F5-F5] EVENT: woman in a red apron cracks the egg into a glass bowl
- [F6-F6] EVENT: view cuts to a close-up of a frying pan on a gas stove
- [F7-F8] EVENT: beaten egg is poured into the frying pan
- [F8-F8] EVENT: boy in a yellow T-shirt comes into view from the right

Now write the events of this window.
```

</details>

### 差分（v6a → v6b）

```diff
--- v6a
+++ v6b
@@ -19 +19 @@
-- You may add one short detail about something that takes part in the event, such as what is shown on a phone screen or what the new place looks like. Do not describe things that do not take part in the event.
+- You may add one short detail about something that takes part in the event, such as what is shown on a phone screen or what the new place looks like. Add only one detail: do not list several objects, texts, signs, or icons. Do not describe things that do not take part in the event.
@@ -23 +23 @@
-- An action that continues over several frames is one event, from its first frame to its last frame.
+- An action that continues over several frames is one event: write it once, with the range from its first frame to its last frame. Do not write a new line for an action that is still going on, and do not write "continues to".
@@ -24,0 +25,8 @@
+
+Do not write lines like these:
+- Wrong (one action split into several lines):
+  - [F6-F6] EVENT: man in a dark suit speaks outside a building
+  - [F7-F7] EVENT: man in a dark suit continues to speak outside a building
+  Right: - [F6-F8] EVENT: man in a dark suit speaks outside a building
+- Wrong (a list of details): - [F5-F5] EVENT: view cuts to a blue screen with "Subscribe" text, two video thumbnails, and icons for Instagram, Twitter, and Snapchat
+  Right: - [F5-F5] EVENT: view cuts to a blue screen with the text "Subscribe"
```

### 結果（3本、40秒・8枚、自動集計）

| 動画 | 全体の時間(秒) | 区間 | 上限到達 | 行数 | 行/区間 | 語数の平均 | 語数の最大 | 区間内の重複 | 1行に複数の文 | EVENT以外 | 時刻不一致 | 解析不可 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `66dwcQ1Y048_0` | 90 | 5 | 0 | 32 | 6.4 | 15.3 | 24 | 1 | 1 | 0 | 0 | 0 |
| `NexB4vj8_54_0` | 86 | 6 | 0 | 41 | 6.8 | 12.1 | 21 | 0 | 1 | 0 | 0 | 0 |
| `BtaVRhoLpC0_0` | 61 | 5 | 0 | 26 | 5.2 | 12.4 | 22 | 4 | 0 | 0 | 0 | 0 |

### なぜこの変更か

v6aの問題1（続く動作を別の行に分ける）と問題2（付ける情報が一塊を超える）への対策。続く動作は範囲で1回だけ書き「continues to」を書かない、付ける情報は1つだけ、と明示し、誤りと正しい例を1組ずつ示した。

### 目視の確認

- 付ける情報は一塊に収まった。v6aで看板3枚の文字を全部並べたVlog 区間2の行は `three men stand side by side, holding hands, with signs in front of them` になった。
- ニュース 区間2で、v6aは人物を「man」と書いたが、v6bは「woman」と書いた。画像（字幕にも "her"）で確認すると女性で、v6bが正しい。

### 問題点

1. **続く動作の分割がまだ残る**（ニュースの区間内の重複4）。ニュース 区間3:

```text
- [F1-F2] EVENT: man in a dark suit speaks outside a building
- [F3-F4] EVENT: man in a dark suit speaks outside a building
- [F5-F7] EVENT: man in a dark suit speaks outside a building
```
   区間4も「woman with glasses and a turtleneck speaks in front of bookshelves」を同じように3行に分けた。料理とニュースで「continues to」が2件残った（`person in black gloves continues to cut cake with serrated knife`、`Rina Gonoi continues to speak outside a building`）。
   - なお、Vlog 区間1の重複（同じ男性がF2とF6で話す）は、別の場面を挟んだ再登場なので正しい記録で、指標の「区間内の重複」はこれも数えている。

2. 人物の名前: 画面の字幕にある実名（Rina Gonoi）を使う行と、見た目で呼ぶ行が混ざった。v6には「実名は画面に書かれているときだけ」の規則がない。

### 次の版の目的

GEBDの「区切りで決める」をそのまま手順にする: まず変化のあるframe（区切り）を見つけ、区切りと区切りの間を1行で書く。同じ人が同じことをしていれば区切りはなく、行の範囲が延びるだけ。小さなカメラの動き・表情の変化・字幕の文字の変化は区切りにしない（ニュースで字幕が毎回変わるのが分割の原因と考えた）。「continues / still / again」を禁止する。

## 26. v6c（2026-10-21）

<details><summary>v6c の本文（全文）</summary>

```text
You are transcribing the events of a video into a time-stamped log. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will read it to answer questions about what happened.

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
3. If the next frame shows the same person doing the same thing, there is no boundary there: the line just gets longer. A small camera movement, a change of the person's facial expression, or new subtitle text is not a boundary.

How to write an event:
- One event per line. Write who does what: name people and animals by how they look, such as "man in a black T-shirt", and use the same name every time.
- You may add one short detail about something that takes part in the event, such as what is shown on a phone screen or what the new place looks like. Add only one detail: do not list several objects, texts, signs, or icons. Do not describe things that do not take part in the event.
- For a change of place, name the new place with at most two features, such as "white room with a blue sofa".
- Write events of people in the background too, but only when you can clearly see what they do. Write the main people first.
- Write only what you can see. Do not guess hidden actions, reasons, or feelings.
- An action that continues over several frames is one event: write it once, with the range from its first frame to its last frame. Never write "continues", "still", or "again" for an action that has not stopped.
- Never write the same event twice. When every change in the frames is written, stop.

Do not write lines like these:
- Wrong (one action split into several lines):
  - [F6-F6] EVENT: man in a dark suit speaks outside a building
  - [F7-F8] EVENT: man in a dark suit continues to speak outside a building
  Right: - [F6-F8] EVENT: man in a dark suit speaks outside a building
- Wrong (a list of details): - [F5-F5] EVENT: view cuts to a blue screen with "Subscribe" text, two video thumbnails, and icons for Instagram, Twitter, and Snapchat
  Right: - [F5-F5] EVENT: view cuts to a blue screen with the text "Subscribe"

Output format:
Each line is: - [Ffirst-Flast] EVENT: description
[F3-F5] means the event is seen from frame 3 to frame 5. Use [F4-F4] for a single frame.

Example (from a different video with 8 frames):
- [F1-F3] EVENT: woman in a red apron talks to the camera in a kitchen with white tiles
- [F4-F4] EVENT: woman in a red apron picks up a brown egg
- [F5-F5] EVENT: woman in a red apron cracks the egg into a glass bowl
- [F6-F6] EVENT: view cuts to a close-up of a frying pan on a gas stove
- [F7-F8] EVENT: beaten egg is poured into the frying pan
- [F8-F8] EVENT: boy in a yellow T-shirt comes into view from the right

Now write the events of this window.
```

</details>

### 差分（v6b → v6c）

```diff
--- v6b
+++ v6c
@@ -15 +15,5 @@
-If nothing changes between frames, write nothing for those frames.
+
+How to find the events:
+1. Compare each frame with the frame before it, and note the frames where something changes. These are the boundaries.
+2. Between two boundaries nothing changes, so write one line that covers all those frames, from the first to the last.
+3. If the next frame shows the same person doing the same thing, there is no boundary there: the line just gets longer. A small camera movement, a change of the person's facial expression, or new subtitle text is not a boundary.
@@ -23 +27 @@
-- An action that continues over several frames is one event: write it once, with the range from its first frame to its last frame. Do not write a new line for an action that is still going on, and do not write "continues to".
+- An action that continues over several frames is one event: write it once, with the range from its first frame to its last frame. Never write "continues", "still", or "again" for an action that has not stopped.
@@ -29 +33 @@
-  - [F7-F7] EVENT: man in a dark suit continues to speak outside a building
+  - [F7-F8] EVENT: man in a dark suit continues to speak outside a building
```

### 結果（3本、40秒・8枚、自動集計）

| 動画 | 全体の時間(秒) | 区間 | 上限到達 | 行数 | 行/区間 | 語数の平均 | 語数の最大 | 区間内の重複 | 1行に複数の文 | EVENT以外 | 時刻不一致 | 解析不可 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `66dwcQ1Y048_0` | 106 | 5 | 0 | 31 | 6.2 | 17.6 | 32 | 1 | 0 | 0 | 0 | 0 |
| `NexB4vj8_54_0` | 103 | 6 | 0 | 39 | 6.5 | 13.1 | 23 | 0 | 1 | 0 | 0 | 0 |
| `BtaVRhoLpC0_0` | 60 | 5 | 0 | 21 | 4.2 | 11.5 | 22 | 3 | 0 | 0 | 0 | 0 |

### なぜこの変更か

v6bでもニュースで同じ「建物の外で話す」が [F1-F2] [F3-F4] [F5-F7] に分かれたので、GEBDの「区切りで決める」をそのまま手順にした（前のframeと比べて変化のあるframeを見つけ、区切りの間を1行で書く。小さなカメラの動き・表情・字幕の文字の変化は区切りにしない）。

### 目視の確認

- 料理 区間2は、v6bと同じく画像と対応（ヨーグルトを注ぐ → 白い粉の器へカット → 入れる → 文字の表示 → ミキサー → 持ち上げる）。
- Vlog 区間4は、v6aと同じく8枚と対応。付ける情報も短くなった（`person holds a smartphone displaying a social media post with colorful sticky notes`）。
- ニュース 区間3では、また3行に分かれた。**画像で確認すると、F1〜F2（中くらいの大きさ）→ F3〜F4（別の場所から横向き）→ F5〜F7（顔のアップ）と、実際にカットが2回あった。分割は正しい区切りだった。**

```text
- [F1-F2] EVENT: man in a dark suit speaks outside a building
- [F3-F4] EVENT: man in a dark suit speaks outside a building
- [F5-F7] EVENT: man in a dark suit speaks outside a building
- [F8-F8] EVENT: view cuts to a woman in a beige turtleneck and glasses in front of bookshelves
```

### 問題点

1. **区切ったのに、何が切り替わったかが書かれず、同じ文が並ぶ。** 読む側には重複にしか見えず、カットの情報（アップになった、別の場所から撮った）が失われる。v6a・v6bで「続く動作の分割」と見ていたもののうち、ニュースの分は、この「同じ文の区切り」だった可能性が高い。
2. **性別の判断がぶれる。** この人物は女性（字幕も "her"）だが、v6cは「man」、v6bは「woman」と書いた。
3. 小さな問題: 料理で `person in black gloves continues to cut the cake with a serrated knife` が1件残った。

### 次の版の目的

- 各行は、その行の最初のframeで何が変わったかを書く。同じ人が同じことを続けたまま見え方が変わったときは「view cuts to」で始め、新しい見え方を書く（前の行と同じ文にしない）。誤りと正しい例を1組見せる。
- 性別がはっきりしないときは「person」と書く。

## 27. v6d（2026-10-21）

<details><summary>v6d の本文（全文）</summary>

```text
You are transcribing the events of a video into a time-stamped log. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will read it to answer questions about what happened.

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
3. If the next frame shows the same person doing the same thing from the same view, there is no boundary there: the line just gets longer. A small camera movement, a change of the person's facial expression, or new subtitle text is not a boundary.
4. Every line must say what changed at its first frame. If the view changes (for example, a cut to a close-up or to another place) while the same person keeps doing the same thing, start the line with "view cuts to" and say what the new view shows, so that the line is different from the line before it.

How to write an event:
- One event per line. Write who does what: name people and animals by how they look, such as "man in a black T-shirt", and use the same name every time. If you are not sure whether a person is a man or a woman, write "person".
- You may add one short detail about something that takes part in the event, such as what is shown on a phone screen or what the new place looks like. Add only one detail: do not list several objects, texts, signs, or icons. Do not describe things that do not take part in the event.
- For a change of place, name the new place with at most two features, such as "white room with a blue sofa".
- Write events of people in the background too, but only when you can clearly see what they do. Write the main people first.
- Write only what you can see. Do not guess hidden actions, reasons, or feelings.
- An action that continues over several frames is one event: write it once, with the range from its first frame to its last frame. Never write "continues", "still", or "again" for an action that has not stopped.
- Never write the same event twice. When every change in the frames is written, stop.

Do not write lines like these:
- Wrong (one action split into several lines):
  - [F6-F6] EVENT: man in a dark suit speaks outside a building
  - [F7-F8] EVENT: man in a dark suit continues to speak outside a building
  Right: - [F6-F8] EVENT: man in a dark suit speaks outside a building
- Wrong (lines that look the same after a cut):
  - [F1-F2] EVENT: woman in a dark suit speaks outside a building
  - [F3-F4] EVENT: woman in a dark suit speaks outside a building
  Right:
  - [F1-F2] EVENT: woman in a dark suit speaks outside a building
  - [F3-F4] EVENT: view cuts to a side view of the woman in a dark suit, speaking in front of a gray wall
- Wrong (a list of details): - [F5-F5] EVENT: view cuts to a blue screen with "Subscribe" text, two video thumbnails, and icons for Instagram, Twitter, and Snapchat
  Right: - [F5-F5] EVENT: view cuts to a blue screen with the text "Subscribe"

Output format:
Each line is: - [Ffirst-Flast] EVENT: description
[F3-F5] means the event is seen from frame 3 to frame 5. Use [F4-F4] for a single frame.

Example (from a different video with 8 frames):
- [F1-F3] EVENT: woman in a red apron talks to the camera in a kitchen with white tiles
- [F4-F4] EVENT: woman in a red apron picks up a brown egg
- [F5-F5] EVENT: woman in a red apron cracks the egg into a glass bowl
- [F6-F6] EVENT: view cuts to a close-up of a frying pan on a gas stove
- [F7-F8] EVENT: beaten egg is poured into the frying pan
- [F8-F8] EVENT: boy in a yellow T-shirt comes into view from the right

Now write the events of this window.
```

</details>

### 差分（v6c → v6d）

```diff
--- v6c
+++ v6d
@@ -19 +19,2 @@
-3. If the next frame shows the same person doing the same thing, there is no boundary there: the line just gets longer. A small camera movement, a change of the person's facial expression, or new subtitle text is not a boundary.
+3. If the next frame shows the same person doing the same thing from the same view, there is no boundary there: the line just gets longer. A small camera movement, a change of the person's facial expression, or new subtitle text is not a boundary.
+4. Every line must say what changed at its first frame. If the view changes (for example, a cut to a close-up or to another place) while the same person keeps doing the same thing, start the line with "view cuts to" and say what the new view shows, so that the line is different from the line before it.
@@ -22 +23 @@
-- One event per line. Write who does what: name people and animals by how they look, such as "man in a black T-shirt", and use the same name every time.
+- One event per line. Write who does what: name people and animals by how they look, such as "man in a black T-shirt", and use the same name every time. If you are not sure whether a person is a man or a woman, write "person".
@@ -34,0 +36,6 @@
+- Wrong (lines that look the same after a cut):
+  - [F1-F2] EVENT: woman in a dark suit speaks outside a building
+  - [F3-F4] EVENT: woman in a dark suit speaks outside a building
+  Right:
+  - [F1-F2] EVENT: woman in a dark suit speaks outside a building
+  - [F3-F4] EVENT: view cuts to a side view of the woman in a dark suit, speaking in front of a gray wall
```

### 結果（3本、40秒・8枚、自動集計）

| 動画 | 全体の時間(秒) | 区間 | 上限到達 | 行数 | 行/区間 | 語数の平均 | 語数の最大 | 区間内の重複 | 1行に複数の文 | EVENT以外 | 時刻不一致 | 解析不可 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `66dwcQ1Y048_0` | 95 | 5 | 0 | 31 | 6.2 | 18.4 | 32 | 1 | 0 | 0 | 0 | 0 |
| `NexB4vj8_54_0` | 82 | 6 | 0 | 36 | 6.0 | 13.9 | 24 | 0 | 1 | 0 | 0 | 0 |
| `BtaVRhoLpC0_0` | 49 | 5 | 0 | 20 | 4.0 | 11.8 | 20 | 3 | 0 | 0 | 0 | 0 |

### なぜこの変更か

v6cで、ニュースの「話す」が3行に分かれたのは実際のカットによる正しい区切りだったが、3行が同じ文で、何が切り替わったかが残らなかった。そこで「各行は最初のframeで何が変わったかを書く。同じ人が同じことを続けたまま見え方が変わったら view cuts to で始める」とし、誤りと正しい例を1組足した。性別がはっきりしないときは person と書かせた。

### 目視の確認

- ニュース 区間2では、場所が変わるカットに「view cuts to」が付いた（`[F4-F4] view cuts to a building with a sign that reads "裁判所"`、`[F5-F6] view cuts to woman in a dark suit speaking outside a building`）。
- 料理 区間3・Vlog 区間1は、これまでと同じく画像と対応。

### 問題点

1. **規則と例を足しても、ニュース 区間3は同じ文が3行のまま**（カットはアップ・別の場所からの横向き・顔のアップ）:

```text
- [F1-F2] EVENT: man in a dark suit speaks outside a building
- [F3-F4] EVENT: man in a dark suit speaks outside a building
- [F5-F7] EVENT: man in a dark suit speaks outside a building
```
2. **同じ女性を、この区間でもまた「man」と書いた**（区間2では woman）。区間ごとに独立して書くので、性別の判断が区間によってぶれる。
3. 看板の長い文章をそのまま写した行（`… holding a sign that reads "HERE'S TO STRONG WOMEN, MAY WE KNOW THEM, MAY WE BE THEM, MAY WE RAISE THEM"`）。「continues cutting」が1件。

### 考え直したこと

林のイベントの定義は「風景が変わったらイベント」。**同じ人が同じ場所で同じことを続けていて、カメラの寄り・引き・角度だけが変わるカット**は風景の変化とは言いにくく、区切らなくてよい。区切るのは場所が変わったカットだけにする。

### 次の版の目的

- 同じ人が同じことを同じ場所で続けているなら、カメラが寄る・引く・角度が変わるだけでは区切らない（1行にまとめる）。場所が変わったときだけ「view cuts to 新しい場所」。誤りと正しい例をこれに合わせて差し替える。
- 長い文字は数語だけ写す。

## 28. v6e（2026-10-21）

<details><summary>v6e の本文（全文）</summary>

```text
You are transcribing the events of a video into a time-stamped log. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will read it to answer questions about what happened.

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
- One event per line. Write who does what: name people and animals by how they look, such as "man in a black T-shirt", and use the same name every time. If you are not sure whether a person is a man or a woman, write "person".
- You may add one short detail about something that takes part in the event, such as what is shown on a phone screen or what the new place looks like. Add only one short detail: copy at most a few words of a long text, and do not list several objects, texts, signs, or icons. Do not describe things that do not take part in the event.
- For a change of place, name the new place with at most two features, such as "white room with a blue sofa".
- Write events of people in the background too, but only when you can clearly see what they do. Write the main people first.
- Write only what you can see. Do not guess hidden actions, reasons, or feelings.
- An action that continues over several frames is one event: write it once, with the range from its first frame to its last frame. Never write "continues", "still", or "again" for an action that has not stopped.
- Never write the same event twice. When every change in the frames is written, stop.

Do not write lines like these:
- Wrong (one action split into several lines):
  - [F6-F6] EVENT: man in a dark suit speaks outside a building
  - [F7-F8] EVENT: man in a dark suit continues to speak outside a building
  Right: - [F6-F8] EVENT: man in a dark suit speaks outside a building
- Wrong (the same line repeated; the camera only moved closer):
  - [F1-F2] EVENT: woman in a dark suit speaks outside a building
  - [F3-F4] EVENT: woman in a dark suit speaks outside a building
  Right: - [F1-F4] EVENT: woman in a dark suit speaks outside a building
- Wrong (a list of details): - [F5-F5] EVENT: view cuts to a blue screen with "Subscribe" text, two video thumbnails, and icons for Instagram, Twitter, and Snapchat
  Right: - [F5-F5] EVENT: view cuts to a blue screen with the text "Subscribe"

Output format:
Each line is: - [Ffirst-Flast] EVENT: description
[F3-F5] means the event is seen from frame 3 to frame 5. Use [F4-F4] for a single frame.

Example (from a different video with 8 frames):
- [F1-F3] EVENT: woman in a red apron talks to the camera in a kitchen with white tiles
- [F4-F4] EVENT: woman in a red apron picks up a brown egg
- [F5-F5] EVENT: woman in a red apron cracks the egg into a glass bowl
- [F6-F6] EVENT: view cuts to a close-up of a frying pan on a gas stove
- [F7-F8] EVENT: beaten egg is poured into the frying pan
- [F8-F8] EVENT: boy in a yellow T-shirt comes into view from the right

Now write the events of this window.
```

</details>

### 差分（v6d → v6e）

```diff
--- v6d
+++ v6e
@@ -19,2 +19,2 @@
-3. If the next frame shows the same person doing the same thing from the same view, there is no boundary there: the line just gets longer. A small camera movement, a change of the person's facial expression, or new subtitle text is not a boundary.
-4. Every line must say what changed at its first frame. If the view changes (for example, a cut to a close-up or to another place) while the same person keeps doing the same thing, start the line with "view cuts to" and say what the new view shows, so that the line is different from the line before it.
+3. If the next frame shows the same person doing the same thing in the same place, there is no boundary there: the line just gets longer. This is true even when the camera only moves closer, farther, or to another angle. A change of the person's facial expression or new subtitle text is not a boundary either.
+4. Every line must say what changed at its first frame, so that it is different from the line before it. When the place changes, start the line with "view cuts to" and name the new place.
@@ -24 +24 @@
-- You may add one short detail about something that takes part in the event, such as what is shown on a phone screen or what the new place looks like. Add only one detail: do not list several objects, texts, signs, or icons. Do not describe things that do not take part in the event.
+- You may add one short detail about something that takes part in the event, such as what is shown on a phone screen or what the new place looks like. Add only one short detail: copy at most a few words of a long text, and do not list several objects, texts, signs, or icons. Do not describe things that do not take part in the event.
@@ -36 +36 @@
-- Wrong (lines that look the same after a cut):
+- Wrong (the same line repeated; the camera only moved closer):
@@ -39,3 +39 @@
-  Right:
-  - [F1-F2] EVENT: woman in a dark suit speaks outside a building
-  - [F3-F4] EVENT: view cuts to a side view of the woman in a dark suit, speaking in front of a gray wall
+  Right: - [F1-F4] EVENT: woman in a dark suit speaks outside a building
```

### 結果（3本、40秒・8枚、自動集計）

| 動画 | 全体の時間(秒) | 区間 | 上限到達 | 行数 | 行/区間 | 語数の平均 | 語数の最大 | 区間内の重複 | 1行に複数の文 | EVENT以外 | 時刻不一致 | 解析不可 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `66dwcQ1Y048_0` | 91 | 5 | 0 | 31 | 6.2 | 16.2 | 24 | 1 | 0 | 0 | 0 | 0 |
| `NexB4vj8_54_0` | 83 | 6 | 0 | 37 | 6.2 | 12.3 | 19 | 0 | 1 | 0 | 0 | 0 |
| `BtaVRhoLpC0_0` | 48 | 5 | 0 | 19 | 3.8 | 10.6 | 14 | 2 | 0 | 0 | 0 | 0 |

### なぜこの変更か

v6dで規則と例を足しても、ニュースで同じ人が話し続けたまま寄り・引き・角度だけが変わるカットで、同じ文が3行並んだ。林のイベントの定義（風景が変わったらイベント）に照らし、同じ人・同じ場所・同じ動作でカメラだけが変わるカットは区切らないことにした。場所が変わったときだけ「view cuts to」。長い文字は数語だけ写す。

### 目視の確認（全区間を読んだ）

- ニュース 区間4は、v6dまで3行に分かれた「本棚の前で話す女性」が1行になった: `[F1-F7] EVENT: woman with glasses and a turtleneck speaks in front of bookshelves`。
- 料理は全工程を重複なく追えた（卵を割る → 黄身を取り出す → 砂糖を入れる → 混ぜる → ヨーグルト → ベーキングパウダー → 泡立てる → 混ぜ合わせる → 型に流す → オーブン → 型から出す → 粉砂糖 → 切る → 皿に載せる → フォークで刺す）。
- 1行の語数の最大は24語以下（v6dは32語）。看板の長い文章は `… signs, including one that reads "HERE'S TO STRONG WOMEN"` と数語になった。

### 問題点

1. ニュース 区間3（寄り・角度のカットが2回ある区間）だけは、同じ文が3行のまま。性別も man のまま:

```text
- [F1-F2] EVENT: man in a dark suit speaks outside a building
- [F3-F4] EVENT: man in a dark suit speaks outside a building
- [F5-F7] EVENT: man in a dark suit speaks outside a building
```
2. 変化ではなく状態だけを書いた行: `[F4-F4] EVENT: three egg yolks are in glass bowl`、`[F6-F6] EVENT: person in black gloves holds bowl with sugar and egg yolks`、`[F5-F5] EVENT: two glass bowls are shown side by side; …`。
3. 「Subscribe」の画面でアイコンを並べる行が1つ残った（`… two video thumbnails, and icons for Instagram, Twitter, and Snapchat`）。料理で `continues cutting` が1件（ただし切る動作の次の回なら、定義上は新しいイベントでよい）。

### 次の版の目的

- 書く前に直前の行と比べ、同じことを書こうとしていたら新しい行にせず、直前の行の範囲を延ばす（自己チェックの手順）。
- 変化を含まず、見た目だけを書く行を書かない（例を2つ示す）。
- これでニュース 区間3の同じ文が直らなければ、プロンプトだけでは難しいと判断し、林に相談する。

## 29. v6f（2026-10-21）

<details><summary>v6f の本文（全文）</summary>

```text
You are transcribing the events of a video into a time-stamped log. This log is the only record of the video that will be kept. Later, someone who cannot watch the video will read it to answer questions about what happened.

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
5. Before writing a line, check the line just before it. If the new line would say the same thing, do not write it: the line before it already covers those frames, so extend its range instead.

How to write an event:
- One event per line. Write who does what: name people and animals by how they look, such as "man in a black T-shirt", and use the same name every time. If you are not sure whether a person is a man or a woman, write "person".
- You may add one short detail about something that takes part in the event, such as what is shown on a phone screen or what the new place looks like. Add only one short detail: copy at most a few words of a long text, and do not list several objects, texts, signs, or icons. Do not describe things that do not take part in the event.
- For a change of place, name the new place with at most two features, such as "white room with a blue sofa".
- Write events of people in the background too, but only when you can clearly see what they do. Write the main people first.
- Write only what you can see. Do not guess hidden actions, reasons, or feelings.
- Do not write a line that only describes how things look without any change, such as "three egg yolks are in the bowl" or "person holds the bowl".
- An action that continues over several frames is one event: write it once, with the range from its first frame to its last frame. Never write "continues", "still", or "again" for an action that has not stopped.
- Never write the same event twice. When every change in the frames is written, stop.

Do not write lines like these:
- Wrong (one action split into several lines):
  - [F6-F6] EVENT: man in a dark suit speaks outside a building
  - [F7-F8] EVENT: man in a dark suit continues to speak outside a building
  Right: - [F6-F8] EVENT: man in a dark suit speaks outside a building
- Wrong (the same line repeated; the camera only moved closer):
  - [F1-F2] EVENT: woman in a dark suit speaks outside a building
  - [F3-F4] EVENT: woman in a dark suit speaks outside a building
  Right: - [F1-F4] EVENT: woman in a dark suit speaks outside a building
- Wrong (a list of details): - [F5-F5] EVENT: view cuts to a blue screen with "Subscribe" text, two video thumbnails, and icons for Instagram, Twitter, and Snapchat
  Right: - [F5-F5] EVENT: view cuts to a blue screen with the text "Subscribe"

Output format:
Each line is: - [Ffirst-Flast] EVENT: description
[F3-F5] means the event is seen from frame 3 to frame 5. Use [F4-F4] for a single frame.

Example (from a different video with 8 frames):
- [F1-F3] EVENT: woman in a red apron talks to the camera in a kitchen with white tiles
- [F4-F4] EVENT: woman in a red apron picks up a brown egg
- [F5-F5] EVENT: woman in a red apron cracks the egg into a glass bowl
- [F6-F6] EVENT: view cuts to a close-up of a frying pan on a gas stove
- [F7-F8] EVENT: beaten egg is poured into the frying pan
- [F8-F8] EVENT: boy in a yellow T-shirt comes into view from the right

Now write the events of this window.
```

</details>

### 差分（v6e → v6f）

```diff
--- v6e
+++ v6f
@@ -20,0 +21 @@
+5. Before writing a line, check the line just before it. If the new line would say the same thing, do not write it: the line before it already covers those frames, so extend its range instead.
@@ -27,0 +29 @@
+- Do not write a line that only describes how things look without any change, such as "three egg yolks are in the bowl" or "person holds the bowl".
```

### 結果（3本、40秒・8枚、自動集計）

| 動画 | 全体の時間(秒) | 区間 | 上限到達 | 行数 | 行/区間 | 語数の平均 | 語数の最大 | 区間内の重複 | 1行に複数の文 | EVENT以外 | 時刻不一致 | 解析不可 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `66dwcQ1Y048_0` | 90 | 5 | 0 | 31 | 6.2 | 16.1 | 24 | 1 | 0 | 0 | 0 | 0 |
| `NexB4vj8_54_0` | 85 | 6 | 0 | 38 | 6.3 | 12.9 | 20 | 0 | 1 | 0 | 0 | 0 |
| `BtaVRhoLpC0_0` | 47 | 5 | 0 | 19 | 3.8 | 10.4 | 14 | 2 | 0 | 0 | 0 | 0 |

### なぜこの変更か

v6eの残り（ニュースの1区間で寄り・角度のカットを挟んだ同じ文3行、状態だけの行）への対策として、書く前に直前の行と比べる自己チェックの手順と、「変化を含まず見た目だけを書く行を書かない」（例2つ）を足した。

### 結果と問題点

**v6eとほぼ同じ出力になり、足した2つの規則はどちらも効かなかった。**

```text
（ニュース 区間3、v6eと同じ）
- [F1-F2] EVENT: man in a dark suit speaks outside a building
- [F3-F4] EVENT: man in a dark suit speaks outside a building
- [F5-F7] EVENT: man in a dark suit speaks outside a building
（料理 区間1、禁止の例に挙げたものと同じ形の行が残る）
- [F4-F4] EVENT: three egg yolks are in a glass bowl
- [F6-F6] EVENT: person in black gloves holds bowl with sugar and egg yolks
```

- 「Subscribe」の画面でアイコンを並べる行も残った。性別のぶれ（同じ女性を man と書く区間がある）も残った（ニュース 区間1では `Rina Gonoi, a man in a dark suit`）。

### v6系の到達点（v6e・v6f）

| | v5（20秒・8枚） | v6e（40秒・8枚） |
| --- | --: | --: |
| 全体の時間 Vlog / 料理 / ニュース（秒） | 480 / 248 / 263 | 91 / 83 / 48 |
| 行数 | 304 / 144 / 148 | 31 / 37 / 19 |
| 書く種類 | 6種類（場面の目録） | EVENTだけ |
| 上限到達・時刻不一致・解析不可・EVENT以外 | 0 | 0 |

- 記録はEVENTだけになり、目視で確かめた区間では画像との対応がほぼ正確。料理は全工程を重複なく追えた。
- 実行時間は林の目標（半分）を超えて、v5の約1/3〜1/5になった。

### 残る問題（プロンプトでは直らなかった）

1. 同じ人が同じ場所で同じことを続け、カメラの寄り・角度だけが変わるカットで、同じ文が並ぶ（ニュースの1区間。v6c〜v6fの4案で直らなかった）。
2. 区間ごとに独立して書くため、同じ人の性別の判断が区間によってぶれる。
3. 状態だけの行・付ける情報の列挙が少し残る。

### 次の版の目的

プロンプトだけでの改善は頭打ち（v6c〜v6fで同じ出力が続いた）。林に相談する（2026-10-21）。

## 30. 区間を20秒・8枚に戻す（v6e のまま、2026-10-21）

### きっかけ（林）

- 「処理時間が減ったので20秒8フレームでやってください」。v6eはv5より速くなった（40秒・8枚で 91 / 83 / 48秒）。
- この記録を、集約（段A・段B）の入力にする。集約の作業ログは [段A・段Bの結果](2026-10-21-event-aggregation-stage-a-b.md) にある。
- 実行と結果は、新リポジトリの `experiments/2026-10-21-event-aggregation/` にある。結果 `trials/v6e-20s.json` は git で追跡しない。

### 結果（3本、20秒・8枚、自動集計）

| 動画 | 全体の時間(秒) | 区間 | 上限到達 | 行数 | 語数の平均 | 区間内の重複 | 時刻不一致 | 解析不可 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `66dwcQ1Y048_0` | 177 | 10 | 0 | 59 | 15.0 | 1 | 0 | 0 |
| `NexB4vj8_54_0` | 166 | 12 | 0 | 65 | 13.0 | 1 | 0 | 0 |
| `BtaVRhoLpC0_0` | 76 | 10 | 0 | 27 | 11.8 | 3 | 0 | 0 |

- 40秒と比べると、時間も行数も約2倍。v5（480 / 248 / 263秒）よりはずっと速い。

### 問題点（集約の段Bで分かったこと）

- 人の呼び方が薄い（`man in a dark suit`、`man in a black T-shirt`）。区間をまたいで同じ人にIDを振ると、別人を同じIDにしてしまう。
  - Vlogでは、案内役のIDに別人の「黒いTシャツの男性」が3行混ざった。
  - プロンプトの例の呼び方が、どれも服1つだけ（`man in a dark suit`、`woman in a red apron`）。ニュースの出力が例とまったく同じ `man in a dark suit` になっていたので、例を真似している可能性が高い（推測）。

### 次の版の目的

- 人の呼び方を詳しくする。ただし、付け足すのは主語の呼び方だけにして、物の情報は今のまま（v5の暴走を繰り返さない）。

## 31. v6g（2026-10-21）

### きっかけ（林）

- 「EVENT出力エージェントにもうちょい頑張ってもらって、人物や物の詳しい情報を加えてあげてもいい」。
- 終了条件（林）: 暴走がなく、かなりうまく動作している（IDの入れ替えなどがない）状態になるまで検討を重ねる。

### 差分（v6e → v6g）

```diff
--- v6e
+++ v6g
-- One event per line. Write who does what: name people and animals by how they look, such as "man in a black T-shirt", and use the same name every time. If you are not sure whether a person is a man or a woman, write "person".
+- One event per line. Write who does what.
+- Name each person by three features that stay the same during the whole video, so that the same person can be found again in other parts of the video:
+  1. the upper clothing, with its color and type (for example, "black T-shirt", "red plaid shirt", "dark gray suit");
+  2. the hair or face (for example, "short brown hair", "long blond hair", "bald", "glasses", "beard");
+  3. one more thing that is easy to recognize (for example, text written on the clothing, a hat, a necklace, black gloves, a backpack).
+  Example: "man in a black T-shirt with "SEEK" text, short brown hair". Write a feature only when you can see it; if you cannot see a feature, write the features you can see. Use the same three features every time the person appears.
+- Write "man" or "woman" only when it is clear. If you are not sure, write "person". Never call the same person "man" in one line and "woman" in another.
+- Name animals in the same way (color, size, one distinctive feature). Things that are not people or animals do not need these features.
```

あわせて、誤りの例・正しい例・出力例の呼び方を、すべて3つの特徴の形に直した（例: `man in a navy suit with gray hair and glasses`、`woman in a red apron with long black hair tied back and silver earrings`）。誤りの例を1組足した: 「1つの特徴だけの呼び方（多くの人が同じ）」 `man in a white shirt` → `man in a white shirt with short black hair and a blue backpack`。

### なぜこの変更か

- 段Bで、珍しい手がかり（服の文字 `"SEEK DISCOMFORT"`、黒い手袋）がある人は正しく1つのIDになった。服1つだけの呼び方では、別人を同じIDにした。
- 先行研究も、区間をまたいだ人の照合を、モデルの呼び方だけに任せていない。MemLife は服・髪・眼鏡を補助に書かせ、TaskMem は顔のIDを与える（[出力形式の調査](../../../../secretary/notes/brainstorm/2026-10-21-event-transcription-prior-work-formats.md)）。

### 結果（3本、20秒・8枚、自動集計）

| 動画 | 全体の時間(秒) | 上限到達 | 行数 | 語数の平均 | 語数の最大 | 区間内の重複 | 時刻不一致 | 解析不可 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `66dwcQ1Y048_0` | 189（v6e 177） | 0 | 59 | 22.7（15.0） | 40 | 1 | 0 | 0 |
| `NexB4vj8_54_0` | 175（166） | 0 | 64 | 14.2（13.0） | 29 | 1 | 0 | 0 |
| `BtaVRhoLpC0_0` | 102（76） | 0 | 27 | 18.6（11.8） | 40 | 2 | 0 | 0 |

IDの評価（目で作った正解と比べた。段Bの方法ごと。方法の説明は [段A・段Bの結果](2026-10-21-event-aggregation-stage-a-b.md) 第7節）:

| 段Bの方法 | 入力 | Vlog 入れ替え / 誤ったIDの行 / 分かれ | 料理 | ニュース |
|---|---|---|---|---|
| v1（語の集合） | v6e | 3 / 4 / 0 | 0 / 0 / 0 | 0 / 0 / 2 |
| v1（語の集合） | v6g | 2 / 10 / 2 | 0 / 0 / 0 | 0 / 0 / 2 |
| v3（欄ごと、色の系統） | v6e | 0 / 0 / 2 | 0 / 0 / 0 | 0 / 0 / 3 |
| v3（欄ごと、色の系統） | v6g | 1 / 2 / 3 | 0 / 0 / 0 | 0 / 0 / 1 |

### 目視の確認

- 暴走なし（上限到達0、ループなし）。語数は平均で約1.5倍、時間は 7%・5%・34% 増えた。
- 呼び方はほぼ3つの特徴になった（例: `man in a black T-shirt with "SEEK DISCOMFORT" text and short blond hair`）。
- 性別のぶれ: ニュースで、Gonoiを `person in a dark gray suit with short brown hair` と書く行が出た（personの規則は効いた）。ただし `man in a navy suit` と書く区間も残った。
- 物の情報は増えなかった（付け足すのは主語だけ、という意図どおり）。

### 問題点

1. **似た3人を区別できない。** ベッドの男性・台所の男性・字幕「money」の男性は別人（拡大した画像で確認）。3人とも `man in a black T-shirt with a beard and dark hair` とほぼ同じ文で書かれた。画像では髪型（波打つ・後ろに流す・巻き毛）とひげの濃さが違う。
2. **例のコンマ**: 例を `…"SEEK" text, short brown hair` とコンマで区切ったため、モデルもコンマで書いた。段Bの主語の取り出しがコンマで止まり、髪の情報が落ちた（段B v5で、コンマの後に見た目の語が続く場合は止めないように直した）。
3. 着替えた人（滑走路でタキシードを着た案内役、昔の映像でフリースを着たGonoi）は、服で照合する限り同じIDにできない。受け入れる限界として扱う。

### 次の版の目的

- 髪型とひげの形を書かせる。似た人どうしは違う特徴を書かせる。
- 例をコンマのない形（`with … and …`）にする。

## 32. v6h（2026-10-21）

### 差分（v6g → v6h）

```diff
--- v6g
+++ v6h
-  2. the hair or face (for example, "short brown hair", "long blond hair", "bald", "glasses", "beard");
+  2. the hair: its color, length, and style (for example, "short wavy brown hair", "long straight blond hair", "slicked-back black hair", "curly black hair", "bald"), and the face when it has glasses or facial hair (say "stubble", "short beard", or "full beard");
-  Example: "man in a black T-shirt with "SEEK" text, short brown hair". Write a feature only when …
+  Example: "man in a black T-shirt with "SEEK" text and short wavy brown hair". Write the features right after "man", "woman", or "person", joined by "with" and "and", before the action. Write a feature only when …
+  Two different people can wear similar clothes. When two people look alike, write the feature that makes them different (for example, "stubble" for one and "full beard" for the other).
-  Right: - [F2-F2] EVENT: man in a white shirt with short black hair and a blue backpack runs across a street
+  Right: - [F2-F2] EVENT: man in a white shirt with short curly black hair and a blue backpack runs across a street
```

### なぜこの変更か

- v6gの似た3人（ベッド・台所・字幕「money」の男性）は、画像では髪型（波打つ・後ろに流す・巻き毛）と、ひげの濃さが違う。それを書かせれば、段Bで区別できると考えた。
- 例のコンマをやめた（第31節の問題点2）。

### 結果（3本、20秒・8枚、自動集計）

| 動画 | 全体の時間(秒) | 上限到達 | 行数 | 語数の平均 | 語数の最大 | 区間内の重複 | 時刻不一致 | 解析不可 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `66dwcQ1Y048_0` | 189（v6g 189） | 0 | 59 | 23.3（22.7） | 38 | 2 | 0 | 0 |
| `NexB4vj8_54_0` | 159（175） | 0 | 65 | 15.3（14.2） | 32 | 0 | 0 | 0 |
| `BtaVRhoLpC0_0` | 96（102） | 0 | 27 | 21.7（18.6） | 51 | 2 | 0 | 0 |

### 目視の確認と問題点

- 暴走なし。
- **髪型の指示はほとんど守られなかった。** ほとんどの人が同じ型の `short dark hair` で書かれた。似た3人は3人とも `man in a black T-shirt with short dark hair and a beard` になり、区別できなかった。屋上の男性だけが `stubble` と書かれた。
- 一部では書かれた（ニュースの `short wavy brown hair`、`short bob haircut`、Vlogの `long straight black hair`）。
- 段B v5（そのときの方法）では、Vlogの入れ替えが 1 → 4 に増えた。同じ型の呼び方が増え、別人どうしが一致しやすくなった。
- 段Bを変えたあと（段B v8、集約の作業ログ 第7.7〜7.11節）は、v6g・v6hともに入れ替え0で、差はほとんどない。

### 判断（AIの考え）

- 4Bのモデルに、プロンプトで「似た人を書き分けさせる」のは難しい。各区間を独立に書くので、別の区間に似た人がいることをモデルは知らない。
- IDの入れ替えは、段Bの規則（ありふれた手がかりだけでは、別の人やカットをまたいでつながない）で防ぐ方が確実だった。
- **記録の既定の候補は v6g とする。** v6hは語数が多いぶん得がない。v6gを、前に暴走した2本でも確かめる（第33節）。

## 33. v6g を、前に暴走した2本で確かめる（2026-10-21）

v5で暴走した2本（第18節）に v6g を当てた: `gtX_oRpLClY`（日常Vlog、スマホの設定画面）と `22iOyzE8Ec0`（理系解説）。

| 動画 | 全体の時間(秒) | 区間 | 上限到達 | 行数 | 語数の平均 | 語数の最大 | 区間内の重複 | 解析不可 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `gtX_oRpLClY_0` | 201（v5 569） | 12 | 0 | 80（v5 495） | 16.0 | 25 | 2 | 0 |
| `22iOyzE8Ec0_0` | 158（v5 278） | 12 | 0 | 46（v5 155） | 23.4 | 36 | 1 | 0 |

- **暴走なし。** v5で色の名前を297行書き続けた設定画面も、v6gでは操作の1行（`selects "Pastel Orange" as the background color on the smartphone screen`）になった。
- 理系解説では、画面の文字を長めに写す行が少し残る（`text overlay: "WHEN THAT SALTY, IONIC WATER FLOWS…"`）。ループではない。
- **新しい問題: 区間ごとに、同じ人の服の推測が変わる。** スマホの動画は最初から最後まで同じ1人の手（黄色と白のしま模様の袖）だが、区間ごとに次のように書いた。
  - `yellow and white striped sleeve`
  - `white and yellow sleeveless top with a gold bracelet`
  - `yellow long-sleeved shirt with a wristband`
  - `white sweater with yellow trim`
  - 袖しか写らないので、服の種類を区間ごとに推測している。区間は前の区間を見ずに独立して書くので、呼び方がそろわない。
  - 段Bでは9個のIDに分かれた（入れ替えはない。集約の作業ログ 第7.12節）。

### 判断（AIの考え）

- 記録の既定は v6g でよい（暴走なし、入れ替えは段Bで防げる）。
- 呼び方を区間の間でそろえるには、プロンプトの規則だけでは足りない。各区間が独立だからである。前の区間で出た人の一覧（IDと呼び方）を渡す、という設計の変更が必要になる。
  - 先行研究では、前の区間の文章を渡すと悪くなるという報告がある（Lando、MemLife）。一方で、人物のIDや一覧を外から与える方式もある（TaskMem、MemLife、Imprint。[出力形式の調査](../../../../secretary/notes/brainstorm/2026-10-21-event-transcription-prior-work-formats.md)）。
  - 進めるかどうかは林と相談する。
