# イベント集約（コードで処理）：入出力と処理の中身（2026-10-22時点）

記録Agentが書いたイベントの行を、コードの規則だけで整理する「集約」について、何を受け取り、どんな処理をし、何を出すのかをまとめます。特に、**コードが作るIDと変数**（`w003-l02`、`A011`、`P04`、`flags`、`status` など）の意味を中心に説明します。

- コード: リポジトリ `2026_10_hayashi_pre_study_agent_system_workbench` の `experiments/2026-10-21-event-aggregation/scripts/`
- 例に使った実行結果: `outputs/2026-10-22_14-09-23/aggregations/`（ニュースの動画 `BtaVRhoLpC0`、約3分、27行）
- LLMは使っていません。英語の文を、単語の一覧と正規表現で判定しています。

---

## 1. 全体の流れ

集約は4つのステップで、前のステップの出力が次のステップの入力になります。

| ステップ | スクリプト | 入力 | 出力（正本） | 新しく作るもの |
| --- | --- | --- | --- | --- |
| 1. 読み込み | `collect_runs.py` | 記録 `records/<動画>/result.json` | `records.json` | 行ID `w003-l02` |
| 2. 段A | `stage_a.py` | `records.json` | `stage_a/stage_a.json` | 印 `flags`、グループID `A011` |
| 3. 段B | `stage_b.py` | `stage_a/stage_a.json` | `stage_b/stage_b.json` | 主語 `subject`、人物ID `P04`、判定 `status` |
| 4. 評価 | `eval_ids.py` | `stage_b/stage_b.json` と正解 | `stage_b_eval.md` | 正解との比較の数 |

```
outputs/<実行した日時>/aggregations/
├── inputs.txt             入力にした記録フォルダの一覧
├── records.json           ステップ1の出力
├── stage_a/
│   ├── stage_a.json       ステップ2の出力（正本）
│   ├── stage_a_<動画>.md    人が読む用の表
│   ├── stage_a_pairs.tsv    比べた組すべての数値
│   └── stage_a_summary.md   件数の一覧
├── stage_b/
│   ├── stage_b.json       ステップ3の出力（正本、集約の最終結果）
│   ├── stage_b_<動画>.md    人が読む用の表
│   ├── stage_b_pairs.tsv    比べた組すべての数値
│   └── stage_b_summary.md   件数の一覧
└── stage_b_eval.md        ステップ4の出力
```

`.json` が正本で、次のステップはこれを読みます。`.md` と `.tsv` は同じ内容を人が読むために表にしたもので、どのプログラムも読み返しません（第7節）。

---

## 2. コードが作る3つのID

集約で出てくるIDは3種類です。どれも**動画ごとの通し番号**で、別の動画・別の実行の同じ番号は無関係です。

### 2.1 行ID（例: `w003-l02`）＝記録の1行

| 項目 | 内容 |
| --- | --- |
| 何を指すか | 記録Agentが書いた1行（イベント1つ） |
| 形 | `w` ＋ 区間の番号（3桁）＋ `-l` ＋ 区間の中の行の番号（2桁） |
| 区間の番号 | **0から**数える。w000 = 0〜20秒、w001 = 20〜40秒、w003 = 60〜80秒 |
| 行の番号 | **1から**数える。モデルがその区間で書いた順 |
| いつ作るか | ステップ2・3でファイルを読み込むとき（`event_text.py` の `load_trial`）。記録の result.json の行には、まだIDがない |
| 変わるか | 変わらない。段A・段Bを通して、元の行を指す名前として使い続ける |

例: `w003-l02` は「60〜80秒の区間で、モデルが2番目に書いた行」です。

```
区間 w003（60〜80秒）でモデルが書いた行:
  1行目 → w003-l01  [60.0–60.0]  stone sign with carved Japanese characters "裁判所" is shown outside a building
  2行目 → w003-l02  [62.5–77.5]  man in a navy suit with short brown hair and a white shirt speaks outside a building
```

### 2.2 グループID（例: `A011`）＝段Aでまとめた後の1行

| 項目 | 内容 |
| --- | --- |
| 何を指すか | 段Aで1つにまとめた行の集まり。**集約後の記録の1行**にあたる |
| 形 | `A` ＋ 通し番号（3桁）。A001, A002, … |
| 番号の付け方 | 行を時刻順に見ていき、新しいグループを作った順 |
| 何行入るか | 1行以上。まとめる相手がいなかった行も、1行だけのグループになる。そのため、全グループを並べると段Aの後の記録の全行になる |
| いつ作るか | ステップ2（段A） |

