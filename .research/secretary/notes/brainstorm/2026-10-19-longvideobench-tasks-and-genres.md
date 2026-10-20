---
date: 2026-10-19
project: agentic-streaming-videoqa
topic: LongVideoBenchの質問の種類・ジャンル・動画の長さの整理と、同じ手法で扱えるタスクの候補
status: exploratory
tags: [longvideobench, question-type, referring-reasoning, dataset-analysis, preview-agent, event-memory, online-evaluation]
---

# LongVideoBenchのタスク・ジャンル・動画の長さ

関連: [2026-10-19 MTG議事録](../../../lab/projects/agentic-streaming-videoqa/meetings/2026-10-19-mtg.md)（「LongVideoBenchにどんなquestion typeがあるか」「ほぼ同じ手法で扱えるタスクを複数選ぶ」への回答。次回MTGは2026-10-21（水）14:30）

各記述の根拠を次の4つで示す。

- **原文で確認**: 原論文（arXiv 2407.15754のHTML版）、公式GitHub、Hugging Faceのデータセットカードで確認した。原論文はWebFetch（要約ツール）経由で読んだので、表の数値は要約ツールの抽出に頼っている。重要な数値は、ローカルデータの集計と一致するかで確かめた。
- **ローカルデータで集計**: 手元のJSONを集計した。
- **推論**: AIの考え。確認していない。
- **未確認**: 調べたが分からなかった。

---

## 結論

1. **タスク（質問の種類）はある。** 17カテゴリで、2つのレベル（L1 Perception 8種、L2 Relation 9種）に分かれる。どの質問も、動画の特定の場面を言葉で指す「referring query」（参照文）から始まる（原文で確認）。
2. **ジャンルもある。** 10種類（映画のあらすじ解説、旅行、Vlog、料理、ニュース、知識系5種）（原文で確認、ローカルデータで集計）。
3. **動画の長さは4グループ。** 8–15秒、15–60秒、180–600秒、900–3600秒（原文で確認）。
4. **分割は val（1,337問、正解あり）と test（5,341問、正解は非公開）だけ。** 学習用の分割はない（原文で確認、ローカルデータで集計）。予習には、valの一部、またはカテゴリの定義そのものを使うことになる（推論）。
5. **参照された場面の位置（`position`）がvalにだけある。** フレーム番号と見られ、動画の最後（質問の時刻）から参照場面までの距離を計算できる。900–3600秒のグループでは、最後の参照場面から動画の終わりまでの中央値は約673秒（約11分）だった（ローカルデータで集計。`position`をフレーム番号とみなすのは推論）。
6. **予習 → イベント記録 → 集約 → 回答に向きそうなタスクのまとまり（推論）:**
   - 出来事系（S2E, O2E, T2E, E3E, T3E, SSS）: val 509問
   - 物体の登場・追跡系（S2O, E2O, T2O, O3O, T3O, SOS, TOS）: val 507問
   - 字幕起点系（T2E, T3E, T2O, T3O）: val 288問
   - 色や形などの細かい属性を問う4カテゴリ（S2A, T2A, SAA, TAA、val 321問）は、テキストに書き落としやすいので難しいと考えられる。比べるための対照群にする案がある。

---

## データの構成（タスク・ジャンル・長さ）

### 1. 問題の形式（原文で確認）

- 多肢選択式。正解1つ、誤答3〜4つ（選択肢は4〜5個）。
  - ローカルデータで集計: valでは選択肢5個が983問、4個が353問、3個が1問。testでは5個が4,062問、4個が1,278問、6個が1問。
- **referring query（参照文）**: 質問は「動画の1つまたは複数の場面を言葉で指す説明」から始まる。指された場面を **referred context** と呼ぶ。
- **referring reasoning**: 参照文を読んで、長い入力の中からその場面を見つけ、その場面について推論して答えるタスク。LongVideoBenchが新しく提案したもの。
- **字幕を挟んだ入力**: 公式の入力は、フレーム画像と字幕を交互に並べ、最後に質問と選択肢を置く。字幕は「字幕の中間時刻の前後のフレームの間」に入れる。
  - 公式ローダーのコード: 選択肢を `A. ...`、`B. ...` の形で並べ、最後に `Answer with the option's letter from the given choices directly.` を付ける。
- 評価: 正答率（%）。zero-shotで、選択肢の文字を直接出力させる。採点用の別モデルは使わない。
  - 原論文の評価では、long-context LMMで最大フレーム数を1〜256の間で変え、最大1fpsにしている。
- 動画の長さに応じた質問数（ローカルデータで集計、val）: 60秒以下は1動画1問（ほぼ全部）、180–600秒は2問（205本）、900–3600秒は3問（188本すべて）。原論文にも長さに応じて質問数を変える記述がある。ただし要約ツールの抽出が乱れていたので、正確な文は未確認。

### 2. 17カテゴリ（原文で確認。件数はローカルデータで集計）

略号の読み方（推論。原論文の表の対応から）: 1文字目が参照の手がかり（S=場面、T=字幕、E=出来事、O=物体）。「2」は「その時点の」、「3」は「前後の」を表す。最後の文字が答えの種類（E=出来事、O=物体、A=属性、S=場面・字幕）。

**L1 Perception（知覚）**: 参照文が1つの場面を指し、その場面で見えるものを問う。

