---
date: 2026-10-19
project: agentic-streaming-videoqa
topic: LongVideoBenchのタスク一覧表（正式名称・質問文の傾向つき）と、字幕系（T系）タスクを当面外す判断
status: decided-tentative
tags: [longvideobench, question-type, question-template, subtitles, task-selection]
---

# LongVideoBenchのタスク一覧（T系は当面外す）

詳しい根拠と集計は [LongVideoBenchのタスク・ジャンル・動画の長さ](2026-10-19-longvideobench-tasks-and-genres.md) にある。この表はそのメモから作った（件数はローカルの `lvb_val.json` / `lvb_test_wo_gt.json` を集計した値）。

## 決めたこと（2026-10-19、林）

- **字幕のセリフを手がかりにするT系7カテゴリ（T2E, T2O, T2A, T3E, T3O, TOS, TAA）は、当面の評価対象から外す。**
- 理由: 字幕を扱う処理（時刻付きで字幕を読み込む、動画ごとの字幕の開始時刻のずれを直す）を作る手間を省き、映像のイベント記録に集中するため。
- T系の問題も、質問が来るのは動画の最後（ほかの問題と同じ）。字幕のセリフは「どの場面のことか」を指すために使われている。そのため、字幕を読まないと場面を特定できない問題が多いと考えられる（推論）。
- 外した後に残るのは S/E/O系の10カテゴリ。valでは1,337問のうち **815問**（約61%）になる。
- 教授からは「普通は全タスクで評価する」と言われている。外す理由（映像のイベント記録が対象で、字幕は範囲外）は、2026-10-21のMTGで確認する。

## 字幕ファイルの場所（ローカルデータで確認）

- 字幕は動画とは**別のファイル**。`/mnt/HDD10TB-2/hayashi/data/LongVideoBench/subtitles.tar`（約117MB）として**ダウンロード済み**。ただし**まだ展開していない**。
- tarの中身は `subtitles/<動画ID>_en.json` 形式で、約9,300ファイル。動画数（約3,760本）より多い理由は未確認。
- 各問題のJSONに `subtitle_path`（例: `86CxyhFV9MI_en.json`）と `starting_timestamp_for_subtitles`（字幕の時刻のずれ。0でない動画がある）が入っている。
- 字幕を使わない今の方針では、展開する必要はない。

## 質問文の共通の形（ローカルデータで集計、val）

- ほぼすべての質問が **「場面の説明（referring query）」＋「短い質問」** の形になっている。JSONには短い質問だけを取り出した `question_wo_referring_query` という欄がある。
  - 例（S2E）: 「On the sea, a woman wearing sunglasses ... is sitting in a cart ...」（場面の説明）＋「What is this woman doing?」（短い質問）
- 場面の説明は毎回違う（その動画の見た目を細かく書いた文）。一方、**短い質問の言い回しはカテゴリごとにほぼ決まっている**。下の表の「質問文の傾向」欄に、各カテゴリの典型的な言い回しを書いた。
- 例外: **SSS**（97問中88問）と **O3O**（66問中19問）は、場面の説明がない。場面は選択肢の側に書かれている（例: 「Which of the following sequences of scenes is correct?」の選択肢が「First, ... Then, ... Finally, ...」）。
- カテゴリごとの定型句の出現率（正規表現で数えた概算）: SSS 100%（sequence）、SOS 100%（where else / which scene / appear）、S2A 98%（color / shape / what kind）、O3O 97%（first / before / after）、SAA 93%（change）、S2O 92%（object / item / present）、S2E 90%（doing / what happens）、E3E 84%（after / before / next）、O2E 74%（first など）。
- 本研究への意味（推論）: 短い質問の型がカテゴリごとに決まっているので、「どんな質問が来るか」を予習しやすい。予習Agentには、カテゴリの定義に加えて、この典型的な言い回しを渡せばよい。予習できないのは「どの場面を聞かれるか」（場面の説明の中身）のほう。

## タスク一覧表

