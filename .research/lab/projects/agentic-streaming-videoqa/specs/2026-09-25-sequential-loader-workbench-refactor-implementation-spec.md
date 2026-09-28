---
date: 2026-09-25
project: agentic-streaming-videoqa
status: implemented
topic: sequential-loader-workbench-refactor-and-turn-based-ui
source: 2026-09-18 MTG、2026-09-25 sequential-loader workbench spec、2026-09-25 current-worktree audit、2026-09-25 user UI requirements
supersedes: []
related_specs:
  - 2026-09-23-new-repository-videoqa-system-implementation-spec.md
last_updated: 2026-09-25
---

# YAML・英語prompt・責務分割とターン型LongVideoQA Workbenchの実装仕様

## 1. 目的

LongVideoBenchをsequential_loaderの公開APIで先頭から前方向decodeするLongVideoQA Workbenchについて、次を一つの実装契約として完了する。

1. 元のWorkbench作業ツリーへ、YAML設定、外部英語prompt、責務別パッケージ構造、逐次readerを反映可能なbranchを届ける。
2. 動画全体を一括実行せず、1処理区間を1ターンとして利用者が明示的に進める画面・APIへ変更する。
3. 各ターンで状況理解と情報集約を連続実行し、前後のターン結果を左右ボタンで閲覧できるようにする。
4. そのターンで採用したframeを、実timestamp順に画面へ表示する。
5. 既存のartifact安全契約、因果的な動画処理、ローカル専用HTTP API、CLI名、実行記録のJSON/JSONL形式を維持する。

本仕様は旧specの実装済み表記を置き換える。旧specで要求したYAML化等の一部は隔離worktreeに存在するが、元の作業ツリーへ未反映であり、ターン型UIは未実装である。

## 2. 現状監査と基準

### 2.1 ユーザーが通常参照する元作業ツリー

対象repositoryは /mnt/HDD18TB/hayashi/2026_09_hayashi_longvideoqa_workbench である。

- 現在branch: feat/step-11-initial-qwen-run
- 基準commit: 7544cd8
- ユーザーの未追跡文書: docs/file-relationships.md、docs/file-responsibilities.md、docs/processing-flow.md
- 現在の設定: configs/longvideobench-p9h.json
- 現在のprompt: JSON内およびconfiguration.pyの日本語文字列
- 現在の構造: configuration.py、pipeline.py、records.py、server.py、adapters/を中心とするフラット構造
- 現在のUI: 一度のPOST /api/runsで動画全体をバックグラウンド実行し、完了した全stageを縦に表示する。ターン操作、過去ターン閲覧、frame画像表示はない。

### 2.2 隔離worktreeに存在する未配送の変更

次のworktreeとbranchには、旧specの一部実装がある。

- worktree: /mnt/HDD18TB/hayashi/research-workspace/.worktrees/longvideoqa-workbench-refactor
- branch: refactor/sequential-loader-workbench
- commit: a4d6aa5

このbranchには、次がある。

- configs/common/longvideobench-qwen3vl.yaml
- configs/recipes/p9h-sequential-1min-8frames.yaml
- prompts/en/配下の3 asset
- config、core、dataset、reader、sampling、model、agent、records、interfaces、webへの責務分割
- sequential_loader公開API readerと時刻グリッド選択

ただし次は未完了である。

- 元作業ツリーのbranchへ未反映である。
- run_chunk_understanding等がmodelへ埋め込む説明文・空evidence文言には日本語が残り、解決済みmodel promptが完全な英語ではない。
- APIは動画全体を一回で処理する。
- UIはターン単位の実行・閲覧を持たない。
- artifactはframe番号・時刻を保存するだけで、画面表示用thumbnailを提供しない。

### 2.3 外部依存の基準

sequential_loaderは次のbranchを基準にする。

- repository: /mnt/HDD18TB/hayashi/sequential_loader
- branch: feat/longvideobench-source-adapter
- commit: e44efbf

LongVideoBenchAdapterは公開入口 import sequential_loader as sl から使う。Workbenchはローダー内部のsrc.*をimportしない。

## 3. 採用範囲と維持条件

### 3.1 採用する変更