| 略号 | 名前 | 何を問うか | val | test |
| --- | --- | --- | ---: | ---: |
| S2E | Scene-referred Event | 場面 → その場面での出来事 | 93 | 317 |
| S2O | Scene-referred Object Existence | 場面 → その場面にある物体 | 72 | 331 |
| S2A | Scene-referred Object Attribute | 場面＋物体 → その物体の属性（色など） | 88 | 322 |
| E2O | Event-referred Object | 出来事 → それに関わる物体・人 | 65 | 328 |
| O2E | Object-referred Event | 物体 → それが映っているときの出来事 | 87 | 314 |
| T2E | Text-referred Event | 字幕 → その字幕と同時の出来事 | 65 | 333 |
| T2O | Text-referred Object Existence | 字幕 → そのとき映っている物体 | 76 | 311 |
| T2A | Text-referred Object Attribute | 字幕＋物体 → そのときの物体の属性 | 79 | 323 |

**L2 Relation（関係）**: 参照文が複数の場面を指し、順序（前・後・同時）や同じものの再登場など、場面どうしの関係を問う。

| 略号 | 名前 | 何を問うか | val | test |
| --- | --- | --- | ---: | ---: |
| E3E | Event before/after Event | 出来事 → その前・後の出来事 | 94 | 312 |
| O3O | Object before/after Object | 物体 → その前・後に現れる物体 | 66 | 328 |
| SSS | Sequence of Scenes | 複数の場面 → 正しい順序 | 97 | 301 |
| SOS | Scene-referred Object Tracking | 場面＋物体 → その物体が現れる別の場面 | 81 | 300 |
| SAA | Scene-referred Object Attribute Change | 2つの場面＋物体 → その間の属性の変化 | 72 | 303 |
| T3E | Event before/after Text | 字幕 → その前・後の出来事 | 73 | 328 |
| T3O | Object before/after Text | 字幕 → その前・後の物体 | 74 | 317 |
| TOS | Text-referred Object Tracking | 場面＋物体 → その物体が再び現れたときの字幕 | 73 | 307 |
| TAA | Text-referred Object Attribute Change | 2つの字幕＋物体 → その間の属性の変化 | 82 | 266 |

- 合計: L1 = val 625 + test 2,579 = **3,204**、L2 = val 712 + test 2,762 = **3,474**。原論文の3,204 / 3,474と一致する（ローカルデータで集計、原文で確認）。カテゴリごとの val+test も原論文の表と一致する（例: S2E 93+317=410、E2O 65+328=393）。
- 原論文によると、**SSSはすべてのモデルで最も難しいカテゴリ**。誤答の選択肢が正解の順序の並べ替えになっているため。L2はL1より難しい（原文で確認）。
- ローカルデータで気づいた点: testの `level` は L1 が `IntraMoment` という別名になっている（valは `L1-Perception`）。testの `topic_category` には `NPs` が1問だけある（NP-News-Programsの表記ゆれと見られる。推論）。

### 3. ジャンル（topic_category）（原文で確認、ローカルデータで集計）

10種類。原論文では大きく Life / Movie / Knowledge / News の4つにまとめている。動画は119チャンネルから集めた（横長99、縦長20）。

| 略号 | ジャンル | val | test |
| --- | --- | ---: | ---: |
| MR | Movie Recaps（映画のあらすじ解説） | 152 | 658 |
| LT | Lifestyle: Travel Guides（旅行） | 150 | 666 |
| LV | Lifestyle: Life Vlogs（日常Vlog） | 169 | 644 |
| LC | Lifestyle: Cooking/Recipes（料理） | 146 | 694 |
| NP | News Programs（ニュース） | 121 | 492（+`NPs` 1） |
| KA | Knowledge: Art（美術） | 142 | 473 |
| KH | Knowledge: History（歴史） | 147 | 486 |
| KG | Knowledge: Geography（地理） | 124 | 506 |
| KS | Knowledge: STEM（理系） | 111 | 386 |
| KC | Knowledge: Computer Science（情報） | 75 | 335 |

### 4. 動画の長さのグループ（duration_group）（原文で確認、ローカルデータで集計）

JSONでは各グループの上限（15, 60, 600, 3600）で表されている。

| グループ | JSONの値 | val 質問数 | val 動画数 | val 動画長（最小 / 中央値 / 最大、秒） | test 質問数 |
| --- | --- | ---: | ---: | --- | ---: |
| 8–15秒 | 15 | 189 | 186 | 8.0 / 11.5 / 15.8 | 700 |
| 15–60秒 | 60 | 172 | 172 | 8.0 / 36.0 / 60.9 | 753 |
| 180–600秒 | 600 | 412 | 207 | 181.3 / 402.9 / 600.1 | 1,555 |
| 900–3600秒 | 3600 | 564 | 188 | 902.6 / 1196.0 / 3574.0 | 2,333 |

- 15–60秒グループに、15秒未満の動画が8問ある（val）。グループの境界は厳密ではない（ローカルデータで集計）。
- 60–180秒、600–900秒の動画はない（ローカルデータで集計）。
- KS（理系）とKC（情報）には、60秒以下の動画がない（ローカルデータで集計）。

### 5. 分割（split）（原文で確認、ローカルデータで集計）

| 分割 | 質問数 | 動画数（ローカル） | 正解 | `position` |
| --- | ---: | ---: | --- | --- |
| val（`lvb_val.json`） | 1,337 | 753（原論文は752） | あり（`correct_choice`） | あり |
| test（`lvb_test_wo_gt.json`） | 5,341 | 3,008（原論文は3,011） | なし | なし |

