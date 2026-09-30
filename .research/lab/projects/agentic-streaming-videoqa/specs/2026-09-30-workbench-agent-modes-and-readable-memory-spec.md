---
date: 2026-09-30
project: agentic-streaming-videoqa
status: implemented
topic: workbench-agent-modes-and-readable-memory
source: 2026-09-25 MTG; 2026-09-29 and 2026-09-30 agent brainstorm; 2026-09-30 user request
last_updated: 2026-09-30
target_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
related_brainstorm:
  - 2026-09-29-agent-orchestration.md
  - 2026-09-30-evidence-adaptive-early-answer-videoqa.md
  - 2026-09-30-workbench-inference-ui-prompt-library-and-qwen-video.md
---

# Workbench: 動画区間理解・Agent記憶モード・可読な根拠記録（実装済みspec）

## 0. 状態・Authority・Gate

`status: implemented`。ユーザーは2026-09-30に**Situation/Memory/Answerの3つのプロンプト方針および選択frame列＋区間相対video timing＋元動画実timestamp manifestの構造を採用**し、同日、第10節の3件を `1A・2A・3 video_clip` と明示承認した。この承認は第8節の先行実装と短時間検証に適用し、実Qwen/GPU実験、push、PR、main統合には及ばない。Companyの変更は146 serverのローカルcloneへ自動反映しない。

同日、改訂前の初回scope（画像列での`none` / `previous_text`、重要イベント記録、機械用・人間用表示、固定4秒8枚）は別途明示承認・実装済み（第12節）。この承認・実装は本改訂で追加した`video_clip`入力・窓単位schema・新promptまで及ばない。

Authority: 現在のユーザー指示（動画入力・窓単位観測、3つのprompt、過去text ON/OFF、重要状態変化、再起動後保存など）→ 2026-09-25 MTG → approvedな現行spec → Evidence/現在コード → exploratory brainstorm。直近の`2026-09-30-workbench-inference-ui-prompt-library-and-qwen-video.md`にある未確定案は、本書で明示採用した部分だけ実装対象とする。

`2026-09-29-workbench-dataset-browser-ui-implementation-spec.md`の別「Step 10 draft」（初期導線/ブラウザ応答性）や早押し/動的samplingは、このspecの名前で勝手に承認・改番・実装しない。既存runの観測全frame形式はbaselineとして残し、新video schemaとはversionで区別する。

## 1. 現行実装の確認（GitHub、2026-09-30）

- 対象コード`RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main`調査時HEAD: `a491757cabb8ed897a2d752da73325fe15f48884`。GitHubの**default branchは旧`feat/step-10-qwen-preflight`**である。Codexはdefaultを現在研究コードと誤認しない。実装前にGitHub main、local main/worktrees/HEAD/dirty、依存loaderをread-only再監査する。
- `agent/pipeline.py`は状況理解→根拠集約をwindowごとに行い、EOF後の最終回答へ渡す。`run_window_turn`が既に`previous_evidence`を持つ一方、`run_chunk_understanding`はそれを入力しない。`core/validation.py`は観測promptへの`previous.evidence`を許可しない。単純なprompt編集だけでは新モードを実装できない。
- `config/loader.py`はYAML recipe/profileとprompt IDをallowlist解決し、`ExecutionSettings`と`RunRecord`が設定/実行別promptを保存。`settings_from_resolved_mapping`は旧runからrestart用に復元する。`interfaces/server.py`と`agent/pipeline.py`の両経路へ同じモードを通す必要がある。
- `records/run.py`は`memory.jsonl`に観測・イベント・`narrative_version`を追記、`memory.json`に最新snapshot、`stages.jsonl`にresolved prompt/raw/validated/elapsedを記録。既存`events.py`は6必須キーのexact検証、`final_output.py`は最終参照を検証する。旧記録を壊さない。
- `web/app.js`は既に`reader_mode`、`window_seconds`、`frames_per_window`、promptの編集と採用画像/実時刻/目標時刻の表示を持つ。新しい観測contextモードとvideo入力は既存`reader_mode`とは独立。
- `core/contracts.py`の`ModelRequest.images`と`model/qwen3vl.py`は現状`type:image`の列であり、video入力契約がない。`agent/observations.py`は旧frameごと完全被覆、`agent/events.py`は旧6キー＋`narrative`を厳密検証。共通`max_new_tokens:256`は8件の長いJSONでは切断の懸念があるが、提示runのfinish reasonはローカル成果物で未確認。
- `StageSettings`はpromptのみ、モデルのadapter/ID・generationはrun共通。別Agentモデル選択と永続prompt libraryは既存実装では未対応であり、別途Gateで実装単位を決める。
- loaderの対象frame専用公開APIは`tamaki-lab/sequential_loader@docs/target-frame-stream`（`76badb1c407a34de6f2dfa7e5d4040ef7c4b2ccc`）で確認済み。採用対象以外のRGB変換は回避するが、先頭からの圧縮decodeは続ける。default`master`や旧`feat/longvideobench-source-adapter`を新APIありと誤認しない。

