---
date: 2026-10-08
last_updated: 2026-10-08
project: agentic-streaming-videoqa
type: implementation
status: approved
target_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 2a40379cf98f3c6d5c9784d0bcb0439c3577cbbb
supersedes:
  - 2026-10-08-workbench-agent-trace-markdown-spec.md
related_specs:
  - 2026-10-07-workbench-runtime-workflow-record-simplification-spec.md
source_brainstorm:
  - 2026-10-08-server-migration-offline-priorities.md
---

# Workbench Run Artifact / Trace 簡略化 spec

## 1. 目的

現在のRecord v2は新Runを6ファイルへ分けて保存している。

```text
execution_settings.json
resolved_prompts.json
question.json
run_status.json
turns.jsonl
final_answer.json
```

現段階の研究用途では、これらを人間が個別に開く必要性が低く、Answerだけを別artifactへ分離する必然性も小さい。

本specでは、新Runのmachine-readable recordを単一の `result.json` へ統合し、人間確認用の `trace.md` と、Situation Agentへ入力したsampled frameを後から確認するための `frames/` を同じRun directoryへ保存する。

最終的な新Run artifactは次とする。

```text
<OUTPUT_ROOT>/
└── YYYY-MM-DD_HH-MM-SS/
    ├── result.json
    ├── trace.md
    └── frames/
        ├── window-001-frame-001.jpg
        ├── window-001-frame-002.jpg
        └── ...
```

この変更の主目的は、研究者が「このRunで何を実行し、各windowで何を入力し、Situation / Summaryが何を出し、最後に何を回答し、正解したか」を1 directoryだけで追えるようにすることである。

## 2. 現在のユーザー判断

2026-10-08の現在指示として次を採用する。

- Run directory名はrandom hash付きではなく、人間が読める日時を基本とする。
- 現行の設定 / Prompt / Questionを複数fileへ分ける必要はなく、machine-readable resultへまとめる。
- Window結果とFinal Answerも同じmachine-readable resultへ統合する。
- Answer完了後は、予測回答、正解回答、正誤を上位で確認できるようにする。
- 正解ラベルはAgent inferenceへ与えず、評価用経路でのみ取得する。
- sampled frame画像はRun artifactへ永続保存する。
- 現時点ではMarkdownへ画像を埋め込まない。
- MarkdownはSituation / Summary / Answerを人間が確認しやすい表とする。
- BrowserではFinal Answerをwindow履歴から分離し、Run全体のtop-levelな「最終結果」カードとして表示する。
- 最終結果カードにはModel Answer、Correct Answer、正解 / 不正解を表示する。
- 正誤は色だけに依存せず、`✓ 正解` / `✕ 不正解` のtext badgeでも明示する。
- goldを持たないv2 / Legacy等のread-only runは `— 判定不可` と表示してよく、正解を推測しない。

## 3. 現行実装の確認

2026-10-08確認時点:

```text
repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
branch: main
commit: 2a40379cf98f3c6d5c9784d0bcb0439c3577cbbb
```

確認済み:

- Runtime / Workflow / Record v2簡略化は現行mainへ実装済み。
- `RunRecord.create()` は6 fileを生成する。
- completed windowは `turns.jsonl` へappendされる。
- Answer成功後は `final_answer.json` を上書きする。
- JSON file更新はtemp fileからのatomic replaceを既に利用している。
- `RunSession` は各sampled frameからJPEG thumbnailを生成しているが、現在はmemory上の `session.thumbnails` にだけ保持する。
- server再起動後はthumbnailを再表示できない。
- `QuestionSample` は意図的にgold labelを持たない。
- LongVideoBench adapterは元annotationの `correct_choice` を `QuestionSample` へ入れない。
- 現行testでも `QuestionSample` に `correct_choice` が存在しないことを確認している。
- LongVideoBench公式dataloaderでは `correct_choice` を0-based indexとしてchoice letterへ変換している。Workbench側のAnswer `choice_index` は1-basedなので、評価時に明示変換が必要。

## 4. 新Artifact Schema

新しいartifact schemaを **Record v3** とする。

`result.json` のtop-levelに必ず