- データセットの説明: 「valは全体の20%で正解を公開する。testは残りの80%で、LongVideoBenchへの過学習を避けるため正解は公開しない」（原文で確認）。
- **学習用の分割はない。** Hugging Faceのカードには「We do not advise to use this dataset for training.」とある（原文で確認）。
- testはHugging Faceのリーダーボード（Space）で順位を出している。しかし、testの予測をどう提出するかは、カード・GitHub・Spaceのどれにも書かれていなかった（未確認）。
- 公式の自動評価（LMMs-Eval）として案内されているのは `longvideobench_val_i` / `longvideobench_val_v` で、どちらもval（原文で確認）。

### 6. JSONのフィールド（ローカルデータで集計）

valの1件の例（`86CxyhFV9MI_0`）:

```json
{
  "video_id": "86CxyhFV9MI",
  "question": "In the video, which subtitles appear at the same time as the man with black hair, dressed in grey clothes with black sleeves, on stage?",
  "question_wo_referring_query": "Which subtitles appear at the same time?",
  "candidates": ["...", "...", "...", "..."],
  "correct_choice": 1,
  "position": [854, 948, 1373],
  "topic_category": "NP-News-Programs",
  "question_category": "TOS",
  "level": "L2-Relation",
  "id": "86CxyhFV9MI_0",
  "video_path": "86CxyhFV9MI.mp4",
  "subtitle_path": "86CxyhFV9MI_en.json",
  "duration_group": 600,
  "starting_timestamp_for_subtitles": 0,
  "duration": 190.16,
  "view_count": 259852
}
```

| フィールド | 意味 | 根拠 |
| --- | --- | --- |
| `question` | 参照文を含む質問の全文 | ローカルデータで集計 |
| `question_wo_referring_query` | 参照文を取り除いた質問。valでは156問、testでは595問が `question` と同じ文 | ローカルデータで集計 |
| `candidates` / `correct_choice` | 選択肢と正解の番号（0始まり）。testには `correct_choice` がない | ローカルデータで集計、公式ローダーのコード |
| `position` | 参照された場面のフレーム番号のリスト（val のみ） | 推論（下を参照） |
| `starting_timestamp_for_subtitles` | 動画ファイルが元動画の途中から始まる場合の、字幕の時刻のずれ（秒）。公式ローダーは字幕の時刻からこの値を引く。val 250問、test 955問で0以外 | 公式ローダーのコードで確認 |
| `duration` | 動画の長さ（秒）。ffprobeで測った長さとの差は、全val動画で2秒以内 | ローカルデータで集計 |
| `duration_group`, `topic_category`, `question_category`, `level` | 上記の分類 | ローカルデータで集計 |

**`position` はフレーム番号と考えられる（推論）。** 公式READMEにフィールドの説明はない。根拠は次のとおり。

- 原論文に「アノテーターは参照した場面をフレーム番号で記録する」とある（原文で確認）。
- valの動画753本のfpsをffprobeで調べ、`position / fps` を計算した。1,337問中1,335問で、値が動画の長さに収まった（ローカルデータで集計）。収まらなかった2問（`Z-1lgAXOEc8_0` の `61388250`、`3hyPwjkdHEA_1`）は注釈の誤りと見られる。
- L1はほぼ1点（625問中619問）、L2はほぼ2点以上（2点が517問、3点が123問）。L1が1つの場面、L2が複数の場面という定義と合う（ローカルデータで集計）。SSSは3点が多く（97問中90問）、3つの場面の順序を問う形と合う。

### 7. 各問題のタスクの見分け方（2026-10-20 追記。ローカルデータで集計）

- **JSONのラベルで分かる。** 各問題に `question_category`（17カテゴリの略号。例: `SSS`, `T3E`）と `level` が入っている。**valにもtestにもある**（testは正解だけが非公開で、カテゴリは公開されている）。
  - `level` は val では `L1-Perception` / `L2-Relation`。test では L1 が `IntraMoment` という別名になっている（上の2.を参照）。
  - 例: `{"id": "...", "question_category": "T3E", "level": "L2-Relation", ...}`
- **質問文からもほぼ分かる。** 短い質問（`question_wo_referring_query`）の言い回しがカテゴリごとにほぼ決まっている（[タスク一覧表のメモ](2026-10-19-longvideobench-task-table-without-subtitles.md) の「質問文の傾向」）。
  - T系は、質問文に「subtitle」「caption」「mention」や引用符で囲んだセリフが入る。正規表現で数えると、T系の val 507/522問、test 2,157/2,185問に入っていた。ただし、画面上の文字を引用符で書いたT系以外の問題（val 90問）にも引っかかるので、これだけでは完全には分けられない。
- **本研究での使い方（推論）**:
  - 評価する問題の選択（T系を外す）と、カテゴリ別の集計には `question_category` を使ってよい。
  - モデルへの入力には `question_category` を渡さない。答える段階でタスクごとの注意事項を使う場合も、タスクは質問文から判定させる。

---

## 集計表

### カテゴリ × 動画の長さ（val）

