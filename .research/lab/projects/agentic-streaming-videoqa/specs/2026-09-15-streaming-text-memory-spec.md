---
date: 2026-09-15
project: agentic-streaming-videoqa
status: implemented
topic: streaming-text-memory-inference
source: 2026-09-11 MTG + current implementation request + 2026-09-15 Codex handoff boundary
last_updated: 2026-09-15
---

# Streaming Text Memory 推論パイプライン実装Spec

## 目的

9/11 MTGで決定した、future frameへアクセスせず動画を先頭から逐次処理し、各時点で `current frame + previous text memory -> new text memory` を繰り返す最小構成を、研究コードとして再利用可能な形で実装する。

今回はEgoCross固有の手法・Reflective Dialogue・既存Agent実装を利用しない。現在の研究repoに既に存在する `sequential_loader` public API接Microsoft.QuickAction.Vpn続を基盤とし、まず単一VLMによるtext Memory更新と最終QAまでのend-to-end経路を成立させる。

## Authority / 前提

- 現在のユーザー指示: 2026-09-15「MTGで話した内容を実現し、過去のEgoCross等とは切り離して本格的な実装を進める」。
- MTG決定: `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-11-mtg.md`。
- 研究コードrepo: `tamaki-lab/2026_09_hayashi_streaming_video_qa`。
- baseline branch: `main`。
- baseline commit: `38eff9ce480271e85b94def34cf51979a6c8a7ce`。
- 実装branchは `feat/streaming-text-memory` とし、上記baseline commitの`main`から作成する。実装・commit・pushはこのbranchだけで行い、`main`へ直接変更しない。
- 実装対象repoは移行済みサーバ上の `/mnt/HDD18TB/hayashi/2026_09_hayashi_streaming_video_qa` にあり、確認時点で `main` は上記commit、worktreeはcleanである。
- `sequential_loader` は別repoの基盤機能として扱い、研究固有ロジックを追加しない。
- 現行repoは50Saladsを `sequential_loader` のpublic API経由で読むacceptance smokeのみを持ち、model / question / memory / QA loopは未実装。
- EgoCrossは移行済みサーバの `/mnt/HDD18TB/hayashi/data/EgoCross` で利用可能である。ただし本specの最初の入力adapterは既存50Salads接続のままとし、EgoCrossを入力datasetへ切り替える変更は含めない。
- 既存smokeの既定50Salads root `/mnt/HDD10TB-2/hayashi/2026_06_hayashi_simple-MeMViT/data/50Salads` は、現サーバでは利用可能であることを確認できなかった。新規CLIと実データsmokeは、実在する50Salads rootを `--dataset-root` で明示指定し、その旧既定値に依存しない。
- ChatGPT上のGitHub操作では、`tamaki-lab/*` は原則read-onlyとして扱う。書き込みはユーザーが個別に明示した場合のみ例外とする。
- 実装作業はCodexへ引き継ぎ、Codexが利用できる研究サーバ上のlocal worktreeで行う。local worktreeとGitHub remoteは別状態として扱う。

## 必須挙動

### 1. Streaming causality

- 動画は `sequential_loader` のpublic APIから先頭順に取得する。
- VLMへ渡す単位は1 frameとする。
- 時刻tの更新で利用してよい情報は次だけとする。
  - Query（t=0から既知）
  - current frame
  - current frameのtimestamp / frame index
  - t-1までに生成済みのtext Memory
- future frame、動画全体の事前特徴、後続frame由来の情報をMemory更新に利用しない。
- frameを全件先読み・保持しない。

### 2. Query

- QueryはCLI引数で明示的に与える。
- Queryはstream開始前から既知として、各Memory更新promptに含める。
- dataset固有の固定質問をコードへ埋め込まない。

### 3. VLM

- 学習は行わず、既存VLMを推論専用で用いる。
- 初期実装の既定model IDは Hugging Face Hubの `Qwen/Qwen3-VL-4B-Instruct` とする。これはユーザー指示で選んだ初期VLMであり、CLIの `--model-id` で別model ID/pathを指定できるようにする。
- 初期実装はHugging Face Transformersの `Qwen3VLForConditionalGeneration` と `AutoProcessor` によるimage-text generation経路で動く単一VLMとする。CLIの初回実行時、ローカルcacheにモデルがなければ `from_pretrained` を通じてHugging Face Hubから取得する。
- Hugging Face cacheとmodel重みはGit管理しない。モデルの取得・ロードに必要な認証や利用規約同意がある場合は、実行前に済んでいることを前提とする。
- 別LLMによる要約、別Agentによる注目助言、tool useは今回のscope外とする。