例: `A011` は `w003-l02` と `w004-l01` の2行をまとめたものです。

```
A011  [62.5–85.0]
  ├─ w003-l02  [62.5–77.5]  man in a navy suit ... speaks outside a building
  └─ w004-l01  [80.0–85.0]  person in a dark gray suit ... speaks outside a building
```

### 2.3 人物ID（例: `P04`）＝同じ人と判定した行の集まり

| 項目 | 内容 |
| --- | --- |
| 何を指すか | 段Bで「同じ人」と判定した行の集まり。変数名は `entity` |
| 形 | 種類の文字 ＋ 通し番号（2桁）。人は `P01`, `P02` …、グループ（people, crowd など）は `G01` …、動物は `N01` … |
| 番号の付け方 | 行を時刻順に見ていき、どの既存のIDにもつながらない人が出たときに次の番号を作る。種類ごとに別に数える |
| 付く行 | 主語が人・グループ・動物の行だけ。人のいない行（`view cuts to a building` など）には付かない |
| いつ作るか | ステップ3（段B） |

例: ニュースの `P04` は Rina Gonoi さんで、8行に付きました。

### 2.4 3つのIDの関係

```
行ID（w...）は、必ず1つのグループ（A...）に入る。
行ID（w...）には、人物ID（P...）が0個か1個付く。
グループ（A...）には、中の行に付いた人物IDが集まる（0個以上）。

  A011 ─┬─ w003-l02 ──→ P04
        └─ w004-l01 ──→ P04
  A011 の人物ID = [P04]

  P04 ─→ w001-l03, w002-l01, w002-l02, w003-l02, w004-l01, w004-l03, w004-l04, w005-l01
         （P04 は A006, A007, A008, A011, A013, A014 にまたがる）
```

stage_b.json では、この関係を次の変数で持っています。

| 関係 | 変数 |
| --- | --- |
| 行 → グループ | `lines[].a_group`（stage_a.json では `groups[].member_ids` が逆向き） |
| 行 → 人物ID | `lines[].entity` |
| グループ → 人物ID | `a_groups[].entities` |
| 人物ID → 行 | `entities[].line_ids` |

---

## 3. ステップ1：読み込み

### 入力

記録の `records/<動画>/result.json`。区間ごとに、モデルの出力を読み取った行（開始秒・終了秒・文）が入っています。

### 処理

1. `collect_runs.py` が result.json から、集約に必要な部分だけを取り出して `records.json` に書きます。画像、プロンプト、token数などの大半は捨てます。
2. ステップ2・3のスクリプトが `records.json` を読むとき（`load_trial`）、各行に行IDを付けて、全区間の行を**時刻順**に1つの一覧に並べます。
3. frame の時刻の間隔（隣り合う frame の時刻の差の中央値）を計算し、`frame_interval` とします（ニュースでは 2.52秒）。

### 出力：行（以後のステップで使う形）

```json
{"id": "w003-l02", "window": 3, "start": 62.5, "end": 77.5,
 "text": "man in a navy suit with short brown hair and a white shirt speaks outside a building",
 "from_window_start": false, "to_window_end": true}
```

| 変数 | 意味 |
| --- | --- |
| `id` | 行ID（2.1） |
| `window` | 区間の番号（0から） |
| `start` / `end` | 開始・終了の秒。終了は「最後に見えた frame の時刻」 |
| `text` | モデルが書いた文（`EVENT:` の後ろの部分） |
| `from_window_start` / `to_window_end` | 区間の最初の frame から始まるか、最後の frame で終わるか。持ち回すだけで、判定には使わない |

---

## 4. ステップ2：段A（`stage_a.py`）

### 入力

ステップ1の行の一覧（時刻順）と `frame_interval`。

### 処理の全体

行を時刻順に1行ずつ取り出し、次の6つを行います。

```
各行について:
  4.1 印（flags）を付ける
  4.2 比べる相手のグループを選ぶ
  4.3 自分と相手の文を、主語と述語に分ける
  4.4 文を単語の列にする
  4.5 近さ（seq）を測る
  4.6 まとめるか決める → 既存のグループに入る or 新しいグループ（A...）を作る
全行が終わったら:
  4.7 各グループの代表の文と印を決める
```

### 4.1 印（`flags`）を付ける

行の文に、正規表現で次の3種類の印を付けます。印を付けても行は消しません。

