---
date: 2026-09-16
project: agentic-streaming-videoqa
status: draft
topic: egocross-observation-prototype-plan
source: 2026-09-16 repository-boundary brainstorm + existing streaming text-memory spec
last_updated: 2026-09-16
---

# EgoCross Observation Prototype 実装計画

## 目的

EgoCrossのtestbed画像列を、既存の`sequential_loader`へ一般化せず、新しい専用repositoryでJSON順に1枚ずつ処理する。まず画像列の因果的なframe observation traceを成立させ、次段階でQwen3-VLの観測文をframe単位で保存する。

この計画の初期ゴールは、QAの最終回答や精度評価ではない。`video_path`の順序を保った逐次decode、future画像を処理しない入力境界、再現可能なtraceを確認することである。

## 対象repositoryと開始状態

- 実装repository: `/mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation`
- GitHub remote: `git@github.com:RuikiHAYASHI/2026_09_hayashi_egocross_observation.git`
- 調査時点: `main`は未commitの空repository。`origin/main`は存在しない状態。
- 実装開始時に初めて`main`からStep 1 branchを作成する。実装前にmainへコードをcommitしない。
- 既存repository `/mnt/HDD18TB/hayashi/2026_09_hayashi_streaming_video_qa` と `/mnt/HDD18TB/hayashi/sequential_loader` は変更しない。
- GitHubへのpush、Pull Request、mergeはこの計画だけでは行わない。ユーザーが別途指示した場合に行う。

## 既存specから引き継ぐ判断

- Queryはstream開始時点から既知としてよい。
- EgoCross標準testbedの1 JSON recordを1 sequenceとして扱う。
- `video_path`配列順を観測順序とし、ファイル名sortや動画化を行わない。
- 標準testbedには実JSON上の正解ラベルがないため、初期traceでaccuracyを計算しない。
- timestampは元動画の絶対時刻ではなく、抽出規則から得た相対timestampとして保存する。標準testbedは原則0.5 FPS、EgoSurgeryとCholecTrack20のVID25・VID111は1 FPSとする。
- 画像path、frame index、timestamp、prompt version、model identifier、code revisionをtrace metadataへ保存する。

## 実装済み基礎経路の処理フロー

以下は`feat/step-04-qwen-observation`で実装済みの、1 recordを処理してframe traceを保存する経路である。これは最終QAやMemoryを含まない観測基盤の動作説明であり、Step 5以降の再現性metadataやAgent機能を追加するものではない。

```text
CLI引数
  │
  ├─ dataset root / manifest未指定時: repository siblingのdata/EgoCrossを選ぶ
  │
  ▼
load_record(manifest, record_id)
  │  質問・選択肢・video_path列を検証する
  ▼
frame_references(record, dataset_root)
  │  video_pathのJSON順、相対timestamp、実画像pathを作る
  ▼
iter_decoded_frames(...)
  │  一枚をPillowでRGBへdecodeする
  ▼
JsonlTraceWriter.write(...)
  │
  ├─ decode-only: decode metadataを保存する
  └─ --observe: current frameだけをQwen3VLObserverへ一回渡し、観測文を保存する
  ▼
outputs/<run_id>/frames.jsonl
```

### 入力と因果境界

1. CLIは`--record-id`を必須とし、`--dataset-root`と`--manifest`が省略された場合はrepository親ディレクトリの`data/EgoCross`と、その配下の`egocross_testbed/egocross_testbed_imgs.json`を使う。
2. `load_record`はstandard manifestから指定IDの1 recordを選び、質問文、選択肢、`video_path`列を検証する。ID重複、必須field不足、空の画像列はここで停止する。
3. `frame_references`は`video_path`をファイル名でsortせず、JSON配列の順番のまま`frame_index=0, 1, ...`を割り当てる。相対timestampは採用済みのFPS規則から計算し、元動画の絶対時刻としては扱わない。
4. `iter_decoded_frames`は現在の参照先画像だけをPillowで開き、RGBへ変換してyieldする。全画像の先読み・一括保持・欠損画像のskipは行わない。画像を開けない場合は、そのframe indexとpathを含む例外で停止する。
5. `--observe`なしではdecode metadataだけをtraceへ保存する。`--observe`ありでは、質問・選択肢・現在frameのindexと相対timestampからpromptを組み、**現在RGB画像一枚だけ**をQwen3-VLへ一回渡す。previous frame、future frame、text Memory、最終回答はこのVLM入力に含めない。

