---
date: 2026-09-16
project: agentic-streaming-videoqa
source_todo: null
topic: egocross-image-sequence-loader
status: exploratory
tags: [brainstorm, egocross, sequential-loader, streaming-videoqa]
---

# EgoCross画像列をSequential Loaderへ接続する壁打ち

## 読み込んだ文脈とEvidence

- プロジェクトの現在方針は、Queryをt=0から既知とし、1 frameずつ `current frame + previous text memory` を処理する因果的な最小VideoQAである。
- `sequential_loader` は、Dataset Adapterが`SequenceSource`を定義し、Coreがchunk順序、padding、lifecycleを担当する構造である。既存の`SequentialVideoReader`はPyAVで動画をdecodeするため、画像列はそのままでは読めない。
- EgoCrossの標準testbed JSONは957レコードで、各レコードの`video_path`は動画ファイルではなく、順序付きの画像path配列である。長さは1〜91枚で、JPEGとPNGが混在する。
- 標準testbedにフレームごとの明示timestampはない。公開READMEは通常0.5 FPS、EgoSurgeryおよびCholecTrack20のVID25・VID111は1 FPSとする。時刻付き派生JSONには`sampled_fps`と`timestamp_rule`がある。
- 既存のStreaming Text Memory実装は50Salads専用sourceとCLIを持つ。Qwen実ロード・実データsmokeは未実行である。

## 中心の問い

動画へ再エンコードせず、EgoCrossの1問分の画像列を有限長の逐次sequenceとして、`sequential_loader`の既存Core契約へ接続できるか。

## 比較した設計

| 案 | 内容 | 判断 |
|---|---|---|
| 画像を動画へ変換して既存VideoReaderを使う | JPEG/PNG列を一時動画にしてPyAV decodeする | 棄却。変換条件が新しい観測・時刻契約を作り、原画像との対応も曖昧になる。 |
| 全画像pathを`source_metadata`に入れる | Readerがpathを取得しやすい | 棄却。metadataは各`SequentialSample`へ転送されるため、下流consumerにfuture画像のpath列を露出する。 |
| EgoCross Adapterと画像列Readerを追加する | AdapterがJSON順を定義し、Readerが必要な画像だけをPillowでdecodeする | 採用候補。既存のAdapter/Core/Reader境界を維持し、raw imageを先読みしない。 |

## 有力方針

### Sequenceの定義

- 標準testbed JSONの1レコードを1つの有限長sequenceとする。
- `sequence_id`と`source_id`はrecord IDから決定的に作る。複数のrecordが同じ元動画・同じ画像を参照しても、質問が異なれば別sequenceとして扱う。
- `stop_frame`は`len(video_path)`として明示し、EOF探索のためのlookaheadは使わない。
- 画像順はJSONの`video_path`配列順だけで決める。ファイル名順への再sortや、元動画のFPSに基づく再samplingはしない。

### AdapterとReaderの責務

- `EgoCrossTestbedAdapter`はJSONをparseし、record ID、質問、選択肢、データセット名、カテゴリ、相対時刻規則を含む`SequenceSource`を生成する。
- Adapterは、Readerだけが参照する`record ID -> ordered image paths`のcatalogを保持する。path列そのものは`source_metadata`、`dataset_metadata`、`evaluation_reference`へ転送しない。
- `EgoCrossImageSequenceReader(adapter=...)`は、要求された連続rangeの画像だけをPillowでRGBの`uint8 [T, 3, H, W]` tensorへdecodeする。将来画像のdecode、画像列全体のtensor化、読み込み失敗のskipは行わない。
- `source_metadata`にはQueryとして許される質問と選択肢、sampled FPS、timestamp originだけを置く。最終QAを採点する正解ラベルは標準JSONにないため扱わない。

### Timestampの意味

- `frame_index`は配列内の0始まりの位置である。元ファイル名に含まれる番号は使用しない。
- `timestamp = frame_index / sampled_fps`とする。`sampled_fps`はrecordに明示値があればそれを使い、標準testbedでは公開READMEの0.5 FPS規則と既知の1 FPS例外から決める。
- このtimestampは抽出画像列の相対時刻であり、元動画の絶対時刻・PTS・evidence window開始時刻ではない。metadataにこのoriginを明記する。

### 実データ動作確認の段階

1. synthetic画像とJSONによるunit/integration testで、順序、bounded終端、RGB変換、PNG/JPEG、時刻、失敗時のfail-fastを確認する。
2. 実EgoCrossでQwenをロードせず、record ID 1（通常JPEG）、54（PNG）、367（EgoSurgery 1 FPS）、224（1 frame）、341（91 frames）を`SequentialDataset`経由で読む。画像数、連続index、相対timestamp、`is_last`、resource解放を確認する。
3. Streaming VideoQA repositoryではpublic APIだけを使うEgoCross sourceとCLI分岐を追加し、record ID 224の1 frame、次にID 1の5 framesで実Qwen smokeを行う。JSONLのMemory連鎖とfinal artifactを確認する。
4. 91-frame recordや957問全体のQwen実行、正解率評価、LoRA、Memory方式比較は別experimentとして扱う。

## 未解決事項

- 標準testbedの1 FPS例外を、公開README記載のVID25・VID111とEgoSurgeryに限ることでよいか。現時点では公開データカードを根拠に採用候補とする。
- 実Qwen smokeに使う既存VLM環境、GPU、モデルcacheの利用可否。これは実装完了後の短時間runの前提であり、コード仕様のblocking項目ではない。
- 標準testbedには正解ラベルがないため、初期smokeの成功判定は逐次処理・artifact・traceのみとし、精度評価は定義しない。

## Research Spec Handoff

- 対象プロジェクト: agentic-streaming-videoqa
- 元依頼: EgoCrossの画像束を動画として扱い、現在の`sequential_loader`へ実装し、実データ動作確認を行う計画を作る。
- 採用方向: JSONの1レコードを1有限長sequenceとする専用Adapterと画像列Readerを`sequential_loader`へ追加する。
- 実装候補: Adapter、Reader、public API、unit/integration tests、Streaming VideoQA側のEgoCross CLI/source、短時間実Qwen smoke手順。
- 評価: synthetic test、選定5 recordのReader実データsmoke、1 frameと5 framesのQwen trace。精度は測定しない。
- 対象外: 動画再エンコード、全問実行、学習/LoRA、採点、Memory方式比較。
- 関連: `experiments/2026-09-15-egocross-qwen-local-investigation.md`、`specs/2026-09-15-streaming-text-memory-spec.md`。