```json
{
  "artifact_schema_version": 3
}
```

を持つ。

Record v2以前は既存artifactとしてread-onlyで閲覧可能にし、新形式へ自動migrationしない。

## 5. Run directory名

新規Runの標準ID / directory名はlocal wall-clock timeを人間可読にした

```text
YYYY-MM-DD_HH-MM-SS
```

とする。

例:

```text
2026-10-08_15-24-30
```

同一秒に既存directoryが存在する場合だけ、

```text
2026-10-08_15-24-30-2
2026-10-08_15-24-30-3
```

のように小さい連番suffixで衝突回避する。

random hashは通常のRun IDへ付けない。

API / BrowserがRun IDをpath segmentとして扱える現在の文字種制約を維持する。

`created_at` 自体は `result.json` 内でtimezone offset付きISO 8601として保持する。directory名は識別・可読性のための表示IDであり、厳密時刻のSSOTではない。

## 6. result.json

### 6.1 原則

`result.json` は新Runのmachine-readable Single Source of Truthとする。

以下を別fileにしない。

- execution settings
- resolved prompts
- question
- run status
- completed turns
- final answer
- evaluation result

RecordServiceはresult全体を読み、変更対象fieldだけを更新し、temp file -> atomic replaceで保存する。

JSONL appendは新Runでは使用しない。

### 6.2 top-level構造

概念schema:

```json
{
  "artifact_schema_version": 3,
  "run_id": "2026-10-08_15-24-30",
  "status": {},
  "answer": null,
  "question": {},
  "config": {},
  "turns": []
}
```

人間がfileを開いたとき最終結果を上部で確認しやすいよう、`status` と `answer` を `turns` より前に配置する。

JSON object orderへ機械的意味は持たせない。

## 7. status

`status` は現行Record v2の状態契約を保持する。

```json
{
  "state": "ready",
  "current_agent": null,
  "current_turn": null,
  "created_at": "...",
  "started_at": null,
  "finished_at": null,
  "error": null
}
```

許可状態:

- `ready`
- `running`
- `awaiting_next_turn`
- `succeeded`
- `failed`
- `cancelled`

status変更ごとに `result.json` をatomic updateする。

absolute local pathをerrorへ露出しない現行sanitize方針を維持する。

## 8. question

```json
{
  "dataset_id": "longvideobench-validation",
  "question_id": "...",
  "video_id": "...",
  "video_path": "...",
  "duration_seconds": 120.0,
  "question": "...",
  "choices": ["...", "..."]
}
```

Run作成時のQuestion snapshotを保持する。

**gold / correct_choiceはここへ入れない。**

Situation / Summary / Answerが参照するQuestion系inputと、評価用gold labelを明確に分離する。

## 9. config

現在の `execution_settings.json` と `resolved_prompts.json` を `config` へ統合する。

概念形:

```json
{
  "config": {
    "execution": {
      "...": "resolved ExecutionSettings",
      "code_version": "...",
      "settings_hash": "..."
    },
    "prompts": [
      {
        "role": "situation",
        "prompt_id": "...",
        "prompt_hash": "...",
        "prompt_version": 1,
        "body": "...",
        "metadata": {}
      }
    ]
  }
}
```

Prompt bodyはRun開始時のsnapshotを保存する。

各turnのAgent resultへ同じresolved prompt本文を重複保存しない。

turn側には必要なら `prompt_id / prompt_hash / prompt_version` を残し、top-level snapshotへ対応付ける。

## 10. turns

`turns` はJSON arrayとし、**completed windowだけ**を順番に保存する。

概念形:

```json
{
  "turn_index": 0,
  "window": {
    "index": 0,
    "start_seconds": 0.0,
    "end_seconds": 60.0,
    "sample_fps": 0.133333,
    "frames": [
      {
        "frame_index": 123,
        "timestamp_seconds": 0.0,
        "target_timestamp_seconds": 0.0,
        "image_path": "frames/window-001-frame-001.jpg"
      }
    ]
  },
  "situation": {
    "situation_description": "...",
    "raw_output": "...",
    "model_info": {},
    "elapsed_seconds": 1.2,
    "prompt_id": "...",
    "prompt_hash": "...",
    "prompt_version": 1,
    "generation": {}
  },
  "summary": {
    "summary": "...",
    "raw_output": "...",
    "model_info": {},
    "elapsed_seconds": 0.8,
    "prompt_id": "...",
    "prompt_hash": "...",
    "prompt_version": 1,
    "generation": {}
  }
}
```