| 値 | 付く条件 | 例 |
| --- | --- | --- |
| `scene_cut` | 文頭が「(the) view / camera / scene / shot / video ＋ cuts / switches / changes / shifts ＋ to」、または文全体が `black screen` / `white screen` / `blank screen` | `view cuts to a crowd of reporters …` |
| `continuation` | 文のどこかに `continues` / `keeps` / `still` がある | `… continues to whisk …` |
| `state_only?` | 文頭から単語が続いたあとに「is / are ＋ shown / seen / visible / displayed / in / on / inside / filled / placed / lying / sitting on」がある | `stone sign … is shown outside a building` |

使っている正規表現:

```python
_CUT_PREFIX = re.compile(r"^(the\s+)?(view|camera|scene|shot|video)\s+(cuts|switches|changes|shifts)\s+to\s+")
_CONTINUES  = re.compile(r"\b(continues|keeps|still)\s+(to\s+)?")
_STATE_ONLY = re.compile(r"^[\w\s,'\"-]*?\b(is|are)\s+(shown|seen|visible|displayed|in|on|inside|filled|placed|lying|sitting on)\b")
```

- `state_only?` の「?」は候補という意味です。動作の文の中の `who is in …` にも当たりえます。
- 印による処理の違いは1つだけです。`continuation` の行は、4.6 のしきい値が 0.8 から 0.5 に下がります。

### 4.2 比べる相手のグループを選ぶ

すでに作ったグループのうち、**グループの終わり（`end`）が、今の行の始まり（`start`）から `gap_seconds` 以内**のものすべてと比べます。

- `gap_seconds` ＝ `frame_interval` × 1 ＋ 0.05 ＝ 2.57秒（ニュース）。つまり frame 1枚分の間隔です。
- 区間の境目は関係ありません。w003 の最後の行と w004 の最初の行も比べます。
- 相手のグループに複数の行が入っていれば、その全部の行と比べ、いちばん近い行の値を使います。

### 4.3 主語と述語に分ける（`split_subject`）

文を「主語（誰が）」と「述語（何をしたか、残り全部）」に分けます。文法の解析器は使わず、次の規則です。

1. 下の 4.4 の前処理（小文字にする、`view cuts to` などを外す）をした文を単語に分けます。引用符の中（`"SEEK DISCOMFORT"`）は1語、コンマも1語です。
2. **主語の中心**を探します。最初の8語の中で、次の一覧にある語です。
    - 人: man, woman, person, boy, girl, child, kid, baby, gentleman, lady, reporter, chef, hand, hands
    - グループ: men, women, people, children, kids, boys, girls, couple, group, crowd, reporters
    - 動物: dog, cat, bird, horse
    - 見つからなければ「主語なし」で、文全体を述語として扱います。
3. 中心から右へ延ばし、次のどれかが出たら止めます。そこまでが主語です。
    - 動詞の一覧の語（walk, stand, sit, talk, speak, run, dance, hug, wave, smile, look, hold, enter, play, eat, ride, jump, watch, pose, is, are, was, were, who, while など）
    - `-ing` で終わる語（服や髪の語を除く）
    - `-s` で終わる語（ただし glasses, pants, jeans などの一覧の語と、直前が a / the / with / in / and / of / 色の語のときは除く）
    - コンマ（ただし直後が色・髪の語・with・and・a なら止めない）
4. 主語の途中に `and` があり、その直後が上の一覧の名詞なら、そこから先を **2人目（`others`）** として主語から切り離します。
5. 主語の後ろ全部が述語です。2人目の部分（`and man in …`）は述語からも外します。

例:

```
man in a navy suit with short brown hair and a white shirt speaks outside a building
→ 主語: man in a navy suit with short brown hair and a white shirt
   （and の直後は white で、一覧の名詞ではないので2人目ではない）
   （speaks は -s で終わり、直前が shirt なので、ここで止める）
→ 述語: speaks outside a building

woman in a black coat with long black hair and a yellow face mask and man in a navy suit ... walk away from camera ...
→ 主語: woman in a black coat with long black hair and a yellow face mask
→ 2人目（others）: man in a navy suit ...
→ 述語: walk away from camera ...
```

### 4.4 文を単語の列にする（`strip_prefixes` → `content_tokens`）

比べる前に、文を次のように変えます。

1. 小文字にし、前後の空白と末尾のピリオドを取ります。
2. 文頭の `view cuts to` などを消します（4.1 の `_CUT_PREFIX`）。
3. 文中の `continues to` / `keeps` / `still` を消します（4.1 の `_CONTINUES`）。
4. 英数字だけを単語として取り出します（記号は捨てる）。
5. 機能語を捨てます: a, an, the, of, with, in, on, at, to, and, is, are, its, it, into, onto, from, by, for, while, as, her, his, their, them, that, this, some, who, which, there, be, being
6. 語尾を雑に落とします。4文字より長い語から、-ing / -es / -ed / -s を1つ外します。

