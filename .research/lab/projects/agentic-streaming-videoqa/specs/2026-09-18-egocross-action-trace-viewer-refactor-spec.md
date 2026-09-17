---
date: 2026-09-18
project: agentic-streaming-videoqa
status: approved
topic: egocross-action-trace-viewer-refactor
source: 2026-09-18 user request + standard EgoCross manifest investigation + trace viewer implementation
last_updated: 2026-09-18
---

# EgoCross action trace 選定・viewer単一frame表示 spec

## 目的

現行viewerのcounting問題中心のlegacy traceではなく、EgoCross標準manifestから選定した以下の三種類の問題について、**各recordの画像列を省略せず全frame** `--agent` で処理し、frame単位の推論traceをviewerで読む。

1. 動作認識（special action identification）
2. action temporal localization
3. 連続動作の推論（action sequence identification）

併せて、現在のviewerでframeを切り替えるたびに観測・state関連カードが残り続けるUI不具合を直す。一つの選択画像に対して、画像・観測・Agent判断・そのframeでのmemory差分だけを一組として表示する。`state_after`全体を別カードで重複表示しない。

これはframe列に対する因果的な観測・状態更新の質的レビューであり、final QA、選択肢回答、accuracy、temporal localizationの正答評価は対象外とする。

## 調査Evidenceと採用record

標準manifestは`/mnt/HDD18TB/hayashi/data/EgoCross/egocross_testbed/egocross_testbed_imgs.json`である。調査時点で、`action sequence identification` は50件、`action temporal localization` は126件、`special action identification` は46件ある。各採用recordの`video_path`全参照画像は存在することを確認した。

| 役割 | record ID | dataset | question type | 質問（原文） | 全frame数 |
| --- | ---: | --- | --- | --- | ---: |
| 動作認識 | 712 | ExtrameSportFPV | special action identification | What action is being performed in the video segment from 7s to 10s? | 5 |
| 時刻局在 | 478 | ENIGMA | action temporal localization | At what approximate timestamp did the operator's right hand perform the second 'contact' with the button within the video segment from 0.00s to 15.00s? | 8 |
| 連続動作 | 823 | ExtrameSportFPV | action sequence identification | What sequence of actions is performed in the time segment from 0s to 20s? | 8 |

合計21 frameである。各recordは質問の種類を代表する表示対象として固定し、実行時に検索結果や順序を変更しない。

standard manifestにはframeごとの絶対timestampがない。viewerの`relative_timestamp_s`は既存のsampling規則に基づくtrace内相対時刻であり、質問文中の絶対秒数・正解時刻として表示または評価しない。

## 複数問題を一つのbrowserで閲覧する契約

三runはすべて同じ`outputs/2026-09-18-action-trace/`配下に保存する。このdirectoryを一つの`--output-root`としてviewerへ渡し、run selectorからID 712、478、823の結果を切り替える。runごとにserverやbrowser tabを分けない。

```bash
python3 scripts/serve_trace_viewer.py \
  --output-root outputs/2026-09-18-action-trace \
  --host 127.0.0.1 --port 8000
```

selectorの各項目にはrun IDだけでなく、manifest検証済みのrecord ID、dataset、question typeを併記する。表示順は動作認識（712）→時刻局在（478）→連続動作（823）とし、同じrecordの複数runがある場合はrun ID降順で新しいrunを先に置く。壊れたrunと、対象外recordの既存runは利用不能または通常runとして一覧に残すが、採用三問題の表示順を崩さない。

## 現在の不具合と原因

現行`viewer_static/viewer.js`の`selectFrame`は`#selected-frame`（画像カード）だけを削除する。その後にappend済みの「観測結果」「記憶更新」「更新後state」「詳細・再現性情報」は削除されないため、frameを切り替えるたびに前frameの内容が残り、同じ種類の情報が複製される。

この変更は表示refactorであり、既存のtrace、metadata、Agent state、API、画像配信、Qwen実行経路を変更しない。

## 採用するviewer表示契約

### runごとに一度だけ表示する情報

- run選択、run ID、mode、record ID、frame数、sampling FPS。
- 「最終QA・accuracyではなく、途中の因果traceである」説明。
- manifest hashが検証済みのときだけ、質問、選択肢、dataset、question type。
- frame navigator（frame番号、trace内相対時刻、action名、error状態）。

### 選択frameに一度だけ表示する情報

`#frame-detail` の単一コンテナを作り、frame選択時にそのコンテナ全体を置換する。コンテナ内の表示順は次に固定する。

1. **Frame**: frame番号、trace内相対時刻、入力画像。画像欠損は同じ位置のplaceholderに置換する。
2. **観測**: 現在画像一枚から生成した`observation`原文。decode-onlyでは「観測・Agent判断はこのrunにはない」と表示する。
3. **Agent判断**: `action`、`confidence`、`reason`、および`state_before` / `state_after`から決定的に得る**一つのmemory差分**だけを表示する。ADD / UPDATE / KEEP / FLAG_UNCERTAIN / CLOSE_EVENTの平易な説明もこの領域に含める。
4. **状態・error**: state連続性警告、legacy provenance注意、frame errorを必要時だけ同じコンテナ内に表示する。model/schema/timing/logical path/raw policy responseは折り畳み`details`に置く。

