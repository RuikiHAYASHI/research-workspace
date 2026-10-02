---
date: 2026-10-02
last_updated: 2026-10-02
project: agentic-streaming-videoqa
type: implementation
status: approved
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: c35b3e2b5a081a5dd953ed36830bc18eb640cc16
depends_on:
  - 2026-09-30-workbench-agent-modes-and-readable-memory-spec.md
  - 2026-10-02-workbench-video-unresolved-schema-contract-regression-fix-spec.md
---

# Workbench: video observation / event time-range contract regression fix spec

## 1. 目的

Stage 9統合後の実LongVideoBench + Qwen3-VL runで、Situation Agentの `unresolved` は正しく `[]` になった一方、最初のChunkで次の出力が生成された。

```json
{
  "window_summary": "...",
  "observations": [
    {
      "start_seconds": 0.0,
      "end_seconds": 4.0,
      "evidence_frame_indices": [0, 12, 24, 36, 48, 60, 72, 84],
      "question_relevance": "high",
      "certainty": "fact"
    }
  ],
  "unresolved": []
}
```

入力windowは `[0.0, 4.0)` 秒だが、manifest上の最後の採用frameのactual source-video timestampは約 `3.503` 秒である。

現在の `validate_video_observation_output()` は、observationの `start_seconds/end_seconds` をmanifest上の最小actual timestamp〜最大actual timestampの範囲内に制約するため、

```text
ObservationValidationError: 動画観測0の時刻が元動画実時刻と整合しません
```

となりrunが停止した。

本修正では、actual source-video frame timestampを証拠時刻の正本とする既存contractを維持し、Situation / Memory video Promptのtime-range指示をvalidatorと一致させる。

## 2. Evidenceと確認済み原因

### 2.1 実run Evidence

2026-10-02、ユーザーが実LongVideoBench + Qwen3-VLで4秒・8frame設定のChunk 1を実行した。

画面上で以下を確認した。

- Situation raw outputはJSONとして成立。
- `unresolved: []` となっており前回のunresolved型修正は有効。
- observationは `start_seconds: 0.0`, `end_seconds: 4.0`。
- evidence frameは0.0秒から約3.503秒までのmanifest frameを参照。
- validationは時刻整合性で停止し、Memory stageへ進まなかった。

このEvidenceはユーザーの実run画面から確認したものであり、ChatGPTがGPU runを再実行した結果ではない。

### 2.2 Current Prompt

Situation video Promptは、

```text
Original video window: [{{chunk.start}}, {{chunk.end}}) seconds.
...
Use source-video absolute seconds.
```

と記述している。

一方、各observationの `start_seconds/end_seconds` を
**current frame manifestのactual timestamp範囲内に限定すること**、
およびchunk boundaryをそのままobservation boundaryへ使わないことは明示していない。

そのため、モデルがwindow全体を要約する際に `[0.0, 4.0]` 相当の区間を返すのは自然である。

### 2.3 Current Validator

`validate_video_observation_output()` はcurrent manifestのactual timestampについて、

```python
lower = min(frame.timestamp_seconds)
upper = max(frame.timestamp_seconds)
```

を作り、

```text
lower <= start_seconds <= end_seconds <= upper
```

を要求する。

さらに、全 `evidence_frame_indices` のactual timestampがobservation interval内に含まれることを要求する。

このstrictnessは「元動画actual timestampを証拠時刻の正本にする」というimplemented specと整合する。

### 2.4 Memory Eventにも同型contractがある

`validate_video_event_output()` もcurrent manifestのactual timestamp最小〜最大を使い、eventの `start_seconds/end_seconds` とevidence frame timestampの整合を要求する。

Memory video Promptは「current manifest frame IDs/timesだけをciteする」と指示しているが、event boundariesの許容範囲を明示していない。

Situationだけ修正すると、Memoryで同型のtime-range violationが起きる可能性がある。

### 2.5 Root cause