| カテゴリ | 8–15秒 | 15–60秒 | 180–600秒 | 900–3600秒 | 計 |
| --- | ---: | ---: | ---: | ---: | ---: |
| S2E | 14 | 11 | 26 | 42 | 93 |
| S2O | 8 | 9 | 22 | 33 | 72 |
| S2A | 12 | 14 | 32 | 30 | 88 |
| E2O | 5 | 12 | 36 | 12 | 65 |
| O2E | 19 | 11 | 33 | 24 | 87 |
| T2E | 12 | 8 | 12 | 33 | 65 |
| T2O | 18 | 8 | 32 | 18 | 76 |
| T2A | 11 | 12 | 14 | 42 | 79 |
| E3E | 12 | 9 | 22 | 51 | 94 |
| O3O | 9 | 13 | 14 | 30 | 66 |
| SSS | 9 | 11 | 35 | 42 | 97 |
| SOS | 8 | 9 | 22 | 42 | 81 |
| SAA | 11 | 3 | 22 | 36 | 72 |
| T3E | 7 | 13 | 20 | 33 | 73 |
| T3O | 8 | 9 | 18 | 39 | 74 |
| TOS | 14 | 10 | 28 | 21 | 73 |
| TAA | 12 | 10 | 24 | 36 | 82 |
| **計** | 189 | 172 | 412 | 564 | 1,337 |

- valでは、1つのカテゴリで900–3600秒の問題は12〜51問しかない。長い動画の1カテゴリだけで正答率を比べると、1問で2〜8ポイント動く（推論）。
- testは各カテゴリ900–3600秒が123〜154問ある。ただし正解は非公開。

### カテゴリ × 動画の長さ（test、正解なし）

| カテゴリ | 8–15秒 | 15–60秒 | 180–600秒 | 900–3600秒 | 計 |
| --- | ---: | ---: | ---: | ---: | ---: |
| S2E | 45 | 48 | 90 | 134 | 317 |
| S2O | 51 | 51 | 91 | 138 | 331 |
| S2A | 48 | 46 | 84 | 144 | 322 |
| E2O | 48 | 44 | 82 | 154 | 328 |
| O2E | 37 | 45 | 85 | 147 | 314 |
| T2E | 38 | 46 | 108 | 141 | 333 |
| T2O | 37 | 48 | 82 | 144 | 311 |
| T2A | 43 | 47 | 104 | 129 | 323 |
| E3E | 45 | 47 | 94 | 126 | 312 |
| O3O | 48 | 42 | 103 | 135 | 328 |
| SSS | 41 | 46 | 82 | 132 | 301 |
| SOS | 35 | 39 | 94 | 132 | 300 |
| SAA | 38 | 45 | 88 | 132 | 303 |
| T3E | 44 | 42 | 98 | 144 | 328 |
| T3O | 42 | 45 | 98 | 132 | 317 |
| TOS | 30 | 41 | 90 | 146 | 307 |
| TAA | 30 | 31 | 82 | 123 | 266 |
| **計** | 700 | 753 | 1,555 | 2,333 | 5,341 |

### ジャンル × 動画の長さ（val）

| ジャンル | 8–15秒 | 15–60秒 | 180–600秒 | 900–3600秒 | 計 |
| --- | ---: | ---: | ---: | ---: | ---: |
| MR 映画あらすじ | 21 | 28 | 40 | 63 | 152 |
| LT 旅行 | 35 | 24 | 37 | 54 | 150 |
| LV Vlog | 42 | 38 | 38 | 51 | 169 |
| LC 料理 | 41 | 29 | 34 | 42 | 146 |
| NP ニュース | 11 | 11 | 51 | 48 | 121 |
| KA 美術 | 15 | 16 | 54 | 57 | 142 |
| KH 歴史 | 14 | 14 | 50 | 69 | 147 |
| KG 地理 | 10 | 12 | 48 | 54 | 124 |
| KS 理系 | 0 | 0 | 36 | 75 | 111 |
| KC 情報 | 0 | 0 | 24 | 51 | 75 |

### 参照場面から動画の終わりまでの距離（val、`position`をフレーム番号とみなした場合）

オンライン処理で、質問が動画の最後に来るとしたときの「証拠から質問までの距離」にあたる。異常値の2問を除いた1,335問で集計した。

| グループ | 問数 | 最後の参照場面 → 動画の終わり（秒）: 最小 / 25% / 中央値 / 75% / 最大 |
| --- | ---: | --- |
| 8–15秒 | 189 | 0.3 / 3.6 / 5.6 / 7.9 / 14.1 |
| 15–60秒 | 172 | 0.0 / 9.0 / 16.5 / 28.0 / 57.0 |
| 180–600秒 | 411 | 14.3 / 112.0 / 186.1 / 298.8 / 595.1 |
| 900–3600秒 | 563 | 26.2 / 388.1 / 673.0 / 984.6 / 3457.0 |

- 900–3600秒のグループ（563問）で、最後の参照場面から終わりまでが 60秒超: 556問、5分超: 477問、10分超: 315問、20分超: 85問（ローカルデータで集計）。
- 参照場面は動画の中で偏りなく散らばっている（動画の長さに対する位置の中央値は約0.5）（ローカルデータで集計）。
- 原論文では、参照場面が動画の始めや中ほどにあるとモデルの正答率が下がり、動画が長いほどその傾向が強いと報告している（原文で確認）。

---

## 例題

valから、各カテゴリ1問ずつ短めのものを選んだ。【参照文】は、`question` から `question_wo_referring_query` を除いた部分にあたる。正解には ✔ を付けた。

