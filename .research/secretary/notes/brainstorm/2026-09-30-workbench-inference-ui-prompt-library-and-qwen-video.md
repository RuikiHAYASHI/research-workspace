---
date: 2026-09-30
project: agentic-streaming-videoqa
source_todo: "2026-09-25 MTG: Agent責務/イベントJSON/複数frameのvideo入力/Workbench設定可視化"
topic: workbench-inference-ui-prompt-library-and-qwen-video
status: exploratory
tags: [brainstorm, workbench, agent, prompt-library, persistence, video-input, qwen3-vl]
---

# 推論画面再設計・Agent別モデル/プロンプト・永続保存・Qwen動画入力の壁打ち

## 出発点とAuthority（2026-09-30 04:29 JST）

ユーザー提示の実画面スクリーンショットは2026-09-29のrun URLを含むが、127.0.0.1の稼働サーバーやローカルDBの実体をChatGPTから直接操作・調査したものではない。画像上、左に専門語の共通profile/read modeと生JSON、中央右に巨大な各stage prompt、Agentの成果物と採用frameが下方に押し出されている。ユーザーは見やすい研究UI、Agent別のモデル選択、プロンプトを個別画面でCRUDして名前/説明/履歴を残すこと、初期タイトル「最初のプロンプト」/説明「実装時に作成したプロンプトです」、英語原本の将来日本語表示、favorite/folder等の再起動後保持、複数画像でなく**選択済みframe列をQwenのvideo入力**として処理、全frame一件JSON強制の廃止を明示希望。

Authority: 2026-09-25 MTGのAgent/オーケストレーション/動画入力比較、2026-09-30ユーザー要求、現在実装、現行draft `2026-09-30-workbench-agent-modes-and-readable-memory-spec.md`の順。現行draftを黙ってapprovedにしない。新たな研究要件は初回draftの前提（全採用frame別JSON義務、全stage単一model、旧画面方式）に影響するため研究specの再レビューが必要。過去text入力ON/OFFや早押し/動的sampling等は別の比較軸。

## GitHub read-onlyで確認した現状と未確認

Workbench repo `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` 調査HEAD `a491757cabb8ed897a2d752da73325fe15f48884`、default branchは旧 `feat/step-10-qwen-preflight`。local worktree/実run未確認。
- `web/index.html` は左側 `profile`、`reader-mode`、`resolved-profile` pre、右の `stage-cards` を持つ。 `web/app.js` は毎stage prompt全文をtextareaで描画し、runtime上書きするが再利用できるprompt libraryではない。
- `core/contracts.py` の `ExecutionSettings.model_adapter/model_id` はrun共通1組、`StageSettings` はstage/promptのみ。`registry` はadapter名でモデルを引く。独立agentモデル選択にはmodel ID/adapter/generationのper-stage resolved contract、GPU footprint、snapshot、旧run互換が必要。
- `model/qwen3vl.py` は `ModelRequest.images` を各 `type:image`として渡す。Qwen native video pathなし。`prompts/en/chunk_understanding.txt` と `agent/observations.py` は入力frame数と同じ `observations`を必須とする。`generation.max_new_tokens`は共通profileで256。スクリーンショットの途中切れと生成長の関係は可能性であり現物run artifact/finish reason未確認。
- `interfaces/library.py` は `default_library_db_path`を `$XDG_DATA_HOME/longvideoqa-workbench/library.sqlite3`、未設定なら `~/.local/share/longvideoqa-workbench/library.sqlite3` とし、favorite/folders/aliasをSQLiteへcommit。CLI `serve --library-db` で上書き可能。再起動時DB path/rootが異なると初期状態に見える可能性。UIデータの実損失か保存先切替かはlive DBと起動引数未確認。旧READMEの `/tmp/.../library.sqlite3` は確認用であり個人永続運用の標準にしない。
- `records/run.py` はrun別resolved prompt本文/hashをsnapshot保存し、`memory.jsonl`を一次記録にする。ユーザーが保存したprompt編集が過去runを変更してはならない。
- `interfaces/cli.py` はserverを前面起動/KeyboardInterruptとserver_close。Company READMEの個人利用・必要時起動・Ctrl+C終了規則を維持。

## 新UI情報設計（候補）