### JsonlTraceWriterによる保存契約

`JsonlTraceWriter`は、1実行につき`outputs/<run_id>/`を新規作成し、その中の`frames.jsonl`へframeごとの`TraceRecord`を一行ずつ保存するwriterである。

- run directoryは`exist_ok=False`で作る。同じ`run_id`が既に存在すると`FileExistsError`にして、過去artifactを上書きしない。
- `write(record)`は`TraceRecord`をJSONへ変換し、1行を書いた直後にnewlineと`flush()`を行う。そのため、後続frameやモデル処理が失敗しても、すでに完了したframeの行は残る。
- decode-onlyの行にはrun ID、record ID、frame index、相対timestamp、logical/実画像path、画像mode・size、code revisionを保存する。
- Qwen観測の行にはさらに観測文、model ID、prompt version、generation parameters、処理時間を保存する。
- Qwen呼出しが失敗した場合、該当frameの`error`、model metadata、処理時間を保存してflushしてから例外を再送出する。この基礎実装では自動retryを行わず、`retry_count`は0である。

### 完了と停止

すべての対象frameを処理するとwriterをcloseし、CLIはrun directoryを表示して終了する。manifest検証、path解決、画像decode、Qwen観測の失敗はsuccessとして扱わず、fail-fastでrunを停止する。ただし、失敗前にflush済みのtrace行は観測済みframeの記録として残る。

## Branch・commit運用

### Branchの階層

Step開始時に、直前Stepの検証済みbranchから新しいStep branchを作成する。

```text
main（空の開始点）
└── feat/step-01-foundation
    └── feat/step-02-manifest
        └── feat/step-03-image-trace
            └── feat/step-04-qwen-observation
                └── feat/step-05-reproducibility
```

Step branchを作るコマンドの型は次のとおりとする。

```bash
git switch <直前の検証済みbranch>
git switch -c feat/step-XX-<topic>
```

最初のStepだけは、実装開始地点でmainから切る。

```bash
git switch main
git switch -c feat/step-01-foundation
```

### Micro Step

- micro Stepごとに、目的が一つになる小さなcommitを作る。
- micro Stepではbranchを増やさず、現在のStep branchへcommitする。
- commit前に対象ファイル、diff、関連testを確認する。
- commit messageは`feat:`、`test:`、`fix:`、`docs:`、`chore:`のいずれかで始める。
- outputs、model weight、dataset画像、credentialはcommitしない。
- Step末尾のtestが失敗した場合、次のStep branchを作らず、同じStep branchで修正commitを追加する。

## Step 1: repository基盤を作る

### 目的

空repositoryを、実験コードとtraceを安全に置ける最小Python repositoryにする。

### Branch

`feat/step-01-foundation`を空の`main`から作成する。

### Micro Step

1. `docs: define egocross observation scope`
   - READMEに目的、対象外、実データrootを外部参照すること、初期成功条件を書く。
2. `chore: add python project metadata`
   - Python version、依存関係、test command、`outputs/`・cache・model weightのignoreを定義する。
3. `feat: add observation package skeleton`
   - `egocross_observation/`、`scripts/`、`tests/`を作り、import可能な最小構造を追加する。

### Step末尾のtest

- package import check
- CLI help check
- Python compile check
- test runnerの空test suite起動確認

### 完了条件

新しいbranchをclone直後の環境から再現でき、生成artifactがGitに入らない。

## Step 2: EgoCross manifest契約を実装する

### 目的

EgoCross標準JSONの1 recordを検証し、指定recordを順序付きframe referenceとして扱えるようにする。まだ画像decodeやQwenは行わない。

### Branch

`feat/step-02-manifest`を`feat/step-01-foundation`から作成する。

### Micro Step

