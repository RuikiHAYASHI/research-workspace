---
date: 2026-09-16
project: agentic-streaming-videoqa
source_todo: null
topic: egocross-sample-selection
status: exploratory
tags: [brainstorm, egocross, sampling, agent]
---

# EgoCross初期サンプル選定

## 出発点

EgoCross testbedは957問（5 domain、4 category）である。初期目的はaccuracyや統計的なbenchmarkではなく、画像列を因果順に処理し、Qwen observationとAgent Memoryのtraceを読むことである。そのため、全体からランダム比率で選ぶより、実装上の境界と研究上の問いを分けて少数の固定recordを使う。

## 3段階のサンプル規模

### 1. Reader / trace機能確認: 5 record、110 frame

| ID | domain | category | frames | 役割 |
|---:|---|---|---:|---|
| 1 | CholecTrack20 | Counting | 5 | 通常JPEG、短系列、0.5 FPS |
| 54 | CholecTrack20 | Counting | 7 | PNG decode |
| 367 | EgoSurgery | Identification | 6 | 1.0 FPS例外 |
| 224 | EgoPet | Identification | 1 | 最短系列・接続smoke |
| 341 | EgoPet | Localization | 91 | 最長系列・EOFと逐次decode |

Qwenは使わず、画像順、decode、timestamp、trace、EOFだけを確認する。91-frame recordを含めても110 image decodeであり、モデル推論を伴わない短時間確認に留まる。

### 2. Qwen接続確認: 2 record、6 frame

- ID 224を1 frameだけ処理し、model load、1画像入力、observation JSONL、artifact保存を確認する。
- 次にID 1を5 frame処理し、current-frame observationが5件順番に保存されることを確認する。

ID 224はAgentの評価対象ではない。1 frameしかないため、Stateの引継ぎやactionの変化を観察できない。

### 3. Observation / Agentの質的レビュー: 5 record、40 frame

| ID | domain | category | frames | 狙い |
|---:|---|---|---:|---|
| 1 | CholecTrack20 | Counting | 5 | 短い手術器具観測 |
| 190 | EgoPet | Localization | 9 | interactionの時点推移 |
| 367 | EgoSurgery | Identification | 6 | 手術ドメインの主体・物体保持 |
| 467 | ENIGMA | Prediction | 15 | 観測と予測に関する不確実性の保持 |
| 712 | ExtrameSportFPV | Identification | 5 | 高速移動する別ドメインの行動観測 |

5 domainすべてとCounting / Localization / Identification / Predictionの4 categoryを含み、合計40 frameである。Agent Controllerでは同じ40 frameについて、Observation、`ADD / UPDATE / KEEP / FLAG_UNCERTAIN`、Memory before/afterを人手で読む。これは定量評価ではなく、Memory操作や不確実性表現の失敗位置を見つけるための固定seed setである。

## 保留

- 957問全体へのQwen / Agent実行は、初期実装の完了条件にしない。
- ID 341の91 frameにQwenを呼ぶ実行は、Memoryが長期で希釈する仮説を調べる別experimentにする。
- 正解ラベルが標準実JSONにないため、このseed setでaccuracyを報告しない。

## Research Spec Handoff

- Reader smoke: ID 1, 54, 367, 224, 341。
- Qwen connection smoke: ID 224、次にID 1。
- Agent質的レビュー: ID 1, 190, 367, 467, 712（40 frame）。
- 初期評価: traceを人手で確認し、future access、action、Memory遷移、不確実性を記録する。
- 対象外: 全957問、accuracy、91-frameのVLM run。