- 「対象」の列: ○ = 評価する、× = 外す（T系）。
- 「GPT-4o」の列: 原論文 Table 7 にある **test** の正答率（%）。要約ツールで読んだときに表が崩れていたため、数値はPDFで要確認。
- 「質問文の傾向」の列: 短い質問（`question_wo_referring_query`）の典型的な言い回し。X = 場面の説明で指された人・物。valの例を読んで、上の集計と合わせてまとめた。
- 略号の読み方: 1文字目は場面を指す手がかり（S=Scene 場面の見た目、E=Event 出来事、O=Object 物体、T=Text 字幕）。最後の文字は答えの種類（E=出来事、O=物体、A=Attribute 属性、S=場面・字幕）。「2」は「その時点」、「3」は「前後」と読める（表の名前からの推論。論文に明記はない）。

### L1 Perception（知覚：1つの場面で見えるものを問う）

| 対象 | 略号 | 正式名称 | 何を問うか | 質問文の傾向 | val | test | GPT-4o |
| :-: | --- | --- | --- | --- | ---: | ---: | ---: |
| ○ | S2E | Scene-referred Event | 場面の説明 → その場面で起きている出来事 | 「What is this man / she doing?」 | 93 | 317 | 76.8 |
| ○ | S2O | Scene-referred Object Existence | 場面の説明 → その場面にある物体 | 「What objects are present in this scene?」「Which of the following items ...?」 | 72 | 331 | 69.8 |
| ○ | S2A | Scene-referred Object Attribute | 場面＋物体 → その物体の属性（色・形など） | 「What color is ...?」「What is the shape of ...?」「What kind of ...?」 | 88 | 322 | 70.9 |
| ○ | E2O | Event-referred Object | 出来事 → それに関わる物体・人 | 説明の中に動作があり、「Who is ...ing?」「What is the object that is ...ing?」で人・物を答える | 65 | 328 | 67.3 |
| ○ | O2E | Object-referred Event | 物体 → それが映っているときの出来事 | 「What did X do the first time he appeared?」「When X first appears, what ...?」（first が多い） | 87 | 314 | 72.8 |
| × | T2E | Text-referred Event | 字幕 → その字幕と同時の出来事 | 「When the subtitle '...' appears, what is X doing / what happens on the screen?」 | 65 | 333 | 67.2 |
| × | T2O | Text-referred Object Existence | 字幕 → そのとき映っている物体 | 「When the subtitle '...' appears, what objects are present?」 | 76 | 311 | 65.3 |
| × | T2A | Text-referred Object Attribute | 字幕＋物体 → そのときの物体の属性 | 「When the subtitle '...' appears, what is the shape / color of ...?」 | 79 | 323 | 77.2 |

### L2 Relation（関係：複数の場面の関係を問う）

| 対象 | 略号 | 正式名称 | 何を問うか | 質問文の傾向 | val | test | GPT-4o |
| :-: | --- | --- | --- | --- | ---: | ---: | ---: |
| ○ | E3E | Event before/after Event | 出来事 → その前・後の出来事 | 「After X ..., what does he do next?」「What happens next?」 | 94 | 312 | 62.6 |
| ○ | O3O | Object before/after Object | 物体 → その前・後に現れる物体 | 「What is the first ... that appears after this?」「Which of these appeared first?」（約3割は場面の説明なし） | 66 | 328 | 61.3 |
| ○ | SSS | Sequence of Scenes | 複数の場面 → 正しい順序 | ほぼ固定で「Which of the following sequences of scenes is correct?」。場面は選択肢に「First ..., then ..., finally ...」と書かれる | 97 | 301 | 44.3 |
| ○ | SOS | Scene-referred Object Tracking | 場面＋物体 → その物体が再び現れる別の場面 | 「In which other scenes does X appear?」「Where else / Where has X appeared before?」 | 81 | 300 | 75.6 |
| ○ | SAA | Scene-referred Object Attribute Change | 2つの場面＋物体 → その間の属性の変化 | 「What changes occur to X?」「What change did X experience?」 | 72 | 303 | 62.6 |
| × | T3E | Event before/after Text | 字幕 → その前・後の出来事 | 「Before / After the subtitle '...', what does X do?」 | 73 | 328 | 64.0 |
| × | T3O | Object before/after Text | 字幕 → その前・後に現れる物体 | 「After the subtitle '...', what is the first object that appears?」 | 74 | 317 | 66.4 |
| × | TOS | Text-referred Object Tracking | 場面＋物体 → その物体が再び現れたときの字幕 | 「Which subtitle appears at the same time as X?」（答えが字幕の文） | 73 | 307 | 62.1 |
| × | TAA | Text-referred Object Attribute Change | 2つの字幕＋物体 → その間の属性の変化 | 「When the subtitle '...' appears, what change occurs to X?」 | 82 | 266 | 66.4 |