## 2. 初回scopeと3 Agentの責務

目的: `sequential_loader`が現在windowから選んだフレーム列を**1つのQwen3-VL動画入力**として与え、Situationがwindow-levelの行動・状態変化・不明点を記述し、Memoryが質問関連情報と人物・物体・場所の重要な変化をテキストで蓄積する。各Agentとpromptの入出力はコードから追え、JSONLの正本と人間表示を一致させる。前記憶のSituation入力`none`/`previous_text`を独立した比較軸として提供する。現在のEOF Answerを保ち、早押し停止は実装しない。

1. **SituationAgent**: 現windowの採用frame列（video）、質問、実時刻manifestを受け、`window_summary`、意味のある出来事/状態の`observations`、`unresolved`を返す。**全採用frameに1件ずつ記述を要求しない**。採用frameをすべて記録する責務はWorkbench側。未観測frame・未来の出来事・選択肢を推測しない。
2. **MemoryAgent**: validated Situation JSON、直前確定済みbounded text narrative、manifestを受け、根拠付き`events`と次版`narrative`/`unresolved`を返す。質問に関わる証拠だけでなく、人物・物体・場所・所持物の重要な状態変化も残す。全イベント台帳と全記憶版はappend-only、次windowへ渡す文章はbounded working memoryとする。
3. **AnswerAgent**: EOF後、質問/選択肢/最終記憶/検証済みevents/frame/timeを受けて回答。現行の5項目`answer`/`evidence_event_ids`/`evidence_frame_indices`/`evidence_timestamps_seconds`/`narrative_version`を維持し、参照を検証する。まだ`CONTINUE/ANSWER`のDecision Agentにしない。

`VideoQAOrchestrator`は追加の推論AgentでなくPythonの決定的な進行管理。Qwen同一model_idなら共有lazy adapterを使う。既存`StageName`、Fake/CLI/server、明示turn、cancel、run記録、EOFと旧runを無断で改変しない。

### 2.1 比較条件

観測方法・記憶入力は別軸:
- `visual_input_mode=image_list`: 既存baseline。`type:image`列、旧全frame観測JSON/validator。未指定の旧保存済みrunはこの挙動で復元。
- `visual_input_mode=video_clip`: 今回の新規モード。`type:video`の選択済みframe列、動画の時間情報、**新window-level JSON schema/validator**。本モードではframe別完全被覆検証をしない。新規runのUIで明示的に選択・表示する。
- `observation_context_mode=none`: Situationへの前記憶なし。`previous_text`: 直前**正常確定済み**`memory.json`の`narrative`だけを追加。初回は過去情報なし。いずれも質問、採用frame、generation、Memory/Answer promptは同条件に固定できる。
- `reader_mode`（`full_rgb`/`target_only`）は上記のどちらとも別。実比較は`target_only`かつ同一window/frameで固定する。

**注意**: 旧`image_list + frame schema`と新`video_clip + window schema`を比較しただけで、「動画入力だけ」の精度差と主張しない。今回の純粋な比較対象はvideo_clip内の`none`対`previous_text`。将来、同じwindow schemaを両入力へ適用した統制比較を別specで扱う。

