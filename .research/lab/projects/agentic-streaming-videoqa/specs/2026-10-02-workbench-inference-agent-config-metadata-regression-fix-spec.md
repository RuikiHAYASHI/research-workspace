---
date: 2026-10-02
last_updated: 2026-10-02
project: agentic-streaming-videoqa
type: implementation
status: approved
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: ae8df468b86db90811d400dcb2086f90be60c400
depends_on:
  - 2026-10-01-workbench-inference-settings-prompt-ux-spec.md
  - 2026-10-01-workbench-run-results-researcher-view-spec.md
---

# Workbench: Inference Agent Config metadata混入 regression fix spec

## 1. 目的

Stage 6/7統合後のInference画面で「設定を確認」または最初のRun開始を行うと、

```text
agents.situationに未対応の項目があります: title, version
```

としてcanonical Config validationに失敗するregressionを修正する。

今回の修正では、Promptの人間向け表示metadataと、実行時にConfig schemaへ渡すAgent設定を明確に分離し、UI表示用fieldを増やしてもAgent Configへ混入しない境界を作る。

研究アルゴリズム、Prompt本文、Agent別model runtime、Memory/Answer schema、Run artifact schemaは変更しない。

## 2. 確認済みの現行実装と原因

基準はWorkbench `main@ae8df468b86db90811d400dcb2086f90be60c400`。

### 2.1 Config schema

`src/longvideoqa_workbench/config/schema.py` の `AgentConfig.from_mapping()` は、Agent設定として次の5 fieldだけを許可する。

```text
backend
model_id
prompt_id
enabled
generation
```

`_exact_keys()` により未知fieldは拒否される。このstrict validationは維持する。

### 2.2 Server capabilities

`src/longvideoqa_workbench/entrypoints/server.py` の `ServerContext.capabilities()` は、`defaults.agents.<role>` に実行Config fieldだけでなく、Prompt表示用の次を追加している。

```text
title
version
```

一方、同じresponseの `defaults.stages` にはすでにPrompt表示に必要な `title`、`description`、`version` が存在する。

### 2.3 Browser state / payload

`src/longvideoqa_workbench/web/app.js` の初期化は、

```javascript
state.agentDefaults = defaults.agents || {};
```

で上記Agent objectを保持する。

`collectSettings()` は、

```javascript
{
  ...state.agentDefaults[role],
  model_id: ...,
  generation: ...,
  prompt_id: ...,
  enabled: ...,
}
```

とspreadするため、`title` と `version` も `agents.<role>` のruntime payloadへ残る。

そのpayloadを `/api/recipe/preview` / `/api/runs` がcanonical Configとして検証すると、`AgentConfig.from_mapping()` が未知fieldとして拒否する。

### 2.4 Root cause

原因はConfig schemaが厳しすぎることではなく、**表示用Prompt metadataをexecution Agent Configへ混ぜた境界違反**である。

Config schemaへ `title/version` を追加して受け入れる修正は行わない。これらは実行条件ではなく表示metadataであり、canonical Agent Configの責務ではない。

## 3. 修正契約

### 3.1 Agent Config projectionを純化する

`/api/capabilities` の `defaults.agents.<role>` は、canonical Agent Configと同じ次のfieldだけを返す。

```text
backend
model_id
prompt_id
enabled
generation
```

Promptの人間向け情報は `defaults.stages` / Prompt Library側を利用する。

### 3.2 Browserから送るAgent payloadをwhitelistで構築する

`collectSettings()` は `state.agentDefaults[role]` を丸ごとspreadせず、canonical Agent Configへ必要なfieldを明示構築する。

少なくとも送信payloadは次だけにする。

```javascript
{
  backend,
  model_id,
  prompt_id,
  enabled,
  generation: {
    max_new_tokens,
    temperature,
  },
}
```

目的は今回の `title/version` を消すだけではなく、今後capabilities/UI側へ表示metadataを追加してもcanonical Configへ暗黙混入しないようにすることである。

### 3.3 Prompt表示は維持する

Inference画面で現在表示できている以下は維持する。

- Situation / Memory / AnswerのPrompt title。
- Prompt version。
- Prompt description。
- Prompt LibraryからのPrompt変更。
- Prompt変更後のtitle/version表示。

表示情報は `state.stages` とPrompt detailを正本として扱い、Agent execution Configへ保存しない。

### 3.4 strict schemaは維持する

`AgentConfig.from_mapping()` の `_exact_keys()` は変更しない。

未知fieldを拒否することで、UI/APIの契約違反を早期検知する現在の性質を維持する。

## 4. Compatibility

維持するもの:

- canonical Config schema。
- `configs/default.yaml`。
- Agent別 `backend/model_id/prompt_id/enabled/generation`。
- PromptServiceとrun snapshot。
- Prompt title/version表示。
- settings template / recent settings呼び出し。
- old run閲覧/restart。
- per-Agent model routing。
- Stage 7 Result / Researcher View。
- run artifact schema。

今回のbug修正で既存保存データのmigrationは行わない。

## 5. 対象外