### 問題数のまとめ

| | val | test | val の 900–3600秒 |
| --- | ---: | ---: | ---: |
| 全17カテゴリ | 1,337 | 5,341 | 564 |
| 対象（○ 10カテゴリ） | **815** | 3,156 | **342** |
| 外す（× T系7カテゴリ） | 522 | 2,185 | 222 |

対象のvalを長さ別に分けると、8–15秒 107問、15–60秒 102問、180–600秒 264問、900–3600秒 342問。

## 対象10カテゴリのまとまり（推論）

[元のメモ](2026-10-19-longvideobench-tasks-and-genres.md) の候補①②からT系を除いたもの。

| まとまり | カテゴリ | val | test | val の 900–3600秒 | 考え方 |
| --- | --- | ---: | ---: | ---: | --- |
| ① 出来事系 | S2E, O2E, E3E, SSS | 371 | 1,244 | 159 | 時刻付きのイベント記録で答える。最初に作る記録Agentにそのまま対応する |
| ② 物体の登場・追跡系 | S2O, E2O, O3O, SOS | 284 | 1,287 | 117 | 物体・人が現れた時刻の台帳で答える。①の記録に「物体」の観点を足す |
| ③ 属性系（対照群） | S2A, SAA | 160 | 625 | 66 | 色・形などの細かい見た目。テキスト記録では落ちやすいと考えて、別枠で報告する |

- 進め方の案: まず①で第1版を作り、②を足して①＋②（val 655問）を主な評価対象にする。③は全体の正答率に含めたうえで別枠で示す。
- SSSはGPT-4oでも44.3%と最も低い。時刻付きの記録があれば場面を並べ替えるだけで解ける可能性があるので、差を出しやすい候補になる。
- 逆に、属性系のS2AはGPT-4oで70.9%と高めだった。「テキスト記録では難しい」という見立ては、実験で確かめる必要がある。

## 第1版の実装方針（2026-10-20 追記、林）

### 決めたこと

1. **T系7カテゴリは外す**（上の「決めたこと」のとおり）。
2. **予習は、当面は人が手で書いたプロンプトで代用する。** 予習Agentは後で作る。
3. **第1版は「記録」と「簡単な回答」まで作る。** 集約（NMSのような処理）と、小さいモデル群で分担して答える形は後回しにする。

### 予習の情報を入れる場所（推論）

- **記録の段階**: 記録している間は質問がまだ来ていないので、タスクごとにプロンプトを切り替えられない。そのため、全タスク向けの観点を1つのプロンプトにまとめて書く。
  - 出来事系（S2E, O2E, E3E, SSS）: 出来事を時刻付きで書く。
  - 物体系（S2O, E2O, O3O, SOS）: 人・物が初めて現れた時刻と、再び現れた時刻を書く。
  - 属性系（S2A, SAA）: 目立つ色・形、その変化を書き添える。
- **回答の段階**: 質問が来た後なので、タスクごとの注意事項を足してよい（例: SSSは「記録の時刻を見て選択肢を並べ替える」）。ただし、どのタスクかは質問文から判定させ、JSONの `question_category` は使わない。

### 気をつけること（推論）

- 評価に使うvalを見ながら手書きのプロンプトを調整すると、評価データへの過学習になる。注意事項は論文のタスク定義から書くか、valを動画ごとに2つに分け（元のメモの案B）、片方だけを見て書く。
- 手書き版は「人が予習した」ものなので、後で作る予習Agentと比べるときのベースライン（または上限の目安）として扱う。