### 4. Text Memory update

各valid frameについて1回、次の意味の更新を行う。

```text
(question, current frame, frame index, timestamp, previous text memory)
    -> updated text memory
```

Memory promptでは次を明示する。

- unseen futureを推測事実として書かない。
- current frameから観測できる出来事、人物/主体、物体、行動、状態を必要に応じて反映する。
- Query回答に有用な過去情報を保持する。
- current frameで否定・更新された過去情報は必要に応じて修正する。
- Memoryは次frameへそのまま渡せるplain textとする。

Memoryの正解性、multi-timescale化、重要イベント専用Memory、容量制限、圧縮方針はこのspecでは研究上の未決事項として固定しない。

### 5. 出力 / provenance

- generated artifactはGit管理せず、既存 `.gitignore` の `outputs/` 配下へ出す。
- 1 frameごとの更新結果をJSONLとして逐次追記する。
- 各recordには最低限以下を保存する。
  - sequence_id
  - frame_index
  - timestamp
  - question
  - previous_memory
  - updated_memory
- EOF後、最終Memoryだけを使って同じVLMにQueryへのfinal answerを生成させる。
- final answerとrun metadataをJSONで保存する。
- run metadataには最低限、model identifier、dataset root、split、sequence id、baseline/実行コードが追える情報を残す。
- 既存artifactを暗黙に上書きしない。runごとに新しい出力directoryを作る。

## 実装interface

新しいCLI entry pointを研究repoへ追加する。

想定する必須引数:

```text
--dataset-root
--question
--model-id
```

50Saladsについては既存実装との整合のため、split / sequence idをCLIで指定できるようにする。default値を置く場合も、既存smokeで使っている `train2 / 02-1` を便宜上のdefaultとし、研究主張として固定しない。

新規CLIの `--dataset-root` に固定のdefaultは置かない。既存 `scripts/smoke_sequential_loader.py` の既定値は互換性のため変更しないが、現サーバで実行するときは同scriptにも実在するrootを明示指定する。

VLM実行device / dtypeはCLIまたは既存Transformersのloading経路で指定可能にするが、今回のspecではGPU番号や特定hardwareを固定しない。

## 実装構造

現在repoが小さいため、過度な抽象化は作らない。ただし推論loopとCLI parsingを分離し、unit testでmodelを実ロードせず検証できる境界を設ける。

最低限必要な責務:

1. 50Salads source選択 + `SequentialDataset` 構築（`frames_per_chunk=1`）。
2. SequentialSampleからvalid current frameを取り出す。
3. VLM input構築。
4. text Memory更新。
5. JSONL逐次保存。
6. EOF後final answer生成とmetadata保存。

既存 `scripts/smoke_sequential_loader.py` はloader acceptance用途として維持し、Streaming QA本体へ置換しない。

## Codex引き継ぎ / 操作境界

### Codexが担当してよい作業

- 実装開始前に、研究サーバ上の対象repository、branch、HEAD commit、dirty state、局所 `AGENTS.md` / `CLAUDE.md` 等を確認する。
- cleanなbaselineから `feat/streaming-text-memory` を作成し、branchと開始時commitを実装報告に記録する。
- `tamaki-lab/2026_09_hayashi_streaming_video_qa` のlocal worktreeで、本specに必要な最小コード・test・config変更を行う。
- `tamaki-lab/sequential_loader` は原則として既存public APIのread-only依存として扱い、本specの都合だけで変更しない。
- fake / stub modelを用いるunit test、compile/import check、既存smokeなど、短時間かつ安全な検証は実装作業に含めてよい。
- local worktree上で生成したdiffを確認し、本spec外の変更やユーザーの既存dirty changeを混ぜない。
- このbranchでの通常の `git add`、`git commit`、`git push -u origin feat/streaming-text-memory` をCodexに許可する。検証済みの論理的な変更単位でcommitし、messageは `sequential_loader` と同様に `feat:`、`test:`、`fix:`、`docs:` 等の種別を先頭につける。
- GitHub上のCompany文書は実装判断のSSOTとして参照する。

### Codexが自動で行ってはいけない作業

