---
date: 2026-09-16
project: agentic-streaming-videoqa
status: draft
topic: egocross-image-sequence-smoke
source: 2026-09-16 EgoCross image-sequence loader brainstorm
last_updated: 2026-09-16
---

# EgoCross画像列Adapterと実データStreaming Smoke Spec

## 目的

EgoCrossの標準testbedを、動画への再エンコードなしで、画像列を順次観測する有限長sequenceとして`sequential_loader`へ接続する。続けて、既存のStreaming Text Memoryパイプラインがこのpublic APIを通じて、少数の実EgoCrossレコードをQwen3-VLへ1 frameずつ渡せることを確認する。

このspecが確認するのは、データ読込、因果的な1 frame入力、Memory trace、artifact保存である。EgoCrossのQA精度やMemoryの有効性は主張しない。

## Authorityと前提

- 現在の依頼: 2026-09-16「EgoCrossのdatasetは画像の束を動画として扱い、現在のsequential-loaderリポジトリで実装する。実データ動作確認計画を具体化し、specに追加する」。
- 既存実装spec: `2026-09-15-streaming-text-memory-spec.md`。同specの「EgoCross固有adapterは対象外」という境界は、今回の依頼でこのspecの範囲に限り更新される。
- 対象loader repository: `/mnt/HDD18TB/hayashi/sequential_loader`、調査時HEAD `cef09aa12560127451a5f569d86d5d51671e6986`、branch `master`、worktreeはclean。
- 対象consumer repository: `/mnt/HDD18TB/hayashi/2026_09_hayashi_streaming_video_qa`、調査時HEAD `1b030974193406fa338eb5bb235a3aeb54c7cf6f`、branch `feat/streaming-text-memory`、worktreeはclean。
- データroot: `/mnt/HDD18TB/hayashi/data/EgoCross`。標準testbedのannotationは`egocross_testbed/egocross_testbed_imgs.json`である。
- 標準testbed JSONは957レコードで、`id`、質問・選択肢、`video_path`（順序付き画像path列）を持つ。正解ラベルは実JSONに存在しない。

## 採用するデータ契約

### Sequence

- JSONの1レコードを1 sequenceとする。1つの元動画に複数質問があれば質問ごとに別sequenceである。
- sequenceは有限長で、`start_frame=0`、`stop_frame=len(video_path)`とする。
- sequence IDはJSONの`id`から決定的に生成する。質問本文と選択肢はQueryとしてt=0から許可されたmetadataである。
- フレーム順はJSONの`video_path`配列順で固定する。ファイル名のsort、元動画へのseek、再sampling、future frameのdecodeを行わない。

### 相対timestamp

- `frame_index`は`video_path`内の0始まりの位置とする。元画像名の数値はframe indexに使わない。
- timestampは`frame_index / sampled_fps`で計算する。
- recordが`sampled_fps`を持つ場合はその正の値を使う。標準testbedではデータカードの規則に従い、EgoSurgeryとCholecTrack20のVID25・VID111を1.0 FPS、その他を0.5 FPSとする。
- metadataに`timestamp_origin: sampled-frame-relative`、`sampled_fps`、採用規則を保存する。timestampを元動画の絶対時刻やPTSとして扱わない。

### Pathとmetadataの境界

- Adapterがmanifestの論理path（`/egocross_testbed/...`等）を指定data rootの下の実pathへ解決する。解決先がdata root外へ出るpath、空配列、重複ID、非文字列path、存在しない画像は明瞭な例外として扱う。
- Reader専用のordered image-path catalogはAdapter/Reader内部にだけ保持する。path列は`SequentialSample`へ転送するmetadataに載せない。
- `source_metadata`にはrecord ID、質問、選択肢、sampled FPS、timestamp originを置く。`dataset_metadata`にはEgoCrossのdataset名、category、question type、manifest path/version識別を置く。
- 標準testbedに正解ラベルがないため、loaderとconsumerは正解・accuracy・A〜Dの無理な正規化を実装しない。

## 変更scope

### `sequential_loader`

1. `EgoCrossTestbedAdapter`を追加する。
   - annotation JSONを読み、recordをID順に検証・列挙する。
   - 指定record IDだけを選ぶAPIを提供する。未指定時は全recordをID順で返す。
   - 各recordを上記契約の`SequenceSource`へ変換し、質問関連metadataとReader私有catalogを提供する。
2. `EgoCrossImageSequenceReader`を追加する。
   - Adapterのprivate catalogに基づき、要求rangeの画像だけをPillowで開き、RGB `torch.uint8 [T, 3, H, W]`として返す。
   - 連続range、bounded source、session lifecycle、`DecodedChunk`の既存契約を守る。
   - 読込失敗・破損画像・次元不一致はsource ID、frame index、pathを含めてfail-fastとし、skipしない。
3. これらを`sequential_loader` top-level public APIへexportし、READMEへ画像列の使用例と時刻の意味を追記する。
4. Pillowを画像decodeの明示的runtime dependencyとして追加する。
5. 既存`SequentialVideoReader`、50Salads Adapter、Core、public APIの既存名と挙動を変えない。

### Streaming VideoQA consumer

1. `streaming_text_memory`に、EgoCross Adapter/Readerをtop-level public APIだけで利用するframe sourceを追加する。
2. CLIにdataset選択とEgoCross record IDを追加する。EgoCrossではmanifestから質問と選択肢を取得し、質問を`--question`で別指定して食い違わせない。
3. artifact metadataに、dataset、record ID、manifest識別子、画像数、sampled FPS、timestamp origin、code revisionsを追加する。
4. 既存50Salads CLIの既存引数と挙動を維持する。

