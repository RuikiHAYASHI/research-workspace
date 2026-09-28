---
date: 2026-09-24
project: agentic-streaming-videoqa
source_todo: null
topic: sequential-loader-workbench-refactor-investigation
status: exploratory
tags: [brainstorm, streaming-videoqa, sequential-loader, refactor, architecture]
---

# sequential_loader 接続を前提にした LongVideoQA Workbench リファクタリング調査

## 出発点と今回の目標

目標は、`sequential_loader` から動画を先頭順に受け取り、およそ10分の時間窓ごとに視覚情報を得て、その要約を次のAgent promptへ引き継ぎ、EOF後に最終回答するAgentシステムである。

今回の範囲は調査と計画であり、両リポジトリのコード、設定、データ、依存関係は変更しない。以下の実装計画は候補であって、承認済みspecではない。

## 読み込んだ根拠

- プロジェクトREADME、2026-09-18 MTG議事録、2026-09-23の最小Streaming VideoQA brainstorm、および既存Workbench実装仕様を読んだ。
- `sequential_loader` の公開facade、50Salads adapter、core Reader/Dataset/DataLoader、旧50Salads実装、tests・debug・文書の参照関係を確認した。
- `2026_09_hayashi_longvideoqa_workbench` の実装、設定、tests、CLI、server、Web UIを確認した。

## 現行実装の事実

### 1. sequential_loader の公開契約

外部利用の入口は `sequential_loader/__init__.py` の `import sequential_loader as sl` である。公開APIの基本経路は次である。

```text
Salads50Adapter
  -> SequenceSource（1動画、start_frame=0、stop_frame=None）
  -> SequentialDataset
  -> SequentialVideoReader（PyAVを1動画につき1回openしてforward decode）
  -> SequentialSample
  -> strict DataLoader（batch_size=1, num_workers=0）
```

`SequentialSample` はCPU上のRGB `uint8 [T, 3, H, W]`、絶対frame index、timestamp、`valid_mask`、sequence境界を返す。`SequenceSource.stop_frame=None` のため、50Salads動画の全frame数を事前decodeして調べない。途中停止するconsumerは `sequential_sample_stream()` のcontextでReader資源を解放する必要がある。

ただし現行のchunk単位は **固定frame数** であり、10分の時間窓ではない。timestamp modeはRAWのみで、50SaladsのPTSが逆行する場合を許容し、timestampの単調性は保証しない。したがって「10分」をPTSだけで境界化することは、現行契約のままでは安全に定義できない。

### 2. `src/adapters/salads50.py` がある理由

これは現行の公開 `Salads50Adapter` である。50Salads固有のファイル配置（`rgb/<split>/rgb-*.avi` と `framelabels_custom/<split>/*-framelabels.txt`）を解釈し、動画をID順に列挙して共通の `SequenceSource` へ変換する。

- 担当するのは「どの動画を読むか」の決定だけである。
- chunk化、forward decode、DataLoader、学習、VLM、Agentは担当しない。
- annotationはファイル参照としてopaqueに渡すだけで、frame alignmentが未検証のためlabelを入力やtargetにしていない。

この設計は、dataset固有の選択子を共通loader入力へ適合させる意味でAdapterとして妥当である。WorkBenchが50Saladsを読むなら、この公開Adapterは必要であり、削除対象ではない。

### 3. `src/salads50/` ディレクトリがある理由

こちらは公開Adapterとは別の、旧来の学習用実装である。

- `Salads50SequentialDataset` はframe labelをparseしてclass ID / targetを作る。
- `salads50_sequential_dataloader.py` はtrain・validation Dataset、transform、class mapping、PyTorch DataLoaderを一括作成する。
- `src/base_sequential_video_dataset.py` はこの旧実装とEPIC-KITCHENS旧実装の基底クラスである。
- `main.py` と `debug/salads50_sequential/step01`〜`step18` が旧 `Salads50SequentialDataset` を直接importしている。

この経路は、現行の公開 `sequential_loader` facadeからはexportされず、公開Adapter/Coreへの依存もない。さらに旧基底経路はclipごとのseekを含むrandom-access decodeであり、loader契約文書に記録されたstrict forward-decode経路とは別系統である。

### 4. 削除の可否

