---
date: 2026-09-15
project: agentic-streaming-videoqa
status: approved
topic: streaming-text-memory-inference
source: 2026-09-11 MTG + current implementation request + 2026-09-15 Codex handoff boundary
---

# Streaming Text Memory 推論パイプライン実装Spec

## 目的

9/11 MTGで決定した、future frameへアクセスせず動画を先頭から逐次処理し、各時点で `current frame + previous text memory -> new text memory` を繰り返す最小構成を、研究コードとして再利用可能な形で実装する。

今回はEgoCross固有の手法・Reflective Dialogue・既存Agent実装を利用しない。現在の研究repoに既に存在する `sequential_loader` public API接続を基盤とし、まず単一VLMによるtext Memory更新と最終QAまでのend-to-end経路を成立させる。

## Authority / 前提

- 現在のユーザー指示: 2026-09-15「MTGで話した内容を実現し、過去のEgoCross等とは切り離して本格的な実装を進める」。
- MTG決定: `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-11-mtg.md`。
- 研究コードrepo: `tamaki-lab/2026_09_hayashi_streaming_video_qa`。
- baseline branch: `main`。
- baseline commit: `38eff9ce480271e85b94def34cf51979a6c8a7ce`。
- `sequential_loader` は別repoの基盤機能として扱い、研究固有ロジックを追加しない。
- 現行repoは50Saladsを `sequential_loader` のpublic API経由で読むacceptance smokeのみを持ち、model / question / memory / QA loopは未実装。
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
- 特定checkpointを研究仕様へ固定しないため、model ID/pathをCLIで指定できるようにする。
- 初期実装はHugging Face Transformersのimage-text generation経路で動く単一VLMとする。
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
- `tamaki-lab/2026_09_hayashi_streaming_video_qa` のlocal worktreeで、本specに必要な最小コード・test・config変更を行う。
- `tamaki-lab/sequential_loader` は原則として既存public APIのread-only依存として扱い、本specの都合だけで変更しない。
- fake / stub modelを用いるunit test、compile/import check、既存smokeなど、短時間かつ安全な検証は実装作業に含めてよい。
- local worktree上で生成したdiffを確認し、本spec外の変更やユーザーの既存dirty changeを混ぜない。
- GitHub上のCompany文書は実装判断のSSOTとして参照する。

### Codexが自動で行ってはいけない作業

- `git commit`、`git push`、Pull Request作成、merge。これらはユーザーの明示指示がある場合のみ行う。
- 長時間GPU run、full-video benchmark、大規模評価、training。コード実装の許可から実験run許可を推定しない。
- `tamaki-lab/sequential_loader` の仕様変更や研究固有ロジック追加。
- dataset、model、checkpoint、split、prompt研究方針など、本specで未決の研究判断を独自に固定すること。
- local worktreeへの変更を、GitHub remoteへ反映済みとみなすこと。

### ChatGPT側の操作境界

- ChatGPTは `tamaki-lab/*` のGitHub repositoryを原則read-onlyで調査する。
- GitHub上の `tamaki-lab/*` へのファイル作成・更新・削除、commit相当の書き込みは、ユーザーがその操作を個別に明示した場合のみ行う。
- Company repository `RuikiHAYASHI/research-workspace` は研究文脈のSSOTとして、Company skillのworkflowに従って更新できる。

## ユーザー側で行う外部作業

Codex / ChatGPTから直接到達できないserver、credential、dataset配布元に関する操作はユーザー担当とする。

### 必須になる可能性が高い作業

- 別serverに存在するEgoCross datasetを、実装・実験を行う研究serverへ `rsync` / `scp` 等でコピーする。
- コピー先のdataset rootをCodexへ伝える。
- コピー前後でdisk容量、file数、directory構造、read permissionを確認する。
- source serverやstorageへのSSH認証、VPN、mount、権限付与など、人間側のcredentialが必要な操作を行う。
- Hugging Face等で利用規約同意や個人tokenが必要なgated dataset / modelを使用する場合、必要な認証・同意を行う。

EgoCross datasetのコピーは**データ配置上の外部作業**であり、EgoCross固有手法・Reflective Dialogueを今回の実装へ導入することを意味しない。

また、現在の実装baselineは既存50Salads接続を利用する。EgoCross datasetを本実装の入力datasetへ変更する場合は、dataset adapter / split / annotation contractが変わるため、Codexが独自に置換せず、別途ユーザー指示またはspec addendumで確定する。

### ユーザー作業待ちの扱い

- datasetコピーなど外部作業が未完了でも、fake model / mock inputで検証可能なコード実装・unit testは先に進めてよい。
- 実datasetを必要とするsmokeに到達した時点でdataset rootが利用不能なら、その項目を未検証として停止し、必要なユーザー作業を具体的に報告する。
- 外部resource不足を理由に、別datasetや別checkpointへ勝手に置換して成功扱いにしない。

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
- 既存smoke scriptは変更されず、import/compileレベルで非回帰を確認する。

### 短時間smoke

VLM/checkpointと実データが利用できる環境では、少数frameまたは短いsequenceで以下を確認する。

- current frameごとにVLMが1回呼ばれる。
- JSONLが逐次増える。
- Memoryが次frameへ引き継がれる。
- EOF後にfinal answerが保存される。

GPUを使う長時間full-video runや精度評価は、この実装承認には含めない。

## Codex完了報告に必要な情報

Codexは実装作業の終了時に、少なくとも次をユーザーへ報告する。

- 実際に編集したrepository / branch /開始時HEAD commit。
- 変更したファイルと各変更の目的。
- 実行したunit / smoke / compile等と結果。
- datasetやGPU不足等により未検証の項目。
- ユーザー側で次に必要な外部作業。
- commit / push / PRを行ったか否か。未指示なら行っていないことを明示する。
- local worktreeがdirtyのままなら、その状態と今回変更との区別。

## 実装後に未検証として残すもの

- text MemoryがVideoQA精度に有効か。
- Memoryが長時間streamで情報希釈するか。
- promptの最適形。
- model間差。
- 50Salads以外のdatasetでの一般化。

これらは実装成立後に別experiment / specで評価する。