原因はvalidatorが厳しすぎることではなく、**window boundaryとevidence timestamp boundaryの意味がPrompt上で十分に区別されていないこと**である。

`chunk.end=4.0` はstreaming windowのhalf-open境界であり、current manifest上のactual observed frame timestampではない。

## 3. 修正契約

### 3.1 Situation video Prompt

次の2 Promptへ同じtime contractを追加する。

- `situation.video.initial`
- `situation.video.previous_text`

必須意味:

```text
For every observation, start_seconds and end_seconds must be source-video absolute seconds within the minimum and maximum actual timestamps present in the current frame manifest.

Every cited evidence frame timestamp must lie inside [start_seconds, end_seconds].

Do not use the chunk/window end boundary as end_seconds unless that value is also an actual timestamp of a current manifest frame.
```

例として、4秒windowでmanifest actual timestampsが `0.000 ... 3.503` の場合、`end_seconds: 4.0` は禁止し、最大でも `3.503` 相当までにする。

frame timestampを丸めて存在しない精度を創作しない。manifestに提示されたactual source timestampを基準にする。

### 3.2 Memory video Prompt

`memory.video.initial` のeventにも同じtime contractを明示する。

- event start/endはcurrent manifest actual timestamp範囲内。
- cited evidence frame timestampはevent interval内。
- chunk boundaryをmanifest frame timestampと混同しない。

### 3.3 Validatorは維持

次は行わない。

- `end_seconds <= window.end_seconds` へvalidatorを緩めること。
- out-of-manifest boundaryをsilent clampすること。
- 4.0 -> 3.503の自動補正。
- evidence frameと矛盾するtime rangeを受理すること。
- validation failureを無視してMemoryへ進むこと。

invalid raw outputはそのまま保存し、validation errorを明示する現在の方針を維持する。

### 3.4 Window boundaryとevidence timeを区別

UI/Prompt上の

```text
Original video window: [start, end)
```

はstreaming区間を表す。

observation/eventの `start_seconds/end_seconds` は、**current sampled evidenceにより支持されるsource-video absolute time interval**を表す。

両者を同一の値に強制しない。

## 4. Compatibility

維持するもの:

- 4秒window / 8 sampled frame設定。
- target timestampとactual timestampの区別。
- actual timestampを一次Evidenceとして扱う方針。
- `window_observation_v1`。
- `event_ledger_v1`。
- existing validators。
- Prompt IDs / metadata schemas。
- `unresolved` array contract。
- old run prompt snapshots。
- raw / validated output分離。
- Memory / Answer algorithm。
- run artifact schema。

## 5. 対象外

- sampling algorithm変更。
- target timestampをactual timestampへ置換。
- validatorのtime tolerance拡大。
- automatic JSON/time repair。
- retry Agent。
- constrained decoding。
- generation parameter変更。
- Qwen model変更。
- `cap_pixels_per_frame` warning対応。
- folder regression。
- Google翻訳。
- 実験精度評価。

## 6. Success Criteria

1. 実run相当のmanifest（例: actual timestamps 0.000〜約3.503）に対し、observation `end_seconds=4.0` がrejectされることをtestで固定する。
2. 同じobservationで `end_seconds=max(manifest actual timestamp)` ならpassする。
3. evidence frame timestampがobservation interval外なら引き続きrejectする。
4. Situation video Prompt 2種にmanifest actual timestamp範囲のcontractが明示される。
5. chunk/window end boundaryをactual frame timestampと混同しない指示が明示される。
6. Memory video Promptにもevent time-range contractが明示される。
7. Memory validatorのstrictnessを変更しない。
8. Prompt IDs / metadata / input/output schemaを変更しない。
9. previous-text Situation Promptも同じcontractを持つ。
10. 新規runのPrompt snapshot/hashに変更後本文が反映される。
11. old run snapshotを変更しない。
12. Stage 6/7/9のPrompt/UI/workflow回帰testが通る。
13. validator/PromptService/workflow tests、compileall、`git diff --check` が通る。
14. 実Qwen/GPUを自動testとして要求しない。

