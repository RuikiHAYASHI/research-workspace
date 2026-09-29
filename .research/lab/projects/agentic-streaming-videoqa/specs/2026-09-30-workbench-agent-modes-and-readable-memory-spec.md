---
date: 2026-09-30
project: agentic-streaming-videoqa
status: draft
topic: workbench-agent-modes-and-readable-memory
source: 2026-09-25 MTG; 2026-09-29 and 2026-09-30 agent brainstorm; 2026-09-30 user request
last_updated: 2026-09-30
target_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
related_brainstorm:
  - 2026-09-29-agent-orchestration.md
  - 2026-09-30-evidence-adaptive-early-answer-videoqa.md
---

# Workbench: 比較可能なAgentモード・重要イベントのテキスト記憶・二形式の証跡（実装spec）

## 0. 状態・Authority・Gate

本書はユーザーが希望した「まずモードを作って実装したい」を、実装対象が特定できる初回scopeへ絞った**draft（レビュー待ち）**。本書の作成自体をコード実装/commit/branch作成/GPU実行の承認としない。ユーザーが本書の初回scopeを明示承認して`approved`になってから、現在の`engineering-task`と本書に従いCodexで実装する。Companyへのspec保存はGitHub上の共有文脈の保存であり、146 serverのローカル作業木へ自動同期された意味ではない。

Authority: 2026-09-25 MTGの3役割・イベントJSON・操作可能なUI、2026-09-30のユーザー判断「質問関連情報＋人物/物体/場所の重要状態変化も残す」（B）、同日希望「過去のテキストを状況理解Agentに入力する／しないをモード化」「JSONL機械用＋人間用」の順。早押し、動的window/枚数は**探索中の別比較軸**。旧browser spec`2026-09-29-workbench-dataset-browser-ui-implementation-spec.md`のStep 10 draft（入口/描画速度）は別scopeであり、この新specのStep番号やAuthorityで上書きしない。

## 1. 現行実装の確認（GitHub、2026-09-30）

- 対象コード`RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main`調査時HEAD: `a491757cabb8ed897a2d752da73325fe15f48884`。GitHubの**default branchは旧`feat/step-10-qwen-preflight`**である。Codexはdefaultを現在研究コードと誤認しない。実装前にGitHub main、local main/worktrees/HEAD/dirty、依存loaderをread-only再監査する。
- `agent/pipeline.py`は状況理解→根拠集約をwindowごとに行い、EOF後の最終回答へ渡す。`run_window_turn`が既に`previous_evidence`を持つ一方、`run_chunk_understanding`はそれを入力しない。`core/validation.py`は観測promptへの`previous.evidence`を許可しない。単純なprompt編集だけでは新モードを実装できない。
- `config/loader.py`はYAML recipe/profileとprompt IDをallowlist解決し、`ExecutionSettings`と`RunRecord`が設定/実行別promptを保存。`settings_from_resolved_mapping`は旧runからrestart用に復元する。`interfaces/server.py`と`agent/pipeline.py`の両経路へ同じモードを通す必要がある。
- `records/run.py`は`memory.jsonl`に観測・イベント・`narrative_version`を追記、`memory.json`に最新snapshot、`stages.jsonl`にresolved prompt/raw/validated/elapsedを記録。既存`events.py`は6必須キーのexact検証、`final_output.py`は最終参照を検証する。旧記録を壊さない。
- `web/app.js`は既に`reader_mode`、`window_seconds`、`frames_per_window`、promptの編集と採用画像/実時刻/目標時刻の表示を持つ。新しい観測contextモードは既存`reader_mode`とは独立。
- loaderの対象frame専用公開APIは`tamaki-lab/sequential_loader@docs/target-frame-stream`（`76badb1c407a34de6f2dfa7e5d4040ef7c4b2ccc`）で確認済み。採用対象以外のRGB変換は回避するが、先頭からの圧縮decodeは続ける。default`master`や旧`feat/longvideobench-source-adapter`を新APIありと誤認しない。

## 2. この初回specの目的と比較軸