1. 選択済dataset/video/QAは上部で簡潔に確認し、データセット変更導線と詳細ポップアップを残す。生JSONを主画面に常時出さず「詳細設定/開発者情報」に隠す。
2. 一次UIは「観測の設定: 対象区間の秒数・枚数・入力形式」「Agentカード3枚: 役割・モデル・モード・選択中promptのタイトル/版・確認ボタン・小さな説明」「実行ボタン」。専門語には日本語ラベルと説明（読取方式: すべてRGB変換 vs 選択frameのみRGB変換、ただし前方decodeは継続）。
3. 各Agentの「プロンプトを確認」→別画面/パネルに一覧、閲覧、編集、名前と説明を付けた新規作成、削除（過去runから削除不可）、版履歴、選択。ユーザー操作だけが変更保存し、キャンセル・一覧閲覧でrun/turn POSTしない。選択中のpromptをrun開始時immutable snapshot化。初期promptのタイトルを**「最初のプロンプト」**、説明を**「実装時に作成したプロンプトです」**とする。内部不変ID/role/localeをタイトルから分離。
4. 翻訳は将来のread-only日本語閲覧で、推論に渡す英語sourceは勝手に翻訳で置換しない。訳文はsource prompt hashと紐づけたcache/任意表示。
5. 実行後は採用frame＋時刻、各Agentの簡単なoutput/実時間、重要eventとmemory timeline、人間用/機械用切替を第一面に。生出力・full promptは展開式。

## 永続保存の候補

個人用data rootをserver起動の作業ディレクトリやrun output、/tmp、Git worktreeから切り離す。既存SQLiteのfavorite/folder/aliasを同一安定DB pathで再利用し、新prompt libraryのmetadata（prompt_id, role, immutable version, title, description, locale, origin, archived, content hash, created/updated）を保管。prompt本文は `$XDG_DATA_HOME/longvideoqa-workbench/prompts/<agent>/<prompt-id>/v0001.txt` のような専用user-data領域か、既存DBに一貫して格納する方針をspecで決める。builtin `repo/prompts/en/*.txt`は不変defaultとして参照し、user copy/versionで編集する。deleteは現在の一覧からarchive/非表示とし、過去run snapshotを破壊しない。原子的書込/DB transaction、異常中止から復旧。testは同じDB/user-data rootでCtrl+C→再起動と、別worktree/CD/出力root、old run復元を含む。cache/outputとuser stateは分離し、ユーザー許可なくDB削除/移行/cleanをしない。

## モデル別選択

per-Agent `model_adapter/model_id/generation` をUIに出す。ただし同一Qwenを選んだ場合は1つのlazy instanceを共有し、Agentごとに別重みを3回常駐させない。複数モデルの選択可否と実load可否を分け、モデルの事前install/cache/使用可能GPUを確認。モデル変更でmemory/input schemaが不一致なら起動前validation failureにする。GPU使用量はモデルが異なると増えうるため、複数checkpointを同時ロードする方式は未承認。モデルを未インストールなら勝手にdownloadしない。run snapshotにstage別modelとgeneration/prompt版を記録して再現性を保つ。

## Qwen3-VL native videoの公式根拠と設計

公式: https://github.com/QwenLM/Qwen3-VL/blob/main/README.md （Process Videos節）。`type:"video"` にframe file pathsの列と `sample_fps`を指定可能、原動画file/urlも可能。前処理例は `process_vision_info(messages, image_patch_size=16, return_video_kwargs=True, return_video_metadata=True)`、戻りvideo tensorとvideo metadataを分けて `processor(... videos=..., video_metadata=..., do_resize=False, **video_kwargs)`。公式utils: https://github.com/QwenLM/Qwen3-VL/blob/main/qwen-vl-utils/README.md 。

研究上は`sequential_loader`が採用したframeのみを一つのvideo inputとしてQwenへ渡す。元動画pathをQwenへ渡して別samplingさせない。現行`ModelRequest.images`に加え、別契約として`video_frames`とtarget/actual timestamp、frame index、start/endを保持し、`image_list` baselineと`video_clip`を独立比較軸にする。動画列のサンプル間隔が不均一の場合、単一sample_fpsで実際時刻を再現できるとは限らないため、時刻metadataを保持し、installed qwen-vl-utils/transformersでどの経路がそれを忠実に扱えるか、小synthetic testと生成入力traceで確かめる。重複採用frameもテスト。二重resizeやsecret/path保存に注意。実Qwen/GPU比較は別承認。