- `main`への直接commit・push、force push、履歴を書き換えるpush、Pull Request作成、merge。これらはユーザーの個別明示指示がある場合のみ行う。
- 長時間GPU run、full-video benchmark、大規模評価、training。コード実装の許可から実験run許可を推定しない。
- `tamaki-lab/sequential_loader` の仕様変更や研究固有ロジック追加。
- dataset、model、checkpoint、split、prompt研究方針など、本specで未決の研究判断を独自に固定すること。
- local worktreeへの変更を、GitHub remoteへ反映済みとみなすこと。

### ChatGPT側の操作境界

- ChatGPTは `tamaki-lab/*` のGitHub repositoryを原則read-onlyで調査する。
- GitHub上の `tamaki-lab/*` へのファイル作成・更新・削除、commit相当の書き込みは、ユーザーがその操作を個別に明示した場合のみ行う。
- Company repository `RuikiHAYASHI/research-workspace` は研究文脈のSSOTとして、Company skillのworkflowに従って更新できる。

## 実行環境とデータ利用

- 実装環境のサーバ移行は完了している。実装対象repoとEgoCrossは同じ `/mnt/HDD18TB/hayashi/` 配下で利用でき、データ転送、SSH、VPN、mount、権限付与をこの実装の前提作業にしない。
- EgoCrossの実データ構成・JSON schema・Qwen参照実装は `experiments/2026-09-15-egocross-qwen-local-investigation.md` に記録済みである。EgoCross固有のadapter、評価、LoRAは引き続き対象外である。
- 最初のend-to-end入力は50Saladsの既存 `sequential_loader` public APIを使う。実行時に利用する50Salads rootはCLIで明示する。旧サーバの固定pathを再現性情報や実行例に使わない。
- Hugging Faceのmodel downloadまたはaccess tokenが必要な場合だけ、必要な認証・利用規約同意はユーザーが行う。認証済みmodel / local checkpointが利用できる場合は、それをCLIのmodel ID/pathで指定する。
- 初期の実モデル実行では `Qwen/Qwen3-VL-4B-Instruct` をHugging Face Hubから取得する。取得先はTransformersの標準cacheとし、研究repoや`outputs/`へ重みを複製しない。
- 実データsmokeでdataset rootまたはmodelが読めない場合、そのsmokeだけを未検証として報告する。別datasetや別checkpointへ暗黙に置き換えない。

## 対象外

- EgoCross固有処理、Reflective Dialogue、Teacher/Solver Agent。
- 学習、LoRA、SFT、online gradient update。
- multi-timescale memory。
- important / anticipatory memory。
- dynamic chunk length。
- 次chunk選択Agent。
- vision encoder / compute resourceの動的切替。
- Memory容量最適化、KV-cache管理。
- GUI / Web UI。
- realtime latency最適化。
- full benchmark、長時間GPU実験、精度主張。

## 互換性

- `sequential_loader` はpublic APIのみを利用し、内部moduleへ依存しない。
- 既存 `scripts/smoke_sequential_loader.py` の挙動を変更しない。
- 既存50Salads smokeのdataset handlingと、RAW timestampを補正しない方針を維持する。
- 既存 `.gitignore` のartifact policyを維持する。

## 成功条件

### 実装成功

- modelを実ロードしないunit testで、Memory update inputが `question + current frame metadata + previous memory` のみから構成されることを検証できる。
- `frames_per_chunk=1` のSequentialSampleを順に処理し、各valid frameにつき1件のJSONL recordを書ける。
- recordのframe index順が入力stream順と一致する。
- previous_memoryが直前recordのupdated_memoryと一致する。
- EOFでloopが正常終了し、final answer用inputがfinal MemoryとQueryだけから構成される。
- 既存smoke scriptは変更されず、import/compileレベルで非回帰を確認する。実データで走らせる場合は、旧既定pathを使わず、実在する50Salads rootを `--dataset-root` で明示する。

### 短時間smoke

VLM/checkpointと、CLIで明示した読取り可能な50Salads rootが利用できる環境では、少数frameまたは短いsequenceで以下を確認する。

- current frameごとにVLMが1回呼ばれる。
- JSONLが逐次増える。
- Memoryが次frameへ引き継がれる。
- EOF後にfinal answerが保存される。

GPUを使う長時間full-video runや精度評価は、この実装承認には含めない。

## 実装Stepとcommit計画