| カテゴリ | 例（id、長さグループ） |
| --- | --- |
| S2E | `XYsCVqz3iug_0`（3600）【机に青い服の女性（左）と灰色の服の女性（右）】What is the woman in blue doing? → ✔ Placed a light blue arrow on the table（他はスイカ・バナナなどを置いた） |
| S2O | `UMFy3keSk-s_2`（3600）【晴れた日の土の道、遠くに森、灰色の半袖の男性】Which objects are present in the scene? → ✔ Elephant |
| S2A | `pFpZvRsEGZs_0`（600）【緑のコートの禿頭の人が電話を耳に当てる、背景は木のブロックの壁】What color is the phone? → ✔ red |
| E2O | `gJuOMPiixUA_0`（15）【白い部屋に、青い服でイヤホンの男性と灰色のスーツの男性】which person turns around and clenches their fist? → ✔ The man wearing a grey suit |
| O2E | `2W2ZkYARds4_2`（3600）【草原、黄色い規制線、6人の警官】What happened when the yellow warning tape appeared? → ✔ 右前の白髪の警官がかがんだ |
| T2E | `-PnG8Jp2gFw_0`（3600）【画面の前の黒い白衣の男性】When he mentions, 'being you don't know that 30-second ad,' what happens? → ✔ The man waved his hand. |
| T2O | `x4dFLY_-vKs_0`（600）【窓の外の木の前で話す眼鏡の男性】When the subtitle mentions 'But we don't understand everything,' what is the man wearing on his head? → ✔ black cap |
| T2A | `vEy6tcU6eLU_0`（3600）【黒背景、オレンジのシャツの男性、左に緑と白の四角い枠】When the subtitle 'Vegetarian and this one means' appears, what is the shape at the center of the green area? → ✔ Circle |
| E3E | `7XWqI121-Q4_0`（3600）【暖色のランプが2つある寝室、ベッドでPCをつけるオレンジの服の女性】What did she do before turning on the computer? → ✔ Took a shower |
| O3O | `kj3Po7zUeyw_0`（600）（参照文なし）What is the ethnicity of the first person to appear in the video? → ✔ Black |
| SSS | `s49y2RP5C7E_0`（3600）Which of the following sequences of events is correct? → ✔ 焚き火で4人の兵士が料理 → 3人の兵士が缶を開ける → 1人が缶を開ける（誤答は同じ3場面の並べ替え） |
| SOS | `88LbBgZP1vQ_1`（600）【赤い壁と黄色い床の屋内バスケットコート、紫の半袖でバスケットボールを持つ女の子】In which of the following places has the girl appeared? → ✔ In a room with a beige sofa |
| SAA | `yFAuXmcGk2Y_1`（3600）【白背景の黒文字、中央に太字の 'Benefit Tasks'】After the phrase 'Benefit Tasks' is enlarged on the screen, what changes occur? → ✔ Covered with yellow overlay |
| T3E | `a_hkRXc_bYg_0`（3600）【放送中、黒いスーツで目と口を閉じた男性】After the subtitle 'here that want to do that my colleague' appears, what does the man do immediately? → ✔ He opens his eyes and mouth |
| T3O | `aX_HgA5SNLQ_2`（3600）【黒枠のガラス戸の前、緑のジャケットであごひげの男性】After he says "spaces," who is the first person to appear? → ✔ 黒い長髪で黒いトップスの女性 |
| TOS | `kN88RP3XWUU_0`（600）【腰に布を巻き、青と白の大きな球を担ぐ男性】Which of the following subtitles has this man appeared with? → ✔ 'punishments one of the Titans Atlas was' |
| TAA | `LB1qPExHQY8_0`（600）【右下に黒い戦車、左下に白い文字 'Plans'】what change occurred to the word 'Plans' when the subtitle said 'upcoming plans next steps are'? → ✔ The text got bigger |

例題から読み取れること（ローカルデータで集計した例を見ての推論）:

- 参照文は、場面の見た目（服の色、背景、物の配置）を細かく書いたものが多い。記録側にも、ある程度細かい見た目の描写が要る。
- T系の参照文は、字幕の文字列をそのまま引用している。字幕を時刻付きで記録しておけば、文字列の一致でその場面を探せる。
- 選択肢の違いがごく小さい問題がある（例: T2Eで「右手の中指で左のまぶたをこする」と「人差し指で右のまぶた」を区別させる `x4UBaEojM6U_2`）。こうした問題は、テキストの記録だけでは解けない可能性が高い。

---

## 本研究への当てはめ（推論）

この節は、すべてAIの推論。実験では確かめていない。

### 1. 予習との相性

- LongVideoBenchの質問は、17カテゴリのテンプレートに近い形をしている（「〜のとき何が起きたか」「〜の前／後に何が現れたか」「〜の色は何か」「場面の正しい順序は」など）。質問の種類が限られているので、**「どんな質問が来るか」を予習する手法とは相性がよい**と考えられる。
- 一方で、**どの場面を聞かれるか（参照文の中身）は予習できない。** 参照場面は動画全体に散らばっている（位置の中央値は約0.5）。そのため「聞かれそうな場面だけ記録する」ことはできず、どの場面もある程度細かく記録しておく必要がある。予習で決められるのは「何を書き残すか（出来事・登場した物体・順序・字幕との対応）」の方になる。
- 予習を「カテゴリの定義だけを知っている」形にするなら、学習データは要らない。17カテゴリの定義は論文に公開されているので、それを予習Agentのpromptに入れる。これが一番簡単な第1版になる。