**同一動画・質問・window・採用frame・モデル・生成設定・Memory更新処理で、「Situation Agentが前windowまでのテキスト記憶を受け取るか否か」だけを切り替え、両方の段階出力・根拠・コストを比較できるようにする。**

最低限の3役割:
1. `SituationAgent`：現在windowの画像と質問から、全採用frameの時刻付き観測を生成。任意の前テキスト入力だけを初回のモード差とする。選択肢/正解/未来frameは渡さない。memory参照時も過去記憶を「参考の仮説」とし、現在画像の事実と混同しない。
2. `MemoryAgent`：validated観測と直前のworking text memoryからイベントと新版の物語記憶を出力。質問関連に加え、人物・物体・場所・所持品などの状態変化を重視する。観測/全イベント/全memory版は追記保持する。旧`evidence_aggregation`と既存のbudget/chaptersを活用。
3. `AnswerAgent`：**現段階はEOF後だけ**呼び、最終記憶・選択肢・根拠event/frame/timeから回答。将来の`CONTINUE/ANSWER`型Decision Agentへの変換は本specではしない。

`VideoQAOrchestrator`は4番目のモデルAgentではない。既存pipelineの実行順・validation・記録/中止/reader closeを明示するPython進行管理役。3 Agentは共通の`ModelAdapter`（単一Qwenインスタンス）を受け取り、Agentごとに重みを多重ロードしない。既存`StageName`、CLI、API、Fake modelと既存helperを尊重し、単に名前を合わせるための全面rewriteをしない。

## 3. モードの厳密な契約

新しい設定キーを`observation_context_mode`とする。`reader_mode`（`full_rgb`/`target_only`）は**別軸**。まず二つのみをallowlistし、未登録値は開始前エラー。run開始後は不変、resolved settings・hash・runtime API・recipe/YAML・restart・UI表示へ通す。

| ID | Situationの入力 | 目的 |
| --- | --- | --- |
| `none`（既定） | 現window採用画像、manifest、質問のみ。前memoryの値・placeholderは一切挿入しない | 既存の独立観測baselineを保持 |
| `previous_text` | 上記＋**直前の正常完了windowから確定した`memory.json`の`narrative`だけ**。初回は過去情報なしと明記する | 記憶条件付き観測を比較 |

`previous_text`へ原`memory.jsonl`全文、未来window、正解ラベル、選択肢、実行中current-windowの集約結果、非検証生出力を渡さない。前windowの正常commit後だけmemory snapshotを可視にする。停止/失敗したwindowから次へ古い部分出力を転送しない。モード`none`では、ユーザーの観測prompt上書きに`{{previous.evidence}}`が含まれていたら黙って挿入せず検証エラー。`previous_text`では新観測promptが前memory変数を明示的に含むことをチェック。`previous_text`で旧`full_rgb`を許す場合も、まずFakeテストで自由文系非回帰を確認し、研究比較は同じ`target_only`設定でのみ評価する。旧未指定runは`none`として復元。

**プロンプト:** `prompts/en/chunk_understanding.txt`の原本は不変、別ID（例`chunk_understanding_with_memory_en`）を追加。既存のJSON観測出力全frame被覆・時刻一致・不確実性・回答禁止を維持する。前memory中の断定を現在frameへコピーせず、現在frameで見えない部分を不明とする。変更したmode/prompt ID/hash/`input_memory_version`をstage traceに追加し、両runの観測prompt/画像を後から照合できる。両モードでMemory AgentとAnswer Agentのprompt/出力契約を同一に保つ。

## 4. 重要イベントをテキストとして残す（B方針の最小実装）

両モード共通で、既存6項目`event_id,start_seconds,end_seconds,description,evidence_frame_indices,certainty`を保持。追加するメタデータは検証できるversioned extensionとして別途任意項目を定義し、旧6キーJSONの読取互換を維持する:
- `importance_reasons`: `question_relevance` / `state_change` / `novelty` / `unresolved_uncertainty` の列挙（複数可、空可）。
- `importance_explanation`: その理由を人が読める短文。確信度のみで重要と断定しない。
- 人物/物体/場所などの具体的な変化はdescriptionに記す。`certainty`によって観測事実・推定・不明を区別する。根拠frame/index/timeへの参照は既存検証を継続する。