**Qwen video入力は各frameを長文で個別説明する義務ではない**。質問に関係する窓全体の時系列event/state change/uncertaintyを`window_summary/events/evidence_frame_indices/time`で出力する新契約へ移す候補。入力全frame manifestはloader/recordに保存しつつ、モデルの出力件数がframe数に等しいことは要求しない。旧`validate_observation_output`・`prompts/en/chunk_understanding.txt`は現行baselineと保持し、新video mode用別prompt/schema/validatorを設ける。256 tokenで8件の全frame JSONを要求すると切れる可能性があるが、スクショだけでfinish reason/原因は断定しない。prompt形式変更・video入力変更・過去textモードを同時に比較しない。

## 段階的な実装・spec再レビュー候補

- 入口Gate: 現行9/30 specがdraftのまま、Agentの入力形式とper-agent model、prompt library/persistent user dataなど新要求と不一致。approvedへ自動昇格しない。現在local branch/dirty/実DB path/実run artifactとGitHub mainを照合したうえで、research-specでscopeを分割して更新。
- A **個人永続データとprompt library**: DB path確認→お気に入り等のrestart回帰→built-in登録/一覧/選択/コピー/編集/版/論理削除/旧run不変。主画面はまずcollapsed layoutにする。
- B **Agent単位の構成/UI**: stage別model/配置・prompt/モード・操作導線、Qwen共有と複数モデルのload境界、resolved snapshot、read-only旧run。3役割はSituation/Memory/Answerの暫定baseline、将来DecisionのCONTINUE/ANSWERは別実験。
- C **Qwen native videoとwindow-level observation**: image baselineを保ち、video inputのmetadata/処理/独立validatorとprompt、4秒8枚fake+short synthetic。実Qwenは明示承認時のみ。
- D **event/memory human-machine views**: 根拠frame/time、question relevance＋entity state change、versioned JSONL正本とそこから生成するhuman view、旧record互換。
- E 後続研究: 観測に過去text ON/OFFの比較、question adaptive window/frame、早押しstop gate、multi-agent異種モデル精度実験。比較軸の固定が条件。
- 別scopeのブラウザ旧Step10（初期推論タブ/描画速度）と重複/衝突をread-only監査。単に同時作業に詰め込まない。
- short unit/Fake/synthetic smokeはscope承認後。大量動画decode、実Qwen/GPU/モデルDL、無断push、phase→mainは別Gate。前面serve→Ctrl+C終了/通常シェル入力復帰を維持。

## 次に判断したいこと

(1) Aの永続prompt管理を最初にするか、Cのモデルvideo入力を優先するか。個人保存rootの実在/現DBのデータをまずread-only検査。(2) モデル別選択はUIのみ先行して同一Qwenの共有を標準にするか、異種checkpointを今から実動作まで含めるか。(3) video modeの新summary schemaとevent schemaの分担、元frameの証拠位置精度をどう評価するか。初回draftを誤ってapprovedにせず、新たなユーザー判断とspec Gateで具体化する。

## 2026-09-30 04:38 JST 追記：FPS算出と固定URL運用（ユーザー補足）

ユーザー補足: データセットには元動画FPSが公開されているため、区間長と採用枚数からサンプリング後のFPSを計算可能。お気に入りが消えたと思った原因は、ユーザーが違うポート番号のブラウザを開いていたこと。個人利用のWorkbenchを必要時に起動するたび**同じポート・同じURL**で開きたい（常駐化ではない）。

### 動画入力の時刻とFPS

等間隔に`N`枚を`T`秒幅で選んだ場合、目標サンプルFPSは`N/T`（4秒8枚なら2fps）。元動画FPSは元frame indexから実時刻を計算/照合する助けになる。ただし現`target_frame_stream`は「目標時刻以降の最初の実frame」を選ぶため、取得時刻のずれ、元のVFR、不整区間、重複画像があり得る。元fpsや一つの`sample_fps`だけを真の実timestampと混同しない。採用frameごとのtarget/actual timestampを保持。Qwen公式の`type:video`＋frame列＋`sample_fps`、`process_vision_info(... return_video_metadata=True)`に基づき、実環境のprocessorが時刻をどう使うかを低負荷テストで確認。オンラインinputには先読み/元動画パス丸渡しをしない。