SituationとSummaryの両方が正常完了したwindowだけを `turns` へcommitする現在の意味を維持する。

completed window追加ごとにresult全体をatomic replaceする。

## 11. sampled frame画像

### 11.1 保存目的

sampled frame画像は、後から

- Situation Agentへどの画像列が入力されたか
- timestamp / frame IDと視覚内容が対応しているか
- Situation出力を人間が動画全体へ戻らず軽く確認できるか

を確認するためのhuman-review artifactとする。

### 11.2 保存形式

既存 `_thumbnail_jpeg` 相当の処理を利用し、JPEG previewとして永続保存する。

標準:

- format: JPEG
- 既存thumbnailと同程度のpreview品質を維持する。
- modelへ入力したtensor / PIL imageのbyte-for-byte dumpを研究正本とはしない。
- exact input identityは `frame_index / timestamp_seconds / target_timestamp_seconds` を正本とする。

保存先:

```text
frames/window-001-frame-001.jpg
frames/window-001-frame-002.jpg
...
```

Windowとframe ordinalは1-based zero-paddingで人間可読にする。

各frame metadataにrelative `image_path` を記録する。

### 11.3 保存タイミング

frame画像はwindowを取得し、Situation Agentへ渡す前に生成・保存する。

これによりSituation / Summaryが失敗したwindowでも、実際に入力予定だったsampled frameをデバッグ用に確認できる。

ただしcompleted `turns` へはSituation + Summary成功後のみwindowを追加する。

failed windowのframe fileが `frames/` に残ることは許容する。これは失敗調査用artifactであり、成功turnを捏造しない。

### 11.4 Browser

server session中は既存memory cacheを利用してよい。

server再起動後は、Record v3の `image_path` から保存JPEGをread-onlyで返せるようにする。

外部から任意pathを指定できるfile serverにはせず、record内に保存したframe metadataから決定的に解決する。

## 12. Answerと評価

### 12.1 Answer保存位置

`final_answer.json` は廃止する。

EOF Answer成功後、`result.json` top-level `answer` を埋める。

概念形:

```json
{
  "answer": {
    "prediction": {
      "answer": "2. ...",
      "choice_index": 2,
      "choice_text": "..."
    },
    "ground_truth": {
      "choice_index": 2,
      "choice_text": "..."
    },
    "correct": true,
    "raw_output": "...",
    "model_info": {},
    "elapsed_seconds": 0.5,
    "prompt_id": "...",
    "prompt_hash": "...",
    "prompt_version": 1,
    "generation": {}
  }
}
```

`choice_index` はWorkbench内では既存Answer契約に合わせて**1-based**とする。

### 12.2 gold leakage防止

正解ラベルを以下へ追加しない。

- `QuestionSample`
- Situation input
- Summary input
- Answer input
- Prompt
- ExecutionSettings
- Run開始時の `question`
- Run開始時の `config`

評価用goldは**Answer Agentが出力し、既存Answer validationを通過した後にのみ取得する。**

Dataset adapter / DatasetService側に、推論inputとは独立したevaluation target取得境界を追加する。

概念interface:

```python
get_evaluation_target(question_id)
```

返す意味:

```text
choice_index: Workbench canonical 1-based
choice_text: exact candidate text
```

RunSession / Workflow / Agentへgoldそのものを事前注入しない。

### 12.3 LongVideoBench

LongVideoBench `lvb_val.json` の `correct_choice` は公式loader上0-basedである。

Workbench保存時:

```text
canonical choice_index = correct_choice + 1
choice_text = candidates[correct_choice]
```

とする。

公式参照:

```text
https://github.com/longvideobench/LongVideoBench/blob/main/longvideobench/longvideobench_dataset.py
```