## 3. 動画入力・時刻・プロンプト/検証契約

### 3.1 VideoWindowからQwenへ

`sequential_loader`の選択済みframeだけをframe ordinal順に`type:"video"`として渡す。元mp4パスをQwenへ送って再サンプリングさせない。`do_sample_frames=False`を保つ。`4秒/8枚`なら目標`sample_fps=8/4=2`、元動画のfpsではない。新video pathは既存`ModelRequest`を破壊せず明示的な動画payload/metadataを持ち、frame数、形状、dtype、順序、ゼロ件、重複元ID、奇数frameにvalidationを設ける。既存image_list pathは変更しない。

**元動画時刻は二重に保持**: `chunks.jsonl`等の正本にvideo ordinal→元frame index→target timestamp→actual timestampを全採用frameについて記録し、Situation promptにも`chunk.frame_manifest`を人が読める形で渡す。Qwen公式の単純frame list＋`sample_fps`は**区間相対時間**（0から）を表すため、promptには`Original video window: [start,end) seconds`を明記し、絶対元時刻と相対動画時刻を混同させない。`raw_fps`を元fpsにするだけではlistの`frames_indices=0..N-1`が元IDになるわけではない。

Qwen processor側は`process_vision_info(... image_patch_size=16, return_video_kwargs=True, return_video_metadata=True)`および`video_metadata`/`do_resize=False`の公式経路を、installed版本の能力と照合する。frame list URI方式または直接memory tensorのうち、選択8枚・順序・timestampが保証できる最小実装を使う。video frameごとの時刻は2-frame temporal patchの平均と表示丸めを受けるので、**厳密な根拠時刻はWorkbenchの実timestampを正本とする**。可変FPS/VFRは実timestampを優先し、単一sample_fpsで実時刻を正確に表したと主張しない。元frame indicesを直接`video_metadata`へ入れ内部動画tokenを絶対時間化する「方法B」は今回**未実装の別比較候補**。入力のrendered prompt時刻/順序はモデルロードなしで検査可能な範囲をunit/syntheticで検証し、実Qwenは別Gate。

### 3.2 新Situation prompt（英語原文の契約）

標準入力: `{{question}}`、`{{chunk.start}}`/`{{chunk.end}}`、`{{chunk.frame_manifest}}`、動画payload。`none`版は前memoryの本文もplaceholderも含めない。`previous_text`版だけ`{{previous.evidence}}`を含め、正常commit済みtextを入れる。両版のその他の本文とgenerationを同じにし、選択肢・正解・未来windowを漏らさない。

新promptの核（実prompt assetに落とす際は以下の意味を保つ）:

> Interpret the provided sampled frames as one chronological video window. Describe directly visible people, objects, places, actions, and meaningful state changes across this window. Consider question-relevant evidence and important question-independent state changes. The video timeline may be relative to this window; the frame manifest specifies source-video frame IDs and actual absolute timestamps. Do not describe every input frame separately. Do not infer unseen frames, future events, answer choices, or unobserved causality. Do not answer the question. Cite only frame IDs and corresponding times found in the manifest; report ambiguous observations as uncertain. Return only one JSON object with window_summary, observations, unresolved.

`previous_text`版のみ次を追加:

> Previous validated text memory: {{previous.evidence}}. Use this as fallible context, not as a newly observed fact. Current visual evidence takes priority. Do not repeat past content as observations of this window.

