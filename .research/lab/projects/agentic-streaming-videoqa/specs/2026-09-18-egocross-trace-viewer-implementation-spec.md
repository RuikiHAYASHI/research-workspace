---
date: 2026-09-18
project: agentic-streaming-videoqa
status: draft
topic: egocross-trace-viewer-implementation
source: 2026-09-18 current-repository and real-trace investigation
last_updated: 2026-09-18
---

# EgoCross Observation Trace Viewer 実装spec

## 目的

EgoCross Observation Prototypeが出力済みの1 runを、ローカルのWebサーバー経由でEdge等のブラウザから読めるようにする。初見の閲覧者が、最終QAの評価結果ではなく、画像列を順に見ながらAgentが「何を観測し、何を記憶に残すか」を追跡する試作であることを理解し、各frameの結果を確認できることをゴールとする。

画面の主役は次の因果順である。

```text
現在画像 → 観測文 → Agent action → 更新後のtext state
```

本specは、既存の実行結果を閲覧する機能だけを追加する。Qwenの実行、最終回答、正解率計算、研究上の性能評価は追加しない。

## 調査結果と前提

### 現在の実装・検証済み範囲

- 対象repositoryは`/mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation`、調査時HEADは`0288519`（`feat/step-07-agent-reproducibility`）である。未commitの`docs/`変更があるため、実装開始時にこれを変更・削除・commitしない。
- `--agent`では、current imageからQwen3-VLが観測文を生成し、previous text stateと観測文だけから別callでactionを生成し、Reducerが次stateを決定する。過去画像・future frame・最終QAはこの経路に含まれない。
- runは`outputs/<run-id>/frames.jsonl`と`run_metadata.json`に保存され、同名runを上書きしない。`frames.jsonl`は1行が1 frameのJSONLである。
- 実Qwenの短時間確認済みrun `20260917T034823Z_1_60ee3a84` はrecord 1の5 frameを処理し、全行で`error: null`、actionは`ADD` 1件と`UPDATE` 4件だった。この事実は経路の動作確認であり、Agentの有効性やQA性能の根拠ではない。
- 現在の依存はPillowとpytestのみで、Web frameworkは導入されていない。ビューアは新規外部依存を追加せず、Python標準ライブラリとブラウザ標準JavaScriptで構成できる。

### 表示上の注意が必要な既知の不整合

`OpenEvent.first_frame` / `last_evidence_frame`はコード・文書ではframe indexとして定義されている。一方、上記実runではframe 1、3、4に対応してそれぞれ`2`、`6`、`8`が記録されており、相対timestamp（秒）が入っている。現在のparserは非負整数であることしか検証しないため、表示画面がこれを「frame番号」として出すと誤った説明になる。

したがって、ビューアはこの値を修正完了まで主表示に使わない。実装の最初に、eventのprovenanceをcurrent `frame_index`から決定的に付与する契約へ直し、既存runは旧schemaとして「eventの開始・最終frameは表示しない」互換表示にする。

## 採用する体験設計

### 最初に読ませる説明

結果画面の上部に、常時見える短い説明を置く。専門語だけを並べず、次を日本語で説明する。

1. この画面は最終解答やaccuracyを示すものではなく、画像列を順に処理した途中記録であること。
2. **観測**は「現在表示中の画像一枚からモデルが述べたこと」であること。
3. **Agent action**は「観測を受け、次frameへ渡す短い記憶をどう扱うか」の選択であり、画像を見直す操作でも回答を選ぶ操作でもないこと。
4. **text state**は過去画像の代わりに引き継ぐ、件数上限付きの短いテキスト記憶であること。
5. ブラウザ上の時系列移動は実行後の結果閲覧であり、モデルがfuture frameを入力に使ったことを意味しないこと。

説明には、`現在画像 → 観測 → action → 次state`の1行図と、`ADD`、`UPDATE`、`KEEP`、`FLAG_UNCERTAIN`、`CLOSE_EVENT`の平易な用語表を含める。全actionが存在しないrunでも説明表は常に表示する。

### 結果の既定表示

結果画面は、次の順に情報を見せる。画面文言は日本語、既存traceに保存された観測文・reason・state本文は改変せず原文のまま表示する。表示のためにLLM翻訳・要約を新規生成しない。