### 12.4 Fake Dataset

Fake Datasetにも短時間test用の決定的なevaluation targetを用意する。

現在のchoices `("event A", "event B")` に対し、既存Fake Answerが返すchoiceと整合する正解を固定する。

### 12.5 正誤

```text
correct = prediction.choice_index == ground_truth.choice_index
```

で決定的に算出する。

LLMに正誤判定させない。

Answer Agent validation失敗時は `answer` を成功結果として埋めない。runは既存どおりfailedとなり、goldだけを先に保存しない。

## 13. trace.md

### 13.1 目的

`trace.md` は人間がAgentの推移を確認するためのderived artifactであり、machine-readable SSOTではない。

Markdownへ画像は埋め込まない。

### 13.2 表

基本形:

```markdown
| Window | Situation Agent | Summary Agent | Answer Agent |
|---:|---|---|---|
| 1 | ... | ... | — |
| 2 | ... | ... | — |
| 3 | ... | ... | — |
| EOF | — | — | 2. ... |
```

Windowは1-based表示。

通常windowのAnswer列は `—`。

Answer成功後のみEOF行を追加する。

正解ラベル・正誤・frame画像・Prompt・model情報・latencyは現段階のMarkdown表へ追加しない。これらは `result.json` / `frames/` で確認する。

### 13.3 escape

- cell内改行は `<br>`
- literal `|` は `\|`
- semantic outputを要約・翻訳・切詰めない
- Unicodeを維持

### 13.4 更新タイミング

- completed windowを `result.json` へcommitした後に更新
- Answer成功後にEOF行を追加して更新
- Markdown生成失敗だけでinference/runをfailedにしない

`trace.md` は `result.json` から再生成可能であること。

## 14. 書き込み順序とfailure semantics

### Window

```text
window取得
  -> frame JPEG保存
  -> Situation
  -> Summary
  -> result.jsonへcompleted turn atomic commit
  -> trace.md更新
  -> awaiting_next_turn
```

### EOF

```text
Answer実行
  -> Answer validation
  -> evaluation target取得
  -> prediction / gold / correct生成
  -> result.json.answer atomic commit
  -> status=succeeded atomic commit
  -> trace.md更新
```

実装上、answer payloadとsucceeded statusを同一atomic updateへまとめられる場合はまとめてよい。

### Failure

- Agent failure時は `status.state=failed` とerrorをresultへatomic保存する。
- 未完了windowを `turns` へ追加しない。
- 既に保存したframe JPEGは削除しない。
- Answer failure時にgoldだけを保存しない。
- `trace.md` failureはrun failureにしない。

## 15. 既存Record互換

### Record v3

新Runは本specの

```text
result.json
trace.md
frames/
```

だけを新artifactとして生成する。

### Record v2

現行6-file Record v2はread-onlyで閲覧可能にする。

- migrationしない
- 追記しない
- resumeしない
- 自動でv3へ変換しない

### さらに古いLegacy

既存LegacyRunReaderのread-only責務を必要最小限維持する。

### Reader判定

概念的には:

```text
result.json + artifact_schema_version=3
  -> v3 reader/writer

run_status.json + artifact_schema_version=2
  -> v2 read-only reader

その他の既存run
  -> legacy read-only reader
```

とする。

旧write pathはv3切替後、新Runから参照されないことを確認して削除する。

backup目的のcopyは残さない。

## 16. Browser / CLI / Restartへの影響

### Browser

現在のAPI route名を変更しない。

Browserはv3 `result.json` から以下を表示できること。

- status
- Question / Choices
- Window metadata
- Situation
- Summary
- Final Answer
- Ground Truth
- 正誤
- frame preview
- saved-run reload

server再起動後も保存済みJPEGを表示可能にする。

#### Final Result card

Final Answerはwindow turn navigationの一部として扱わず、Run全体のtop-level resultとして独立した「最終結果」cardへ表示する。

推奨構成:

```text
┌ 最終結果 ────────────────────────── [✓ 正解 / ✕ 不正解 / — 判定不可]
│ Model Answer
│ 2. ...
│
│ Correct Answer
│ 2. ...
└────────────────────────────────────
```

