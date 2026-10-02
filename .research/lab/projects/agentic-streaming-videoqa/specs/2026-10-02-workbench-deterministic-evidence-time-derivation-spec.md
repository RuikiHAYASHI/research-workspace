---
date: 2026-10-02
last_updated: 2026-10-02
project: agentic-streaming-videoqa
type: implementation
status: approved
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 09b5b4277981dc985d4ceb1d499e90ea1ee93040
source_brainstorm:
  - .research/secretary/notes/brainstorm/2026-10-02-workbench-deterministic-evidence-time-grounding.md
related_specs:
  - 2026-09-30-workbench-agent-modes-and-readable-memory-spec.md
  - 2026-10-02-workbench-video-unresolved-schema-contract-regression-fix-spec.md
  - 2026-10-02-workbench-video-observation-time-range-contract-regression-fix-spec.md
---

# Workbench Stage 11: Evidence frameからの決定的時刻導出 spec

## 0. Authority / Approval

2026-10-02の実LongVideoBench + Qwen3-VL実行で、Situation Agentがmodel-generated `start_seconds/end_seconds` とmanifest actual timestampの不一致によりvalidation failureを繰り返した。

ユーザーは2026-10-02に、**時刻は計算可能なmetadataでありQwenに再生成させず、Evidence frame参照からコード側で決定する**方向を採用した。また「計画と実装用プロンプト」を明示要求したため、本書を `approved` とし、engineering-taskへ引き継げる。

Stage 10はGitHub `main@09b5b4277981dc985d4ceb1d499e90ea1ee93040` へmerge/push済みである。Stage 10はPrompt 3ファイルと回帰testだけを変更し、validator/runtime/artifact schemaは変更していない。したがってStage 9へreset/revertせず、Stage 10を履歴として残したままforward changeする。

## 1. 目的

Situation / Memory AgentがEvidenceの意味内容とframe参照を判断し、**時刻metadataはBackendがmanifestのactual source-video timestampから決定的に導出する**責務分離へ変更する。

これにより次を構造的に除去する。

- Qwenがwindow end `4.0` をobservation endとして出す。
- actual `3.503...` を `3.5` 等へ丸める。
- target timestampとactual timestampを混同する。
- model-generated floatを `1e-6` toleranceで再照合する。
- 動画PTS/frame gridの違いによってschema adherenceが変わる。

Qwenには「何が起きたか」「どのframeが根拠か」を担当させ、コードが既知metadataを担当する。

## 2. 現行Evidence

### 2.1 Sampling

`sequential_loader` のTimeGridSamplingPolicyは4秒8frameならtargetを概ね

```text
0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5
```

とする。

TargetFrameSelectorは各targetについて `timestamp >= target` を最初に満たすsource frameを採用するため、actual timestampは動画PTSにより `0.500...`, `1.001...`, `3.503...` 等になり得る。これは正常な量子化であり、現時点でdecoder時刻異常のEvidenceはない。

### 2.2 Manifest

Workbenchはmodelへ各frameの

- `video_ordinal`
- `frame_index`
- `timestamp_seconds` = actual source-video timestamp
- `target_timestamp_seconds`

を渡している。

### 2.3 Current failure

現行video Situation raw schemaは各observationへ

- `start_seconds`
- `end_seconds`
- `description`
- `evidence_frame_indices`
- `question_relevance`
- `certainty`

をmodelに生成させる。

validatorはmodel-generated start/endをmanifest actual timestampと照合するため、Evidence refs自体が正しくても、Qwenが `end_seconds=4.0` と返すだけでrunが停止する。

Memory eventにも同じ冗長性がある。

## 3. 採用設計

### 3.1 Situation raw model output

新しいbuilt-in video Situation Promptでは、各observationからmodel-generated `start_seconds/end_seconds` を削除する。

新raw observation contract:

```json
{
  "description": "...",
  "evidence_frame_indices": [24, 36, 48],
  "question_relevance": "high",
  "certainty": "fact"
}
```

top-level `window_summary`, `observations`, `unresolved` は維持する。

