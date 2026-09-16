---
date: 2026-09-16
project: agentic-streaming-videoqa
source_todo: null
topic: egocross-observation-repository-boundary
status: exploratory
tags: [brainstorm, egocross, repository, streaming-videoqa]
---

# EgoCross Observation Prototypeのリポジトリ境界

## 判断したいこと

EgoCrossの画像列を1枚ずつ処理する初期検証を、既存の`2026_09_hayashi_streaming_video_qa`へ追加するか、新規リポジトリに分けるかを検討した。

## Evidence

- 既存repositoryは、50Saladsを`sequential_loader`経由で読むこと、Qwen3-VLによるtext Memory更新、EOF後の最終QA、run artifactを目的としている。
- EgoCrossの最小検証は、JSON順の画像列を1枚ずつ観測してframe-level observation traceを得る段階であり、loader一般化、Memory、最終QAを必要としない。
- 両者はQwen呼び出しやJSONL artifactという一部の実装を共有し得るが、入力契約・成功条件・失敗の読み方が異なる。

## 比較

| 選択肢 | 利点 | 欠点 |
|---|---|---|
| 既存Streaming VideoQA repositoryへ追加 | Qwen wrapperやartifact writerを再利用できる | 50Salads/loader/Memory/QAとEgoCross/観測traceが一つのCLI・依存・テストに混ざり、最小検証の失敗原因が見えにくい。 |
| 新規EgoCross Observation repository | 入力データ、観測trace、実行手順、依存を最小に保てる。既存の完了済み50Salads実装を安定に残せる。 | Qwen wrapperやartifact writerを最小限コピーまたは再実装する必要がある。 |

## 有力な方向性

新規repositoryを作り、EgoCross専用の短いprototypeとして始める案を推奨する。repositoryは研究ワークスペース上の独立プロジェクトにはせず、同じ`agentic-streaming-videoqa`プロジェクトのコード実験として管理する。

初期repositoryの責務は次に限定する。

1. EgoCross testbed JSONの指定recordを読む。
2. `video_path`の記載順で画像を1枚ずつdecodeする。
3. record ID、配列index、相対timestamp、画像pathをJSONLへ保存する。
4. 次段階として、Qwenが各frameに対して生成した観測文を同じtraceへ追加する。

`sequential_loader`、text Memory、final QA、MCQ採点、full benchmarkは依存にもscopeにも含めない。

## 未決事項

- 新repository名と、初期段階でQwen観測まで入れるか、decode traceだけに留めるか。
- Qwen wrapperとartifact writerを既存repositoryからコピーするか、初期はより小さい実装にするか。

## Research Spec Handoff

- 対象プロジェクト: agentic-streaming-videoqa
- 採用候補: 新規のEgoCross Observation prototype repository。
- 実装目的: 画像列の因果的な1-frame観測traceを得る。
- scope: EgoCross JSON reader、Pillow decode、JSONL trace、必要ならframe observation用Qwen呼び出し。
- 対象外: `sequential_loader`、Memory、final QA、採点、全件run。
- 主要な未決事項: repository名、初回実行の到達点。
