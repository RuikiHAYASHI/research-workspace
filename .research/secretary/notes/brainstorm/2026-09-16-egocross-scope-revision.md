---
date: 2026-09-16
project: agentic-streaming-videoqa
source_todo: null
topic: egocross-scope-revision
status: exploratory
tags: [brainstorm, egocross, streaming-videoqa, scope]
---

# EgoCross初期検証のscope再検討

## 出発点

EgoCrossの画像列を`sequential_loader`へ接続し、Qwenで最終QAまで行うdraftを作成した後、loader一般化と最終QAが最初の研究目的に必要かを再検討した。

## 現在の問い

最初に確認したいのは、EgoCrossの画像列を因果順に1枚ずつ観測し、各時点の出力を監査可能なtraceとして残せるかである。

## 評価した選択肢

| 選択肢 | 利点 | コスト・問題 | 判断 |
|---|---|---|---|
| `sequential_loader`へ画像列Adapter/Readerを追加 | 将来の画像列datasetに共通のAPIを提供できる | Reader、manifest catalog、Pillow依存、相対timestamp、public API互換性を新たに設計・検証する。EgoCross初期traceには過剰。 | 保留 |
| Streaming VideoQA側にEgoCross専用iteratorを置く | JSON順の1枚ずつの観測を最短で検証でき、失敗箇所を切り分けやすい | dataset固有コードになる | 採用候補 |
| 最初からtext Memoryと最終QAを実装 | end-to-endの見た目を早く得られる | 観測、Memory更新、MCQ形式、最終回答が混ざり、標準testbedに正解ラベルもないため評価できない | 保留 |

## 有力な最小構成

1. 指定record IDのJSONを読み、`video_path`配列順で1枚ずつPillow RGBとしてyieldする。
2. record ID、配列index、相対timestamp、画像path、画像decode結果をframe単位のJSONLに保存する。
3. 最初はVLMを呼ばず、順序、欠損、1枚ずつの読込、trace再現性を実データで確認する。
4. 次にVLMを接続する場合も、完了条件はframeごとの短い観測文の保存に限定する。previous text Memory、final QA、選択肢への回答正規化、採点は段階を分ける。

標準testbedのtimestampは`frame_index / sampled_fps`による抽出画像列の相対時刻として記録し、元動画の絶対時刻として扱わない。

## 判断理由

- `sequential_loader`は動画containerとその逐次decodeの共通基盤であり、EgoCrossは有限の画像path列である。両者を共通化する価値は、複数datasetへの再利用要求が明確になった時点で評価できる。
- 標準testbedの実JSONには正解ラベルがなく、最終QAの精度を初期成功条件にできない。
- observation traceなら、future画像を使わないこと、VLMが各画像に応答できること、後続のMemory設計に必要な情報を直接観察できる。

## 現在の方向性

`sequential_loader`対応を含む`2026-09-16-egocross-image-sequence-smoke-spec.md`はdraftのまま承認しない。次のspec化では、Streaming VideoQA repository内のEgoCross専用iteratorとframe-level observation traceだけを最小scopeとする。

## Research Spec Handoff

- 対象プロジェクト: agentic-streaming-videoqa
- 採用方向: EgoCross専用iterator + frame-level observation trace。
- 変更scope: Streaming VideoQA repositoryのみ。loaderは変更しない。
- 成功条件: 指定recordの画像をJSON順に1枚ずつdecodeし、再現可能なframe traceを保存する。VLM接続時は1画像につき1観測文を保存する。
- 対象外: `sequential_loader`一般化、text Memory更新、final QA、MCQ採点、全件実行、精度評価。
- 保留: 共通画像列Reader、Memory更新、最終QA。複数datasetへの再利用またはtraceのEvidenceが出た時点で再検討する。