### 第1版の流れ

| 段階 | 中身 | 第1版での扱い |
| --- | --- | --- |
| 予習 | どんな質問が来るかを知る | 手書きのプロンプトで代用 |
| 記録 | Qwen3-VLが動画を先頭から順に見て、イベントを時刻付きでMarkdownに書く | 作る（本体） |
| 集約 | 似たイベント・重なったイベントをまとめる | 後回し |
| 回答 | Markdown全体と質問・選択肢をLLMに渡して選ばせる | 簡単なものを作る |

- 確認すること: 手書きをどこまで許すかを、2026-10-21のMTGで教授に確認する。

## Workbenchの使い方の方針（2026-10-20 追記、林）

### 2つの使い方に分ける

| | ブラウザで確認する場合 | ブラウザを使わない場合 |
| --- | --- | --- |
| 目的 | **プロンプトがうまく働いているかを見る** | 正答率を出す（評価） |
| 対象 | 1本ずつ（少数） | 複数の動画をまとめて |
| 動画の選び方 | データセット＋動画・質問の選択画面で選ぶ | 一覧ファイル（manifest）で指定する |
| 実行中 | 一気に推論を進め、進み具合のゲージだけを出す | CLIで進み具合を出す |
| 実行後 | ターンごとに、サンプリングした画像列とMarkdownの記録を並べて見る | 結果の表（カテゴリ別の正答率など）を保存する |

- ブラウザで動かす利点は、「自分で動画を探して選ぶ手間が省ける」ことくらい。そのため、実行中に1ターンずつ見る画面は作らない。結果は実行後にまとめて表示する。

### 動画選択画面への変更

- 動画一覧に**タスクのタグ**（その動画の質問のカテゴリ。例: SSS, E3E）を付ける。
- **検索でもタスクで絞り込めるようにする。**
- 選択画面の変更は、ほぼこれだけ。今の選択画面は気に入っている。

### 今出ている不具合（林の報告）

- 実行するたびに、プレビューの高速化が外れる。
- 名前を変えた（rename）動画が、元の名前に戻る。
- 原因は未調査。別名は `browser/library.py` の SQLite（`WORKBENCH_HOME` の下）に保存されているので、実行時に別の保存先を見ている可能性がある（推論）。

### ブラウザを使わない場合（複数動画の同時実行）

- 既存の `./scripts/workbench.sh batch-run MANIFEST` は、質問IDを並べた manifest を**1件ずつ順番に**実行する（`entrypoints/batch.py`）。設定を比べるために作ったもの。
- 設計で考えること（推論。詳細はこれから詰める）:
  - 一覧の作り方: 条件（カテゴリ、長さ、問題数、シード）で選んで manifest を作る。選択画面の絞り込み結果を書き出せるようにする案もある。
  - 実行の単位: 記録は動画ごとに1回、回答は質問ごと。
  - 同時実行: GPUごとに1つの処理を立てて、動画を順に割り振る。
  - 途中で止まったときの扱い: 終わった動画は飛ばして、続きから再開する。1本が失敗しても全体は止めない。
  - 出力: 動画ごとの記録・画像と、全体の結果の表。同じ出力先なら、後でブラウザでも見られるようにする。
- **規模の決定（2026-10-20、林）**: 今は大規模に回す必要はない。**1つのGPUで、複数の動画を1回のコマンドで順番に実行できれば十分。** 目的は、(1) 実行時間の目安を測ること、(2) 正答率を出す必要が出たときに広げられるようにしておくこと。
  - 作るもの: 一覧ファイルでの実行、モデルを1回だけ読み込んで動画を順に処理、動画ごとの記録・質問ごとの回答、動画ごと・段階ごと（記録／回答）の処理時間の保存、結果の表、終わった動画を飛ばす再開、1本が失敗しても続行。
  - 作らないもの: 複数GPUでの同時実行、動画の割り振りの工夫。
  - 将来に備えること: 動画ごとの出力を独立させておく。そうすれば、一覧ファイルを分けて別のGPUで回し、結果の表を後で結合するだけで広げられる（推論）。