新出力`schema_version="window_observation_v1"`の論理形:
- `window_summary`: nonempty string。観測不能/変化なしなら見えた範囲を明記し、架空の行動を作らない。
- `observations`: 0件以上の配列。**フレームではなく意味のある出来事/状態単位**。要素は`start_seconds,end_seconds,description,evidence_frame_indices,question_relevance,certainty`。時刻は元動画の絶対秒で、`evidence_frame_indices`は今回manifestに存在する元frame IDだけ。`question_relevance`は`high|medium|low|uncertain`、`certainty`は`fact|inference|uncertain`。実timestampと整合する範囲でしか時刻を報告しない。厳密な小数精度/見えていない中間動作を作らない。
- `unresolved`: string配列。画面から判別できなかった事項を残す。根拠のない推測を事実にしない。
- 新schemaの全観測は`memory.jsonl`に`schema_version`を付けて保存し、元frame manifestは件数に関係なく全採用frame分を別記録。旧`validate_observation_output`は旧mode専用に保持し、新validatorは`observations.length == frames.length`を要求しない。無関係な出来事なしの0件を許容し、その場合も状況要約を保存する。

`max_new_tokens`は現行全Agent共通256を盲目的に流用しない。stage別の明示generation上限と出力切断/JSON parse failureをrunに記録する。実Qwenでの適切な上限値や品質は未測定なので成功を仮定しない。

### 3.3 新Memory prompt（共通）

validated Situation JSON、`{{question}}`、`{{previous.evidence}}`、`{{current.observation}}`、`{{chunk.frame_manifest}}`のみを入力し、動画を再送しない。`none`/`previous_text`の両モードで同じMemory promptを用いる。

> Integrate the current validated observations with previous text memory in chronological order. Extract supported events and explain why each matters using zero or more of question_relevance, state_change, novelty, unresolved_uncertainty. Preserve important changes to people, objects, places and possessions even when question relevance is low. Keep all supported events in the ledger; retain a concise working narrative containing question evidence, important entity states, temporal order, contradiction and unresolved points. Separate facts, inferences and uncertainty, cite only current manifest frame IDs/times, do not fabricate future events, causality or resolved unknowns, and never silently overwrite contradictory memory. Do not answer the question. Return JSON only with events, narrative, unresolved.

新`memory_aggregation_v1`の論理出力: `events`は旧6フィールドに`importance_reasons`(許可enumの配列、空可)と`importance_explanation`(短い理由、該当なしならその旨)を追加。`narrative`はnonemptyのbounded text。`unresolved`はstring配列。新`events=[]`を許容し、根拠のないeventを作らない。全eventを追記台帳に保存し、次windowへは最新`narrative`だけを渡す。旧6キーの読取・旧`events+narrative`のvalidatorは旧runで維持。新schemaのevent参照・時刻・ID一意性、memory版と証拠整合を検証する。memory圧縮の現行切詰め処理を「重要情報を正しく保持できる」とは主張しない。

### 3.4 新Answer prompt（EOFのみ）

`{{question}}`＋`{{choices}}`、validated evidence (latest narrative/event ledger/source frame manifest/version)を入力。Situation/Memoryへ選択肢を漏らさない。

> Answer only after end-of-video has been reached. Compare the choices using validated evidence, not imagined content. Select the supported choice and cite only existing event IDs, frame IDs and timestamps. Report uncertainty without inventing a reference. Return only JSON containing answer, evidence_event_ids, evidence_frame_indices, evidence_timestamps_seconds, narrative_version.

新video modeでも現行の**5キー出力・根拠ID/時刻/version検証を維持**。既存`answer`は選択番号と選択肢文。将来のDecision Agent/`CONTINUE/ANSWER`は別契約とする。動画全体で参照eventが0件の場合は`insufficient_evidence`をrunに記録し、回答選択とAnswer Agent呼出しを行わず終了する。

### 3.5 Prompt asset・履歴と対応関係

既存`prompts/en/chunk_understanding.txt`、`evidence_aggregation.txt`、`final_answer.txt`は旧baseline/旧runのため無断で上書きしない。新`video_clip`にはmode別Situation 2種（例`chunk_understanding_video_en`、`chunk_understanding_video_with_memory_en`）と共通Memory/Answerのversioned prompt IDを導入し、入力変数allowlist・output schema・validator・model requestを一対一対応させる。旧未指定runは旧prompt/旧schemaで復元。