例:

```
述語 "speaks outside a building" → [speak, outside, build]
```

### 4.5 近さを測る（`seq`、`jaccard`、`subject`）

2つの単語の列から、次の3つの数を作ります。

| 変数 | 何を測るか | 計算 |
| --- | --- | --- |
| `seq` | 述語どうしの近さ（**判定に使う**） | Python の `difflib.SequenceMatcher(None, 列1, 列2).ratio()`。同じ順に並ぶ共通の語の数 × 2 ÷ 両方の語の数の合計。0〜1 |
| `subject` | 主語どうしの近さ | 主語の単語の列で、同じく `seq` を計算 |
| `jaccard` | 述語の語の集合の重なり（分析用、判定には使わない） | 共通の語の数 ÷ どちらかにある語の数 |

`subject` が 0.5 未満のときは、`seq` を 0 にします（別の人の行は、述語が同じでもまとめない）。

### 4.6 まとめるか決める

次の3つをすべて満たすとき、今の行を相手のグループに入れます。

| 条件 | しきい値の変数 | 値 |
| --- | --- | --- |
| `seq`（述語の近さ）がしきい値以上 | `tau`（`continuation` の行は `tau_cont`） | 0.8（0.5） |
| `subject`（主語の近さ）がしきい値以上（4.5 で `seq` を 0 にすることで判定） | `tau_subject` | 0.5 |
| 数の語の集合が同じ | — | 数の語: 数字、one〜ten、another、more、several、many |

- 入れられるグループが複数あれば、`seq` がいちばん高いグループに入れます。
- 入れたら、グループの `start` / `end` を広げ、`scores` と `reasons` に記録します。
- どのグループにも入れなければ、次の番号で新しいグループ（`A...`）を作ります。

### 4.7 各グループの代表の文と印を決める

全行が終わったら、グループごとに次を決めます。

| 変数 | 決め方 |
| --- | --- |
| `text`（代表の文） | グループの中で、4.4 の単語の列が**いちばん長い行**の文をそのまま使う |
| `flags` | 中の行の印をすべて合わせたもの。中の行の主語の性別の語（man / woman など）が食い違えば `gender_conflict` を足す |
| `member_ids` | 中の行の行ID |

### 出力：stage_a.json

```json
{"source": "<入力の records.json のパス>",
 "videos": [
   {"question_id": "BtaVRhoLpC0_0", "frame_interval": 2.52, "gap_seconds": 2.57,
    "records": [ ...行の一覧... ],
    "groups":  [ ...グループの一覧... ],
    "params":  {"tau": 0.8, "tau_cont": 0.5, ...}}
 ]}
```

`records`（行の一覧）: ステップ1の行に `flags` を足したもの。行は1つも消えません。

```json
{"id": "w003-l01", "window": 3, "start": 60.0, "end": 60.0,
 "text": "stone sign with carved Japanese characters \"裁判所\" is shown outside a building",
 "from_window_start": true, "to_window_end": false, "flags": ["state_only?"]}
```

`groups`（グループの一覧）:

```json
{"id": "A011", "start": 62.5, "end": 85.0,
 "text": "man in a navy suit with short brown hair and a white shirt speaks outside a building",
 "member_ids": ["w003-l02", "w004-l01"],
 "flags": [],
 "scores": [{"line": "w004-l01", "with": "w003-l02", "seq": 1.0, "jaccard": 1.0, "subject": 0.533}],
 "reasons": ["same_text+cross_window"]}
```

| 変数 | 意味 |
| --- | --- |
| `id` | グループID（2.2） |
| `start` / `end` | 中の行全体の最初の開始秒と最後の終了秒 |
| `text` | 代表の文（4.7） |
| `member_ids` | 中の行の行ID。最初の1つが、グループを作った行 |
| `flags` | 4.7 |
| `scores` | 2行目以降を入れたときの値。`line` が入れた行、`with` が比べた相手の行、`seq` / `jaccard` / `subject` は 4.5 の値 |
| `reasons` | 2行目以降を入れた理由。`same_text`（`seq` が 0.8 以上）、`continuation`（`continuation` の行で `seq` が 0.5〜0.8）。区間をまたいだら `+cross_window` が付く |

### 例（ニュース）

