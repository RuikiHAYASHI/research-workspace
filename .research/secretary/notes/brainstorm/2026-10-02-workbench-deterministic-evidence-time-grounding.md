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
