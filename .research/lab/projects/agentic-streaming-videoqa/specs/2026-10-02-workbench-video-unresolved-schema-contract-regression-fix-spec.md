---
date: 2026-10-02
last_updated: 2026-10-02
project: agentic-streaming-videoqa
type: implementation
status: draft
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 33bb63ded6ed9a95d72108ed69d1860f618470a4
depends_on:
  - 2026-09-30-workbench-agent-modes-and-readable-memory-spec.md
  - 2026-10-02-workbench-inference-agent-config-metadata-regression-fix-spec.md
---

# Workbench: video Situation / Memory unresolved schema contract regression fix spec

## 1. 目的

実LongVideoBench + Qwen3-VLの最初のSituation turnで、モデルが次を返した。

```json
{
  "window_summary": "...",
  "observations": [...],
  "unresolved": false
}
```

Workbenchの `window_observation_v1` validatorは `unresolved` をstring配列として要求するため、

```text
ObservationValidationError: unresolvedは空でない文字列の配列にしてください
```

となり、Situation後にrunが停止した。

本修正では、既に承認済みのschemaを変更せず、Promptとvalidatorの型契約を一致させる。
未解決事項がない場合は `unresolved: []`、ある場合は非空stringの配列を返すことをSituation / Memory Promptへ明示する。

## 2. Evidenceと確認済み原因

### 2.1 実run Evidence

2026-10-02、ユーザーがLongVideoBenchを選択し、実Qwen3-VLでChunk 1を実行した。

Situationのraw outputはwindow summaryと1件のobservationを生成できていたが、末尾が

```json
"unresolved": false
```

であった。

画面はSituation 36.631秒の後、Memoryを実行せずObservationValidationErrorで停止した。

このEvidenceはユーザーの実行画面から確認したもので、ChatGPTがGPU上で再実行した結果ではない。

### 2.2 Validator contract

`src/longvideoqa_workbench/workflow/observations.py` の `validate_video_observation_output()` は、

- `unresolved` がlistであること
- 各要素がnon-empty stringであること

を要求する。

空list `[]` は許容される。

このcontractは、implemented specの `window_observation_v1` と整合しており維持する。

### 2.3 Situation Promptの曖昧さ

現在の

- `prompts/situation/video/initial/prompt.en.txt`
- `prompts/situation/video/initial-with-memory/prompt.en.txt`

は、

```text
Return only one JSON object with window_summary, observations, unresolved.
```

とは指示しているが、`unresolved` のJSON typeを明記していない。

そのため、boolean `false` は自然言語上「未解決事項なし」を表す出力としてモデルが選び得る。

### 2.4 Memory Promptにも同じ曖昧さ

`prompts/memory/video/initial/prompt.en.txt` も、

```text
Return JSON only with events, narrative, unresolved.
```

とだけ記述している。

一方、`validate_video_event_output()` はSituationと同様に `unresolved` をstring配列として要求する。

したがってSituationだけ直すと、次のMemory stageで同型のfailureが起こる可能性がある。

### 2.5 Root cause

原因はstrict validatorではなく、**Promptがoutput schemaの型制約を十分に表現していないこと**である。

## 3. 修正契約

### 3.1 Situation video Prompt

次のbuilt-in Prompt両方へ、同一の型契約を追加する。

- `situation.video.initial`
- `situation.video.previous_text`

必須意味:

```text
unresolved must be a JSON array of non-empty strings.
Use [] when there is no unresolved uncertainty.
Never return false, true, null, or a bare string for unresolved.
```

既存のwindow summary、observations、frame evidence、absolute source time、question relevance、certainty contractは変更しない。

### 3.2 Memory video Prompt

`memory.video.initial` にも同じ `unresolved` 型契約を追加する。

必須意味:

```text
unresolved must be a JSON array of non-empty strings.
Use [] when there is no unresolved issue.
Never return false, true, null, or a bare string for unresolved.
```

events / narrative / evidence / importance contractは変更しない。

### 3.3 Validatorはstrictのまま維持

次は行わない。

- `false -> []` のsilent normalization。
- `null -> []` のsilent normalization。
- bool/stringを配列として受理するcompatibility fallback。
- validation errorを無視してMemory stageへ進むこと。

invalid model outputはraw outputとvalidation errorとして正直に記録する既存方針を維持する。

### 3.4 Prompt snapshot / old run

built-in Prompt本文変更後、新規runは変更後本文と新content hashをsnapshotする。

既存runのsaved resolved prompt / hash / raw outputは変更しない。

PromptServiceの現在のbuilt-in version `v1` semantics自体は本bugfixで再設計しない。Git commitとcontent hashで変更を追跡し、Prompt versioningの再設計は別scopeとする。

## 4. Compatibility

維持するもの:

- `window_observation_v1` schema。
- `event_ledger_v1` schema。
- Situation / Memory validator。
- `observations=[]` と `events=[]` の許容。
- raw / validated output分離。
- Prompt ID。
- Prompt title / description。
- run prompt snapshot。
- old run read-only表示。
- Agent model / generation設定。
- Memory algorithm。
- Answer stage。
- artifact schema。

## 5. 対象外

