---
date: 2026-10-02
project: agentic-streaming-videoqa
source_todo: null
topic: workbench-deterministic-evidence-time-grounding
status: exploratory
tags: [brainstorm, research, workbench, timestamp, grounding]
---

# Workbench: model生成時刻をやめた決定的Evidence時刻導出の壁打ち

## 出発点

実LongVideoBench + Qwen3-VLで、Situation Agentの出力がschema validationを繰り返し停止させた。

2026-10-02時点で確認した例:

- 4秒window / 8 sampled frame。
- target timestampは概念上 `0.0, 0.5, ..., 3.5`。
- actual source-video timestampは動画PTSに従うため、例として `0.0, 0.500..., 1.001..., ..., 3.503...`。
- Situationは `evidence_frame_indices` を正しく参照しつつ、`end_seconds: 4.0` を返すことがある。
- strict validatorはcurrent manifestのactual timestamp最大値を超えるためrejectする。
- Stage 10ではPromptにtime contractを追記したが、Prompt遵守だけに依存する構造自体は残る。

## 現在の確認済み実装

### target sampling

`tamaki-lab/sequential_loader` の `TimeGridSamplingPolicy` はwindow内を等間隔targetへ分ける。

`TargetFrameSelector` は各targetについて、単調にdecodeされたframeのうち **timestamp >= targetを初めて満たすframe** を採用する。

そのためactual timestampはtargetと完全一致するとは限らない。これは異常なdriftではなく、元動画PTS/frame gridへの量子化として自然である。

### Workbench manifest

Workbenchは各sampled frameについて少なくとも次をPromptへ渡す。

- `video_ordinal`
- `frame_index`
- `timestamp_seconds` = actual source-video timestamp
- `target_timestamp_seconds`

### Current validation

Situation / Memory validatorはmodelが生成した `start_seconds/end_seconds` をactual timestamp範囲と照合し、さらにcited evidence frame timestampがinterval内に入ることを要求する。

## 問い

`start_seconds/end_seconds` はmanifestと `evidence_frame_indices` から決定的に導出できるにもかかわらず、なぜLLMに再生成させる必要があるか。

特にactual timestampが `3.503...` のような値になる動画では、LLMへ浮動小数の忠実な再生成を要求し、その結果を `1e-6` toleranceで検証すること自体が脆い可能性がある。

## 仮説

他動画でエラーが出なかった理由は、sampling処理の正常/異常差ではなく、以下のいずれかである可能性が高い。

1. actual timestampがtargetときれいに一致し、LLMがmanifest値をコピーしやすかった。
2. LLMがそのrunでは `end_seconds=3.5` 等を返し、validatorを通過した。
3. failing videoではwindow boundary `4.0` がPrompt上で強く見え、LLMがevent boundaryとして採用した。
4. actual timestampが複雑な小数であるほど、LLMが丸める・window境界へ置き換える確率が上がる。

現時点で「decoderが誤った時刻を返している」というEvidenceはない。

## 有力案: modelはsemantic evidenceだけを返し、時刻はbackendで導出する

Situation observationのmodel出力から `start_seconds/end_seconds` を外す。

modelに返させる候補:

```json
{
  "description": "...",
  "evidence_frame_indices": [24, 36, 48],
  "question_relevance": "high",
  "certainty": "fact"
}
```

validator/backendがmanifestからcanonical timeを決定する。

```text
start_seconds = min(actual_timestamp(frame_id) for cited evidence)
end_seconds   = max(actual_timestamp(frame_id) for cited evidence)
```

Memory eventも同様に、current evidence frame IDsからcanonical time intervalを導出する。

### 利点

- LLMによるtimestamp hallucination/roundingを除去できる。
- target / actual / window boundaryの混同をmodel出力schemaから排除できる。
- actual timestampをEvidenceの正本にする既存方針と一致する。
- raw model outputとcanonical structured outputの責務が明確になる。
- 動画fps/PTSの違いによるschema adherence差を減らせる。
- Promptを短くできる。