保存prompt library UIはユーザー要求として有効だが、本件の先行実装には同梱せず、別spec/後続microで扱う。新promptのsource ID/hash/immutable versionとrun snapshotは今回保持し、過去runの`resolved_prompt`本文/hashは変更しない。将来のlibraryではbuiltinの表示タイトル「最初のプロンプト」/説明「実装時に作成したプロンプトです」、作成/編集/削除(archive)/選択/再起動後復元/日本語表示用の拡張を検討する。

## 4. 重要イベントをテキストとして残す（B方針）

`importance_reasons`は`question_relevance`/`state_change`/`novelty`/`unresolved_uncertainty`の複数選択。質問に無関係でも人物/物体/場所の大きな状態変化を重要候補として残し、`importance_explanation`に理由を書く。モデルの重要度判断は仮説であり、正解ラベル・未来フレームで後付けしない。

入力画像8枚に対してeventが1件でも0件でもよい。入力frame一覧はすべて`chunks.jsonl`へ保持、観測/イベント/`narrative_version`をschema-versioned `memory.jsonl`へappend-only保存。`narrative`に採用した情報と前後の矛盾、解消していないことを残す。認識事実と推論/不確実を区別し、認識不能なら推測で埋めない。旧event 6キー形式と新video event形式はrun/schemaで判別し、過去recordに架空の重要度を追加しない。新eventの根拠frame IDは当該windowのmanifestだけから参照可能。

## 5. 機械用・人間用の二つの閲覧形式

正本は既存`chunks.jsonl`（全選択frame/target/actual時刻）、`memory.jsonl`（新旧schemaの観測・event・各記憶版）、`memory.json`（最新状態）、`stages.jsonl`（raw/validated/elapsed/input-summary）およびresolved settings/prompt本文・hash。`visual_input_mode`、`observation_context_mode`、input memory version、video target sample fps、stage別モデル/生成設定（対応する段階で実装された範囲）をrunごとに明示する。

人間用は**同じ正本から決定的に生成**するread-only timeline。window summary、採用画像と元時刻、意味のある観測と根拠frame、重要eventの理由、現在narrativeと版差分、unresolvedを表示。未記録の旧runは「未記録」と表示し、架空の値を補完しない。prompt全文・raw JSONは詳細で開く。run閲覧GETやpromptの確認はrun/turn POSTを起こさず、履歴再表示でmodelを呼ばない。過去runのimmutable prompt snapshotを変更しない。保存用human Markdownを出す場合もJSONLから再生成可能な派生物にする。

## 6. 4秒・8枚の固定設定の可視化

`target_only`、`window_seconds:4`、`frames_per_window:8`の短いFake/合成動画で、元動画上の時刻・目標時刻・元frame index・video ordinalの対応、Situationのwindow-level output、event IDへの逆引きと新旧run UIを確認する。空観測/同じ元frame採用/実時刻の小さなずれも対象。元fpsは参照値であり、目標`sample_fps=2`と混同しない。既存の標準recipeを無断変更しない。推論前の任意seekプレビューと本online pipelineは別scope。

## 7. 対象外と追加実験の境界

初回の研究軸に含めない: 動的な次window秒数/枚数、実早押し停止/EOF前回答、Qwen native絶対時間metadata方法B、途中で戻って未読未来をseekするonline混入、独立Event Agentの追加モデル呼出し、重要度の精度向上を実証済みとする主張、全件/長尺実Qwen評価、モデル自動取得、sequential_loaderの無承認内部変更、他者GPU・既存runの削除。

**別spec/後続micro**: Agent別モデル選択、persistent prompt libraryのCRUD/日本語閲覧、初期推論画面再設計。新promptのID/hash・run snapshotとAgent別設定へ接続できる契約は本specで維持する。既存の個人DBと固定ポート8765の非回帰は今回の検証対象であり、標準化・移行は対象外。既存browser Step10 draftの初期タブ/応答性は別管理。

## 8. 実装対象と順序