- Config schemaへ `title/version` を追加すること。
- Prompt metadata schemaの再設計。
- Agent/Workflow、Memory、Answerの研究挙動変更。
- Qwen model選択/ロード方式の再設計。
- Dataset Browser変更。
- 実Qwen/GPU run。
- LongVideoBenchの長時間run。
- Google Cloud Translationの契約変更。
- 翻訳providerの置換。

Google Cloud Translationが有料である点は本bugとは独立している。API key未設定でも英語原文でWorkbenchを使用できる現状を維持する。無料/ローカル翻訳providerへ変更する場合は、provider選定・品質・dependency・cache contractが変わるため別brainstorm/specで扱う。

## 6. Success Criteria

1. 現在の失敗を自動testで再現できる。
   - capabilities初期値からInference payloadを構成した場合、修正前は `agents.situation ... title, version` 相当でvalidation failureになることを示せる。
2. 修正後の `/api/capabilities` の `defaults.agents.<role>` に `title` / `version` が含まれない。
3. `defaults.agents.<role>` のkey setがcanonical Agent Configの5 fieldと一致する。
4. Inference画面のPrompt title/version/description表示は維持される。
5. `collectSettings()` がAgent payloadをwhitelistで構築し、表示metadataを送信しない。
6. Dataset/Question選択後、標準設定のまま「設定を確認」で `/api/recipe/preview` がvalidation errorにならない。
7. Fake Dataset/Fake modelでRun作成まで成功し、実modelをloadしない。
8. Promptを別Promptへ変更した後も、payloadには選択した `prompt_id` が入り、title/versionは混入しない。
9. 「設定を呼び出す」のdefault/recent/templateを適用しても同じvalidation errorを再発しない。
10. strict Config unknown-field rejection testは引き続き通る。
11. Stage 6/7関連の既存unit/API/browser tests、compile checkが通る。
12. 実Qwen/GPU、model download、長尺LongVideoBench runを修正検証として要求しない。

## 7. Ambiguity Gate

### blocking

なし。

原因と修正責務境界は現行コードから一意に確認できる。

### non-blocking

- regression testを既存 `tests/test_stage6_settings_and_models.py` へ追加するか、専用bugfix test fileへ分けるか。
- browser payloadのwhitelist helperを関数化するか `collectSettings()` 内へ直接書くか。
- exact key assertionの記述方法。

これらは既存test/code styleに従い、不要な抽象化を追加しない。

## 8. Implementation Steps / Git Strategy

過去Stage 3/4で採用した、**main / Stage / StepのlaneをGit graph上に残す方式**を使う。

実装開始時の基準:

```text
repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline branch: main
baseline commit: ae8df468b86db90811d400dcb2086f90be60c400
Stage branch: stage-8-inference-config-regression-fix
```

実装着手直前にGitHub `main` とlocal worktreeのbranch / HEAD / dirty stateを再確認する。baselineよりmainが進んでいる場合は古いcommitへresetせず、最新mainからStage branchを作成して差分を再確認する。

### Git topology

```text
main
  \
   stage-8-inference-config-regression-fix
      \
       stage8-step01-reproduce-agent-metadata-leak
      \
       stage8-step02-separate-agent-config-and-display-metadata
      \
       stage8-step03-regression-audit
```

- 各Step branchは、その時点のStage branch HEADから作成する。
- Step branch内は意味のあるmicro-step commitへ分ける。
- commitをsquashせず履歴を残す。
- Step完了後、対象testを通してStage branchへ **`--no-ff` merge** する。
- Step branchを直接mainへmergeしない。
- Stage全体の検証完了後に実装報告を行う。
- Stage→main mergeはユーザー確認後に **`--no-ff`** で行い、Stage laneを残す。
- remote push / Stage→main mergeは、実装依頼時または完了確認時の明示許可に従う。
- ユーザーの既存dirty変更をstage/commitへ混ぜず、対象fileを明示してaddする。

### Step 1: regression再現

branch:

```text
stage8-step01-reproduce-agent-metadata-leak
```

内容:

- `/api/capabilities` defaults Agent projectionの契約をtest化。
- capabilities由来のUI相当payloadがcanonical Configへ渡る経路を再現。
- `title/version` 混入を原因として失敗する現状を固定する。
- strict unknown-field rejection自体が正しいことを維持する。

主な候補:

- `tests/test_stage6_settings_and_models.py`
- 必要ならserver/API test。

commit例:

```text
Stage 8 Step 1: Agent設定metadata混入の回帰を再現

変更内容:
- capabilitiesのAgent projectionに表示metadataが混入する状態をtest化
- UI相当payloadのConfig validation failureを再現
- strict Agent Config contractを明示

理由:
- 修正前の失敗条件を固定し、原因と修正対象を限定するため

検証:
- 対象pytest
```

Step 1 testはbug再現testのため、修正前に期待どおりfailureを確認した後、同Stepまたは次Stepで恒久testとしてpass条件へ更新してよい。

### Step 2: execution / display metadata境界修正

branch:

```text
stage8-step02-separate-agent-config-and-display-metadata
```

内容:

1. Server capabilities:
   - `defaults.agents` から `title/version` を除外。
   - Prompt表示metadataは `defaults.stages` に残す。
2. Browser payload:
   - `collectSettings()` のAgent object spreadをやめる。
   - canonical Agent Config fieldだけを明示構築。
3. Prompt選択:
   - `state.stages` のtitle/version/description表示を非回帰確認。
   - selected `prompt_id` は実行payloadへ反映。

主な候補:

- `src/longvideoqa_workbench/entrypoints/server.py`
- `src/longvideoqa_workbench/web/app.js`
- Step 1で追加したtests。

commitはserver projectionとbrowser payloadが独立して検証できる場合は分ける。

commit例:

```text
Stage 8 Step 2: Agent Configと表示metadataを分離

変更内容:
- capabilitiesのAgent defaultsをcanonical fieldだけに限定
- browserのAgent payloadをwhitelist構築へ変更
- Prompt title/version表示はstage metadata側で維持

理由:
- UI表示情報が実行Configへ混入しvalidationを壊すregressionを解消するため

検証:
- Stage 6 settings tests
- API preview regression
```

### Step 3: regression audit

branch:

```text
stage8-step03-regression-audit
```

内容:

- default設定のpreview成功。
- Prompt変更後preview成功。
- settings default/recent/template再適用。
- Fake modelのRun作成。
- Stage 6/7 UI/API regression。
- compile/import。
- `git diff --check`。
- scope外変更がないことをdiff audit。

候補check:

```bash
PYTHONPATH=src python3 -m pytest -q \
  tests/test_stage6_settings_and_models.py \
  tests/test_config_service.py \
  tests/test_server.py

PYTHONPATH=src python3 -m compileall -q src tests
git diff --check
```

既存test構成を確認し、必要ならPrompt/browser関連の狭いtestを追加する。full pytestが短時間で既存運用上通常のcheckならStage完了前に実施してよいが、実Qwen/GPU/長尺runへ拡大しない。

commit例:

```text
Stage 8 Step 3: Inference設定回帰を検証

変更内容:
- default/Prompt変更/settings再利用の回帰testを整理
- Fake runとcompile checkを確認

理由:
- Stage 6/7の既存UXを維持したままvalidation regressionが解消したことを確認するため

検証:
- 関連pytest
- compileall
- git diff --check
```

## 9. Stage Completion Gate

Stage branchで以下が揃った時点で実装完了候補とする。

- Section 6のSuccess Criteriaを満たす。
- Step 1–3がStage branchへ`--no-ff`統合済み。
- Prompt title/version表示が壊れていない。
- Config strict validationを緩めていない。
- real Qwen/GPUや長時間runを実行していない。
- unrelated diffがない。
- local dirty stateとGit graphを報告できる。

その後、ユーザーが確認した場合のみStage→mainを`--no-ff` mergeし、必要なremote pushを行う。

## 10. Implementation Handoff

- approved spec: 本書。2026-10-02、ユーザーがStep 1–3を実装させるプロンプト作成を明示し、実装開始を承認した。
- 実装目的: Prompt表示metadataのAgent Config混入によりInference validationが失敗するregressionを修正する。
- 基準repository/commit: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `ae8df468b86db90811d400dcb2086f90be60c400`。着手時に最新mainを再確認する。
- 変更scope: Section 3、Section 8。
- 対象外・維持条件: Section 4–5。
- success criteria: Section 6。
- 許可されている短時間検証: Config/API/browser/Fake model pytest、compile/import、diff check、Git graph確認。
- 長時間runの許可状態: 未許可。実Qwen/GPU、model download、長尺LongVideoBench runを開始しない。
- Git操作: 2026-10-02の実装指示により、Stage/Step branch作成、対象fileだけのmicro-step commit、Step→Stageのlocal `--no-ff` mergeは許可済み。remote push、PR、Stage→main mergeは未許可。Stage→mainはユーザー確認後にのみ `--no-ff` で行う。
- 未検証予定: 実Qwen/GPU品質・速度、実LongVideoBench長時間run。


## 11. Approval（2026-10-02）

ユーザーは本specで定義した以下のStepを実装させるプロンプト作成を明示した。

1. regression再現
2. Agent Config / 表示metadata境界修正
3. regression audit

これを本specの内容承認および実装開始指示として扱い、statusを `approved` とする。

Git操作の許可境界:

- Stage branch作成: 許可済み。
- Step branch作成: 許可済み。
- 対象fileのみをstageしたmicro-step commit: 許可済み。
- Step→Stageのlocal `--no-ff` merge: 許可済み。
- remote push: 未許可。
- PR作成: 未許可。
- Stage→main merge: 未許可。Stage 8完了報告後にユーザー確認を待つ。
- 実Qwen/GPU、model download、長尺LongVideoBench run: 未許可。

実装者はStep 1→2→3を順番に完了し、Stage branch上でSuccess CriteriaとGit graphを確認したところで停止して報告する。