```
w003-l02 [62.5–77.5]  主語 man in a navy suit ...          述語 speaks outside a building
w004-l01 [80.0–85.0]  主語 person in a dark gray suit ...  述語 speaks outside a building
  時刻の間: 80.0 − 77.5 = 2.5秒 ≤ 2.57 → 比べる
  seq = 1.0（[speak, outside, build] が完全一致） ≥ 0.8
  subject = 0.533 ≥ 0.5
  数の語: どちらもなし
  → w004-l01 を A011 に入れる。A011 = [62.5–85.0]
  → 代表の文: w003-l02（単語の列が長い）

w004-l03 [87.5–87.5]  述語 stands outside a building
w004-l04 [90.0–92.5]  述語 speaks outside a building
  seq = 0.667 < 0.8 → 入れない。w004-l04 は新しいグループ
```

結果: 27行 → 23グループ。

---

## 5. ステップ3：段B（`stage_b.py`）

### 入力

ステップ2の stage_a.json（行の一覧 `records` とグループの一覧 `groups`）。

### 処理の全体

行を時刻順に1行ずつ取り出し、次を行います。

```
各行について:
  5.1 主語（subject）を取り出す                 → なければ status = no_subject で終わり
  5.2 主語を見た目の欄（appearance）に分ける    → 見た目の値がなければ status = weak で保留
  5.3 既存の人物IDそれぞれと比べる（points、conflicts）
  5.4 つなぐか決める → 既存のIDにつなぐ（matched） or 新しいID（new）
全行が終わったら:
  5.5 保留（weak）の行に、段Aのグループから人物IDを受け継ぐ（inherited / unresolved）
  5.6 人物IDごとの一覧（entities）を作る
  5.7 グループごとに人物IDを集める（a_groups）
```

### 5.1 主語を取り出す（`subject`）

4.3 と同じ関数（`subject_of`）で主語を取り出し、次の変数を作ります。

| 変数 | 意味 | 例 |
| --- | --- | --- |
| `phrase` | 主語の句 | `man in a navy suit with short brown hair and a white shirt` |
| `head` | 主語の中心の名詞 | `man` |
| `category` | 中心の名詞の種類。`person` / `group` / `animal` | `person` |
| `gender` | 中心の名詞から決めた性別。man, men, boy … → `male`、woman, women, girl … → `female`、person, hand などは null | `male` |
| `attributes` | 主語の中の、色・服・髪の語と引用符の語の一覧 | `[brown, hair, navy, shirt, short, suit, white]` |
| `others` | 2人目の主語（4.3 の手順4）。いなければ null | null |

主語がなければ（人・グループ・動物の名詞がない）、`subject` は null、`status` は `no_subject` になり、この行の処理は終わりです。

### 5.2 見た目の欄に分ける（`appearance`）

`phrase` の単語を、決まった一覧と照らし合わせて、次の欄に分けます（`appearance_of`）。

| 欄 | 作り方 | 例 |
| --- | --- | --- |
| `garments` | 上の服の語（shirt, t-shirt, jacket, coat, suit, dress, sweater, fleece, uniform, apron, sleeve など）ごとに、直前3語までの色の語を集める | `{"suit": ["navy"], "shirt": ["white"]}` |
| `hair_color` | `hair` の直前の色の語を系統に直す。blond → light、brown / black / dark → dark、red → red、gray / white → gray | `dark` |
| `hair_length` | `hair` の直前の short / long / medium / shoulder-length。bald / shaved があれば bald | `short` |
| `hair_style` | `hair` の直前の curly / wavy / straight / slicked-back / spiky など | null |
| `beard_type` | stubble → stubble、full / thick beard → full、short beard → short | null |
| `face` | glasses があれば `{"glasses": true}`、beard / mustache / stubble があれば `{"beard": true}`。直前に no があれば false | `{}` |
| `accessories` | 持ち物の語（hat, cap, mask, backpack, glove, bag, watch, tie, bow-tie, headphones, sunglasses など） | `[]` |
| `text_marks` | 引用符の中の文字を単語に分けたもの | `["seek", "discomfort"]` |

服・髪の色・顔・持ち物・服の文字のどれにも値がなければ（`person` だけ、など）、`status` を `weak` にして保留し、5.5 で扱います。ただし、直前の人の行と `phrase` が一字一句同じなら保留せず 5.4 へ進みます。

### 5.3 既存の人物IDと比べる（`points`、`conflicts`）

既存の人物IDのうち、`category` が同じものすべてと比べます。

まず、そのIDの**代表の見た目（`profile`）**を作ります。そのIDに付いた行の `appearance` を集め、欄ごとにいちばん多い値を取ったものです。

次に、今の行の `appearance` と `profile` を欄ごとに比べ（`compare_appearance`）、次の変数を作ります。