`window_summary` と `description` の統合は別brainstorm事項であり、本Stageでは変更しない。

### 3.2 Situation Backend enrichment

Backendは `evidence_frame_indices` を先にstrict validationする。

必須:

- list。
- 1件以上。
- int。
- current manifestに存在するframe IDのみ。
- 重複なし。

valid refsに対してmanifest actual timestampを引き、

```text
start_seconds = min(actual timestamp of cited evidence frames)
end_seconds   = max(actual timestamp of cited evidence frames)
```

を計算する。

validated/canonical observationは既存互換のため次を保持する。

```json
{
  "start_seconds": 1.001,
  "end_seconds": 2.502,
  "description": "...",
  "evidence_frame_indices": [24, 36, 48],
  "question_relevance": "high",
  "certainty": "fact"
}
```

`start_seconds/end_seconds` の意味は**真のevent境界ではなく、cited evidenceが支持するEvidence time range**とする。

### 3.3 Memory raw model output

新しいbuilt-in Memory video Promptでも、各eventからmodel-generated `start_seconds/end_seconds` を削除する。

新raw event contract:

```json
{
  "event_id": "w0-e0",
  "description": "...",
  "evidence_frame_indices": [24, 36, 48],
  "certainty": "fact",
  "importance_reasons": ["state_change"],
  "importance_explanation": "..."
}
```

top-level `events`, `narrative`, `unresolved` は維持する。

### 3.4 Memory Backend enrichment

既存どおりevent evidence refsはcurrent validated Situation observationでsupportされたframe IDだけを許可する。

valid refsについてmanifest actual timestampsからmin/maxを計算し、canonical eventへ `start_seconds/end_seconds` を付与する。

### 3.5 Single-frame Evidence

Evidence frameが1枚だけなら、

```text
start_seconds == end_seconds
```

のzero-length Evidence rangeを正しい値として許容する。

存在しないdurationを推測で広げない。

### 3.6 Legacy raw compatibility

既存User Promptや旧built-in本文をcopy済みのPromptは `start_seconds/end_seconds` を引き続き出力する可能性がある。

新validatorはvideo Situation / Memoryについて、次の2 raw shapeだけを許容する。

1. 新shape: start/endなし。
2. legacy shape: start/endあり。

legacy shapeの `start_seconds/end_seconds` は**非authoritativeなcompatibility fieldとして無視する**。値がwindow end、丸め値、またはactual manifestと不一致でも、それ自体ではtime validation failureにしない。

canonical start/endは常にEvidence refsから再計算する。

legacy以外の未知fieldは従来どおりrejectし、schema strictnessを無制限に緩めない。

この互換経路により既存User Promptを一括migrationしない。

## 4. Prompt contract

### 4.1 Situation Prompt

`situation.video.initial` と `situation.video.previous_text` からStage 10で追加したmodel-generated time contractを削除する。

modelへ要求するのは:

- visible semantic observation。
- valid current manifest frame IDsによる `evidence_frame_indices`。
- relevance / certainty。
- unresolved array contract。

時刻をJSONへ出力させない。

manifest actual timestampはQwenが時刻fieldを生成するためではなく、frame Evidenceの人間可読contextおよびBackend SSOTとして維持する。

### 4.2 Memory Prompt

`memory.video.initial` からmodel-generated event time contractを削除し、eventはsemantic content + evidence refs + certainty + importanceだけを返す。

Backendが時刻を付与する。

## 5. Schema / Prompt metadata / artifact compatibility

### 5.1 Prompt metadata

今回はbuilt-in Prompt ID、role、input_schema、output_schema metadata名を変更しない。

理由:

- `window_observation_v1` / `event_ledger_v1` はcanonical validated outputとして既存shapeを維持する。
- 変更するのはmodel raw representationとBackend enrichment responsibility。
- PromptServiceの互換判定、User Prompt、Run settingsを不要にmigrationしない。

### 5.2 Artifacts

新規run:

- raw model outputには新built-in Prompt使用時はstart/endを含めない。
- validated/structured outputにはBackend-derived start/endを含める。
- `memory.jsonl`, timeline, results view等のcanonical表示は既存start/endを利用できる。
- rawとvalidatedを混同しない。

既存run:

- 保存済みraw output、validated output、Prompt snapshot/hashを変更しない。
- read-only表示時に再validation・再enrichmentしない。
- migrationしない。

### 5.3 Stage 10

Stage 10のPrompt time instructionsは新設計では不要なので削除する。

Stage 10の「modelが正しい時刻を生成すること」を確認するtestは、Evidence refsからBackendが決定的に時刻を導出するtestへ置換・整理する。

Git historyは書き換えない。

## 6. 対象外

- Situationの `window_summary` / observation `description` 統合。
- evidence frame ID自体をmodelから除去すること。
- video ordinalだけをmodelへ出させる再設計。
- retry Agent / JSON repair / constrained decoding。
- sampling algorithm。
- target timestamp生成。
- sequential_loader変更。
- Qwen model / generation parameter変更。
- `cap_pixels_per_frame`。
- Memory algorithm / Answer algorithm。
- Config schema。
- Google翻訳。
- Dataset Browser。
- old run migration。
- 実Qwen/GPU/長尺評価。

## 7. Ambiguity Gate

### blocking

なし。

ユーザーはmodel-generated時刻を廃止しBackend計算へ移す方向を明示採用した。canonical start/endを維持する最小互換案、single-frame zero-length、Stage 10をrevertせずforward changeする方針も直前の壁打ちから確定可能である。

### non-blocking

- raw field set判定のprivate helper名。
- Situation / Memory validator内で共通helperを切るか各module内に短く実装するか。
- test fixtureの具体的frame ID / timestamp値。
- Prompt英文の表現。

既存styleと最小差分を優先する。

## 8. Success Criteria

1. 新built-in Situation raw observationはstart/endなしでvalidationできる。
2. canonical Situation observationにはBackend-derived start/endが入る。
3. derived start/endはcited frameのactual timestamp min/maxと完全一致する。
4. target timestamp、window start/end、model-generated timeはderived valueに使わない。
5. single-frame Evidenceはstart==endでpassする。
6. unknown / empty / duplicate evidence refsはstrict reject。
7. legacy Situation raw shapeのstart/endは無視され、Evidence refsから再計算される。
8. legacy raw start/endが `4.0`、丸め値、文字列等でもcanonical timeはEvidence refsから決まり、time mismatch failureを起こさない。
9. 新built-in Memory raw eventはstart/endなしでvalidationできる。
10. canonical Memory eventにもEvidence refs由来start/endが入る。
11. Memory event refsはcurrent validated Situation support内だけを許可する。
12. single-frame Memory eventもzero-length rangeでpassする。
13. legacy Memory raw start/endも無視して再計算する。
14. Situation/Memory built-in Promptからmodel-generated time requirementが消える。
15. Stage 10のPrompt time-contract testがdeterministic derivation contractへ置換される。
16. Prompt ID / role / input_schema / output_schema metadataは不変。
17. new runのraw outputとvalidated outputの責務差をartifact/testで確認できる。
18. existing UI/results/timelineはcanonical start/endを引き続き表示できる。
19. old run snapshot/artifactは再計算・書換えされない。
20. image_list legacy pathは非回帰。
21. Stage 6/7/8/9/10関連の設定・Prompt・run/browser回帰が通る。
22. related pytest、compileall、`git diff --check` が通る。
23. 実Qwen/GPU/model download/LongVideoBench長尺runを自動実行しない。

## 9. Git Strategy — Stage / Step / micro step

過去のStage 1 / Stage 3 / Dataset Browser specsの規約へ戻し、**1 Step = 1 branch、1 micro step = 1独立commit**を必須とする。

Stage branch:

```text
stage-11-deterministic-evidence-time
```

Step branches:

```text
stage11-step01-contract-regression
stage11-step02-situation-deterministic-time
stage11-step03-memory-deterministic-time
stage11-step04-artifact-prompt-regression
```

概念graph:

```text
main
  \
   stage-11-deterministic-evidence-time
      \
       stage11-step01-contract-regression
          m1.1 -- m1.2
      \
       stage11-step02-situation-deterministic-time
          m2.1 -- m2.2 -- m2.3
      \
       stage11-step03-memory-deterministic-time
          m3.1 -- m3.2 -- m3.3
      \
       stage11-step04-artifact-prompt-regression
          m4.1 -- m4.2 -- m4.3
```

各Stepは、その時点のStage HEADから作る。Step完了時に関連testを通し、micro commitsをsquashせずStageへ `git merge --no-ff` でlocal mergeする。次Stepは更新済みStage HEADから作る。

### 9.1 Commit message

各micro commitの1行目:

```text
Stage 11 Step N: <日本語の完結した変更タイトル>
```

本文:

```text
変更内容:
...

理由:
...

検証:
...

影響:
...  # 必要な場合
```

Step→Stage merge commitも日本語タイトル＋本文で、統合したmicro commitとtest結果を記録する。

巨大なStep末尾一括commitは禁止。各microは **実装 → 最小関連test → diff確認 → 対象fileだけstage → commit** の順で行う。

`git add .`、squash、rebase、reset --hard、clean、force push、履歴書換えは禁止。

## 10. Step / micro step plan

### Step 1: Contract regression

branch:

```text
stage11-step01-contract-regression
```

#### micro 1.1 — Situationの現行依存を固定

commit title:

```text
Stage 11 Step 1: Situationのmodel生成時刻依存を回帰テストで固定する
```

- current raw schemaがstart/endを要求していることをcharacterization testで固定。
- out-of-range model timeで現行failureが起きることを固定。
- Evidence refsとactual timestamp fixtureを明示。
- production codeは変更しない。

#### micro 1.2 — Memoryとsingle-frame境界を固定

commit title:

```text
Stage 11 Step 1: Memoryのmodel生成時刻依存と単一Evidence境界を固定する
```

- Memory eventでも現行start/end依存をcharacterization。
- single evidence frameから導出すべきzero-length rangeの期待をtest caseとして準備。
- current support-ref strictnessを固定。

Step末尾でcharacterization testsを通し、Stageへ `--no-ff` mergeする。

### Step 2: Situation deterministic time

branch:

```text
stage11-step02-situation-deterministic-time
```

#### micro 2.1 — Backend derivation

commit title:

```text
Stage 11 Step 2: SituationのEvidence時刻をframe参照から決定的に導出する
```

- new raw observation shapeを受理。
- refsをstrict validation後、actual timestamp min/maxをcanonical start/endへ付与。
- single-frame zero-lengthを許容。
- unknown/empty/duplicate refsはreject。

#### micro 2.2 — legacy raw compatibility

commit title:

```text
Stage 11 Step 2: 旧Situation raw時刻fieldを非authoritative互換入力として扱う
```

- legacy shapeも受理。
- raw start/endは値に依存せず無視。
- canonical timeをEvidence refsから再計算。
- legacy以外のunknown fieldsはreject。

#### micro 2.3 — Situation Prompt責務整理

commit title:

```text
Stage 11 Step 2: Situation Promptから時刻生成責務を除去する
```

- built-in Situation video 2種からstart/end生成要求とStage 10 time-contract段落を削除。
- evidence_frame_indicesの正当なmanifest ID参照を明示。
- unresolved contract等は維持。
- Prompt ID/metadataは変更しない。
- PromptService/hash testsを更新。

Step末尾でSituation validator / Prompt testsを通しStageへ `--no-ff` mergeする。

### Step 3: Memory deterministic time

branch:

```text
stage11-step03-memory-deterministic-time
```

#### micro 3.1 — Backend derivation

commit title:

```text
Stage 11 Step 3: Memory eventのEvidence時刻をframe参照から決定的に導出する
```

- new raw event shapeを受理。
- current validated Situation support内のrefsだけ許容。
- actual timestamp min/maxをcanonical start/endへ付与。
- single-frame zero-lengthを許容。

#### micro 3.2 — legacy raw compatibility