全eventを`memory.jsonl`へ追記する。新版narrativeでは質問関連情報に加え、人物・物体・場所の重要な状態変化と未解決事項を残すよう**両モード共通の集約prompt**を設計する。eventが重要でないと判定されても台帳から削除せず、後から判断基準を検証可能にする。モデルのimportance理由を正解ラベルから逆算しない。追加schemaを使う新runと、旧runのイベントは明示的に区別し、旧recordに存在しない重要度を捏造しない。既存`final_output`の参照整合性と`memory_budget_tokens`の契約は維持し、章圧縮による情報保持を実証済みとは主張しない。

## 5. 機械用・人間用の二つの閲覧形式

- **正本:** 既存`memory.jsonl`/`stages.jsonl`/`execution_settings.json`と`memory.json`。新runではmode、memory版、重要度とその理由、event→frame/time、raw/validated/error/elapsedが追える。append-only、runごと非上書き、既存run/JSON readers互換。
- **人間用:** 同じ正本から決定的に描画するread-only timeline（時刻、出来事、事実/推定、importanceの理由、根拠frame、現在のworking narrative、前版との差分）。既存UIの段階詳細に追加する。必要なら同じrender処理で再生成可能な`memory_readable.md`をrun別artifactに出す。二番目のLLMに再要約させて別の正本を作らない。run閲覧はGETのみでQwenを呼ばず、POST run/turnも実行しない。
- モードごとにrunを別作成して保存する。同一run途中でモードを変えない。未実行turn/古いrunで表示できない項目は「未記録」と表示し、嘘の重要理由やmemory差分を生成しない。

## 6. 4秒・8枚の固定設定の可視化

`target_only`、`window_seconds:4`、`frames_per_window:8`を短いFake/合成動画で確認し、1 windowにつき目標/実timestamp・元frame ID・8枚の画像/欠落を既存turn UIで閲覧する。既存標準recipeの60秒8枚/600秒32枚を無断変更しない。推論前に任意の中間区間へseekするプレビューは別の`offline inspect`機能として保留し、オンライン実験のモデル入力へ未来情報を渡さない。

## 7. 対象外と追加実験の境界

今回の変更に含めない: 動的なwindow秒数/画像枚数を実readerへ反映すること、早押しによる実際の停止・中間回答の評価、event selectionの学習/数値重要度順位、Agentごとの別GPU/別重み、モデル再訓練、長尺/全件Qwen評価、実データ大量decode、任意seekをオンラインrunへ混入、sequential_loaderの内部変更、関連のないbrowser Step 10（初期推論タブ/フォルダ遅延）。これらは探索ノートに残す。任意の`shadow sampling proposal`も初回の必須scopeに入れない。多モードの追加余地は保持するが、未決モードを先に作って架空の出力を出さない。

## 8. 実装対象と順序（approved後の候補）

1. **現状照合/非回帰**：current local branch/HEAD/status、worktrees、GitHub main、旧runとFake pipeline、loaderの公開APIを確認。ユーザーdirty/未追跡を保全。snapshot baselineと対象テストを把握。局所AGENTS/CLAUDEを読む。
2. **Agentの見通しとモード設定**：`ExecutionSettings`・allowlist/YAML/runtime/restore・UI/defaultに二値を追加。Situation/Memory/Answer責務をコード上明示し、既存`run_window_turn`/server/CLIへ同じmode契約を通す。Qwen共有。新prompt assetとhash/既存prompt overrideを確認。
3. **Memory入力と偽モデル検証**：window 0の空文脈、window 1以降の前snapshot、`none`の絶対非混入、選択肢/正解/未来情報なし、prompt hash、missing/bad settings、`full_rgb`非回帰、`target_only`全frame構造化出力、CLI/API一致。
4. **event extensionと人間表示**：新event validation・旧6キー互換・必須根拠、`memory.jsonl`にimportanceの理由、human timeline/memory versions/根拠リンク・既存run graceful表示。GETでrunが進行しない。Fakeの決定的goldenを作る。
5. **短い受入確認**：`target_only`の4秒8枚と既存reader/turn/frame UIをFake/小さい合成動画で検査、全関連pytest/compile/CLI help/軽いserver/API smoke。既存browserデータ選択→質問→推論・restart/cancel/history・前面serveとCtrl+Cを回帰確認。実Qwen/GPUは別Gate。