| 対象 | 結論 | 根拠 | 安全な扱い |
| --- | --- | --- | --- |
| `src/adapters/salads50.py` | 維持 | 現在のpublic APIの50Salads source discoveryであり、WorkBenchの接続候補。 | 維持し、公開APIだけをWorkBenchから利用する。 |
| `src/salads50/` | 削除候補 | 旧学習用label/DataLoader系で、public facadeと現在のstrict coreから未使用。 | まずdeprecated扱いにし、旧main/debug/EPIC依存を整理した後に別branchで削除する。 |
| `src/base_sequential_video_dataset.py` | `src/salads50/` と一括でのみ削除候補 | 旧50SaladsだけでなくEPIC-KITCHENS旧実装も継承する。 | 50Salads単独では削除不可。EPIC旧系統の移設・削除方針を先に決める。 |
| `debug/salads50_sequential/` と旧文書 | 研究資料として保留 | 旧経路の検証過程・性能根拠を含む。 | code削除後もdocs/legacyへ移すか、Git履歴に残すかを決める。 |

従って「50Salads adapterを消す」ではなく、**公開Adapterを残し、旧学習用 `src/salads50/` を段階的に退役させる**のが有力である。削除前の必須確認は、(a) `src/epic_kitchens/` の扱い、(b) 旧debugを再現資料として残す要否、(c) 旧importを使う外部利用者がいないこと、である。

## WorkBenchの構造に関する調査

### 現状

現行Workbenchは小規模なため、`src/longvideoqa_workbench/` 直下にcontracts、configuration、validation、chunking、prompts、pipeline、records、CLI、serverが並び、dataset/modelの実装だけを `adapters/` にまとめている。

- 設定は `configs/longvideobench-p9h.json` であり、3段階のprompt本文も同じJSONまたは `configuration.py` の `DEFAULT_PROMPTS` に重複している。
- `LongVideoBenchAdapter` はOpenCVで各指定時刻へseekする。これは逐次decoderではない。
- `pipeline.py` は区間ごとに「区間理解 -> 根拠集約」、EOFで「最終回答」を実行する。逐次推論順は正しいが、現在の区間生成は動画全体のdurationを先に知るtime-based samplingである。
- WorkBenchのdataset adapter契約は `get_question(question_id)` と `read_frames(sample, timestamps)` である。50Salads public adapterの契約（split -> `SequenceSource` -> `SequentialSample`）とは異なる。

### 接続時に必要な境界変更

50SaladsはQAデータセットではないため、質問、選択肢、正解を提供しない。LongVideoBenchと同じ `question_id -> QuestionSample` を直接実装することはできない。接続には次の分離が必要である。

```text
Data catalog / source selector
  - 50Salads: split, sequence_id, public Salads50Adapter
  - LongVideoBench: annotation, video_id, question_id
Question provider
  - manual question（初期候補）
  - dataset question（LongVideoBench用）
Sequential frame source
  - sequential_loaderのSequentialSample stream
Window assembler
  - source streamを因果的に約600秒のwindowへ束ねる
Agent pipeline
  - window observation -> rolling evidence -> EOF final answer
```

この分離により、50Saladsでは手入力questionでloaderの接続とAgent経路を確認し、LongVideoBenchではdataset questionを使える。正解labelや50Salads annotationはAgent入力へ渡さない。

### 10分windowを定義するための未決事項

現行loaderのRAW timestampは逆行し得るため、以下のどれを「10分」とするかを決める必要がある。

1. **decode-clock（推奨候補）**: `frame_index / trusted_fps` をwindow境界とし、source順を保つ。50SaladsのRAW PTS逆行に影響されないが、fpsのprovenanceをWorkBench側で明示保存する必要がある。
2. **PTS-clock**: 生PTSで600秒を区切る。動画のpresentation timeを尊重するが、RAW PTS逆行の仕様を先に解決または拒否する必要がある。
3. **frame-count近似**: `600 * nominal_fps` frameで区切る。実装は容易だがVFRやfps根拠を曖昧にしやすい。

いずれの場合も、10分ぶんの全frameをGPUへ渡してはならない。loaderの小さいdecode sampleを受け、固定間隔または上限付きの因果的samplingでVLM入力画像を選ぶ `WindowSampler` が必要である。動画終端を事前に知る必要がある均等samplingは初版に不向きで、固定時間間隔samplingが有力である。

## 構成変更の候補

### YAML configと英語prompt

YAML化は可能であるが、Python標準ライブラリにはYAML readerがない。runtime dependencyとしてPyYAML等を明示追加し、safe loaderだけを使う必要がある。

prompt本文をconfigから分離する場合、configは任意pathではなく登録済み `prompt_id` またはallowlist内の相対名を参照する。実行時には解決済みの英語prompt本文、prompt ID、content hashをrun artifactへsnapshotする。これによりUIで編集した場合にも再現性を保てる。

