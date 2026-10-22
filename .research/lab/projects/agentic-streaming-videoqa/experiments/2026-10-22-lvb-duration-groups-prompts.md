---
date: 2026-10-22
project: agentic-streaming-videoqa
topic: 動画長グループ別の試行で使うプロンプト（記録 v6g-lvb、回答 a1）の設計ログ
status: log
tags: [prompt-engineering, record-agent, answer-agent, longvideobench, pre-study]
---

# 動画長グループ別の試行のプロンプト（2026-10-22）

実験の本体（条件・実行・結果・考察）は [動画長グループ別の試行](2026-10-22-lvb-duration-groups.md) にある。このファイルには、プロンプトを作った経緯と版ごとの差分を残す。

- 林の判断（2026-10-22）: 事前情報は**人が設計した**ことにする（予習Agentに書かせる案 (b) ではなく、文章を人が書く案 (a)）。
- 対象は字幕を使わない10カテゴリ（S2E, S2O, S2A, E2O, O2E, E3E, O3O, SSS, SOS, SAA）。
- 本文: Workbenchリポジトリ `2026_10_hayashi_pre_study_agent_system_workbench` の `prompts/history/record/v6g-lvb.txt` と `prompts/history/answer/a1.txt`。

## 1. 記録 v6g-lvb（v6g ＋ LongVideoBenchの事前情報）

### 方針

- v6g の本文は1文字も変えない。最初の段落（目的）の直後に「どんな質問が来るか」の1節だけを足す。比べたいのは「事前情報の有無」だけにするため。
- 事前情報の出どころは、論文で公開されている17カテゴリの定義（[タスクとジャンル](../../../../secretary/notes/brainstorm/2026-10-19-longvideobench-tasks-and-genres.md) 第2節）。字幕を使わない10カテゴリの「何を問うか」を、英語の箇条書き6つにまとめた。valの質問文・選択肢・正解は使っていない。
- 計画の時点で「v6gにはもう質問の傾向の説明が入っている」と考えていたが、誤りだった（それはv5の冒頭）。v6gにあるのは「後で質問に答える」という一般的な一文だけなので、①と②の差ははっきりしている。

### 差分（v6g → v6g-lvb）

```diff
 You are transcribing the events of a video into a time-stamped log. ...
+
+What the questions will ask (known in advance):
+The questions are multiple-choice. Each question first points to one or more moments of the video by describing how they look (the place, the people and their clothes, the objects that are visible), and then asks one of these:
+- what a person or animal does at that moment;
+- which objects are there at that moment, or which person or object takes part in an event;
+- what an object looks like at that moment (its color, shape, or number);
+- what happens just before or just after an event, or which object appears just before or after another object;
+- in which order several scenes happen;
+- in which other scene the same object or person appears again, or how its look changes between two scenes.
+So write the log so that each moment can be found again from how it looks: name people by how they look, name the objects that people use, hold, or point at with their color, and name the new place by what is easy to see there when the view changes (at most two features, as written below).
```

| 箇条書き | 対応するカテゴリ |
|---|---|
| what a person or animal does | S2E, O2E |
| which objects are there / takes part in an event | S2O, E2O |
| what an object looks like | S2A |
| just before or just after | E3E, O3O |
| in which order | SSS |
| appears again / how its look changes | SOS, SAA |

### 気をつけたこと

- v5までは、物や文字を細かく書かせると暴走した（色の名前を297行など。[プロンプトの変遷](2026-10-21-record-prompt-evolution.md) 第18節）。v6gは「細部は1つだけ」「場所は特徴2つまで」で抑えている。
- 最初の案は「場面が変わったら主な物を書く（name the new place with its main objects）」だったが、v6gの「場所は特徴2つまで」とぶつかり、物を並べる暴走につながりそうなので、「at most two features, as written below」に直してから使った。
- 物については「人が使う・持つ・指す物を色つきで」に限った。画面に見える物すべてではない。

## 2. 回答 a1（新規）

### 方針

- モデルは記録と同じ `Qwen/Qwen3-VL-4B-Instruct`。画像は渡さず、テキストだけ。temperature 0、`max_new_tokens` 16。
- 入力は3通りで、プロンプトの本文は同じ。変えるのは `<log>` の中だけ（段Bでは、IDの説明を1文足す）。
  - 記録だけ: 記録Agentの全行を時刻順に `- [mm:ss.s-mm:ss.s] 文`。
  - 段A: 段Aのグループ（まとめた後の行）を同じ形で。
  - 段A+段B: 段Aのグループの文の前に、段BのID（`P04: …`）。
- 出力は番号だけにさせる。10/09の失敗（`answer_validation_failed` で生出力が残らなかった）を受けて、次のようにした。
  - 生出力は必ず保存する。
  - 番号の読み取りは段階を分ける: 番号だけ（strict）、文の中の最初の番号（lenient）、選択肢の文と一致（text）、失敗。
  - 失敗は「予測なし・不正解」として数え、形式の失敗の数は別に集計する。
- 分割統治は今回は入れない。今回の目的は「どの長さでも最後まで動くこと」なので、1回の呼び出しで答える。記録が長くなりすぎた場合に、区間ごとに分けて関係のある行を抜き出す段を足す。入力token数は毎回保存する。