1. `feat: add egocross record model`
   - `id`、dataset、category、question、options、`video_path`を表す不変データ構造を追加する。
2. `feat: add manifest loader`
   - JSON fileの読込、record ID選択、ID重複・必須key・空path列・path型の検証を追加する。
3. `feat: add image path resolver`
   - `/egocross_testbed/...`などの論理pathを指定data rootへ解決する。
   - data root外への脱出、欠損file、対応しない拡張子を明示的に拒否する。
4. `feat: add relative timestamp policy`
   - recordの明示`sampled_fps`を優先する。
   - 標準testbedでは0.5 FPSを基本とし、EgoSurgeryとVID25・VID111を1 FPSとする。
   - timestamp originを相対時刻として記録する。
5. `test: cover manifest validation`
   - valid record、ID選択、JSON順保持、path解決、FPS例外、invalid recordをテストする。

### Step末尾のtest

合成JSONを使い、fixtureのファイルをまだdecodeせずにmanifest loader全体のunit testを実行する。

### 完了条件

同じmanifestとdata rootから、同じrecordのordered frame referencesとtimestampが毎回同じ順で得られる。

## Step 3: 画像列の逐次decodeとtraceを実装する

### 目的

指定recordの画像を、JSONの順序で必要な1枚ずつdecodeし、Qwenなしで観測traceを保存する。

### Branch

`feat/step-03-image-trace`を`feat/step-02-manifest`から作成する。

### Micro Step

1. `feat: add single-frame image iterator`
   - PillowでRGB画像を開き、1 frameずつyieldする。
   - 先読み、全画像のtensor化、欠損画像のskipは行わない。
2. `feat: add trace record schema`
   - run ID、record ID、frame index、relative timestamp、image path、decode metadata、code revisionを定義する。
3. `feat: add incremental jsonl writer`
   - 各frameの処理直後にflushする。
   - runごとに新規output directoryを作り、既存artifactを上書きしない。
4. `feat: add observation trace cli`
   - `--dataset-root`、`--manifest`、`--record-id`、`--max-frames`、`--output-root`を受ける。
   - 初期CLIは画像decodeとtrace保存までとし、VLMを必須にしない。
5. `test: cover sequential image trace`
   - JPEG/PNG、JSON順、frame index、timestamp、max frames、flush、欠損/破損画像のfail-fastをテストする。

### Step末尾のtest

- synthetic imagesでCLIを実行し、JSONL record数と順序を確認する。
- 実EgoCrossではQwenなしで、ID 1（5 frames）、ID 54（PNG、7 frames）、ID 367（EgoSurgery、6 frames）、ID 224（1 frame）を読む。
- ID 341（91 frames）は画像decodeとEOFのみ確認し、VLMは呼ばない。

### 完了条件

実データで全対象画像が1回ずつ順序どおり処理され、traceからfuture画像のdecodeやskipがないことを確認できる。

## Step 4: Qwen frame observationを追加する

### 目的

各current frameに対してQwen3-VLが観測文を1回生成し、その結果をtraceへ追記する。text Memoryとfinal QAはまだ追加しない。

### Branch

`feat/step-04-qwen-observation`を`feat/step-03-image-trace`から作成する。

### Micro Step

1. `feat: add qwen observation adapter`
   - 既存のQwen3-VL参照実装を基に、model ID、dtype、device mapをCLIから指定できるadapterを追加する。
   - model weightはHugging Face cacheに置き、repositoryへコピーしない。
2. `feat: add observation prompt contract`
   - `question + options + current frame + frame metadata`だけを入力する。
   - previous frame、future frame、text Memory、最終回答用入力は渡さない。
   - 出力は回答選択肢ではなく、current frameから観測できる短いplain-text observationとする。
3. `feat: append model observations to trace`
   - model ID、prompt version、generation parameters、処理時間、生成文、error/retryを記録する。
4. `test: cover qwen observation boundary`
   - fake modelでcurrent frameだけが渡されること、frameごとに1 callであること、失敗時のtrace状態を検証する。

### Step末尾のtest