## 7. Ambiguity Gate

### blocking

なし。

implemented specではactual source frame timestampをmanifestの証拠時刻として保持することが確定しており、current validatorもその契約を実装している。

### non-blocking

- Prompt文面の具体的な英語表現。
- test fixtureで3.5と3.503のどちらを使うか。

実際のcontractを示せる最小fixtureと既存Prompt styleに従う。

## 8. Implementation Steps / Git Strategy

Stage branch:

```text
stage-10-video-time-range-contract-fix
```

Step branches:

```text
stage10-step01-reproduce-window-boundary-time-mismatch
stage10-step02-align-situation-memory-time-contract
stage10-step03-time-contract-regression-audit
```

### Step 1: regression再現

- current validatorでmanifest maxより大きいend_secondsがrejectされるtest。
- max actual timestampまでならpassするtest。
- evidence refsがinterval外ならrejectするtest。
- Situation / Memory Promptでtime boundary指示が不足している現状確認。

### Step 2: Prompt contract修正

変更候補:

- `prompts/situation/video/initial/prompt.en.txt`
- `prompts/situation/video/initial-with-memory/prompt.en.txt`
- `prompts/memory/video/initial/prompt.en.txt`
- relevant tests。

validatorは変更しない。

### Step 3: regression audit

- Observation/Event validator。
- PromptService。
- Prompt snapshot/hash。
- Stage 6/7/9 Prompt UI。
- Fake workflow。
- old run read。
- compileall。
- `git diff --check`。

実Qwen/GPU/LongVideoBench実runは自動実行しない。

### Git rules

過去Stageと同様:

- 最新mainからStage branch。
- 各Stepはその時点のStage HEADから作成。
- 対象fileだけstage。
- 日本語詳細commit。
- squashしない。
- Step→Stageはlocal `--no-ff`。
- push / PR / Stage→mainは実装開始時の明示許可に従う。

## 9. Implementation Handoff

- approved spec: 本書。2026-10-02、ユーザーがStage 10実装用プロンプト作成を明示し、本specの実装開始を承認した。
- 実装目的: Situation / Memory video Promptのevent time-range指示をactual manifest timestamp validator contractと一致させる。
- 基準repository/commit: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `c35b3e2b5a081a5dd953ed36830bc18eb640cc16`。着手時に最新mainを再確認。
- 変更scope: Section 3、Section 8。
- 対象外・維持条件: Section 4–5。
- success criteria: Section 6。
- 許可されている短時間検証: validator / PromptService / workflow / browser Fake tests、compile/import、diff check。
- 長時間runの許可状態: 未許可。
- Git操作: 2026-10-02の実装開始指示により、Stage/Step branch作成、対象fileだけのmicro-step commit、Step→Stageのlocal `--no-ff` mergeは許可済み。remote push、PR、Stage→main mergeは未許可。
- 未検証予定: Prompt修正後の実Qwen time-range adherence率、実LongVideoBench品質・速度。


## 10. Approval（2026-10-02）

ユーザーは本specに対する「Stage 10実装用プロンプト」を明示的に依頼した。
これを本specの内容承認および実装開始指示として扱い、statusを `approved` とする。

実装順はSection 8のとおり、Step 1 → Step 2 → Step 3とする。

Git操作の許可境界:

- Stage branch `stage-10-video-time-range-contract-fix` 作成: 許可済み。
- Step branch作成: 許可済み。
- 対象fileのみをstageしたmicro-step commit: 許可済み。
- Step→Stageのlocal `--no-ff` merge: 許可済み。
- remote push: 未許可。
- PR作成: 未許可。
- Stage→main merge: 未許可。Stage 10完了報告後にユーザー確認を待つ。
- 実Qwen/GPU、model download、LongVideoBench実run、Google Cloud Translation実API: 未許可。

実装者はStep 1〜3をStage branchへ統合し、Success CriteriaとGit graphを確認したところで停止して報告する。