| 変数 | 意味 |
| --- | --- |
| `conflicts` | 食い違った欄の一覧 |
| `points` | 一致した欄の点数の合計 |
| `matched` | 一致した欄の一覧（人が読む用） |
| `garment_match` | 服が1つ以上一致したか |
| `text_match` | 服の文字が一致したか |
| `accessory_match` | 両方とも服の欄が空で、持ち物が一致したか |

欄ごとの判定:

| 欄 | 一致（点数） | 食い違い |
| --- | --- | --- |
| 服 | 同じ種類の服で、色の系統が重なる：2点 | 同じ種類の服で、色の系統が重ならない |
| 髪の色 | 同じ：1点 | 違う |
| 髪の長さ | — | long と short、bald とそれ以外 |
| 髪型 | 系統が重なる：1点 | 重ならない（wavy は curly とも straight とも重なる） |
| ひげの形 | — | stubble と full |
| 眼鏡・ひげの有無 | 両方 true：1点 | true と false |
| 持ち物 | 共通の持ち物1つにつき1点 | — |
| 服の文字 | 共通の単語がある：3点 | 両方にあって共通の単語がない |

服の色の系統: black → dark、navy → dark と blue、dark → dark、gray → gray、beige → beige と brown、pink → pink と red など。そのため、black・navy・dark gray のスーツどうしは、dark で重なるので一致になります。

性別（`gender`）は比べません。

### 5.4 つなぐか決める（`entity`、`status`、`score`）

`conflicts` が1つでもあるIDにはつなぎません。食い違いがないIDについて、次のどれかに当たればつなぎます。

| 種類 | 条件 | 例 |
| --- | --- | --- |
| 強い手がかり | `text_match`（服の文字が一致）、または `accessory_match`（服の欄が空で持ち物が一致）、または「服が一致し、行の場所の句がそのIDのどれかの行の場所の句と同じ」 | `"SEEK DISCOMFORT"`、手袋、`outside a building` |
| ありふれた手がかり | 服が一致して `points` が3以上、かつ、直前の人の行がそのIDで、今の行が `scene_cut` でない | 前の行の人と、同じ服・同じ髪 |
| 直前と同じ呼び方 | 直前の人の行と `phrase` が一字一句同じで、今の行が `scene_cut` でない | 同じ区間で続けて出る人 |

- **場所の句**（`place_of`）: 主語より後ろで、最後に出る in front of / outside / inside / against / near / beside / next to / at / on / in の後ろの単語。同じとみなすのは、色以外の単語が2つ以上共通、または色以外の単語の集合が同じとき。例: `outside a building` → `[build]`。
- **直前の人の行**: 主語が人の行のうち、いちばん最近に人物IDが付いた行。見た目の値がない人の行が間に入ると、リセットされます。
- 当たるIDが複数あれば、`points` がいちばん高いIDにつなぎます。

結果として、行に次の変数が付きます。

| 変数 | 値 |
| --- | --- |
| `entity` | つないだ人物ID。どれにも当たらなければ新しい人物IDを作ってそれを入れる |
| `status` | 既存のIDにつないだら `matched`、新しいIDを作ったら `new` |
| `score` | `{"points": 点数, "matched": [一致した欄, …]}`。直前と同じ呼び方でつないだときは `points` 0、`matched` は `["直前の人と呼び方が同じ"]` |

### 5.5 保留した行の扱い（`inherited`、`unresolved`）

5.2 で `weak`（見た目の値がない）にした行について、その行が入っている段Aのグループ（`a_group`）を見ます。

- グループの他の行に付いた人物IDが**ちょうど1つ**なら、それを受け継ぎます。`status` は `inherited`。
- 0個か2個以上なら、人物IDは付けません。`status` は `unresolved`。

### 5.6 人物IDごとの一覧を作る（`entities`）

人物IDごとに、付いた行を集めて次の変数を作ります。

| 変数 | 意味 | 例（P04） |
| --- | --- | --- |
| `id` | 人物ID | `P04` |
| `category` | `person` / `group` / `animal` | `person` |
| `line_ids` | このIDが付いた行ID（時刻順） | `[w001-l03, w002-l01, …, w005-l01]`（8行） |
| `appearances` | 写っていた時間帯。行の時刻範囲を並べ、間が `appear_gap_seconds`（frame 2枚分＋0.05＝5.09秒）以下ならつなぐ | `[[27.5, 50.0], [62.5, 112.5]]` |
| `genders` | 行の `gender` の回数 | `{"female": 3, "male": 2}` |
| `gender_conflict` | `genders` に2種類以上あるか | `true` |
| `attributes` | 行の `attributes` の語の回数 | `{"hair": 8, "short": 8, "suit": 8, …}` |
| `phrases` | 行の `phrase`（呼び方）の回数 | `{"person in a dark gray suit with short brown hair": 3, …}` |