### 本文（a1）

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
3. If the log does not say it clearly, choose the option that fits the closest lines best. Always choose one option.

Answer with the number of the option only, for example: 2
```

`{{log_note}}`（段A+段Bのときだけ）: ` A tag such as P04 before the event names a person or animal: lines with the same tag show the same one (people who change clothes may get a new tag).`

### 設計の理由

- 記録と質問の境目は `<log>…</log>` のタグで区切る（[回答Agentへの記録の渡し方](../../../../secretary/notes/brainstorm/2026-10-22-record-input-format-for-answer-agent.md)）。形は、そのメモの第一候補「1行1イベントの箇条書き」にした。表やJSONとの比較は、後でやる。
- 「場面を見た目で探す → 前後の行も読む → 選ぶ」の3段は、LongVideoBenchの質問の作り（参照文で場面を指してから聞く）に合わせた。
- 「わからなくても必ず1つ選ぶ」としたのは、答えない出力（"The log does not mention…"）で形式の失敗が増えるのを防ぐため。
- 理由を書かせる（chain of thought）形にはしなかった。今回は動作の確認が目的で、出力が長くなると形式の失敗と時間が増えるため。精度を上げる段で試す候補にする。

### a1 の結果（パイロットの長い2グループ、各条件 25問 × 3入力）

- 範囲外の答え `0` が、15回答中3〜5回あった。同じ質問では入力の形を変えても `0`。
- `0` を答えた質問は、参照文が長く細かい（例: 「黄・緑・青の Y, G, B のブロックの前で、眼鏡にスーツの男性が右手に算数セットを持っている」）。記録にその場面がないので、「どれでもない」の意味で `0` を出したと考える（推測）。正解の位置の偏りではない（3問とも正解は2番目、ほかの問は散らばる）。

## 3. 回答 a2（a1 → 選択肢を A〜E の文字にする）

```diff
-Answer with the number of the option only, for example: 2
+Answer with the option's letter from the given choices directly, for example: B
```

- コードの側でも、選択肢を `A. …` の形で並べる。LongVideoBench公式の評価コードと同じ文（`Answer with the option's letter from the given choices directly.`）にした（[タスクとジャンル](../../../../secretary/notes/brainstorm/2026-10-19-longvideobench-tasks-and-genres.md) 第1節）。
- 文字なら、範囲外の `0` は出ない。

### a2 の結果（パイロット全4グループ、35問 × 6 = 210回答）

- `0` はなくなったが、**答えを断る出力が33回**出た。例:
  - `None of the log entries describe tofu, a wooden cutting board, white paper,`
  - `There is no line in the log that describes an "olive-colored animal head`
  - `None of the options are supported by the log. The log describes a person preparing`
- プロンプトの「Always choose one option.」は守られなかった。a1 の `0` も、同じ「断り」が数字になったものだと考える。
- `C. White` のように説明つきの出力は、lenient で正しく読めた。

## 4. 回答 a3（a2 → 場面が見つからなくても推測で選ばせる）

```diff
-3. If the log does not say it clearly, choose the option that fits the closest lines best. Always choose one option.
+3. The log may miss the moment or describe it in other words. Then guess: choose the option that fits the log best. You must always choose one option. Do not explain and do not say that the log does not mention it.

-Answer with the option's letter from the given choices directly, for example: B
+Answer with the option's letter from the given choices directly.
+The best answer is:
```

- 「記録が場面を落としている、または別の言葉で書いている」ことを、先に認めておく。そのうえで、推測で選ぶことと、断りの文を書かないことを明示した。
- 最後の `The best answer is:` は、動画QAの評価でよく使われる形を借りた（Video-MME などの評価コードにある、という記憶にもとづく。原文は未確認）。答えの書き始めを文字に誘導するため。
- 例の `for example: B` は外した（Bに偏るのを避けるため）。

### a3 の結果（同じ210回答）

| 回答プロンプト | 失敗（断り・範囲外） | lenient | 
|---|--:|--:|
| a2 | 33 | 6 |
| a3 | **4** | 7 |

- 残った断りは1問だけ（`@asianfoodrecipes-7109221563697876225_0`、3入力 + 1）。
  - 質問は「木の板に白い紙、6切れの**豆腐**に赤いソース、右にピンクのはけ。何が起きているか」。正解は「はけで豆腐にソースを塗る」。
  - 記録は `person in plastic gloves brushes ketchup onto potato slices`。frame（6秒）を見ると、画面の字幕は「add ketcup on the top」で、丸く切ったじゃがいもにケチャップを塗っている。**記録は正しく、質問の側が「豆腐」と呼んでいる。**
  - 回答Agentは、記録の「ケチャップをはけで塗る」が正解の選択肢と同じ内容なのに、「tofu がない」ことにこだわって断った。言葉が違うと場面を結び付けられない、という失敗の例。
- 正答率は a2 と同じか少し上（パイロットの問題数は少ないので参考値）。
- **本番は a3 で行う。** 残る失敗は「予測なし・不正解」として数え、表では別に示す。