### 注意点

- eventが「2つの証拠frameの間の連続動作」を表す場合、min/max evidence timestampは観測可能なsupport intervalであり、真のevent開始/終了時刻ではない。
- したがってfieldの意味を `event true temporal boundary` と主張せず、`evidence_time_range` として扱う方が正確かもしれない。
- 既存artifact/UIとの互換性をどう保つかをspecで決める必要がある。

## schema候補

### A. 既存structured outputを維持し、raw model schemaだけ簡略化

model output:
- `description`
- `evidence_frame_indices`
- relevance/certainty

backend validated structured output:
- 上記
- `start_seconds`
- `end_seconds`

を追加する。

artifact/UIは現在と近い形を維持できる。

### B. field名もEvidence意味へ変更

canonical structured outputを `evidence_start_seconds` / `evidence_end_seconds` へ変更する。

意味は最も明確だがartifact/schema/UI migrationの影響が大きい。

### C. 時刻を持たず、UI表示時に都度manifestから導出

最も正規化されるが、artifact単体の可読性と既存downstream利用に影響する。

## 現在の方向性

有力候補は **A**。

理由:
- modelから冗長なtimestamp生成を除去できる。
- actual timestampのSSOTをmanifestに一本化できる。
- existing UI/artifactの `start_seconds/end_seconds` 表示をbackend derived fieldとして維持しやすい。
- 研究上の意味変更を最小化できる。

ただし、field名の `start_seconds/end_seconds` が「真のevent境界」と誤読される懸念があるため、UIラベル・schema documentationでは「Evidence区間」であることを明示する候補を残す。

## 反例・未解決

- 1枚のevidence frameだけをciteした場合、derived intervalはzero-lengthになる。それでUI/Memory意味上問題ないか。
- 複数frameの間で発生した動作について、min/max cited frameをevent durationとして扱うのが妥当か。
- Memoryが過去window eventを再記述する場合、current manifestだけからderiveする現在contractで十分か。
- evidence frame ID自体をLLMに生成させる契約は引き続き必要。将来的にはvideo ordinalを出させてbackend mappingする方がrobustかもしれない。
- modelが誤ったframe IDをciteした場合はstrict rejectを維持するか、retryを導入するか。

## Stage 10状態

2026-10-02にWorkbench `main` を再確認。

- main HEAD: `09b5b4277981dc985d4ceb1d499e90ea1ee93040`
- commit: `Stage 10: video observationとeventの実時刻契約修正をmainへ統合`
- Stage 10はGitHub `main` へmerge/push済み。
- Promptにはactual manifest timestamp範囲を使うtime contractが追加済み。

Stage 10はPrompt adherence改善であり、model-generated timestampという設計自体は変更していない。

## 次の判断候補

1. model raw outputから `start_seconds/end_seconds` を削除し、backendでevidence refsから導出する方向を採用するか。
2. canonical field名を既存の `start_seconds/end_seconds` のまま維持するか、`evidence_*` へ変更するか。
3. single-frame evidenceのzero-length intervalを許容するか。
4. その後、research-specでnew model output schema / backward compatibility / artifact semanticsを確定する。


## 2026-10-02 14:16 追記: Situation Agent出力の重複整理

Situation Agentの出力に `window_summary` と `description` の両方を持たせる必要はない、というユーザー判断を記録する。

### 判断

- `window_summary` と `description` は役割が重複しており、Situation Agentの1回の推論から両方を生成・保持する設計は不要。
- Situation Agentのsemantic text outputは、原則として単一の情報表現へ整理する方向とする。
- どちらのfield名を残すか、また既存artifact/UI/Memory Agentとの互換性をどう扱うかは、現行実装と後段データフローを確認した上でspecで確定する。
- この記録は設計判断のbrainstormであり、現時点ではコード変更やapproved specを意味しない。

### 背景