commit title:

```text
Stage 11 Step 3: 旧Memory raw時刻fieldを非authoritative互換入力として扱う
```

- legacy event shapeも受理。
- old raw start/endは無視。
- canonical timeはEvidence refsから再計算。
- duplicate event ID / refs / importance strictnessは維持。

#### micro 3.3 — Memory Prompt責務整理

commit title:

```text
Stage 11 Step 3: Memory Promptから時刻生成責務を除去する
```

- built-in Memory video Promptからstart/end生成要求とStage 10 time-contract段落を削除。
- event Evidence refsの意味を明示。
- narrative / unresolved / importance contract維持。
- metadata不変。
- PromptService/hash tests更新。

Step末尾でMemory validator / Prompt / workflow testsを通しStageへ `--no-ff` mergeする。

### Step 4: Artifact / Prompt / regression integration

branch:

```text
stage11-step04-artifact-prompt-regression
```

#### micro 4.1 — raw / validated artifact separation

commit title:

```text
Stage 11 Step 4: 新規Runのraw出力とBackend導出時刻をartifactで分離して検証する
```

- Fake video runでnew raw outputにstart/endがなくてもpipeline成功。
- structured/validated outputにはderived start/endが存在。
- memory.jsonl / stages / results projectionの既存canonical time利用を確認。
- raw outputへBackend-derived timeを捏造して書き戻さない。

#### micro 4.2 — old run / User Prompt compatibility

commit title:

```text
Stage 11 Step 4: 旧Runと既存User Promptの時刻互換を回帰テストで固定する
```

- old saved runはread-onlyでそのまま表示。
- legacy raw shapeを出すUser Prompt相当でも新規runはEvidence refsからcanonical timeを導出。
- Prompt copy/history/snapshotを壊さない。

#### micro 4.3 — Stage 10回帰test整理

commit title:

```text
Stage 11 Step 4: Prompt時刻遵守テストを決定的Evidence時刻導出テストへ置き換える
```

- Stage 10で追加した「modelがmanifest time rangeを生成する」前提のassertionを削除・置換。
- Prompt metadata不変、new raw contract、Backend derivationを確認。
- unrelated Stage 6/7/8/9 testsを変更しない。

Step末尾でtargeted integration testsを通しStageへ `--no-ff` mergeする。

## 11. Stage completion audit

Stage branch上で:

- Success Criteria 1–23を照合。
- related pytest。
- 可能なら通常の短時間full pytest。
- `PYTHONPATH=src python3 -m compileall -q src tests`
- `git diff --check`
- `git status`
- `git log --graph --oneline --decorate --all`
- mainとの差分を確認。

実Qwen/GPU/LongVideoBench実runは行わない。

## 12. Git permission boundary

今回のユーザー指示により次は許可済み:

- Stage branch作成。
- Step branch作成。
- **各micro stepの独立commit作成。**
- Step→Stageのlocal `--no-ff` merge。
- 短時間unit/integration/Fake/browser tests。
- compileall / diff check。

未許可:

- remote push。
- PR。
- Stage→main merge。
- branch削除。
- 実Qwen/GPU/model download。
- LongVideoBench実動画run/長時間評価。
- Google Cloud Translation実API。

Stage 11完了後、Stage→main直前で停止しユーザー確認を待つ。

## 13. Implementation Handoff

- approved spec: 本書。
- 実装目的: model-generated timeを廃止し、Evidence refsからBackendがactual timestamp rangeを決定的に導出する。
- 基準repository/commit: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `09b5b4277981dc985d4ceb1d499e90ea1ee93040`。着手時にremote/local最新状態を再確認。
- 変更scope: Sections 3–5, 9–10。
- 対象外・維持条件: Section 6。
- success criteria: Section 8。
- 許可されている短時間検証: validator / PromptService / workflow / artifact / browser Fake tests、compile/import、diff check。
- 長時間runの許可状態: 未許可。
- Git操作: Section 12。micro-stepごとのcommit必須。
- 未検証予定: 実Qwenでのschema adherence、LongVideoBench品質・速度。