- JSON実行設定を廃止し、allowlistで解決するYAML profile/recipeへ移行する。
- 既定の3 stage promptをprompts/en/の英語text assetへ分離する。
- modelへ渡す動的値も英語にする。具体的には区間画像数の説明、空の過去evidence、空の最終evidenceを英語にする。
- Pythonをconfig/、core/、dataset/、reader/、sampling/、model/、agent/、records/、interfaces/、web/へ責務分割する。
- sequential_loader経由の前方向decode、VideoWindow、time_grid_first_after_targetを唯一の動画読込・frame選択経路にする。
- 1ターンにつき状況理解と情報集約を実行し、利用者の明示操作で次ターンへ進むUI/APIを追加する。
- 選択frameの画面表示用thumbnailを、実行serverが生きている間だけ提供する。
- 既存artifactにturn境界を追加し、過去ターンの文字結果を再読込可能にする。

### 3.2 維持するもの

- CLI名 longvideoqa、run、serve、qwen-preflight。
- 127.0.0.1だけで待ち受けるHTTP serverと既存のGET /api/capabilities、POST /api/recipe/preview、POST /api/runs、GET /api/runs/<run_id>。
- 既存artifactのexecution_settings.json、run_status.json、chunks.jsonl、stages.jsonl、final_answer.json。
- 実行単位 (video_id, question_id)、LongVideoBench validation annotationのvideo_pathによる動画解決、字幕無効、正解ラベル非混入。
- 一動画一reader session、SequenceSource(start_frame=0, stop_frame=None)、batch_size=1、num_workers=0、shuffle=False、in_order=True、valid_mask=Trueのみ利用、timestamp単調非減少の拒否。
- 実行artifactへの画像本体、絶対パス、正解ラベル、モデル重み、認証情報の非保存。
- 実LongVideoBench、実Qwen、GPU推論、全件評価、性能計測は実装検証の対象外。

### 3.3 明示的な非互換

- configs/longvideobench-p9h.json とJSON設定読込を削除する。YAML recipeへ移行し、JSON設定用の互換layerは作らない。
- chunk_seconds / frames_per_chunk は window_seconds / frames_per_window に統一する。
- 旧フラットmodule pathとsparse seek readerは削除し、恒久的な互換wrapperを置かない。
- 画面の実行開始は全動画を最後まで実行しない。1ターンだけを実行する操作へ変わる。

## 4. YAML・英語prompt・構造の契約

### 4.1 配置

~~~
configs/
├── common/
│   └── longvideobench-qwen3vl.yaml
└── recipes/
    └── p9h-sequential-1min-8frames.yaml
prompts/
└── en/
    ├── chunk_understanding.txt
    ├── evidence_aggregation.txt
    └── final_answer.txt
src/longvideoqa_workbench/
├── config/
├── core/
├── dataset/
├── reader/
├── sampling/
├── model/
├── agent/
├── records/
├── interfaces/
└── web/
~~~

profileはデータセット登録名、モデルID、生成設定、字幕無効、decoder_frames_per_sample=16、stageとprompt IDを持つ。recipeはprofile、question_id、window_seconds、frames_per_windowだけを持つ。初期recipeは60秒・最大8画像である。

### 4.2 prompt

3 assetは英語で記述する。解決後のpromptに挿入する次の値も英語である。

- chunk.frames: 例 8 images sampled from this window
- 空のprevious.evidence: 例 No previous evidence is available.
- 空の最終evidence: 例 No evidence is available.

画面のprompt編集は1 runだけへの上書きとし、assetファイルを変更しない。実行開始時には本文、prompt ID、SHA-256 hashをexecution_settings.jsonとresolved_prompts.jsonへ保存する。

## 5. ターン実行の契約

### 5.1 ターンの意味

通常ターンnは1つのVideoWindowに対応し、次を順に実行する。

~~~
選択frame + 質問 + 選択肢
  -> chunk_understanding
  -> current observation

previous evidence + current observation + 質問 + 選択肢
  -> evidence_aggregation
  -> updated evidence
~~~

次の通常ターンへ渡すのはupdated evidenceだけである。chunk_understandingは現在windowのframe、質問、選択肢だけを受け、過去結果や未来frameを受けない。

動画EOFが検出された後、利用者の次の操作で最終ターンを実行する。

~~~
final evidence + 質問 + 選択肢
  -> final_answer
~~~

final_answerは一回だけ実行する。動画全体を開始操作だけで最後まで進めない。

### 5.2 API

既存APIに次を追加する。