`更新後state`カード、event ledger全件カード、同じ差分を繰り返す別の「記憶更新」カードは作らない。選択frame以外の本文はDOMに残さない。trace由来文字列は引き続き`textContent`で表示し、`innerHTML`を使わない。

新規v2 traceではevent provenanceを差分・detailsに含めてよい。legacy traceでは開始・最終根拠frameを表示せず、legacy注意だけを出す既存互換を維持する。

## 実行するAgent trace

UI実装・自動test・commitが完了し、cleanな最終branch HEADを基準にした後で、次の三つを**一件ずつ**実行する。`--max-frames`は指定しない。これによりmanifestに記録された全画像列を処理する。

Qwenをload・使用するpreflightと各`--agent` commandは、必ず`CUDA_VISIBLE_DEVICES=2,3`を付ける。この環境変数により物理GPU 2・3だけをプロセスへ公開し、既存CLIの`device_map=auto`がその可視deviceを用いる。GPU番号はshell実行時だけに与え、source、config、run metadataへ固定・保存しない。

```bash
cd /mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation

CUDA_VISIBLE_DEVICES=2,3 .venv/bin/python scripts/check_qwen_runtime.py

CUDA_VISIBLE_DEVICES=2,3 .venv/bin/python scripts/observe_egocross.py \
  --record-id 712 --agent --max-new-tokens 256 \
  --output-root outputs/2026-09-18-action-trace

CUDA_VISIBLE_DEVICES=2,3 .venv/bin/python scripts/observe_egocross.py \
  --record-id 478 --agent --max-new-tokens 256 \
  --output-root outputs/2026-09-18-action-trace

CUDA_VISIBLE_DEVICES=2,3 .venv/bin/python scripts/observe_egocross.py \
  --record-id 823 --agent --max-new-tokens 256 \
  --output-root outputs/2026-09-18-action-trace
```

固定条件は既存Agentと同じである。観測には質問・選択肢・現在画像一枚だけを渡す。policyにはprevious text stateとcurrent-frame observationだけを渡す。過去画像、future frame、final answerを入力に渡さない。Qwen model ID、generation、state schema、event provenance契約はこの変更のために変えない。

各run後、JSONL行数が順に5、8、8であること、`frame_index`が`0..N-1`であること、全frameの`observation`・`parsed_decision`・`state_before`・`state_after`が存在し、state連続性とmetadataのmanifest hash / code revisionが正しいことを確認する。一件でもerrorがあれば後続recordを自動実行しない。

## Branch・commit規約

基準repositoryは`/mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation`、開始基準は現行のclean HEAD `647701e`（`feat/step-11-trace-viewer-verification`）とする。`main`、既存branch、既存traceを変更しない。push、PR、mergeは対象外である。

```text
feat/step-11-trace-viewer-verification
└── feat/step-12-action-trace-viewer-layout
    └── feat/step-13-action-trace-viewer-verification
```

- **1 Step = 1 branch**。Step末尾testが成功してから直前StepのHEADから次branchを作る。
- **1 micro-step = 1 commit**。commit titleは下表どおりとする。
- commit本文は`対象`、`変更`、`理由`、`検証`、`影響`、`次`を日本語で各一行含める。
- `outputs/`、dataset画像、model weight、credentialをcommitしない。GPU inference、dataset更新、既存artifactの書換えをcommit工程に含めない。

### Step 12: single-frame viewer layout

**Branch:** `feat/step-12-action-trace-viewer-layout`

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 12.1 | `refactor: isolate selected trace frame detail` | 画像・観測・Agent判断・detailsを一つの`#frame-detail`へ収め、選択変更時に前frameの全表示を置換する。 |
| 12.2 | `refactor: render compact agent frame judgment` | action、confidence、reason、単一memory差分を一領域へ統合し、`更新後state`全体と重複カードを除く。 |
| 12.3 | `feat: label action trace questions in viewer` | 一つのrun selectorで採用三問題を固定順に切替え、record ID・dataset・question typeを併記する。trace内相対時刻と質問文の絶対秒を混同しない説明を置く。 |
| 12.4 | `test: cover selected frame detail replacement` | frame切替後に選択frame以外の観測・判断・detailsがDOMに残らないこと、全action・legacy・error表示をtestする。 |

**Step末尾test:** `python3 -m pytest -q`、`python3 -m compileall egocross_observation scripts`、synthetic loopback browser smoke。

### Step 13: action trace verification and usage guide

**Branch:** `feat/step-13-action-trace-viewer-verification`