- fake modelによるunit test。
- 実Qwenは別の短時間runとして、まずID 224の1 frame、次にID 1の5 framesで実行する。
- 実runではmodel download、GPU、認証、生成artifactが必要なため、unit test合格から自動実行を推定しない。

### 完了条件

各valid frameに対してQwenが1回だけcurrent imageを受け、観測文と実行metadataがJSONLへ追記される。

## Step 5: 再現性と実行手順を整える

### 目的

別環境で同じrecord traceを追跡できる状態にし、初期実装を研究実験として固定する。

### Branch

`feat/step-05-reproducibility`を`feat/step-04-qwen-observation`から作成する。

### Micro Step

1. `docs: document decode-only run`
   - EgoCross data root、manifest、record ID、output確認手順を書く。
2. `docs: document qwen observation run`
   - model取得、短時間実行、GPU条件、未検証項目を書く。
3. `feat: add run metadata manifest`
   - dataset root、manifest hash、record ID、image count、sampling rule、model、repository commit、実行引数を保存する。
4. `test: verify reproducible trace metadata`
   - output schema、non-overwrite、metadata必須項目を検証する。

### Step末尾のtest

- repository全体のunit test
- compile/import check
- decode-only smokeの再実行
- 利用可能な環境でのみQwen 1-frame smoke

### 完了条件

traceとmetadataだけから、どのEgoCross recordをどの規則・model・code revisionで処理したか追跡できる。

## 初期成功条件

- 新規repositoryのmainには直接実装commitを置かず、Step branchから開始する。
- 各Step branchは直前Stepの検証済みbranchから作成される。
- 各micro Stepが独立commitになり、Step末尾のtest結果が記録される。
- EgoCross画像列がJSON順に1枚ずつdecodeされ、JPEG/PNG、短系列、長系列、timestamp例外を確認できる。
- `outputs/`にframe traceとrun metadataが保存され、Git管理されない。
- Step 4完了時点で、Qwenはcurrent frameの観測文だけを生成し、text Memoryやfinal QAを実行しない。
- 既存の`2026_09_hayashi_streaming_video_qa`と`sequential_loader`には変更がない。

## 対象外

- `sequential_loader`へのEgoCross Adapter/Reader追加。
- text Memory更新、Memory圧縮、multi-timescale Memory、Agent、tool use。
- final QA、選択肢正規化、正解率、提出JSON。
- 957件全体のQwen実行、長時間GPU run、学習、LoRA。
- 元動画の絶対timestampやevidence windowの復元。

## Blocking / Non-blocking

### Blocking

- Step 4開始前に、実Qwen smokeで使用するmodel ID/pathと実行可能なGPU環境を確認する必要がある。Step 1〜3はこれなしで実装・検証できる。
- `--question`をmanifestの質問本文・選択肢から固定するか、外部queryを許可するかは、Step 4のprompt契約に入る前に確定する。初期案はmanifest由来queryを固定する。

### Non-blocking

- package manager、formatter、型checkerの選択は新repositoryの最小構成に合わせる。
- record IDのCLI型は現JSONの整数IDを文字列として受けてもよいが、内部では正規化する。
- Qwen adapterのdtype/device指定は既存参照実装に合わせ、研究比較条件として固定しない。

## Approval Gate

この計画書は`draft`であり、ここではコード変更、branch作成、commit、push、Qwen実行を行わない。実装開始前に、次の範囲を承認する。

1. 新規repositoryをEgoCross専用の観測prototypeとして使うこと。
2. 初期ゴールをframe-level observation traceとし、final QAを対象外にすること。
3. Step branchを階層的に作成し、micro Stepごとにcommitし、Step末尾でtestすること。

## 関連記録

- `specs/2026-09-15-streaming-text-memory-spec.md`
- `experiments/2026-09-15-egocross-qwen-local-investigation.md`
- `.research/secretary/notes/brainstorm/2026-09-16-egocross-scope-revision.md`
- `.research/secretary/notes/brainstorm/2026-09-16-egocross-observation-repository-boundary.md`
- `.research/secretary/notes/brainstorm/2026-09-16-egocross-observation-repository-boundary.md`