0. 調査: Company main/spec、target Workbench main/現在local HEAD/status/worktrees/dirty、依存`sequential_loader`の公開API、インストール済みTransformers/Qwen utils対応、旧runとFake fixturesをread-only照合。デフォルトブランチの旧`feat/step-10-qwen-preflight`を起点にしない。
1. 契約とprompt: 二つの比較軸をresolved YAML/runtime/restore/UIで明示し、新Situation 2 prompt・共通Memory/Answer promptを別IDで登録。stageによるモデル/生成設定の実装範囲はGate確定分のみ。旧prompt/adapter/validatorをそのまま残す。
2. Video adapter: 選択済みframe列のみ`type:video`で送るQwen path、相対`sample_fps`、絶対時刻manifest、`do_sample_frames=False`。画像baselineと時刻traceのsynthetic/Fake test。video対応不可のmodelは起動前にエラー、黙ったimage fallback不可。
3. New schema: Situationはwindow-level、Memoryはevent/重要理由とnarrative/unresolved、Answerは既存5キー。旧schemaと保存runのread/restore互換、新schema versionとvalidation-failure記録。model output切断/parse failureを隠さない。
4. 二形式表示: JSONL source frame/event/timeへ逆引き可能なhuman timelineとAgent stage results。旧runは読取だけ、明示turn以外では推論しない。
5. 4秒8枚の短いFake/合成video、CLI/API/UI/restart/cancel/browser、前面serve/`Ctrl+C`、同一固定`8765`と永続DBの回帰。実Qwen/GPUや動画全件decodeは別Gate。

実装microの境界とGit操作は現行`engineering-task`に従う。作業branch/commit/push/main mergeを曖昧な一括許可から推定しない。

## 9. 検証・受入条件

| 受入項目 | Fake/短い合成videoで検証可能な結果 |
| --- | --- |
| 動画入力 | Qwen pathに動画1本として選択frame列が渡り、Qwen側で再sampleしない。画像旧modeに退行なし |
| 時刻 | target/actual/source IDとvideo ordinalの対応が一致。relative 2fps/絶対秒の区別がpromptと記録から分かる |
| 状況理解 | 新`window_observation_v1`では1frame1件強制なし。0件と複数event、unresolved、未知frame ID/矛盾時刻/invalid JSONを検証 |
| 記憶 | 質問関連性＋重要状態変化の理由、全eventsと全記憶版追記。旧6キーrecordと既存run復元可能 |
| 2 context mode | video_clipで`none`は過去text非混入、`previous_text`は前の正常版のみ。frame/model/generation/Memory/Answer promptを固定 |
| 回答 | EOF後の5キーとevent/frame/time/version参照一致。推測による架空IDなし |
| trace/UI | 1次JSONLとread-only human表示が同一ID/時刻。閲覧で追加run/turn/model callなし |
| 安全・境界 | fake/unit/短合成テスト、既存CLI/API/ブラウザ・cancel/restart非回帰。serveは前面起動しCtrl+Cで停止する |

テスト成功は**実Qwenでの正答率・時刻グラウンディング・速度改善の証明ではない**。実Qwen/共有GPU/大規模dataset runは別途現在のユーザー実行許可が必要。

## 10. Ambiguity Gate（2026-09-30、実装前）

**確定済み（新たな確認不要）:** 3 promptの方針、Situationの窓単位の観測で全frame個別JSONを強制しないこと、Memoryの質問関連＋状態変化の蓄積、EOF Answer、新Qwen video inputには選択済みフレーム列＋区間相対fps＋元実timestamp manifestを使用、旧image/frame schemaの保持、前memory入力`none/previous_text`の比較。方法Bの直接absolute動画metadataは後続。

**解決済みblocking（2026-09-30、ユーザー承認）**
1. **今回の実装単位**: (A) 新video入力・3 prompt・2 context mode・根拠台帳/人間表示をひとまとまりとして先行し、個人prompt library/Agent別モデル/UI大改修は別spec/次microにするか、(B) ユーザーが既に希望したprompt CRUD/Agent別model/UIを同じ承認scopeに含めるか。後者は永続データ/モデルinstance/GPU境界を追加specで先に定義する必要がある。
2. **不足証拠の最終扱い**: 新`observations=[]`/`events=[]`を許すと、動画全体で参照イベントが0のrunがあり得る。既存final validatorは非空の引用を要求するため、(A) `insufficient_evidence`をrun上に記録し回答選択せず終了、(B) 参照なしを許す新final schemaを設けて回答未確定と表示、のいずれにするか。証拠を捏造した選択は認めない。
3. **新規runの初期表示**: 新UIの`video_clip`を既定で選択するか、旧`image_list`を既定に保って明示的に切り替えるか。**既存runの未指定設定は常に旧`image_list`**で復元する。