## 実装・検証計画

| 段階 | 対象 | 実施内容 | 合格条件 |
|---|---|---|---|
| 1 | loader unit test | 一時JSONと同寸法のJPEG/PNGを作り、AdapterのID順、path解決、metadata非露出、timestamp規則を確認する。 | JSON順のframe index、期待timestamp、public API exportを確認できる。 |
| 2 | loader integration test | 3枚のsynthetic画像を`frames_per_chunk=2`で読み、tail padding・`is_last`・reader closeを確認する。 | `[0,1]`と`[2,-1]`、最後だけ`is_last=True`、resource解放が得られる。 |
| 3 | loader failure test | empty path列、root外path、欠損/破損画像、range不連続、サイズ不一致を与える。 | 画像をskipせず、source/frame/pathを含む例外で停止する。 |
| 4 | 実データReader smoke | 下記5 recordをQwenなしで`SequentialDataset`から読む。 | 全画像がRGB uint8として1回ずつ返り、index・timestamp・終端が期待どおり。 |
| 5 | consumer unit test | fake public loaderとfake VLMで、manifest由来のQuery、1 frameごとのMemory連鎖、artifact metadataを確認する。 | future画像をモデルへ渡さず、record間の設定混入がない。 |
| 6 | 実Qwen短時間smoke | record 224を1 frame、次にrecord 1を5 frames処理する。 | `memory.jsonl`が各frame直後に増え、前recordのMemoryが次recordへ渡らず、final answer/metadataが保存される。 |

### 実データReader smokeの固定対象

| record ID | データ | 画像数 | 目的 |
|---:|---|---:|---|
| 1 | CholecTrack20 | 5 | 標準JPEG・0.5 FPSの基準ケース |
| 54 | CholecTrack20 / VID110 | 7 | PNG decode。VID110は1 FPS例外ではないことも確認する。 |
| 367 | EgoSurgery | 6 | JPEG・1.0 FPS例外 |
| 224 | EgoPet | 1 | 最短sequenceと実Qwen 1-frame smoke |
| 341 | EgoPet | 91 | 最長sequenceのReaderのみのEOF・逐次性確認 |

### 実Qwen smokeの実行境界

- 実モデルの初回取得、GPU使用、record 224/1の短時間smokeは、実装完了後にユーザーが明示して実行する。
- record 341の91回VLM呼び出し、957問全体の処理、精度評価、LoRA/学習は本specの検証に含めない。別experiment/specと実行許可を要する。
- 実行時はdata root、model ID/path、dtype、device map、record ID、max frames、manifest hash、両repositoryのcommitをartifactへ保存する。

## 成功条件

- `sequential_loader`のpublic APIだけで、EgoCrossの任意recordを有限長の`SequentialDataset`として構築できる。
- `frames_per_chunk=1`では、時刻tのReaderがdecodeする画像はJSON列のt番目だけであり、future画像tensorを読み込まない。
- sampleのvalid frameはframe indexが0から連続し、timestampが採用したsampled FPSと一致する。
- JPEG/PNG、1-frame、91-frame、0.5/1.0 FPS規則を実データsmokeで通過する。
- Consumerの各Memory更新は1 imageのみを受け、JSONLの`previous_memory`が直前の`updated_memory`と一致する。
- run artifactから、入力dataset、record、時刻規則、モデル、コードrevision、処理frame数を再現できる。
- 既存`sequential_loader` test suiteとStreaming VideoQA test suiteが通過し、50Salads経路に回帰がない。

## 対象外

- EgoCrossの画像列を動画ファイルへ変換する処理。
- 標準testbedの正解率、提出JSON、選択肢正規化、Dynamic ICL、LoRA、学習。
- 957問のfull benchmark、91-frame Qwen実行、長時間GPU run。
- timestampを元動画の絶対時間へ復元する処理。
- Memory方式、prompt、model、chunk長の研究比較。

## 互換性・リスク

- 既存Coreは`SequenceSource.source`を`Path`として扱う。EgoCrossではこれをmanifestを識別するPathとして使い、画像path列の解釈は専用Readerに閉じ込める。VideoReaderはEgoCross sourceに使わない。
- 異なる画像サイズを同一chunkにstackできない場合、Readerは明示エラーにする。初期Consumerは`frames_per_chunk=1`固定であり、画像サイズ統一は要求しない。
- 標準testbedのsampled FPS例外は公開データカードに基づく相対時刻規則である。正確なevidence windowの絶対時刻を回復したと解釈してはならない。
- 実JSONとREADMEの正解ラベルschemaは不一致であるため、accuracyを計算したように見えるartifactを作らない。

## Approval Gate

このspecはdraftであり、コード変更・commit・push・実Qwen runを許可しない。実装へ進める前に、以下を承認する。

1. 標準testbedの相対timestamp規則（0.5 FPS、EgoSurgeryとVID25/VID111のみ1 FPS）。
2. `sequential_loader`にEgoCross専用Adapter/ReaderとPillow依存を追加すること。
3. 実装対象をloaderとStreaming VideoQA consumerの両repositoryとすること。

## 関連記録

- `experiments/2026-09-15-egocross-qwen-local-investigation.md`
- `specs/2026-09-15-streaming-text-memory-spec.md`
- `.research/secretary/notes/brainstorm/2026-09-16-egocross-image-sequence-loader.md`