### 5.7 グループごとに人物IDを集める（`a_groups`）

段Aのグループ1つずつに、中の行に付いた人物IDを集めて付けます。**これが集約し終わった記録**です。

| 変数 | 意味 |
| --- | --- |
| `id` | グループID（段Aと同じ） |
| `start` / `end` | 段Aと同じ |
| `text` | 段Aの代表の文（書き換えない） |
| `entities` | 中の行に付いた人物IDの一覧（重複なし）。人のいない行だけのグループでは空 |
| `flags` | 段Aと同じ |

### 出力：stage_b.json

```json
{"source": "<入力の stage_a.json のパス>",
 "videos": [
   {"question_id": "BtaVRhoLpC0_0", "appear_gap_seconds": 5.09,
    "lines":    [ ...行の一覧（5.1〜5.5）... ],
    "entities": [ ...人物IDの一覧（5.6）... ],
    "a_groups": [ ...集約し終わった記録（5.7）... ],
    "params":   {"method": "slots", "min_points": 3, ...}}
 ]}
```

`lines` の1行:

```json
{"id": "w003-l02", "window": 3, "start": 62.5, "end": 77.5,
 "text": "man in a navy suit with short brown hair and a white shirt speaks outside a building",
 "a_group": "A011",
 "subject": {"phrase": "man in a navy suit with short brown hair and a white shirt",
             "head": "man", "category": "person", "gender": "male", "others": null,
             "attributes": ["brown", "hair", "navy", "shirt", "short", "suit", "white"],
             "appearance": {"garments": {"suit": ["navy"], "shirt": ["white"]},
                            "hair_color": "dark", "hair_length": "short", "hair_style": null,
                            "beard_type": null, "face": {}, "accessories": [], "text_marks": []}},
 "entity": "P04",
 "status": "matched",
 "score": {"points": 5, "matched": ["navy suit", "white shirt", "髪 dark", "同じ場所 build"]}}
```

| 変数 | 意味 |
| --- | --- |
| `id` 〜 `text` | ステップ1と同じ |
| `a_group` | この行が入っている段Aのグループ |
| `subject` | 5.1・5.2。主語がなければ null |
| `entity` | 付いた人物ID。付かなければ null |
| `status` | 下の表 |
| `score` | 5.4。`matched` のときだけ値がある |

`status` の値（最終的に残るもの）:

| 値 | 意味 | `entity` |
| --- | --- | --- |
| `no_subject` | 主語がない（人・グループ・動物の名詞がない） | null |
| `new` | どの既存IDにもつながらず、新しい人物IDを作った | 新しいID |
| `matched` | 既存の人物IDにつないだ | 既存のID |
| `inherited` | 見た目の値がなく、段Aのグループから受け継いだ | 受け継いだID |
| `unresolved` | 見た目の値がなく、受け継ぐIDも決まらなかった | null |

### 例（ニュース）

```
00.0 w000-l01 woman in a black coat with long black hair and a yellow face mask ...
     → IDがまだない → 新しい P01（new）
07.5 w000-l02 man in a navy suit with short black hair and a white face mask ...
     → P01 と比べる: 髪 short ≠ long で食い違い → 新しい P02（new）
20.0 w001-l01 woman in a dark gray suit with long black hair and a brown backpack ...
     → P01: coat と suit で服の一致がない／P02: 髪 long ≠ short → 新しい P03（new）
25.0 w001-l02 view cuts to a building entrance ... → 主語なし（no_subject）
27.5 w001-l03 woman in a dark gray suit with short brown hair and a white shirt speaks outside a building
     → P03: 髪 short ≠ long で食い違い → 新しい P04（new）
40.0 w002-l01 woman in a dark blue suit with short dark hair and a white shirt ... outside a building
     → P04: suit（dark で重なる）2点、shirt white 2点、髪 dark 1点 ＝ 5点、食い違いなし
        ＋ 場所 [build] が P04 の行と同じ → 強い手がかり → P04（matched）
45.0 w002-l02 （直前の人の行と phrase が同じ）→ P04（matched、points 0）
60.0 w003-l01 stone sign ... → 主語なし（no_subject）
62.5 w003-l02 man in a navy suit with short brown hair and a white shirt ... outside a building
     → P04: 5点、食い違いなし、同じ場所 → P04（matched）。gender は比べないので man でもつながる
```