| 領域 | 常時表示する内容 | 意図 |
| --- | --- | --- |
| run概要 | run ID、mode、record ID、frame数、sampling FPS、`最終QA・accuracyは未実装`の注記 | この結果の範囲を最初に誤解させない。 |
| 問題文脈 | 質問文、選択肢、dataset、question type | 何を意識して観測したrunかを分かるようにする。 |
| 時系列ナビゲータ | frame番号、相対時刻、action色、エラー状態を持つ横並びの選択ボタン | frameを任意順に閲覧でき、処理順も見えるようにする。 |
| 現在frame | 選択frameの画像、frame番号、相対時刻、画像欠損時の明確なplaceholder | 入力と出力の対応を中心に置く。 |
| 観測結果 | `observation`を「この画像からのモデル観測」として表示 | 画像から生成した原出力を確認する。 |
| 記憶更新 | action、confidence、reason、stateの人間可読diff（追加・更新・維持・不確実性・閉鎖） | Agentが何をしたかをJSONなしで理解できるようにする。 |
| 更新後state | `scene_summary`、`event_ledger`、`watch_next`、`uncertainties`を区画別のカードで表示 | 次frameへ何が渡るかを確認する。 |

質問文・選択肢は既存の`run_metadata.json`には保存されていない。そのため、viewerはmetadataのmanifest pathとSHA-256を検証してから同一recordを読み直す。manifestが欠損・改変・record不一致なら、問題文脈の代わりに「入力manifestを検証できないため表示しない」と表示し、現在のmanifest内容を黙って結果へ混ぜない。

### 折り畳む情報と表示しない情報

- 詳細パネルには、model ID / revision、prompt・state schema version、generation parameters、コードrevision、各処理時間、logical pathを置く。絶対filesystem path、GPU番号、CLI全体は既定表示しない。
- `raw_policy_response`は検証済みの結果ではなく、失敗解析用の生文字列である。正常frameでは詳細パネル、parseまたはReducer失敗時だけエラー説明とともに目立つ位置へ出す。
- `state_before`の全文は既定で閉じる。前frameの`state_after`との連続性はviewer内部で検証し、連続していない場合だけ警告を出す。
- final answer、選択肢の順位、accuracy、モデル出力の正誤ラベル、全run比較、性能グラフは対象外とする。現在のartifactからは正当な根拠を作れないためである。

## 実装契約

### 実行方法と公開範囲

- 新しいCLIを`python3 scripts/serve_trace_viewer.py`として追加する。
- `--output-root`（既定`outputs`）、`--dataset-root`（既存の既定EgoCross root）、`--host`（既定`127.0.0.1`）、`--port`（既定`8000`）を受ける。
- 起動時に`http://127.0.0.1:<port>/`を標準出力へ表示する。EdgeはユーザーがこのURLを開く。ブラウザを自動起動しない。
- serverはloopbackを既定とし、`0.0.0.0`など外部公開可能なhostは本specの対象外とする。
- serverは既存artifactを読むだけで、Qwenをload・実行せず、`outputs/`、dataset、trace、metadataを書き換えない。

### serverとデータ境界

標準ライブラリの`http.server`を基に、専用のread-only handlerを`egocross_observation/viewer.py`へ実装する。静的assetは`egocross_observation/viewer_static/`に置き、package dataとして配布対象へ含める。

| endpoint | 振る舞い |
| --- | --- |
| `GET /` | HTML/CSS/JavaScriptのsingle-page viewerを返す。 |
| `GET /api/runs` | `output-root`直下の、有効なmetadataとJSONLを持つrunの要約一覧を返す。 |
| `GET /api/runs/<run-id>` | metadata、検証済み問題文脈、全frameの表示用データを返す。 |
| `GET /api/runs/<run-id>/frames/<index>/image` | 当該trace行が参照し、かつ`dataset-root`内に解決されるJPEG/PNGだけを返す。 |