採用: **1A**（先行実装のみ）、**2A**（参照event 0件なら`insufficient_evidence`で回答せず終了）、**3 `video_clip`**（新規runのUI既定）。既存runの未指定設定は`image_list`で復元する。blockingな未決事項はない。

**non-blocking:** UI内の配置/文言・class配置・内部helper名は既存styleに合わせる。Qwen packageの現在版が動画を正しく処理できない場合はsilent fallbackでなく明示ブロック、依存変更を報告。stage別生成上限の初期値はテストで調整し、runtime/configとsnapshotへ明示して最終報告。元の動画より高精度の時間情報を創作しない。

**Gate提示するscopeの要約:** 「既存baselineを保持したうえで、新動画モードでは1区間1動画として入力、Situationはevent単位JSON、Memoryは根拠付きtext記憶、AnswerはEOF時、過去text ON/OFFを比較する。Qwen元時刻manifest・JSONL/人間用表示・4秒8枚を検証する。先行範囲/不足証拠/新run既定を決めた後にapprovedとする」。

## 11. Engineering Handoff（approved後のみ）

- SSOT: 本specの承認済み契約と第14節の実装結果。
- 基準: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main`（調査HEAD `a491757cabb8ed897a2d752da73325fe15f48884`。着手時にremote/local双方を再確認）。別作業treeのdirty/未追跡・旧run・個人SQLite/promptを壊さない。
- 対象: video path/manifest、new prompt IDsとwindow schema、`none`/`previous_text`、Memory event importance、human/machine trace、旧baseline互換。新規runのUI既定は`video_clip`、参照event 0件は`insufficient_evidence`。prompt CRUD/Agent別model/UI大改修は別scope。
- 許可なし: 実Qwen/GPU/大規模評価、モデル自動download、sequential_loaderの無関係な変更、他者のprocess停止、無承認のpush/PR/main merge。
- 個人用Workbench: 固定`8765`と同じ永続DB rootを使い、必要時のみ前面serve起動→同じ端末の`Ctrl+C`で終了。`nohup`/`&`/常駐化を導入しない。

## 12. 改訂前の初回scopeの実装・検証結果（2026-09-30）

- 対象repoのlocal `main` `a491757cabb8ed897a2d752da73325fe15f48884`を基点に、独立worktree `/tmp/longvideoqa-workbench-agent-memory-20260930`、branch `feat/workbench-agent-modes-readable-memory`で実装した。実装HEADは`a50570c5e6d12b69691fe124c2960fc9affde311`。
- `SituationAgent`、`MemoryAgent`、`AnswerAgent`と呼出し順をソース上で明示し、同一の`ModelAdapter`を共有する。`observation_context_mode`の`none` / `previous_text`を設定・CLI・server・UI・保存・旧run復元へ通した。
- `previous_text`は直前の正常確定済み`memory.json` narrativeだけをSituationへ渡す。初回、失敗、旧run、`full_rgb`、CLI、serverをFakeで回帰確認した。`none`では過去textもplaceholderも挿入しない。
- 重要イベントへversionedな`importance_reasons` / `importance_explanation`を追加し、旧6項目eventを読める互換性を維持した。同じ`memory.jsonl`と観測台帳からtimeline、根拠frameの実/目標時刻、memory版と差分をGET時に決定的生成する。独立した第二の正本は作成していない。
- Fake API受入で`target_only`、4秒、8枚についてframe ID `0..7`、目標時刻`0.0..3.5`秒、実時刻、画像枚数を確認した。明示next/final、cancel、restart、保存run、GET非推論も回帰した。
- 全回帰`168`件成功。Firefox UI回帰`9`件成功。`python -m compileall -q src tests`成功。top-level / `run` / `serve` / `qwen-preflight`のCLI help成功。差分検査`git diff --check main...HEAD`成功。
- 未検証は実Qwen/GPU、LongVideoBench実データ、長時間・精度比較。Node.jsが環境にないため`node --check`は実行できなかったが、追加UIはheadless Firefoxで実行確認した。
- 対象repoの元`main`と既存未追跡docs 3件は変更していない。push、PR、main統合、`sequential_loader`変更、常駐server起動は行っていない。

## 13. 参照

- MTG: `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-25-mtg.md`
- 概念整理: `.research/secretary/notes/brainstorm/2026-09-29-agent-orchestration.md`、`2026-09-30-evidence-adaptive-early-answer-videoqa.md`、`2026-09-30-workbench-inference-ui-prompt-library-and-qwen-video.md`
- baseline: `2026-09-25-workbench-target-stream-and-hierarchical-memory-spec.md`（frontmatterのimplementedと本文旧draft記述の不一致があるため、現在コードを優先して現物確認）、`2026-09-29-workbench-dataset-browser-ui-implementation-spec.md`

## 14. 承認後実装結果（2026-09-30）

- 対象: Workbenchの独立worktree `.worktrees/longvideoqa-workbench-video-clip`、branch `feat/workbench-video-clip-memory`。基点は先行実装済み `a50570c5e6d12b69691fe124c2960fc9affde311`。変更は未commitで、元`main`・既存未追跡docs・過去run・個人SQLiteは変更していない。
- micro 1（設定・prompt）: `visual_input_mode=image_list|video_clip`を設定、復元、API、UIへ追加。新規UIは`video_clip`を既定とし、未指定の旧runは`image_list`へ復元。新Situation 2種・Memory・Answerのversioned prompt ID/hashとstage別生成上限（Situation 1024、Memory 768、Answer 384）を保存。旧prompt assetは維持。
- micro 2（動画入力・時刻）: 選択済みRGB frame列だけをQwen processorへ1本の`type:video`として渡し、`do_sample_frames=False`、目標fps `frames/window_seconds`、相対ordinalを使用。元frame ID・target/actual秒をprompt manifestと`chunks.jsonl`へ保持し、絶対時刻の正本はactual秒とする。Qwen processorの空間resizeは直接メモリ入力の既定処理に委ね、元動画パスはモデルへ渡さない。
- micro 3（3 Agentと記録）: Situationは窓単位`window_observation_v1`で0件も許容、Memoryは根拠frame・重要理由付き`memory_aggregation_v1`、AnswerはEOF後の既存5キーを検証。validated観測・全event・全記憶版を`memory.jsonl`に追記、最新narrativeを`memory.json`に保存。raw/validated・生成上限到達・検証失敗を`stages.jsonl`/run statusに残す。全区間でevent 0件なら`insufficient_evidence`で回答を選ばず終了。
- micro 4（閲覧）: `chunks.jsonl`と`memory.jsonl`から区間summary、観測、採用frame/時刻、event理由、記憶版差分をread-onlyで表示。mode切替で対応するprompt ID/hashを表示し、履歴GETは推論を開始しない。
- micro 5（検証）: Workbench全181件成功（Firefox UI 10件を含む）、Python compile、`git diff --check`成功。短い合成動画の4秒8枚、FakeのON/OFF・0件・invalid JSON・旧baselineを確認。Workbench仮想環境の旧editable loaderには新APIがなかったため、既存の`docs/target-frame-stream` commit `76badb1c407a34de6f2dfa7e5d4040ef7c4b2ccc`から依存取得なしでローカルwheelを入れ直し、公開`target_frame_stream`と通常環境の合成動画テストを確認した。loaderソースは変更していない。
- 未検証: 実Qwen/GPU、LongVideoBench実データ、長尺動画、正答率・時刻グラウンディング・速度、stage別生成上限の実機適正。モデル自動download、push、PR、main統合、常駐server起動はしていない。