単一の承認済みspecのscopeに限る。git運用は実装着手時の現行repo/他worktreeを基準にユーザーの既存規約を確認し、新作業branchのみに変更。旧`feat/step-10-qwen-preflight`から作らない。local commitはユーザーの実装指示を確認のうえ論理micro単位・検証後とし、push/PR/main mergeは別の明示許可なしに行わない。

## 9. 検証・受入条件

| 条件 | 偽モデル/短時間テストで観測する結果 |
| --- | --- |
| 比較モード | 同じwindow/frame/question/generationの二runでSituation入力の過去memoryだけ差があり、Memory/Answer promptが共通 |
| 初回と境界 | window0で過去なし、window1で前の正常`narrative`のみ。未承認window/不正JSON/途中失敗からmemoryを混入させない |
| 非回帰 | 設定未指定は旧`none`、既存stage名/prompt/CLI/API/旧run restoreと履歴閲覧に退行なし |
| 証跡 | 全採用frame観測が時刻・index整合、全event保存、importance根拠、memory版を両表示で逆引き |
| 可読性 | ソースを開くと3 Agentの役割/使用モデル/設定/順序が追え、UIでmodeと結果が分かる |
| 読取 | 4秒8frameの採用と実/目標時刻表示。オンライン処理で未来window先読みなし |
| 安全 | 明示的なstart/next turn以外で実推論開始せず、サーバーは前面起動・Ctrl+C終了、他者のGPU/プロセスに触れない |

比較の科学的評価は**未実施**と報告し、構造テスト成功から精度向上/性能改善を主張しない。モデル/動画の実行は別の現在承認が必要。

## 10. Ambiguity Gateと承認時の確認

**blocking（実装前）:** ユーザーがこの初回scope（`none` / `previous_text`の二つを先行実装し、重要イベント二形式を共通化する。実動的sampling/早押しは対象外）を承認して`approved`へ更新すること。もし「今回から実早押し」または「任意seekプレビューも必須」を希望するなら、研究意味・Reader契約・実行範囲が変わるため別途設計して本specを更新する。

**non-blocking:** 人間用画面の配置・CSS等は既存UIパターンに合わせる。コードのclass配置は既存責務境界を守る最小構成とし、不要な汎用frameworkや将来用modeを足さない。

**確認するscopeの一文:** 「最初は状況理解への過去text入力ON/OFF、共通の重要イベント記録、JSONLから生成する人間用表示、固定4秒8枚の確認まで実装。動的区間変更と早押しは今回しない」。

## 11. Engineering Handoff（承認後にのみ有効）

- approved spec: 本ファイル。現時点は`draft`なので未有効。
- 対象: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench`のcurrent local main基点から、他作業を保全した独立作業branch。
- 変更範囲: mode settings／Situationへの前memory入力／Agent責務の可読化／共通importance付きevent／machine-human view／静的4秒8枚受入。既存`target_only` public loaderを利用。
- 維持対象: old default、旧run/CLI/API、frame/target timestamp、順次因果性、原prompt assets、Qwen共有、明示ターン実行、run別artifact、Ctrl+C終了。
- 許可検証: unit、Fake、合成動画の短いsmoke、compile、CLI help。実Qwen/GPU/大規模評価は**未許可**。
- Git: 実装commitは実装指示/現行rulesに従う。push/PR/main mergeは未許可。成果物はold runを上書きしない。

## 12. 参照

- MTG: `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-25-mtg.md`
- 概念整理: `.research/secretary/notes/brainstorm/2026-09-29-agent-orchestration.md`、`2026-09-30-evidence-adaptive-early-answer-videoqa.md`
- baseline: `2026-09-25-workbench-target-stream-and-hierarchical-memory-spec.md`（frontmatterのimplementedと本文旧draft記述の不一致があるため、現在コードを優先して現物確認）、`2026-09-29-workbench-dataset-browser-ui-implementation-spec.md`