## 記録プロンプトの設計（2026-10-20 追記）

### 前提（林・研究室の方の意見）

- 過去のプロンプトは短すぎて、モデルを制御できていないと指摘された。
- 研究室の方の意見: Qwen専用の言い回しは要らない。汎用的なモデル向けのプロンプトで十分。
  - AIの考え: プロンプトの文面は汎用でよい。Qwenに合わせる必要があるのは、frameと時刻の渡し方、出力の上限（今の `max_new_tokens: 256` は記録には足りない可能性）、モデルの大きさ（今は `Qwen3-VL-4B-Instruct`）などの、コードと設定の側。

### 決めたこと（2026-10-20、林）

1. **前の区間の記録は見せない。** 区間ごとに独立して記録する。
2. **例は1つだけ、短く入れる。** 評価に使う動画から作らない。
3. 出力形式は、1行に1つの事実を書く決まった形式にする（AIの提案。異論がなければこれで進める）。
4. **TEXT（画面上の文字）を記録に含める。** 字幕が画面に焼き込まれている動画ではTEXTが実質的に字幕になるが、それでよいとする。
5. **`max_new_tokens` を増やす**（まず768程度）。
6. **区間の既定値は20秒・8枚**（約2.5秒に1枚）。ブラウザ上では変えられる。
7. **続いている動作は1行にまとめる。** 複数のframeで同じ人・物が同じ動作を続けていたら、最初のframeから最後のframeまでの1行にする（例: 16秒間ずっとカメラに向かって話している → `[100.0-116.0] EVENT: ... talks to the camera`）。動作・人・場所が変わったときだけ新しい行にする。途中のframeで見えなくなったら、そこで行を分ける。区間の境目をまたぐ動作は2行に分かれるので、つなぐのは後の集約の段階で行う（推論）。

### 前の記録を見せないことの影響（推論）

- 区間ごとに独立しているので、「初めて現れた／再び現れた」は記録の段階では判断できない。記録では「この区間に何が見えるか」だけを書き、登場・再登場は後の段階（集約か回答）で、見た目の呼び方を照らし合わせて判断する。
- そのため、**人・物を見た目の特徴で呼ぶルール**が一番大事になる。区間をまたいで同じ呼び方になるかどうかで、物体系（O3O, SOS など）の正答率が決まると考えられる。

### プロンプト案 v1（未確定。v0に「続いている動作のまとめ方」を足し、例を差し替えた）

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

### プロンプト案 v1 でできること・できないこと（2026-10-20、林の整理にAIが補足）

| 林の整理 | 補足（推論） |
| --- | --- |
| シーンの切り替わりを記録できる（1区間にSCENEが複数あれば背景が変わった） | 区間の中だけ。区間の境目での切り替わりは、前の記録を見せないので集約の段階で判断する。カメラの移動と場面の切り替わりも区別していない |
| 人がいれば観測できる | ENTITYとして記録できる。区間をまたいで同じ人かどうかは、見た目の呼び方の一致に頼る |
| 一連の動作を記録できる（最後のframeでは、動作が終わったかは分からない） | 最初のframeについても同じで、動作が区間の前から続いていたかは分からない |
| 動作の変化を記録できる（EVENTが複数あれば動作が変わったと分かる。ただし今の挙動はもっと柔軟） | 区切り方はモデル任せなので、同じ動画でも区切り方がぶれる可能性がある |
| 動画内の字幕が分かる | **画面に焼き込まれた文字だけ**。LongVideoBenchの字幕の多くは別ファイル（`subtitles.tar`）なので、T系の問題の大半は依然として解けないと考えられる |

決めたこと（2026-10-20、林）: **区間の端で動作が続いているかは、コードで判定する。** 行の開始時刻が区間の最初のframe、終了時刻が最後のframeと一致するかを見て、「区間の最初から続いている／最後まで続いている」の印を付ける。プロンプトは変えない。集約の段階で、前の区間の「最後まで」と次の区間の「最初から」が、同じ呼び方・同じ動作ならつなぐ。