### 2. 予習に使えるデータ（学習用の分割がないため）

| 案 | 内容 | 注意点 |
| --- | --- | --- |
| A | 17カテゴリの定義と、論文に載っている例だけを使う | 最も安全。「データの質問を見て予習」とは少し違う |
| B | valを動画単位で2つに分け、片方を予習用、もう片方を評価用にする | 評価用の問題数が半分になる（900–3600秒の1カテゴリで6〜25問程度） |
| C | valで予習し、testで評価する | testの正解は非公開。提出方法が未確認 |
| D | 他のデータセットの学習用の質問で予習する | LongVideoBenchとは質問の傾向が違うかもしれない。「違う傾向の質問には対応できない」という議事録の懸念をそのまま試すことになる |

- testの質問文は正解なしで公開されている。しかし、評価に使う質問そのものを予習に使うのはチーティングに近いので避けるべきだと考える。
- 議事録の「学習データの質問を見て予習する」の意図に一番近いのはBだと考える。ただし、どれを使うかは先生に確認したい。

### 3. 向きそうなタスク・難しそうなタスク

**向きそうなもの:**

- **出来事（E）を答えるもの**: S2E, O2E, T2E, E3E, T3E。「いつ・何が起きたか」をタイムスタンプ付きで残すイベント記録の形にそのまま合う。前後を問うE3E・T3Eは、記録の時刻順がそのまま手がかりになる。
- **SSS（場面の順序）**: モデルには最も難しいカテゴリと報告されている。しかし、場面をタイムスタンプ付きで残していれば、選択肢の場面を記録と照らし合わせて時刻順に並べるだけで解ける。予習した記録が効きやすい候補だと考えられる。ただし、選択肢に書かれた場面の描写と記録の描写が一致するかが鍵になる。
- **字幕起点のもの（T2E, T3E, T2O, T3O）**: 参照文が字幕の文字列なので、字幕を時刻付きで記録しておけば、場面を探す部分は文字列検索で済む。小さいモデルに分担させやすい。
- **物体の登場・再登場（S2O, E2O, T2O, O3O, T3O, SOS, TOS）**: 「どの物体・人がいつ現れたか」の台帳を作れば扱える。予習Agentが「物体の初登場・再登場を聞かれやすい」と知っていれば、記録の観点として足せる。

**難しそうなもの:**

- **細かい見た目の属性（S2A, T2A）や属性の変化（SAA, TAA）**: 色・模様・形・文字の大きさなど、細かい見た目を問う。テキストにすると落ちやすく、全場面の全物体の属性を書き残すのは現実的でない。議事録にある「周辺の画像特徴も入れておく」形（タイムスタンプ付きで画像や特徴を保存し、質問が来てから見直す）でないと難しいと考えられる。ただし、過去を見直すことを禁止するオンライン設定では、保存した画像を後から見ることを認めるかどうかも決める必要がある。
- **選択肢の差がごく小さい問題**: どのカテゴリにも少しずつある。

### 4. 同じ手法で扱えそうなタスクのまとまり（候補）

括弧内は質問数（val / test）。val の内訳は [8–15秒, 15–60秒, 180–600秒, 900–3600秒]。

| 候補 | 含むカテゴリ | val | test | val の長さ別内訳 | val の動画数 | 考え方 |
| --- | --- | ---: | ---: | --- | ---: | --- |
| ① 出来事系 | S2E, O2E, T2E, E3E, T3E, SSS | 509 | 1,905 | 73 / 63 / 148 / 225 | 285 | 「いつ・何が起きたか」の時刻付きイベント記録で答える。議事録で最初に作るとした「イベントをファイルに書くAgent」にそのまま対応する |
| ② 物体の登場・追跡系 | S2O, E2O, T2O, O3O, T3O, SOS, TOS | 507 | 2,222 | 70 / 70 / 172 / 195 | 289 | 物体・人の登場台帳（初登場・再登場の時刻）で答える。①と同じ記録Agentに、予習した観点「物体」を足して扱う |
| ③ 字幕起点系 | T2E, T3E, T2O, T3O | 288 | 1,289 | 45 / 38 / 82 / 123 | 163 | 場面の特定を字幕の文字列で行う。参照の難しさを減らし、記録と前後関係だけを試せる。①②と重なる |
| ④ ①＋②（属性以外すべて） | 上の13カテゴリ | 1,016 | 4,127 | 143 / 133 / 320 / 420 | 574 | valの約76%。属性系4カテゴリ（S2A, T2A, SAA, TAA、val 321 / test 1,214）だけを「テキスト記録では難しい」対照群として別に報告する |

- 進め方の案: まず①で第1版を作り、②を観点の追加として足し、最終的に④を主な評価対象にする。属性系は全体の正答率に含めたうえで、別枠で「テキストで落ちる部分」として示す。そうすれば「普通は全タスクで評価する」という指摘にも答えられる。
- 長い動画に絞る場合、valの900–3600秒は ① 225問、④ 420問ある。

### 5. LongVideoBenchを「オンライン処理」として評価するときに必要なこと