| 操作 | endpoint | 動作 |
| --- | --- | --- |
| run作成 | POST /api/runs | 設定を解決・検証し、artifactとreader sessionを作る。model呼出しはしない。 |
| 次ターン実行 | POST /api/runs/<run_id>/turns/next | 通常turnを一つ、またはEOF後にfinal turnを一つだけ実行する。 |
| run取得 | GET /api/runs/<run_id> | status、既完了turn、stage、選択frame metadata、next actionを返す。 |
| thumbnail取得 | GET /api/runs/<run_id>/turns/<turn_index>/frames/<frame_index>.jpg | 同一server lifetimeに限り、選択frameの縮小JPEGを返す。 |
| cancel | POST /api/runs/<run_id>/cancel | reader sessionを閉じ、runをcancelledとして終了する。 |

POST /api/runsの後、画面は同じ利用者操作の中でturns/nextを呼び、Turn 1を実行する。以後の実行ボタンは常に一つ先のturnだけを実行する。

一つのserverでは同時に一つのactive runだけを許可する。turn実行中の重複要求は409で拒否する。

### 5.3 状態と資源解放

run_status.jsonの状態はready、running、awaiting_next_turn、succeeded、failed、cancelledを許可する。

TurnSessionはreader context manager、window iterator、current evidence、次turn番号、thumbnail cacheを所有する。正常完了、reader EOF後のfinal回答、モデル例外、cancel、server shutdownの全てでreader contextを閉じる。reader contextを跨いで別動画を開かない。

CLIのlongvideoqa runは従来どおり全turnを連続して実行できる便利入口として維持する。ただし内部ではserverと同じ1-turn処理関数を繰り返し、stage実装を二重化しない。

## 6. 過去結果と選択frameの表示

### 6.1 UI

実行領域を次の構成にする。

~~~
[← 前のターン]  Turn 3  [次のターン →]
[Turn 4を実行] または [最終回答を生成]

現在turnの時刻範囲
  ├─ picked frames: timestamp昇順のthumbnail gallery
  ├─ 状況理解
  └─ 情報集約

最終turn:
  └─ 最終回答
~~~

- 左右ボタンはすでに完了したturnを閲覧するだけで、modelやreaderを動かさない。
- 実行ボタンは最新turnを閲覧しているかに関係なく、未実行の次turnだけを進める。
- 現在表示中turn、実行済みturn数、次操作を明示する。
- 実行中は実行ボタンを無効化する。failed/cancelled時は再実行せず理由を表示する。
- 既存のstage prompt詳細とraw output詳細は現在表示turnだけに表示する。
- DOMはtextContentと属性設定で構成し、innerHTMLを使わない。

### 6.2 frame thumbnail

thumbnail galleryには、選択順（timestamp単調非減少）で次を表示する。

- 画像
- target timestamp
- 実際のtimestamp
- frame index

readerからの元画像はVLM呼出し後に解放する。表示用には最大辺480pxのJPEG thumbnail bytesだけをactive TurnSessionに保持する。thumbnailは同一browser/server sessionでの過去turn閲覧のためだけに使い、artifactへ保存しない。server再起動後や過去artifactの再表示では、文字結果とframe metadataは表示するが、画像はこの実行のthumbnailは利用できませんと表示する。

この非永続契約により、既存の画像artifact非保存条件を維持する。ページ再読込後やserver再起動後にも画像閲覧を要求する場合は、本仕様を変更して画像保存方針を別途承認する。

## 7. artifact契約

既存ファイル名を保ち、次を追加・拡張する。

- execution_settings.json: 解決済みYAML設定、prompt ID/hash/body、code version、settings hash。
- resolved_prompts.json: stage別のprompt ID/hash/body。
- chunks.jsonl: turn_index、window範囲、time_grid_first_after_target、target timestamps、採用frame index/timestamp。
- stages.jsonl: stage、turn index、chunk index、resolved prompt、raw output、validated output、elapsed seconds。
- turns.jsonl: turn index、kind（windowまたはfinal）、chunk index、開始・終了時刻、実行完了時刻。
- run_status.json: 第5.3節の状態、current turn、error category。

turns.jsonlを使い、server再起動後も文字結果とmetadataをターン単位に再構成できるようにする。thumbnail bytes、raw frame array、絶対path、正解ラベルは書き込まない。

## 8. 実装範囲と手順

### Step A: 基準と既存refactorの配送

1. 元作業ツリーの未追跡文書3件を確認し、内容を変更・追加・削除しない。
2. a4d6aa5を基準にrefactor/turn-based-workbenchを作る。
3. 元ツリーの旧JSON、フラットmodule、sparse readerを再実装しない。YAML・英語asset・責務分割・逐次readerは基準branchの実装を正とする。
4. 実装完了後、元作業ツリーを更新する前にbranch、未追跡文書、パス衝突を再確認する。未追跡文書と衝突しない場合だけ、feat/step-11-initial-qwen-runを成果branchへfast-forwardする。mainへの統合、push、PR作成、強制更新は対象外とする。