v1ではできないこと（推論）:

- 発話の内容: 音声を入力していないので「話している」は分かるが、「何を話しているか」は分からない。
- frameとframeの間（約2.5秒）に起きた短い出来事。
- 初登場・再登場の判断: 集約か回答の段階で行う。

### 細かい情景が削れる問題（2026-10-20、林の指摘）

- 林の指摘: 1行程度で書かせると、「女性の隣の机に花瓶がある」「右上の時計が何時を指している」のような細かい情景が削れる。LongVideoBenchでは細かい情景が必要な問題がある。
- 細かさが要る場面は2つある（ローカルデータで集計、val、T系以外）:
  1. **場面を探すとき**: 質問文の場面の説明（referring query）は中央値32語、上位10%で57語ある。服の色、背景の物、位置、画面の文字まで書かれている。SAAは中央値49語。
  2. **答えるとき**: S2O（その場面にある物）、S2A（色・形・髪型など）、SAA（属性の変化）は、細かい物や見た目そのものを問う。
- 対応案（推論）:
  - 細かさは「長い1行」ではなく「行を増やす」ことで残す。物1つにつき1行（位置・色・数・文字を含める）とし、「目立つものだけ」ではなく、見える物をできるだけ挙げさせる。
  - その結果、記録は長くなる（20秒で数十行、1時間の動画で数千行）。4Bのモデルに全部を読ませて答えさせるのは難しいので、**回答の段階では、質問文の場面の説明で記録を検索して、関係する時刻の行だけを渡す**形が必要になる。
  - それでも文字にしきれない細部（時計の時刻、細かい模様）のために、**frame画像も時刻付きで保存し、回答のときに見直せる**ようにする案がある。オンライン設定で、保存した画像を後で見るのを認めるかは、教授に確認する。

### 記録の役割と行の単位（2026-10-20）

決めたこと（林）:

1. **テキストの記録は「索引」として扱う。** 何が・いつ・どこにあったかを探すためのもの。文字にしきれない細部は、記録だけでは残せない前提とする。
2. **第1版は、1回の呼び出しで全種類を出力させる。** 「何があるか」と「何が起きたか」を2回に分ける案は、v1の結果を見てから考える。
3. **物もしっかり記録する。** 物1つにつき1行（OBJECT）とし、見える物をできるだけ挙げさせる。

動作の行の単位（AIの提案、推論）:

- 「コップを取って水を飲む」は、**動作ごとに分けて3行**（取る／飲む／置く）にする。1行に書くのは「1人（1つの物）が1つの動作をする」ことだけ。
- 理由: E3E（「〜した後に何をしたか」）は、数秒の間の連続した小さな動作を問う（例:「胸の前で手を合わせた後、女性は何をしたか」→「白いボトルを手に取った」）。まとめて1行にすると、前後関係が消える。
- 「水を飲んでいる」のようなまとまった行動の要約は、記録では作らない。後の集約の段階（時間スケールごとにまとめる）で作る。
- 同じ動作が続いている場合は、これまでどおり1行にまとめる（「話している」が16秒続いたら1行）。分けるのは動作が変わったときだけ。
- 注意: frameの間隔は約2.5秒なので、「取る」の瞬間が写らないことがある。写っていない動作は書かせない（推測させない）。

### プロンプト案 v2（未確定。v1にOBJECTと動作の単位を足した）

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

- 設定: `max_new_tokens` は、v2では行数が増えるので768でも足りない可能性がある。最初の試行で `hit_max_new_tokens`（上限に達したかの記録）を見て決める。

## 未確認・今後

- T系を外すことを、2026-10-21のMTGで教授に確認する。
- GPT-4oの正答率はPDFで要確認。
- 「質問文の傾向」はvalの例と正規表現での概算から作った。testでも同じ傾向かは確認していない。
- 字幕ファイルが動画数より多い理由（約9,300ファイル）は未確認。
- 字幕を後で入れる場合は、字幕を届いた時刻に記録ファイルへ追記する形が考えられる。`starting_timestamp_for_subtitles` が0でない動画は時刻をずらす必要がある（推論）。