```text
configs/recipes/50salads-manual-question.yaml
prompts/chunk-observation.en.yaml
prompts/evidence-update.en.yaml
prompts/final-answer.en.yaml
```

英語化の対象は初期prompt本文、UIのprompt例、CLI error/help、READMEとdocsのどこまでかを分けるべきである。利用者向けの操作説明まで英語化するかは未決である。初期計画では、**prompt assetとモデルへ渡る構造化指示は英語化し、コードコメント・研究文書の言語は一括変更しない**とする。

### 推奨するコード構造

```text
longvideoqa_workbench/
├── src/longvideoqa_workbench/
│   ├── application/       # CLI/serverから呼ぶユースケース、run orchestration
│   ├── domain/            # immutable contracts、validation、prompt binding、window policy
│   ├── data/              # source catalog、LongVideoBench、sequential_loader bridge、fake source
│   ├── models/            # Qwen3-VL、fake model、model registry
│   ├── agents/            # observation / evidence / final stageの実行
│   ├── storage/           # run artifact作成・追記・read model
│   ├── interfaces/        # CLI、HTTP server、web asset配信
│   └── web/               # HTML/CSS/JS
├── configs/
│   ├── recipes/           # version管理するYAML recipe
│   └── registries/        # dataset/modelの安全な登録例（絶対path・秘密情報なし）
├── prompts/               # 英語prompt asset
├── data/                  # Git管理しない実datasetの説明・mount規約だけ。実データは置かない
├── models/                # Git管理しないweight/cacheの説明・mount規約だけ。実weightは置かない
├── tests/
└── docs/
```

ここでrootの `data/` と `models/` は実データ・重みを置くための任意mount pointまたは説明用directoryであり、Python sourceではない。Pythonコードのdata/model実装をrootの `data/` や `model/` に置くと、現在の `pyproject.toml` の `where = ["src"]` から外れ、package化・import・testが不安定になる。そのためコードは `src/longvideoqa_workbench/data/` と `models/` に置く。

ユーザーの「srcと同じ階層にmodelやdata」を、source codeをrootに分散する意図で言っている場合は別案になる。その場合はpackaging方式を全面変更する必要があり、推奨しない。実assetの配置を意図するなら上記構成で満たせる。

## 採用候補・保留・棄却寄り

| 区分 | 方針 | 理由 |
| --- | --- | --- |
| 採用候補 | WorkBenchは`import sequential_loader as sl`のpublic APIだけに依存する | 内部`src.*`への依存を避け、loaderの責務と独立に更新できる。 |
| 採用候補 | public `Salads50Adapter`を残し、WorkBenchにbridgeを追加する | dataset選択とforward decodeを再利用できる。 |
| 採用候補 | fixed frame decode sample -> causal 10分window -> bounded image sampling -> 3-stage Agent | loaderの逐次性と長尺contextの制約を両立する。 |
| 採用候補 | config YAML + prompt asset + resolved snapshot | prompt比較の再現性を確保する。 |
| 保留 | 50Salads old learning treeの削除 | EPIC旧系統・debug・外部importの影響を監査してから行う。 |
| 保留 | 10分のclock定義 | RAW PTSが逆行するため、decode-clockかPTS方針の明示判断が必要。 |
| 保留 | LongVideoBenchを新構造へ同時移行するか | 50Salads接続を最初の実sourceにするなら、dataset questionの扱いを別途決める。 |
| 棄却寄り | WorkBenchからloader内部の`src.sequential.*`をimportする | public contractと独立更新を壊す。 |
| 棄却寄り | 10分windowの全frameを保持・VLMへ投入する | メモリ・token量が非現実的で、サンプリング規則も再現不能になる。 |
| 棄却寄り | config内にprompt本文を重複保持する | assetの版管理とrun比較を複雑にする。 |

## リファクタリング計画（実装前の候補）

### Phase 0: 意思決定と互換性の基準を固定する

1. 10分windowのclockを決める。推奨は、50Salads初期接続ではdecode-clockを採用し、fpsとwindow境界をartifactへ保存すること。
2. 初期質問providerを決める。50Saladsではmanual questionを使うか、別のQA datasetを最初から接続するかを決める。
3. 既存LongVideoBench runの再現を互換性基準にするか、旧recipeとして残すだけにするかを決める。
4. root `data/` / `models/` が実asset用か、Python code用かを確定する。推奨は実asset用である。

### Phase 1: 依存と設定資産を先に整える