### 同じURLと永続DB

現在コード`interfaces/cli.py`は`serve --port`の既定値が`8765`。以前のFake/LVB確認READMEは`18767`、`18768`と確認専用`/tmp/.../library.sqlite3`を利用するため、普段の保存先と混同しやすい。Webサーバーのportは受付先であってSQLite保存先ではない。別portでも`--library-db`が同じならlibraryは共有可能、同じportでも保存先/`XDG_DATA_HOME`が変われば別libraryが見える。今回のユーザー認識を尊重しつつ、技術的には複数instanceのroot/DB分離も考慮して原因を断定しない。過去favoriteデータがあるDBを移動・上書き・初期化せず、現在利用中の起動引数、`--library-db`、`XDG_DATA_HOME`、DBの既存実体をまずread-only照合する。

本人用の標準起動は同一固定ポート（現行実画面の`8765`を候補）と同一永続library path、同じrun-output root、同じ最新版worktreeの`PYTHONPATH`を明示。`--port 8765`を毎回固定し、SSH tunnel/VS Code forwarded local portも同じ番号（`localhost:8765`）に固定、URLをbookmark化する。port使用中は**黙って別の空portへ変更しない**、利用中processを確認してユーザーへ伝える。他者のport/processは殺さない。SSH tunnelがremoteでなく手元に立つ場合は手元8765→server8765のマッピングを指定する。server側から手元ブラウザを勝手に開くのは別操作。閲覧によって実runを開始しない。

既定通り**サーバーは前面起動、Ctrl+Cで終了、非常駐**。`nohup`、`&`、systemd、自動kill、ポート競合時の強制終了は採用しない。異なるworktree/開発branchからの起動や、試験用`/tmp`のDBを普段用へ流用しないこと。固定ポート/保存先に関するCodexへの引継ぎは明示し、別scopeの研究specを勝手に`approved`へ変更しない。

## 2026-09-30 04:47 JST 追記：Qwenに入れる元時刻とvideo_metadataの違い

ユーザーは「Qwenへフレーム列を渡すのか、元動画の時刻情報を入力へどう含めるか」を具体的に確認した。Qwen公式と`qwen-vl-utils`およびtransformersの現在実装で次を区別した。

- 単純なvideo入力: `{"type":"video","video":[選択フレーム画像URI...],"sample_fps":2.0}`。Qwen公式はframe URI列を許す。`process_vision_info(... image_patch_size=16, return_video_kwargs=True, return_video_metadata=True)`でvideoとmetadataを得てprocessorへ渡す。Workbenchに到着済み選択8枚のみを使い、元mp4 pathをQwenへ渡して再samplingさせない。
- 重要な落とし穴: `qwen_vl_utils/vision_process.py`のlist pathは`frames_indices=range(len(video))`を持つ**fake metadata**を作り、`sample_fps`からその相対時刻を算出する。`raw_fps`だけを元FPSにしてもframe indexが0..7のままなので、20秒地点を正しく表現できない。
- Qwen3-VLの`replace_video_token`は`metadata.frames_indices / metadata.fps`の時間を計算し、2フレームずつのtemporal patchで初終フレーム時刻を平均して`<x.x seconds>`の動画時刻token/textへ変換する。つまりvideoのfps情報は視覚入力の一部として時刻表示に反映されるが、フレームごとの高精度時刻がそのまま個別video tokenで表示されるわけではない。
- 基本運用は、video dataは8枚＋`sample_fps=8/4=2`の**区間相対時間**、Agentへのtextは`Original video window: [20,24) seconds; frames: local 0->orig frame500@20.00s, ...`を渡す。時間が不均一でも実timestampは別のmachine-readable frame manifestを保持し、読める形でモデルのpromptにも渡す。回答はイベントの元frame IDを参照し、厳密な時刻は保存済みmanifestから引く。Qwenの秒表示とframe manifestが矛盾しないよう区間相対と絶対をラベルで区別。
- さらに正確に元の時間を内部video timestampへ載せる**比較候補**: 採用frameを先に用意して`processor(..., videos=[frames], video_metadata=[VideoMetadata(total_num_frames=source_total_frames, fps=source_fps, frames_indices=original_frame_indices)], do_sample_frames=False, ...)`と明示する。CFRなら`orig_idx/source_fps`が元時刻に対応。VFR/PTSやフレームidx重複にはこれだけでは厳密でないため実timestampを正本にし、場合によりmillisecond timebase相当のvirtual indexで表す方法を検討するが未検証。native modeのvideo metadata書換は installed transformers版/Fake・短いsyntheticとrendered token timestampで必須検証し、安易に直接書き換えて本番runしない。
- `do_sample_frames=False`が重要。Qwen側で追加サンプリングさせない。`VideoMetadata.frames_indices`はQwenのtimestamp placeholderを作るための座標値であり、選択済み8枚を元動画中のframe IDと1対1対応させるのはWorkbenchの責務。
- model内部の2-frame temporal patch平均と表示丸め(約0.1秒)、奇数frameのpadding、時刻/フレーム対応、GPU用video tensorと画素budget等をテスト観点として残す。純粋なfps=2だけでは元20秒absolute offsetを表せないことを明記。現在の`Qwen3VLAdapter`は画像typeのみ、提案はまだ未実装。