最終結果: 人物ID 6個（P01〜P06）、主語なし 5行、未決 1行。P04 は8行で、`genders` が female 3・male 2 なので `gender_conflict` が true。

---

## 6. ステップ4：評価（`eval_ids.py`）

### 入力

stage_b.json と、目で作った正解 `ground_truth_ids.json`（今は5本）。正解には、時刻の範囲ごとに、そこに写っている人の名前が書いてあります。

### 処理と出力

1. 行ごとに、その行の時刻（±0.1秒）に写っている正解の人の集合を作ります。同じ時刻に2人写っていれば、2人とも入ります。
2. 人物IDごとに、付いた行の正解の集合を並べ、**全部の行に共通する人（`common`）**を求めます（正解の集合が空の行は除く）。
3. 次の3つを数えて `stage_b_eval.md` に書きます。

| 数 | 数え方 |
| --- | --- |
| 入れ替え | 正解のある行が2行以上あるのに、`common` が空の人物ID の数（別人を同じIDにした）。P・G・N すべてが対象 |
| 誤ったIDの行 | 入れ替えのIDの中で、いちばん多く出る正解の人が写っていない行の数 |
| 分かれ | 2つ以上の人物ID（P のみ）の `common` に入っている正解の人の数 |

注意: `common` は「その時刻に写っている人」から作るので、2人が一緒に写る場面では、もう1人も `common` に入ることがあります。そのため、`stage_b_eval.md` の「分かれ」の一覧には、その人の行ではないIDも並ぶことがあります（ニュースの companion に P01, P02, P03 が並ぶのはこのため）。

ニュースの結果: IDの数 6、入れ替え 0、誤ったIDの行 0、分かれ 2。正解のない動画は空になります。

---

## 7. 人が読む用のファイル

正本（.json）と同じ内容を表にしたものです。

| ファイル | 中身 |
| --- | --- |
| `stage_a_<動画>.md` | 冒頭: しきい値と件数。第1節: 2行以上のグループと中の行の `seq`。第2節: しきい値の少し手前（0.2以内）でまとめなかった組。第3節: 印の付いた行。第4節: 全グループ（＝段Aの後の記録） |
| `stage_a_pairs.tsv` | 4.2 で比べたすべての組。列: `question_id`, `line`（今の行）, `compared_line`（相手の行）, `group`, `gap_s`（時刻の間）, `seq`, `jaccard`, `continuation`, `cross_window`, `threshold`, `merged`（まとめたら1）, `count_change`（数の語の食い違い）, 両方の文 |
| `stage_a_summary.md` | 動画ごとの件数: `l0_lines`（元の行数）, `a_groups`（グループ数）, `merged_groups`（2行以上のグループ数）, `lines_absorbed`（ほかの行に吸収された行数）, `cross_window_merges`, `continuation_merges`, 各印の数 |
| `stage_b_<動画>.md` | 冒頭: 方法と件数。第1節: 人物IDの一覧（`entities`）。第2節: 人物IDごとの行と `status`・一致した欄。第3節: 一致点はあったがつながなかった組。第4節: `gender_conflict` のID。第5節: 人物IDが付かなかった行。**第6節: 集約し終わった記録（`a_groups`）** |
| `stage_b_pairs.tsv` | 5.3 で比べたすべての組。列: `line`, `entity`（比べたID）, `points`, `conflicts`, `merged`, `matched`, `profile`（IDの代表の見た目）, 今の行の主語, そのIDの最初の行の主語 |
| `stage_b_summary.md` | 動画ごとの件数: `lines`, `no_subject`, `with_attrs`（new＋matched）, `inherited`, `unresolved`, `P_ids` / `G_ids` / `N_ids`（IDの数）, `ids_reappearing`（`appearances` が2つ以上のID）, `gender_conflict_ids` |

`stage_b_<動画>.md` の第6節（集約し終わった記録）の一部:

| 段A | 時刻 | ID | 印 | 文（代表） |
| --- | --- | --- | --- | --- |
| A009 | 00:52.5–00:57.5 |  | scene_cut | view cuts to a large building with a stone sign in front that reads "裁判所" |
| A010 | 01:00.0–01:00.0 |  | state_only? | stone sign with carved Japanese characters "裁判所" is shown outside a building |
| A011 | 01:02.5–01:25.0 | P04 |  | man in a navy suit with short brown hair and a white shirt speaks outside a building |
| A012 | 01:27.5–01:27.5 |  | scene_cut | view cuts to a crowd of reporters with cameras and microphones |