1. YAML safe loaderをruntime dependencyへ追加し、JSON loaderを即削除せず移行期間を設ける。
2. `configs/recipes/` と `prompts/` を追加し、現行3 promptを英語assetへ移す。
3. recipeにはprompt本文ではなくprompt ID、source selector、question provider、window policy、sampling policy、model、generationを置く。
4. recipe / promptの解決結果・hashをartifactに保存するテストを追加する。

### Phase 2: WorkBench内部を責務ごとに移動する

1. `contracts.py` と `validation.py` を `domain/` へ分解する。
2. `adapters/longvideobench.py` とfake datasetを `data/` へ、`qwen3vl.py` とfake modelを `models/` へ移す。
3. `chunking.py` を `domain/windowing.py` とし、現行のrandom-seek policyと新しいsequential window policyを別実装にする。
4. `pipeline.py` のstage実行を `agents/` へ、run制御を `application/` へ、`records.py` を `storage/` へ移す。
5. CLI/server/Webは `interfaces/` に残し、import方向を `interfaces -> application -> domain/data/models/storage` とする。
6. 各移動で旧import互換shimを短期間だけ残すか、同一PR内で全testsを移すかを決める。実装時には一方式に固定する。

### Phase 3: sequential_loader bridgeを追加する

1. `data/sequential_loader_source.py` を追加し、public `sl.Salads50Adapter`、`sl.SequentialDataset`、`sl.SequentialVideoReader`、strict `sl.build_sequential_dataloader`だけを使う。
2. sampleの`valid_mask`でpaddingを除外し、frames / absolute indices / timestamps / sequence lifecycleをWorkBench内部のsource eventへ変換する。
3. consumer中断・例外時にも `sl.sequential_sample_stream()` を必ずcloseする。
4. annotation / evaluation referenceをAgentの入力・sampling判断へ渡さないことをtestする。
5. fake sequential sourceで、source順、frame index順、EOF、途中失敗・closeをunit testする。実50Salads runは別許可にする。

### Phase 4: 10分windowとAgent pipelineを実装する

1. `WindowAssembler` がforward sourceから約600秒単位でwindowをyieldするようにする。境界をまたぐdecode sampleの扱いを明文化し、future frameを前windowのVLM入力へ渡さない。
2. `WindowSampler` に固定間隔・max frames・画像resize等の明示設定を置く。採用frameのindex / timestamp / selection reasonをartifactへ保存する。
3. 英語の `chunk-observation` promptでwindowごとの観測・出来事・根拠・不確実性を生成する。
4. 英語の `evidence-update` promptで過去evidenceと現在window summaryだけを集約する。
5. EOF後に一度だけ `final-answer` promptを実行する。final stageが全動画frameやevaluation referenceを直接読まないことをtestする。

### Phase 5: 50Salads旧系統の退役を別作業として判断する

1. `src/salads50/`、`src/base_sequential_video_dataset.py`、`src/epic_kitchens/`、`main.py`、debug群のimport graphを確定する。
2. 外部利用者がいないこと、旧debugの保存方法、EPIC旧系統の扱いを確認する。
3. deprecation文書とmigration guideを追加する。
4. 独立branchで旧tests・debugの扱いを確定してから削除する。WorkBenchのリファクタリングと同じ変更には混ぜない。

## 実装specへ渡すために不足している決定

- 「10分」の時間基準: decode-clock / PTS-clock / frame-count近似のどれか。
- 50Saladsでの質問の与え方: manual question / 外部QA対応付け / 50Saladsをloader smoke専用とするか。
- 初期対象データ: 50Saladsだけか、LongVideoBenchも同時に残すか。
- root `data/` / `models/` の意味: 実asset用か、code用か。
- UIから編集したpromptを、保存済みassetへの新versionとして扱うか、そのrun限定overrideとして扱うか。
- `src/salads50/` の旧学習・EPIC系統をリポジトリとして維持する意図があるか。

## Research Spec Handoff 候補

- 対象プロジェクト: agentic-streaming-videoqa
- 実装目的: public `sequential_loader`から因果的にframeを受け、約10分windowの観測・要約・最終QAを行う構成へWorkBenchを再編する。
- 採用方向: public 50Salads Adapterを維持し、WorkBench側にsource bridge、windowing、question providerを追加する。
- 変更scope候補: YAML recipe、英語prompt assets、package責務分割、sequential_loader bridge、window Agent、tests、docs。
- 対象外候補: loader内部への変更、実データ・重み・outputsのcommit、実Qwen/full dataset run、旧50Salads treeの即時削除。
- 主な未決: 10分clock、50Salads question provider、LongVideoBench移行範囲、root data/model directoryの意味、旧treeの退役方針。