| Micro | Commit title | 完了条件 |
| --- | --- | --- |
| 13.1 | `test: cover action trace record selection` | standard manifestからID 712 / 478 / 823のquestion type、frame数、全image path存在をread-only testまたは検証scriptで固定する。 |
| 13.2 | `test: cover compact action trace viewer flow` | 同じoutput rootの複数runをHTTP経由で選択し、frame切替、画像、観測、Agent判断、memory差分、errorとlegacy表示を検証する。 |
| 13.3 | `docs: document action trace viewer workflow` | 採用record、全frame実行、viewer上の相対時刻の意味、Qwen実行とartifact非変更をREADME・利用文書に記載する。 |

**Step末尾test:** `python3 -m pytest -q`、`python3 -m compileall egocross_observation scripts`、`python3 scripts/serve_trace_viewer.py --help`、合成fixtureのloopback手動browser受入。

## 対象外・互換性

- final QA、回答選択、accuracy、temporal localization正答の採点・表示。
- prompt / model / Reducer / state schemaの研究上の変更。
- run比較、live inference、ブラウザからのQwen実行・停止・削除、外部公開。
- standard manifest、dataset画像、既存run、既存JSONL / metadataの移行・書換え。
- 既存のdecode-only / observe / agent traceの読取り互換性。legacy traceはevent frameを隠して表示する。

## 成功条件

### 実装・viewer

- frame切替後、DOMに選択frame一組だけが存在し、前frameの観測・判断・detailsは残らない。
- agent frameでは画像、観測、action / confidence / reason、単一memory差分を一回ずつ表示する。
- `state_after`全体やevent ledgerの重複表示がない。
- 一つのbrowser・server・output rootで、ID 712 / 478 / 823のrunをselectorから切り替えられ、各runのframe詳細が一組だけ表示される。
- action question typeとtrace内相対時刻の意味が読め、質問文の絶対timestampを結果として偽装しない。
- HTML特殊文字、画像欠損、error、legacy trace、decode-only / observeの既存安全表示が回帰しない。

### 新規trace（GPU実行が明示許可された後）

- ID 712 / 478 / 823について、合計21 frameの新規v2 Agent traceが専用output rootに作られる。
- Qwen runtime preflightと三つのAgent runが`CUDA_VISIBLE_DEVICES=2,3`で起動される。
- 各frameの`error`がnullで、観測、parsed decision、連続state、metadataが揃う。
- viewerで三runの全frameを同じbrowserから切替え、各frameの画像・観測・Agent判断・一つのmemory差分を読める。

## Gate

### Blocking

- 21 frameのAgent実行には、実装完了後にユーザーからGPU利用を含む明示許可が必要である。実装許可と実run許可は分離する。

### Non-blocking

- 見出し・色・余白は既存viewer styleに合わせる。
- 画像横幅やnavigatorの細部は、単一frame表示と既存accessibilityを損なわない範囲で既存styleに合わせる。
- GPU物理番号2・3はshell環境変数でのみ指定し、source、config、metadataへ固定しない。

## Approval Gate

実装開始には、次を明示承認する必要がある。

1. ID 712（動作認識）、478（action temporal localization）、823（action sequence）の全21 frameを表示対象として固定すること。
2. viewerを「選択画像一組の画像・観測・Agent判断・単一memory差分」に縮約し、`state_after`全体カードを廃止すること。
3. 同一browserで三問題を切り替え、Qwen利用時は`CUDA_VISIBLE_DEVICES=2,3`を使うこと。
4. final QA・accuracy・時刻局在の正答評価は追加しないこと。

GPU / Qwen Agent runは、実装承認とは別に、実装完了後の明示許可を必要とする。

## Implementation Handoff

- approved spec: 本文書
- 実装目的: action関連EgoCross traceを全frameで読み、選択frameの情報を重複なく表示するviewerへrefactorする。
- 基準repository/commit: `feat/step-11-trace-viewer-verification` の clean HEAD `647701e`。
- 変更scope: viewer static UI、viewer test、action record選定検証、利用文書。
- 対象外・維持条件: Qwen prompt / model / Reducer変更、final QA、accuracy、既存artifact変更、外部公開を行わない。
- success criteria: 本文のviewer回帰test、同一browserでの三run切替、明示許可後のCUDA_VISIBLE_DEVICES=2,3による21 frame trace検証。
- 許可されている短時間検証: unit / API / static UI / loopback smoke。GPU inferenceは含まない。
- 長時間runの許可状態: 未許可。ID 712 / 478 / 823の全frame Agent runは、CUDA_VISIBLE_DEVICES=2,3を用いる別途明示許可待ち。
- 未検証予定: action推論・時刻局在・連続動作推論の意味的正しさ、およびfinal QA性能。

## 関連記録

- `2026-09-18-egocross-trace-viewer-delivery-plan-spec.md`
- `2026-09-18-egocross-demo-agent-run-spec.md`
- `experiments/2026-09-15-egocross-qwen-local-investigation.md`