- boolean `false` をvalidatorで自動変換すること。
- JSON repair / retry Agentの新設。
- constrained decoding / grammar decoding。
- Qwen generation parameterの変更。
- max_new_tokens / temperature変更。
- model変更。
- `cap_pixels_per_frame` warning対応。
- Google翻訳provider。
- Dataset folder初期化bug。
- LongVideoBench dataset変更。
- Memory / Answer algorithm変更。

将来、Promptを明示しても実Qwenでschema violationが頻発する場合は、retry / constrained decoding / repair layerを別brainstorm/specとして検討する。

## 6. Success Criteria

1. 現在の `unresolved: false` がSituation validatorでrejectされることを回帰testで固定する。
2. `unresolved: []` がSituation validatorでpassする。
3. non-empty string listがSituation validatorでpassする。
4. Situation video Prompt 2種に `unresolved` のarray contractが明示される。
5. Situation Promptに「未解決なしは[]」「false/null/stringは禁止」が明示される。
6. Memory video Promptにも同じarray contractが明示される。
7. `unresolved: false` がMemory validatorでrejectされる既存strictnessを維持する。
8. `unresolved: []` がMemory validatorでpassする。
9. Prompt ID / role / input_schema / output_schema metadataを変更しない。
10. 新規runのPrompt snapshotは変更後本文/hashを保存できる。
11. old runのsaved Prompt snapshotを変更しない。
12. Stage 6/7 Prompt UIとrun詳細表示が非回帰。
13. 関連validator / PromptService / workflow tests、compileall、`git diff --check` が通る。
14. 実Qwen/GPUを自動testとして要求しない。

## 7. Ambiguity Gate

### blocking

なし。

approved schemaでは `unresolved` はstring配列で確定しており、現在のPromptが型制約を欠いていることが直接確認できる。

### non-blocking

- 型契約文を1文にまとめるか複数文にするか。
- Prompt contract testを本文substring assertionにするかPromptService経由のresolved body assertionにするか。

既存Prompt/test styleに従い、過度に脆い全文一致testは避ける。

## 8. Implementation Steps / Git Strategy

推論を直接停止するbugのため、Dataset folder bugとは独立して実装可能とする。

Stage branch:

```text
stage-10-video-unresolved-schema-contract-fix
```

Step branches:

```text
stage10-step01-reproduce-unresolved-type-mismatch
stage10-step02-align-video-prompt-schema-contract
stage10-step03-prompt-validator-regression-audit
```

### Step 1: regression再現

- Situation `unresolved=false` rejectionをtest化。
- Situation `[]` / string list acceptanceを確認。
- Memory側もfalse rejection / [] acceptanceを確認。
- Prompt本文が現在array typeを明記していないことを調査Evidenceとして確認。

候補:

- observation validator tests。
- event validator tests。
- PromptService tests。

### Step 2: Prompt contract修正

変更対象:

- `prompts/situation/video/initial/prompt.en.txt`
- `prompts/situation/video/initial-with-memory/prompt.en.txt`
- `prompts/memory/video/initial/prompt.en.txt`
- 必要なregression tests。

実装:

- `unresolved` はJSON array of non-empty strings。
- noneなら `[]`。
- boolean / null / bare stringは禁止。

validator、schema metadata、Agent設定は変更しない。

### Step 3: regression audit

確認:

- PromptService resolve。
- Prompt ID / schema metadata不変。
- validator strictness。
- Prompt snapshot/hash。
- Stage 6 Prompt UI関連test。
- Stage 7 run detail関連test。
- workflow/Fake tests。
- compileall。
- `git diff --check`。

実Qwen/GPUは自動実行しない。

### Git rules

過去Stageと同様:

- Stageは最新mainから作る。
- 各Stepはその時点のStage HEADから作る。
- 対象fileだけstageする。
- micro-step commitは日本語詳細形式。
- Step→Stageはlocal `--no-ff`。
- squashしない。
- push / PR / Stage→mainは実装時の明示許可に従う。
- user dirty changeを巻き込まない。

## 9. Stage Completion Gate

- Section 6を満たす。
- validatorを緩めていない。
- Situation / Memory Prompt双方がschemaを明示。
- old run / Prompt ID / schema metadata非回帰。
- related tests / compile / diff check成功。
- 実Qwen/GPUを勝手に実行していない。
- Git graphとdirty stateを報告可能。

## 10. Implementation Handoff

- approved spec: ユーザー承認後に本書をapprovedへ変更。
- 実装目的: video Situation / Memory Promptの `unresolved` 型指示をvalidator contractと一致させ、実Qwenのboolean出力によるrun停止を防ぐ。
- 基準repository/commit: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `33bb63ded6ed9a95d72108ed69d1860f618470a4`。着手時に最新mainを再確認。
- 変更scope: Section 3、Section 8。
- 対象外・維持条件: Section 4–5。
- success criteria: Section 6。
- 許可されている短時間検証: PromptService / validator / workflow / browser Fake tests、compile/import、diff check。
- 長時間runの許可状態: 未許可。
- Git操作: draft段階。実装開始指示後にStage/Step topologyを使用。
- 未検証予定: Prompt修正後の実Qwen schema adherence率、実LongVideoBench品質・速度。