現在の構成ではSituation Agentが同一レスポンス内で複数fieldを構造化出力する想定であり、`window_summary` を生成した後に別推論で `description` を生成する2段階構成ではない。そのため、意味の近い2つのtext fieldを同時に保持することによる情報上の利点が明確でなく、schema・prompt・downstream処理を複雑にする可能性がある。

### 次のspec候補

- Situation Agentのcanonical semantic text fieldを1つに統一する。
- field名を `description` とするか `window_summary` とするかを、現在コード・artifact・UI・Memory入力の利用箇所を確認して決める。
- 既存保存済みartifactとの後方互換性が必要かを確認する。


## 2026-10-02 14:24 追記: deterministic time derivation方針を採用

ユーザーは、Situation / Memory Agentに `start_seconds/end_seconds` を生成させず、モデルが返したEvidence参照からbackendが時刻を決定的に導出する方向を採用した。

### 採用方向

model raw outputでは、時刻そのものを出力させない。

Situation observationのmodel出力候補:

```json
{
  "description": "...",
  "evidence_frame_indices": [24, 36, 48],
  "question_relevance": "high",
  "certainty": "fact"
}
```

backendはvalidated evidence refsからactual source-video timestampを参照し、

```text
start_seconds = min(actual timestamp of cited evidence frames)
end_seconds   = max(actual timestamp of cited evidence frames)
```

をcanonical structured outputへ付与する。

Memory eventも同様に、model-generated `start_seconds/end_seconds` を廃止し、validated evidence refsからbackendが導出する方向とする。

### canonical output互換性

現時点の最有力は、model raw schemaから時刻fieldを削除しつつ、backendで導出した `start_seconds/end_seconds` をcanonical validated structured outputには残す案。

これにより:

- UI / artifactの既存time表示を維持しやすい。
- model-generated floatの丸め・hallucinationを除去できる。
- actual timestampのSSOTをmanifestへ一本化できる。
- old runはsaved raw/validated outputをそのままread-onlyで保持できる。

時刻fieldの意味は真のevent boundaryではなく、**cited evidenceが支持するEvidence time range**として文書化する必要がある。

### Stage 10の扱い

Stage 10差分をGitHubで確認した結果、変更は以下のみ。

- Situation video Prompt 2種へのtime contract追記。
- Memory video Promptへのtime contract追記。
- Prompt/time validator回帰test追加。

validator本体、artifact schema、sampling、runtimeはStage 10で変更していない。

したがってStage 9へreset/revertする必要はない。公開済みmainの履歴を巻き戻さず、Stage 10を「Prompt adherenceで解決を試した履歴」として残し、次Stageで以下をforward changeする方針とする。

- Stage 10で追加したmodel向けtime contract文を削除または再構成。
- model raw schemaから `start_seconds/end_seconds` を削除。
- backend validator/enrichmentでEvidence refsから時刻を導出。
- Stage 10のPrompt-time adherence testを新しいdeterministic derivation testへ置換・整理。

### Git方針

次の実装Stageは現在の `main@09b5b4277981dc985d4ceb1d499e90ea1ee93040` を起点にする。

Stage 9 `c35b3e2...` へreset/revertしない。Stage 10のmerge履歴を保持したまま新設計へ進める。

### 未決事項

research-spec化時に以下を確定する。

1. Situation raw model schemaから `start_seconds/end_seconds` を完全削除する。
2. Memory raw event schemaからも同fieldを完全削除する。
3. canonical validated structured outputでは互換性のため同fieldをbackend-derived値として維持する。
4. single evidence frameの場合は `start_seconds == end_seconds` のzero-length Evidence区間を許容する。
5. UI/文書上では時刻を「eventの真の開始終了」ではなく「Evidence区間」として扱う。


## 2026-10-02 14:40 昇格

このbrainstormで採用したdeterministic Evidence時刻導出方針は、次のapproved specへ昇格した。

- `.research/lab/projects/agentic-streaming-videoqa/specs/2026-10-02-workbench-deterministic-evidence-time-derivation-spec.md`

以後の実装契約は上記specを正本とする。