各Stepは対応するunit testまたは短時間checkを同じcommitに含め、`origin/feat/streaming-text-memory` へpushする。途中commitも既存smokeを壊さず、model重みや生成artifactはcommitしない。

1. `feat: add text memory prompt contracts`
   - Memory更新とfinal answerのprompt/input contractを実装し、future情報を渡さないunit testを追加する。
2. `feat: add causal text memory pipeline`
   - fake VLMで動作するframe順のMemory状態遷移を実装し、呼出回数・順序・Memory連鎖・EOF後のfinal answerを検証する。
3. `feat: add sequential loader frame source`
   - `sequential_loader` public APIから `frames_per_chunk=1` でvalid frameを供給する50Salads接続を実装し、reader lifecycleを確認する。
4. `feat: persist streaming QA artifacts`
   - run別のJSONL、final answer JSON、run metadataを実装し、逐次保存と非上書きを検証する。
5. `feat: add Qwen3-VL streaming CLI`
   - `Qwen/Qwen3-VL-4B-Instruct` を既定とするHugging Face adapterとCLIを実装する。`--max-frames` は短時間smoke専用の任意上限とする。
6. `docs: document streaming text memory run`
   - 依存関係、Hugging Faceからの初回モデル取得、短時間smoke、artifact確認の実行手順をREADMEへ記録する。

## Codex完了報告に必要な情報

Codexは実装作業の終了時に、少なくとも次をユーザーへ報告する。

- 実際に編集したrepository / branch /開始時HEAD commit。
- 作成したbranch、各commit SHA、originへのpush結果。
- 変更したファイルと各変更の目的。
- 実行したunit / smoke / compile等と結果。
- datasetやGPU不足等により未検証の項目。
- 実データsmokeで使用したdataset root、model ID/path、split、sequence id。
- commit / push / PRを行ったか否か。未指示なら行っていないことを明示する。
- local worktreeがdirtyのままなら、その状態と今回変更との区別。

## 実装後に未検証として残すもの

- text MemoryがVideoQA精度に有効か。
- Memoryが長時間streamで情報希釈するか。
- promptの最適形。
- model間差。
- 50Salads以外のdatasetでの一般化。

これらは実装成立後に別experiment / specで評価する。

## 実装結果

- 実装repository: `/mnt/HDD18TB/hayashi/2026_09_hayashi_streaming_video_qa`
- branch: `feat/streaming-text-memory`（`origin/feat/streaming-text-memory` へpush済み）
- 実装commit: `0bc1479`, `29a9371`, `2e31669`, `81aed83`, `ee47949`, `aa5255e`, `03deddb`, `1b03097`
- 実装済み: 因果prompt contract、fake VLMでの逐次Memory状態遷移、50Salads public API source、run別artifact、Hugging Face Qwen3-VL CLI、実行手順。
- 検証済み: `python3 -m unittest discover -s tests -p 'test_*.py'`（7 tests）、`python3 -m py_compile streaming_text_memory/*.py scripts/*.py`、`python3 scripts/run_streaming_text_memory.py --help`。
- 未検証: 現ホストの実行用`.venv`にはtorch、sequential_loader、transformersが未導入のため、Hugging Faceからの実モデル取得・実Qwen推論・実50Salads smokeは未実行。これは長時間のモデルdownload / GPU runを含むため、実装完了とは分けて扱う。

## 更新履歴

| 日付 | 内容 |
|---|---|
| 2026-09-15 | サーバ移行完了とEgoCrossのローカル利用可能状態を反映。旧サーバの固定50Salads pathへの依存を除き、新規CLIとsmokeは実在するrootを明示指定する契約に更新。実装scopeは変更していない。 |
| 2026-09-15 | `feat/streaming-text-memory` をmainから作る実装branchとして指定。Codexに同branchでの通常のcommit・origin pushを許可し、`sequential_loader` に合わせたcommit message種別を定めた。mainへの直接変更、force push、PR作成、mergeは引き続き対象外。 |
| 2026-09-15 | 既定VLMをHugging Face Hubの `Qwen/Qwen3-VL-4B-Instruct` として追加。初回CLI実行時の標準cacheへの取得、重みをGit管理しない方針、6 Stepのcommit計画を明記。 |
| 2026-09-15 | 実装を`feat/streaming-text-memory`へ8 commitで完了しoriginへpush。unit test、compile、CLI helpを確認。実Qwenロードと実データsmokeは未実行として分離し、specをimplementedへ更新。 |