1. **動画を先頭から順に1回だけ読む**: 既存のWorkbench（`sequential_loader`）で、先頭からEOFまで前方向にdecodeする仕組みはすでにある（README 2026-09-25）。
2. **質問は動画の終わりに初めて渡す**: 記録の段階では、`question` も `candidates` も Agent に見せない。予習の情報（カテゴリの傾向）だけを渡す。正解ラベルは今のWorkbenchでもモデル入力に含めていない（Workbenchの `docs/longvideobench.md`）。
3. **参照文で場面を探す**: 質問が来たら、参照文の説明（場面の見た目、字幕の文字列）と記録を照らし合わせて場面を探す。この「探す」が referring reasoning の中心で、記録の書き方で正答率が大きく変わると考えられる。
4. **字幕を使うかを決める**: 公式の入力は字幕付き。T系7カテゴリ（val 522問）は参照文が字幕の文字列なので、字幕なしだと場面の特定が難しくなる。オンラインで字幕を使うなら、字幕も各行の時刻に届いたものとして順に渡す必要がある。`starting_timestamp_for_subtitles` が0でない動画では時刻をずらす。Workbenchの初期recipeは「字幕なし」なので、変更が必要。
5. **報告の分け方**: 全体の正答率に加えて、カテゴリ別・L1/L2別・長さ別・「最後の参照場面から終わりまでの距離」別に出す。距離はvalの `position` から計算できる（上の表）。既存のStreaming手法のLongVideoBenchの報告は全体の正答率だけだった（[2026-10-18 離れた証拠のベンチマーク](2026-10-18-long-range-evidence-benchmark-online-methods.md)）ので、ここで違いを出せる。
6. **比べる相手**: 原論文の結果は「動画全体から一様にフレームを取るオフライン評価」。オンライン処理と同じ条件ではないことを明記する。

---

## 追加調査（2026-10-19 追記）

上の「未確認事項」のうち、調べて分かったこと。

### 1. `position` の意味は、公式も説明していない（原文で確認）