表示規則:

- v3のAnswer validationとevaluationが完了した後だけFinal Result cardを表示する。
- `answer.prediction` をModel Answerとして表示する。
- `answer.ground_truth` をCorrect Answerとして表示する。
- `answer.correct == true` は `✓ 正解`。
- `answer.correct == false` は `✕ 不正解`。
- gold / correctnessを持たないv2 / Legacy等のread-only runは `— 判定不可` とし、正解を推測しない。
- 正誤は色だけで表現しない。icon / text badgeを必須とする。
- choice indexとchoice textを両方読める表示にする。
- raw output / Prompt / generation / model info / latencyはFinal Result cardへ詰め込まず、既存の詳細表示へ残す。
- Question choices自体へのpredicted / correct markerや色付けは初期scopeに含めない。
- Window履歴はFinal Result cardの下で従来どおり追跡できる構成とする。
- v3ではFinal AnswerをWindow turn countへ含めず、Window navigationはcompleted windowだけを対象とする。

gold leakage防止のため、実行中のBrowser payloadへGround Truthを含めない。Answer validation成功後にevaluation targetを取得し、`result.json.answer` へ保存された後だけBrowser projectionへ公開する。

新規v3のLongVideoBench / Fake RunではAnswer成功後にGround Truthとboolean `correct` が存在することを必須とする。

### CLI

CLIのRun実行経路を変えず、完了後にrun IDと最終回答を標準出力できる現在UXを維持する。

### Recent settings

現在 `execution_settings.json` を読むrecent settings復元は、v3では `result.json.config.execution` から復元する。

v2 read-only runについては既存 `execution_settings.json` を読める互換を維持してよい。

### Restart

v3のrestartは `result.json.config.execution` から設定を復元し、**新しいv3 Runを先頭から作成**する。

old runを上書きしない。

## 17. 削除対象

v3新経路が成立しrepo-wide参照が無くなったことを確認後、新Run書込用の次を削除する。

- `execution_settings.json` writer
- `resolved_prompts.json` writer
- `question.json` writer
- `run_status.json` writer
- `turns.jsonl` writer
- `final_answer.json` writer
- v2 write専用helper
- v3で不要になった旧trace writer/helper

ただしv2 / Legacy read-only readerに必要なcodeは明示的な互換責務として残す。

repository内にbackup copy、`old/`、`legacy_impl/` 等を作らない。

## 18. 対象外

本specでは以下を行わない。

- Situation / Summary / AnswerのPrompt変更
- Agent責務変更
- window / frame sampling policy変更
- model / generation設定変更
- Answer format変更
- Early Answer
- dynamic window
- multi-timescale memory
- Markdownへの画像埋め込み
- Notion API連携
- 複数Run比較表
- accuracy集計
- Dataset全件評価
- 新dependency導入
- Record v2 / Legacy artifact migration
- 実Qwen / GPU / LongVideoBench full run
- model download
- main merge
- remote push
- Pull Request

## 19. Git運用

### Branch

実装開始時に最新 `main` / HEAD / dirty stateを確認する。

本spec作成時の基準は

```text
main@2a40379cf98f3c6d5c9784d0bcb0439c3577cbbb
```

だが、実装時にmainが進んでいれば差分を確認し、意味が変わっていなければ最新mainから開始する。

最新mainから**1本の実装branchだけ**を作る。

推奨:

```text
refactor/run-artifact-v3
```

Stepごと・micro stepごとにbranchを増やさない。

### Micro-commit

独立して説明・検証できる意味単位でmicro-commitを積む。

- 小さすぎるcommitへ過度に分割しない
- 異なる責務を1 commitへ無関係に混在させない
- 各commit後、その変更に最も近い短時間test / compile / smokeを行う
- 全体回帰はbranch完成時に行う
- squash前提にせず意味のある履歴を保持する

### Commit message

日本語で **タイトル + 本文5〜6行程度**。

本文は箇条書きにせず、

- 何を変更したか
- なぜ変更したか
- どの責務・経路へ影響するか
- 何を検証したか