公式: https://github.com/QwenLM/Qwen3-VL/blob/main/README.md#process-videos ; https://github.com/QwenLM/Qwen3-VL/blob/main/qwen-vl-utils/src/qwen_vl_utils/vision_process.py ; https://github.com/huggingface/transformers/blob/main/src/transformers/models/qwen3_vl/processing_qwen3_vl.py ; https://github.com/huggingface/transformers/blob/main/src/transformers/video_utils.py ; https://github.com/huggingface/transformers/blob/main/src/transformers/video_processing_utils.py 。

今は探索記録のみ。実装契約は現行draft specを再レビューし、image baselineとnative video modeは別run/別比較軸。GPU/Qwen runは別許可。

## 2026-09-30 04:52 JST 追記：実装前レビュー用の3 Agentプロンプト案

ユーザーは前節の選択frame列＋動画入力と元時刻manifest分離の構成を方向性として了承し、**実装前に現在のプロンプトを見直したい**と希望。現行コードに保存済みの実promptと、まだ提案段階の文案は別物として示す。今回もexploratoryであり、9/30 agent modes specはdraftのまま。実装前のresearch-spec改訂・承認が必要。

### 現行promptと仕様のギャップ

- `prompts/en/chunk_understanding.txt`: `Question` / `Window` / `Frames` / `Frame manifest`。全入力画像からちょうど同数の`observations`各6フィールド必須。現行modelは`type:image`連列である。
- `prompts/en/evidence_aggregation.txt`: 前narrative/current観測から`events`6キー＋`narrative`を返す。質問関連＋人物/物体/場所の状態変化を保持する明示基準/importance reasonsは未実装。
- `prompts/en/final_answer.txt`: EOF後に選択肢を入力、`answer,evidence_event_ids,evidence_frame_indices,evidence_timestamps_seconds,narrative_version`の厳密JSONを返す。Decisionの早押し判断はまだ無い。
- `configs/common/longvideobench-qwen3vl.yaml` は全stage共通`max_new_tokens:256`。`frame`ごとの長文JSONだと切断リスクがあるが、特定runの終了理由未確認。
- 先行のdraft specは旧全frame観測を前提。ユーザーの新video入力/窓単位説明/agent別model/prompt libraryと一致しないため、承認前の改訂が必要。

### 候補A：Situation（動画区間全体、image baselineと区別）

共通入力: 現windowの選択フレームを`type:video`（Qwen動画経路）として渡し、`{{question}}`, `{{chunk.start}}`, `{{chunk.end}}`, `{{chunk.frame_manifest}}`（video ordinal→元frame ID・実timestamp・目標timestamp）をテキストで渡す。`none`と`previous_text`の2版を作り、後者のみ正常commit済み`{{previous.evidence}}`を加える。

候補の英語指示（まだprompt assetではない）:

> Interpret the provided sampled frames as one chronological video window. Describe directly observable actions, objects, people, places and meaningful state changes across the window, especially question-relevant evidence, without ignoring important question-independent changes. The video timeline may be relative to this window; the frame manifest gives absolute source-video times. Never infer unobserved frames, future events, causality or answer choices. Treat previous memory, if supplied, only as fallible context; current visual evidence takes priority. Do not answer the question. Return a single JSON object with window_summary, observations, unresolved. Each observation describes an event or meaningful state (not each input frame) and contains start_seconds, end_seconds, description, evidence_frame_indices, question_relevance, certainty. Reference only source-frame IDs in the manifest; use the corresponding actual times and avoid unwarranted subframe precision. observations may be empty when nothing relevant is visible. unresolved is a list of concise uncertainties. Output JSON only.

`previous_text`版には`Previous validated text memory: {{previous.evidence}}`と、先行メモリを現在の映像で確認できた事実扱いしない命令を追加。二版のその他の指示とgenerationを同じにする。「全入力frameに1件ずつ必須」は削除するが、manifestは全採用frameをWorkbenchの正本として保持する。frame-level旧modeはbaseline専用として不変保存。

### 候補B：Memory（重要イベントと記憶更新）

入力: question、validated current Situation JSON、前のbounded narrative、現在window manifest。画像再入力なし。新指示案:

> Integrate current visual observations with the previous validated text memory in chronological order. Extract all supported events; never discard a record just because it is not retained in working memory. For every event, explain its importance using zero or more of question_relevance, state_change, novelty and unresolved_uncertainty. Preserve important changes to people, objects and places even when the question relevance is low. Separate direct facts from inferences and uncertainties, cite only frame IDs/times present in the current manifest, and do not fabricate causality, future outcomes or resolved unknowns. Update a concise working narrative that retains question evidence, important entity states, temporal order, contradictions and unresolved points. If evidence contradicts previous memory, state what changed and the supporting source; do not silently overwrite. Return only one JSON object with events, narrative, unresolved. Every event retains the existing six fields plus versioned optional importance_reasons and importance_explanation.

Importance理由の例: `["state_change"]`、`["question_relevance","novelty"]`。全eventはappend-only ledger、最新のbounded narrativeのみ次windowへ。旧event reader互換とversioningが前提。Memoryの1回呼出しbaselineと、event extraction/更新の2段階呼出しは後続比較軸。

### 候補C：Answer（今はEOFのみ）

入力: question+choices、最新working narrativeとevent ledger/frame manifestから検証済み根拠、現在のmemory version。新指示案:

> Answer only after end-of-video has been reached. Use the supplied validated evidence, not imagined video content. Select the supported choice and cite only existing event IDs, frame IDs and timestamps. Distinguish direct support from uncertainty and contradiction; do not fabricate references. Return only one JSON object with answer, evidence_event_ids, evidence_frame_indices, evidence_timestamps_seconds, narrative_version, preserving the current validator contract.

現行`answer`は番号＋選択肢文、選択肢を受け取るのはこのstageのみ。将来`DecisionAgent`で`CONTINUE/ANSWER`を扱う場合は回答権限と停止基準を別prompt/schemaとして研究する。今回のSituation/Memoryへ選択肢/GTを渡さない。

### 先に決めるprompt reviewの論点

1. Situationは「質問を知った観測」でよいか、それとも質問を隠す`question_blind`比較も将来用に確保するか。今回は質問を渡すbaselineで、次windowの適応は別実験。
2. Situationで`observations`をイベント単位にし、0件許す。各eventのframe/time参照を必須にする場合、Qwenの2-frame temporal patchでは正確な1枚特定が常に可能ではない。明確な根拠がない時刻は捏造せずuncertainにし、検証済み参照のみ使う。
3. Memoryのテキスト形式（時系列物語＋状態/未解決、単一`narrative`か複数fieldか）・token budget。schemaとpromptを同期。
4. `max_new_tokens=256`のstage共通上限は見直し。Agent別の生成上限と出力切断の検出・失敗時のrecord保存を設計し、実Qwen値は未測定。
5. これらは比較可能性のため`image_list` vs `video_clip`、`none` vs `previous_text`、Agent別modelを別run設定とし、複数の差を一度に評価しない。
6. Prompt libraryには各Agent初期builtinの表示名「最初のプロンプト」、説明「実装時に作成したプロンプトです」。原文英語・将来の日本語訳は閲覧用で分け、本文/ID/hash/versionをrun snapshotに保存。編集で旧runは変わらない。

今回のユーザー発話は「文案を見直してから実装」であり、実装・実Qwen/GPU実験・draft specのapproveは未実施。