- 公式GitHubの [issue #6「The meaning of position information in the dataset」](https://github.com/longvideobench/LongVideoBench/issues/6)（2024-10-15）で同じ質問が出ている。2025-11-16にも「質問の手がかりがあるフレーム番号か？」という追加の質問があるが、**著者の回答はなく、issueは開いたまま**。
- つまり、フレーム番号とみなす解釈は公式の裏付けがない。論文やスライドで使うなら「公式の説明はなく、フレーム番号と仮定した」と明記する必要がある（推論）。

### 2. testの提出先は、実質的に分からない（原文で確認）

- 原論文には「test set leaderboard に報告する」とあるだけで、提出方法や評価サーバーの説明はない。
- [issue #14「Where to submit for test subset evaluation」](https://github.com/longvideobench/LongVideoBench/issues/14)（2025-06-11）は、2026-03まで「+1」が付くだけで回答なし。
- [issue #15「Submit result to leaderboard」](https://github.com/longvideobench/LongVideoBench/issues/15)（2025-06-16）では、著者のメールアドレス（NTUと rhymes.ai）にも送れなかったと報告されている。回答なし。
- そのため、予習データの案C（valで予習、testで評価）は**今のところ実行できない**と考える（推論）。評価はvalで行うことになり、案Aか案Bが現実的になる。

### 3. 選択肢の重複（原文で確認、ローカルデータで集計）

- [issue #9](https://github.com/longvideobench/LongVideoBench/issues/9) で、testに同じ文の選択肢が2つある問題が報告されている。著者は「確認する」と答えたまま。
- ローカルで集計すると、同じ文の選択肢を含む問題は **val 8問、test 44問**。valの8問はすべて「誤答どうしが重複」で、正解は重複していなかった。**valの採点には影響しない**。
- 動画IDが `@` で始まるもの（TikTok系と見られる）は val 135問、test 577問。issueでは異常の一部として挙がっているが、ローカルのJSONでは動画IDと問題IDが対応しているので、そのまま使える（ローカルデータで集計。読み込み時にIDの扱いだけ注意）。

### 4. 略号の数字の意味（原文で確認）

- 論文に、数字（2と3）の明確な定義はない。表2から読めるのは「最初の文字が参照文の種類、最後の文字が答えの種類」という規則だけ（例: Scene-referred Event → S2E、Event before/after Event → E3E）。
- 「2 = その時点を参照」「3 = 前後（before/after）を参照」という読み方は、表2の名前との対応からの推論のまま。

### 5. 長さに応じた質問数（原文で確認、一部は要確認）

- 原論文の記述: 180–600秒は2問、900–3600秒は3問。60秒以下は1問（要約ツールの抽出では「longer than 60 seconds」となっていたが、ローカルデータでは60秒以下が1問なので、抽出の誤りと考える）。

### 6. カテゴリ別の既存モデルの正答率（原文で確認。ただし表の抽出が乱れていたため要確認）

原論文 Table 7（**testの結果**）。要約ツールの抽出では表が崩れていて、列の位置から数値を割り当てた。主要な商用モデルだけ取り出した。オープンソースのモデルの行は原論文の Table 7 にある。

| モデル | S2E | S2O | S2A | E2O | O2E | T2E | T2O | T2A | E3E | O3O | SSS | SOS | SAA | T3E | T3O | TOS | TAA | test全体 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GPT-4o (0513) | 76.8 | 69.8 | 70.9 | 67.3 | 72.8 | 67.2 | 65.3 | 77.2 | 62.6 | 61.3 | **44.3** | 75.6 | 62.6 | 64.0 | 66.4 | 62.1 | 66.4 | 66.7 |
| Gemini-1.5-Pro (0514) | 74.6 | 58.3 | 76.2 | 68.7 | 73.3 | 66.2 | 63.6 | 76.7 | 61.9 | 58.6 | **55.2** | 69.0 | 59.0 | 58.9 | 60.5 | 53.3 | 62.5 | 64.4 |
| Gemini-1.5-Flash (0514) | 68.5 | 64.7 | 68.0 | 64.5 | 72.5 | 63.6 | 68.0 | 76.7 | 56.5 | 61.0 | **43.1** | 67.3 | 56.2 | 57.5 | 55.0 | 55.3 | 60.7 | 62.4 |
| GPT-4-Turbo (0409) | 74.9 | 60.1 | 64.2 | 63.9 | 69.4 | 62.5 | 61.3 | 69.9 | 57.5 | 55.9 | **44.8** | 66.0 | 53.2 | 56.5 | 53.6 | 56.2 | 60.2 | 60.7 |

読み取れること（推論）:

- **SSS（場面の順序）は4モデルすべてで最低か、それに近い**（43〜55%）。上の「向きそうなタスク」で、時刻付きの記録で解きやすいと考えた候補なので、**差を出しやすいカテゴリ**になりうる。
- **L2の「前後」を問うカテゴリ（E3E, O3O, T3E, T3O, TOS）は、L1の「その時点」を問うカテゴリ（S2E, O2E など）より5〜10ポイント低い傾向**がある。候補①②に含まれ、イベント記録の時刻順が効く部分と一致する。
- 一方、**属性系（S2A, T2A）は意外に高い**（64〜77%）。「テキスト記録では難しい」と考えた対照群は、オフラインの強いモデルにとっては簡単な部類だった。テキスト記録で落ちるかどうかは、実験で確かめる必要がある。

---

## 未確認事項

- **`position` の意味**: 公式の説明がない（issue #6 は未回答）。フレーム番号とみなすのは推論のまま。
- **testの予測の提出方法**: 公式に提出先がない（issue #14, #15 は未回答）。testでの評価は今のところ難しい。
- **原論文の表の数値**: 要約ツールで読んだため、動画数の表（長さ別・横長／縦長別）と Table 7（カテゴリ別の正答率）の抽出が乱れていた。スライドに載せる前に、PDFで数値を確認する。
- **動画数の差**: ローカルのvalは753本、testは3,008本。原論文は752本と3,011本。理由は未確認。
- **Qwen3-VLなどでのカテゴリ別の結果**: 手元ではまだない。valで1回回せば、上の表と比べられる。
- **略号の数字（2と3）の意味**: 論文に明記はない（表2の名前からの推論）。
- **予習データの使い方**: testが使えないので、案Aか案Bのどちらにするかを先生に確認したい。

---

## 出典

- 原論文: Wu, Li, Chen, Li. "LongVideoBench: A Benchmark for Long-context Interleaved Video-Language Understanding." NeurIPS 2024 Datasets and Benchmarks. [arXiv 2407.15754（HTML版）](https://arxiv.org/html/2407.15754)（WebFetchの要約ツール経由で読んだ）
- 公式GitHub: [longvideobench/LongVideoBench](https://github.com/longvideobench/LongVideoBench)
- 公式ローダーのコード: [longvideobench_dataset.py](https://raw.githubusercontent.com/longvideobench/LongVideoBench/main/longvideobench/longvideobench_dataset.py)
- Hugging Faceのデータセットカード: ローカルの `/mnt/HDD10TB-2/hayashi/data/LongVideoBench/README.md`（[longvideobench/LongVideoBench](https://huggingface.co/datasets/longvideobench/LongVideoBench) からダウンロードしたもの）
- リーダーボード: [Hugging Face Space](https://huggingface.co/spaces/longvideobench/LongVideoBench)
- 公式GitHubのissue: [#6 positionの意味](https://github.com/longvideobench/LongVideoBench/issues/6)、[#9 選択肢の重複](https://github.com/longvideobench/LongVideoBench/issues/9)、[#14 testの提出先](https://github.com/longvideobench/LongVideoBench/issues/14)、[#15 リーダーボードへの提出](https://github.com/longvideobench/LongVideoBench/issues/15)（2026-10-19にGitHub APIで取得）
- ローカルデータ: `/mnt/HDD10TB-2/hayashi/data/LongVideoBench/`（`lvb_val.json`、`lvb_test_wo_gt.json`、`subtitles.tar`、`videos/` に3,991本）。Workbenchの説明では `/mnt/HDD18TB/hayashi/data/LongVideoBench` と書かれているが、このマシンにはそのパスはなかった。
- 集計スクリプト（リポジトリ外）: `/tmp/claude-1129/-mnt-HDD10TB-2-hayashi-research-workspace/61e7b882-eee2-431f-93c0-cfe455849729/scratchpad/count_lvb.py`、`/tmp/claude-1129/-mnt-HDD10TB-2-hayashi-research-workspace/61e7b882-eee2-431f-93c0-cfe455849729/scratchpad/pos.py`、`/tmp/claude-1129/-mnt-HDD10TB-2-hayashi-research-workspace/61e7b882-eee2-431f-93c0-cfe455849729/scratchpad/groups.py`
- 関連メモ: [2026-10-18 離れた証拠のベンチマーク](2026-10-18-long-range-evidence-benchmark-online-methods.md)、[Agentの役割の分類：2回目（4.3節）](2026-10-17-agent-role-classification-round2.md)、[2026-09-25 LongVideoBenchの性能と集約](2026-09-25-longvideobench-performance-and-aggregation.md)