が文章で分かるようにする。

### 許可

Codex / 実装者に許可するGit操作:

- 現在状態確認
- 実装branch作成
- 実装
- 短時間検証
- micro-commit

禁止:

- main merge
- remote push
- PR
- history rewrite

実装完了時のゴールは、**実装branch最新commit上で本specと短時間検証が成立していること**。

main merge / pushはユーザーが実装確認後に行う。

## 20. 推奨実装順

### Step 1: Record v3 core

- human-readable Run ID
- result.json schema
- atomic read/update/write
- status / config / question / turns / answer統合
- v3 reader
- v2 / Legacy reader判定

verify:

- Record unit tests
- concurrent/partial read safety
- run ID collision test
- compile

### Step 2: frame persistence

- frame JPEGをRun directoryへ保存
- frame metadataへrelative image_path
- session thumbnailと保存JPEGの責務整理
- saved-run thumbnail route

verify:

- JPEG signature
- expected file count
- browser route 200 / image/jpeg
- server restart後のread-only preview

### Step 3: evaluation boundary

- Dataset evaluation target interface
- LongVideoBench 0-based -> canonical 1-based変換
- Fake target
- Answer成功後のみgold取得
- correctをcode-side比較
- result.answer保存

verify:

- goldがQuestion / Prompt / Agent inputへ存在しない
- correct / incorrect両ケース
- invalid Answer時にgoldだけ保存されない

### Step 4: Markdown trace

- v3 resultからMarkdown表生成
- windowごとSituation / Summary
- EOF Answer
- multiline / pipe escape
- no image embed

verify:

- exact Markdown test
- partial Run
- final Run
- presentation failure isolation

### Step 5: Browser Final Result / CLI / recent settings / restart

- v3 projection
- Final Result cardをwindow履歴から独立表示
- Model Answer / Correct Answer / 正解・不正解badge
- v3 Final Answerをwindow navigationから分離
- 実行中のgold非公開
- v2 / Legacyの判定不可表示
- v3 recent settings
- v3 restart
- saved-run reload
- v2 / Legacy read-only regression

verify:

- correct v3 Runで `✓ 正解`
- incorrect v3 Runで `✕ 不正解`
- Model Answer / Correct Answerのindex + text表示
- Answer完了前にgoldがBrowser payload / DOMへ存在しない
- v2 / Legacyでgoldを推測せず `— 判定不可`
- Final Answerがwindow navigation件数へ入らない
- Fake HTTP / Browser E2E
- Fake CLI
- restart
- reload
- v2 fixture
- legacy fixture

### Step 6: old writer cleanup + docs + full regression

- new Runから不要な6-file writer削除
- repo-wide references監査
- README / development docsをv3実態へ更新
- backup codeを残さない

verify:

- full short pytest
- compileall
- CLI help
- Fake HTTP / Browser / CLI smoke
- `git diff --check`
- `git status`

## 21. Success Criteria