`run-id`と`index`は厳格に検証し、`..`、slash、任意path、任意queryをfile pathへ使わない。画像endpointはtraceに記録された画像だけを対象とし、さらに解決済みpathがconfigured dataset root配下であることを再確認する。壊れたJSONL、欠損metadata、画像欠損、manifest hash不一致はサーバーを停止させず、該当run/frameだけを利用不能としてUIに理由を返す。

### 表示用データの正規化

- `mode=decode-only`では、画像と入力provenanceのみを示し、「観測・Agent stateはこのrunにはない」と表示する。
- `mode=observe`では、画像と観測文を示し、「Agent action / stateはこのrunにはない」と表示する。
- `mode=agent`では、観測、parsed decision、state before/after、エラーを上記体験設計どおりに出す。
- actionの色だけに意味を依存しない。action名と日本語説明を必ず併記し、エラーはactionと別の明確な警告にする。
- HTMLへの挿入は`textContent`等で行い、trace由来文字列を`innerHTML`へ渡さない。
- 選択frameのstate diffは、`parsed_decision`と`state_before` / `state_after`から決定的に作る。モデルにUI用説明の追加生成は依頼しない。

## 先行して修正するevent provenance契約

viewerの主表示に先立ち、次を実装する。

1. action JSONでモデルに`first_frame`と`last_evidence_frame`の値を決めさせない。
2. `ADD`時はReducerまたはその直前の決定的な正規化処理が、現在の`frame_index`を両fieldに設定する。
3. `UPDATE`時は既存eventの`first_frame`を保持し、`last_evidence_frame`を現在の`frame_index`へ設定する。
4. `CLOSE_EVENT`時も対象eventの開始frameを保持し、閉鎖を決めたcurrent `frame_index`をtraceに明示する。既存のactive stateからeventを外す挙動は維持する。
5. stateの構造名は既存のままとし、旧runのJSONを書き換えない。新しいrun metadataまたはtrace schema versionで新旧を識別する。

これは最終QAやAgent方策の内容を変える変更ではなく、modelが勝手に値を埋めていたprovenanceを実入力由来へ固定するための修正である。旧runは時刻/番号を画面に出さないことで表示互換を保つ。

## 変更範囲と実装順

基準は実装開始時に確認する`0288519`とする。現在branch上の未commit文書は利用してよいが、ユーザーの変更として保全する。実装用branchは、dirty stateを取り込まず基準commitから作る。

1. **event provenance contract**
   - `agent.py`、`agent_policy.py`、`reducer.py`、`agent_pipeline.py`、`run_metadata.py`と対応testを最小変更する。
   - prompt、decision parse、Reducer、traceの責務を維持しつつ、frame番号を決定的に付ける。
   - schema versionと利用文書の該当説明を更新する。
2. **viewer server**
   - `viewer.py`と`scripts/serve_trace_viewer.py`を追加し、run探索、metadata/manifest照合、表示用payload、画像配信を実装する。
   - `pyproject.toml`へ静的assetのpackage-data設定を追加する。外部Web frameworkは追加しない。
3. **single-page UI**
   - `viewer_static/`にHTML、CSS、JavaScriptを追加する。
   - run選択、説明、frame navigator、結果カード、詳細・エラー表示を実装する。
4. **テストと手動確認**
   - 合成fixtureだけでserverとUIのデータ契約を検証し、既存の実agent runをread-onlyでブラウザ確認する。

`outputs/`、dataset画像、model weight、credentialをGitへ追加しない。既存の観測CLIのデフォルト挙動と、`--observe`・`--agent`の因果入力境界を変えない。

## 検証可能な成功条件

### 自動test

- 全5 actionを含むagent trace fixture、`decode-only`、`observe`、error行、旧schema runを用意する。
- event provenanceの新契約について、ADD/UPDATE/CLOSE_EVENTがcurrent frame indexを正しく記録し、旧runを変更しないことを確認する。
- `GET /api/runs`が有効runのみを一覧化し、`GET /api/runs/<run-id>`がframe順を保存して返すことを確認する。
- manifestのhash一致時だけ質問・選択肢を返し、不一致・欠損時は明示状態を返すことを確認する。
- image endpointがtrace参照かつdataset root配下の画像のみを返し、path traversal、未参照画像、存在しないrun/indexを拒否することを確認する。
- trace由来のHTML特殊文字がテキストとして扱われること、エラーrunが他runの閲覧を妨げないことを確認する。
- 既存の`pytest`一式、import check、viewer CLIの`--help`を実行する。Qwenのdownload・GPU runはこの変更の必須testに含めない。