### Step B: 英語promptの完全化

1. 英語assetとruntime埋込値を見直し、modelへ渡るresolved promptの日本語を除く。
2. prompt assetのhashと実行時上書きのhashをtestで確認する。
3. JSON configとJSON prompt本文を削除する。

### Step C: turn engineとartifact

1. agent/pipeline.pyを、通常turn処理とfinal turn処理を共有できる関数へ分割する。
2. interfaces/server.pyにTurnSessionと新endpointを追加する。
3. records/run.pyに状態、turns.jsonl、turn indexを追加する。
4. reader contextの資源解放をsuccess/failure/cancel/server shutdownで保証する。
5. CLI全連続実行が同じturn関数を用いるよう変更する。

### Step D: turn UIとframe gallery

1. web/index.htmlにturn navigator、turn action、gallery、empty/error stateを追加する。
2. web/app.jsを全run polling表示からturn payload表示へ変更する。
3. web/style.cssにtimestamp順gallery、現在turn、disabled操作、狭い画面向けlayoutを追加する。
4. thumbnail endpointはJPEGだけを返し、CSP、Content-Type、Cache-Control、run ID validationを維持する。

### Step E: 文書と検証

1. READMEと逐次処理境界文書をturn操作・thumbnail非永続契約へ更新する。
2. config、prompt、reader、turn engine、artifact、HTTP API、UI assetのtestを追加する。
3. 全test、構文検査、CLI help、擬似入力のローカルAPI smokeを実行する。

## 9. 検証可能な成功条件

1. 元作業ツリーではJSON config、旧日本語prompt、旧フラットmodule、sparse readerが残らず、指定のYAML/asset/package構造だけが存在する。
2. 3 stageのassetとmodelに渡るresolved promptは英語であり、本文・ID・hashがartifactへ残る。
3. POST /api/runsだけではmodelを呼ばず、各turns/next要求は通常window一つの状況理解と情報集約だけを実行する。
4. EOF後の一回のturns/nextだけが最終回答を生成し、二回目は拒否される。
5. 過去turnの左右閲覧はreaderやmodelを呼ばず、表示中turnだけを変更する。
6. galleryは採用frameを実timestamp昇順で表示し、画像、target timestamp、timestamp、frame indexがchunks.jsonlと一致する。
7. thumbnailはartifactに保存されず、active server session以外では利用できないことを明示表示する。
8. cancel、model失敗、reader失敗、server shutdownでreader contextが閉じ、run_statusが適切な終端状態になる。
9. CLI全連続実行、既存JSON/JSONL artifact名、ローカルAPI入口、正解ラベル非混入、絶対path非保存は回帰しない。
10. Workbench全test、sequential_loader全test、両方のcompileall、全CLI help、生成動画decode、擬似API smokeが成功する。

## 10. 対象外

- 実LongVideoBench、実Qwen、GPU推論、読込速度測定、精度評価、全件評価、学習。
- 字幕、有効frame以外の利用、動的frame選択、次window注目prompt、frame単位memory。
- artifactへのfull-resolution画像またはthumbnailの永続保存。
- mainへの統合、push、PR作成、強制更新。

## 11. 承認GateとImplementation Handoff

- 承認状態: approved（2026-09-25、サムネイルはserver session内のみ保持する方針を承認）。
- 実装状態: implemented（2026-09-25、Workbench commit 7957b66、feat/step-11-initial-qwen-runへfast-forward済み）。
- 実装目的: YAML/英語prompt/責務分割/逐次readerを元作業ツリーへ配送し、1 window 1 turnの実行・閲覧・thumbnail UIを実現する。
- 基準repository/commit: Workbench refactor/sequential-loader-workbench / a4d6aa5、外部ローダー feat/longvideobench-source-adapter / e44efbf。
- 変更scope: 第3〜8節。
- 対象外・維持条件: 第3.2節、第3.3節、第10節。
- short verification: unit/integration test、compileall、CLI help、生成動画decode、fake model/API smoke。
- 長時間run: 未許可。
- 未検証予定: 実LongVideoBench・実Qwenの速度と精度、GPU、全件評価。
- 検証結果: Workbench 63 tests passed、sequential_loader 169 tests passed、両repositoryのcompileall成功、全CLI help成功、生成動画decodeとfake API smoke成功。
- 環境制約: Node.jsが未導入のためnode --checkは未実施。browser asset testとinnerHTML非使用testは成功。