1. 新Run directory名が `YYYY-MM-DD_HH-MM-SS` を基本としrandom hashを含まない。
2. 同一秒衝突時は連番suffixで安全に別Runを作る。
3. 新Runのmachine-readable SSOTが `result.json` 1つになる。
4. `result.json.artifact_schema_version == 3`。
5. status / question / config / turns / answerをresult内で保持する。
6. 新Runで現行6 JSON/JSONL fileを並行生成しない。
7. JSON更新はatomicで、読み取り側が途中書込みを観測しない。
8. completed windowだけがturnsへ保存される。
9. Situation / Summary semantic outputとexecution metadataを保持する。
10. Prompt bodyをturnごとに不必要に複製せずtop-level snapshotを保持する。
11. sampled frame JPEGを `frames/` へ永続保存する。
12. 各frame metadataからrelative image pathを追跡できる。
13. server再起動後のv3 saved runでもframe previewを読める。
14. Markdownへ画像を埋め込まない。
15. `trace.md` がWindow / Situation / Summary / Answerの表を持つ。
16. Markdownはresultから決定的に再生成できる。
17. Markdown生成失敗だけでrunをfailedにしない。
18. Answerは別fileでなくtop-level `answer` に保存する。
19. prediction、ground_truth、correctをAnswer成功後に保存する。
20. Workbench canonical choice_indexはprediction / goldとも1-based。
21. LongVideoBench `correct_choice` の0-based値を正しく1-basedへ変換する。
22. gold labelをQuestionSample / Prompt / Agent input / Run開始時recordへ混入させない。
23. Answer validation失敗時にgoldだけをartifactへ保存しない。
24. correctnessはPythonで決定的に比較し、LLMへ判定させない。
25. Record v2とそれ以前のLegacy Runはread-onlyで閲覧できる。
26. v2 / Legacyをv3へ自動migrationしない。
27. v3 restartは新しいRunを作り、source Runを変更しない。
28. Dataset Browser / Prompt Library / Config等、本spec対象外の主要機能を壊さない。
29. 不要な旧writer / helperをrepo内backupとして残さない。
30. short full regression / compileall / diff checkが成功するか、環境依存failureを分離報告する。
31. 実Qwen/GPU/LongVideoBench full runを実装成功条件に含めない。
32. v3 BrowserでFinal Result cardがwindow履歴から独立して表示される。
33. v3 correct RunでModel Answer / Correct Answerと `✓ 正解` が表示される。
34. v3 incorrect RunでModel Answer / Correct Answerと `✕ 不正解` が表示される。
35. 正誤表示は色だけに依存せずtext / iconでも判別できる。
36. Answer validation / evaluation完了前のBrowser payloadとDOMにGround Truthが露出しない。
37. v2 / Legacy等goldを持たないread-only runでは正解を推測せず `— 判定不可` と表示できる。
38. v3 Final Answerはwindow navigationのturn countへ含めず、completed windowだけを履歴移動対象にする。
39. Final Result cardへraw output / Prompt / generation / latencyを重複表示せず、既存詳細表示の責務を維持する。

## 22. Ambiguity Gate

### blocking

なし。

現在のユーザー指示と現行コード調査から、本specの外部挙動を変える未決事項は残していない。

### non-blocking

実装者が既存styleに合わせて決めてよい:

- Record v3内部class名
- evaluation target用dataclass / tuple等のprivate表現
- JSON update helperのprivate method名
- thumbnail helperの配置
- v2 read-only readerの具体class名
- test fileの分割

これらを理由に追加の汎用frameworkやdependencyを導入しない。

## 23. Spec Gate

本specは2026-10-08のユーザー判断と「spec更新 + Codexへの実装prompt出力」の依頼を、実装への明示的な引き継ぎ意図として扱い、**approved** とする。

コード変更自体はこのCompany更新では実行しない。

長時間run、実Qwen/GPU、main merge、push、PRは別Gateのままとする。

## 24. Implementation Handoff

- approved spec: 本spec
- 実装目的: Record v2の6-file出力をRecord v3の `result.json + trace.md + frames/` へ単純化し、gold leakageなしでFinal Answerの正誤まで保存し、Browserの独立したFinal Result cardでModel Answer / Correct Answer / 正誤を確認できるようにする。
- 基準repository: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench`
- spec作成時基準: `main@2a40379cf98f3c6d5c9784d0bcb0439c3577cbbb`
- 実装開始点: 最新mainを再確認し、stalenessがなければそこから1 implementation branchを作る。
- 変更scope: Record / Runtime frame persistence / Dataset evaluation boundary / Presentation trace / Browser Final Result card・saved-run projection / CLI/restart/recent-settings / tests /必要最小限docs。
- 対象外: Section 18。
- success criteria: Section 21。
- 許可される短時間検証: unit、Fake workflow、Fake HTTP/Browser、Fake CLI、restart/reload、v2/Legacy read-only、compileall、diff check。
- 長時間run: 未許可。
- Git: 1 implementation branch + meaning-based micro-commits。main merge / push / PRは禁止。
- 旧実装: v3新経路から不要なwrite codeは参照監査後に削除。read-only compatibilityのみ残す。
- 未検証予定: 実Qwen/GPU/LongVideoBench実run、長尺runでのartifact容量、Notionへの画像込み貼付。