### 手動受入

既存の5-frame agent runを使い、`--host 127.0.0.1 --port 8000`でserverを起動し、Edgeで`http://127.0.0.1:8000/`を開く。次を満たせば受入とする。

1. 最初の画面だけで「最終QA・accuracyではなく、途中の観測と記憶更新を表示する」と分かる。
2. frame 0〜4を選ぶと、対応する画像・観測文・action・更新後stateが入れ替わる。
3. actionが`ADD` / `UPDATE`である理由とstateの変化を、raw JSONを開かず確認できる。
4. 質問・選択肢はmanifest hashが一致する場合だけ表示される。
5. model revision、処理時間、生policy出力などは必要時だけ詳細パネルで見られる。
6. ブラウザ操作、viewer起動ともにQwen実行や既存artifactの書換えを発生させない。

## 対象外

- final QA、正解率、回答選択肢の採点・表示。
- 957件全体の実行、run比較、統計・性能グラフ。
- live inference監視、実行中traceのtail、ブラウザからのQwen実行・停止。
- 未来画像をAgentへ渡すこと、frame skip、動的chunk長、再観察。
- 外部ネットワーク公開、認証、クラウド配信、Edgeの自動起動。
- raw trace・datasetを別形式へコピーまたは編集するmigration。

## Blocking / Non-blocking

### Blocking

1. event provenanceを「frame番号」として正しく固定する上記契約を採用するか。採用しない場合、既存フィールドを結果画面に安全に説明できない。
2. 最初のviewerを「既存runのread-only閲覧」に限定するか。実行中のlive表示を含めると、run途中のJSONL読み取り、更新通知、失敗・中断のUI契約が別途必要になる。

本specでは両方について、前者を修正し、後者をread-only閲覧に限定する案を推奨する。理由は、現在ある実artifactをそのまま理解可能にし、Qwen実行・GPU・live更新を追加せずに目的を達成できるためである。

### Non-blocking

- 色、余白、アイコン、カードの細部は既存のrepository styleに合わせる。
- ポートは既定8000とし、競合時は`--port`で変更する。
- run一覧の並びはrun IDの降順を既定とする。
- 表示用の日本語説明文は実装時に短く調整してよいが、最終QAでないことと因果入力境界を省略しない。

## Approval Gate

この文書は`draft`であり、コード変更、branch作成、commit、server起動、Edge表示を許可しない。実装開始には、次を明示承認する必要がある。

1. 主表示を「画像・観測文・action・state diff」とし、raw JSONと再現性metadataを詳細へ退避すること。
2. event provenanceのframe番号をモデル出力でなくcurrent `frame_index`から決定的に付与すること。
3. 初版をloopback上のread-only viewerに限定し、live推論監視・最終QA評価を含めないこと。

## Implementation Handoff

- approved spec: 本文書（現時点ではdraft）
- 実装目的: 既存EgoCross traceを、初見者が因果的な観測・記憶更新として読めるローカルWeb viewerにする。
- 基準repository/commit: `/mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation` の `0288519`。未commitの`docs/`変更は保全する。
- 変更scope: event provenance契約、read-only HTTP server、静的single-page UI、package data、test。
- 対象外・維持条件: Qwen実行、最終QA、accuracy、live監視、外部公開、既存traceの書換えは行わない。画像入力の因果境界を維持する。
- success criteria: 本文書の自動testと手動受入を満たす。
- 許可されている短時間検証: pytest、import/CLI help、loopback serverで既存runをread-only表示する確認（承認後）。
- 長時間runの許可状態: 未許可。Qwen実行・GPU runは別途指示が必要。

## 関連記録

- `specs/2026-09-16-egocross-observation-prototype-plan-spec.md`
- `specs/2026-09-16-egocross-observation-agent-addendum-plan.md`
- `experiments/2026-09-16-egocross-agent-text-state-smoke.md`
- `materials/2026-09-17-streamagent-related-work-mtg-materials.md`
