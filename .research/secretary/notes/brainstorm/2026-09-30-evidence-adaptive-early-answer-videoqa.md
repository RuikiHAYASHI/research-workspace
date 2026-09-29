---
date: 2026-09-30
project: agentic-streaming-videoqa
source_todo: "2026-09-25 MTG: Agent運用・イベント記憶・複数frame入力とオーケストレーション"
topic: evidence-adaptive-early-answer-videoqa
status: exploratory
tags: [brainstorm, streaming-videoqa, early-answer, memory, agent, sampling]
---

# 証拠量適応の早押しVideoQAと対象frame読取の壁打ち

## 出発点・Authority

2026-09-30のユーザー判断: Memory Agentは質問関連情報に加え、人物・物体・場所の重要な状態変化も蓄積する（B案）。3 Agentのうち最終回答のみを担当するAgentに限らず、十分な証拠の到着時に観測停止・回答する「早押し」型を研究候補として検討する。質問/データセットごとに必要な証拠の時間幅・出現時刻が異なるため、短い局所証拠も長い分散証拠も扱い、記憶/画像token/処理コストを抑える研究案を探索する。ユーザーは確定実装ではなく「一つの案」と明言。4秒間から8frameのような指定区間/指定枚数の取得・可視化、および不要な全frame decodeの解消状況を確認する。

明示MTG決定: `meetings/2026-09-25-mtg.md`。直前の探索: `2026-09-29-agent-orchestration.md`。現行WorkBench main `a491757cabb8ed897a2d752da73325fe15f48884`、loaderの対象frame機能を含む公開branch `tamaki-lab/sequential_loader@docs/target-frame-stream` `76badb1c407a34de6f2dfa7e5d4040ef7c4b2ccc`。loaderのdefault `master` と `feat/longvideobench-source-adapter` は公開対象frame APIを含まず、古いブランチだけで未実装と誤判断しない。GitHub上の状態であり、146 serverの現在install/dirty/未pushは未確認。

## まず守る区別

- 観測可能時間の境界/停止時刻 `t_stop` と、実際に答えを支える証拠の時間幅 `[t_first,t_last]` は別。証拠が短くても動画後半で現れること、複数の離散区間にまたがることがある。長さだけでなく出現位置、複数断片、因果関係/反証可能性を見る。
- EOSまで見なければ答えられない総数/最後/最も等の質問を、初出の高確信フレームだけで早押ししてはならない。質問型による必要条件と「未観測の未来で反証できるか」を明示する。必要ならEOFまでCONTINUEまたはABSTAIN（未判断）とする。
- 早期停止で未来のdecode/追加model call/視覚token/新memory更新は省略し得る。ただしQwenの常駐モデル重みそのもののVRAM、すでに保存済みのappend-only ledgerは停止だけでは小さくならない。peak VRAM、合計GPU計算、入力token、working-memory token、ストレージ、wall timeを分離測定する。
- オフライン動画を先頭から再生するonline/causal評価と、任意範囲seekを許すoffline retrievalは別実験。将来のフレーム・全動画要約・GTを停止判定へ漏らさない。

## 3 Agent責務の発展候補（現行実装はEOF回答のまま）

1. **Perception/Situation**: 現在windowの選択frameと実timestampから、見える人物・物体・位置・行動・変化、不明を観測。画像/動画入力形式比較は別軸。フレーム完全被覆とID整合を検証。
2. **Memory**: question-relevant evidenceに加え、関係する人物・物体・場所の状態変化、初期/変更後の関係、未解決事項を記録。全観測/全event/版はappend-only、次に渡すbounded text stateは明示更新。単純単語切断で重要度が保たれるとは主張しない。前述A:一呼出しでevents＋narrative、B:同じMemory Agent内部の二stageでイベント抽出と記憶統合を分離。
3. **Decision/Answer（仮）**: window境界で、questionと最新validated memory、event/frame/time根拠に基づきCONTINUE/ANSWER/（場合によりABSTAIN）を返す。ANSWER時だけ最終選択肢と根拠付き回答を確定し、停止理由、時刻、使った証拠spanとmemory版を保存する。現行の選択肢を最終段階だけへ渡す契約はbaselineとして保ち、途中判定への選択肢入力は明示的な別条件とする。毎windowのLLM判断による呼出し費用には注意する。

Orchestrator（モデルを増やさないPython制御）はread→perception→memory→validate/store→stop gate→continue or answer。明示start以外で実行開始しない。早押し時は既存reader contextを閉じ、`ended_reason=evidence_sufficient`等でEOFと区別し、保存済みrun/partial evidenceを維持。途中失敗/中止/EOFと明確に区別する。Qwen instanceは共有し、Agent class/role/config/prompt/in-out/validation/記憶をコードで一覧可能にする。

## 比較候補と反例

| 仮説 | 研究案 | 反例/コスト |
| --- | --- | --- |
| 答える時刻を学習的に扱えるか | evidence readiness gate: 検証済みevent・質問型・支持/反証の可能性で判断し、停止時刻と根拠を出す | Qwen自己確信は過信し得る。全動画依存問題にはEOF必要 |
| 必要画像数が場面で違う | coarse-to-fine causal observation: 通常低密度、動作開始・高関連・不確実なら次の未来windowを短く/高密度で観測 | 事後的な過去へ戻るとonline条件が変わる。window終端の判断で次だけ変更 |
| 長い証拠を低予算で保持できるか | dual text memory: question evidence と object/person/place state＋時刻付きevent ledger、必要IDを選んでfinalへ | 任意要約で否定/反証が消える可能性。追記台帳で監査 |
| 次に何を探すかを示せるか | question-guided anticipation: 未確実事項を1文で表し、次windowでの観測視点/枚数を調節 | query biasで質問外の状態変化を見落とす。generic event streamを維持 |
| 複数断片の統合はできるか | temporal evidence stitching: 離れた複数時刻のイベントをリンクして回答判定 | 連続幅だけでは必要証拠量を測れない |

実装/比較順候補: (0) 現行EOF/full RGBまたはtarget_onlyを固定baseline、(1) 早期停止を行わないwindowごとのready trace記録、(2) 設計した停止gateだけ有効化しaccuracyと処理量を比較、(3) 動的window/枚数を**別比較**、(4) 記憶の選別/長期保持を比較。初期からstop gate、sampling、memory、モデル入力形式を同時に変えない。

## loaderの確認済み事実

- `tamaki-lab/sequential_loader@docs/target-frame-stream/src/sequential/target_stream.py`: PyAVの `container.decode` を先頭から前方向に反復。非採用frameはtimestamp判定のみで `to_ndarray(rgb24)` をしない。採用frameが複数targetを満たしてもRGB変換は元frame一回。`TimeGridSamplingPolicy(duration_seconds,window_seconds,frames_per_window)` が各窓の目標時刻を定め、最初にtarget以上となるframeを採用。早期にcontextを抜ければreaderをcloseする。任意時刻へseekして非対象区間の圧縮decodeまで省く実装ではない。
- `tests/test_target_stream.py` で選択順、途中停止と通常終了のclose、失敗close、非採用frameのRGB conversion回数0の検証がある。spec実装報告はloader 182 testとWorkbench接続を記録するが、実LongVideoBench/Qwen長時間速度/精度は未評価。
- loaderの古いfull RGB経路 `src/sequential/reader.py` は毎decode frameに `to_ndarray(rgb24)` する。`target_only` を有効にすると非選択frameの画像展開/保存を避けるが、動画圧縮の前方decodeを避けるわけではない。
- `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main/src/longvideoqa_workbench/reader/{sequential,windows}.py` は `target_only` を公開 `target_frame_stream` に接続し、欠ける場合はエラーにする。旧recipeのdefaultはfull_rgb、専用recipeは600秒32枚。UI/内部には`window_seconds`、`frames_per_window` 設定と各turn採用frame画像/実時刻・目標時刻の表示がある。
- 4秒8枚では目標時刻0,0.5,...,3.5秒（その後4,4.5,..）。ただし実動画の実時刻はfirst-after-target、重複元frameの可能性あり。任意の`[start,end)`範囲を**推論前**に8枚だけプレビューする専用API/UIは確認できず、今の画面は実行したturnの採用サムネイルを見せる。任意位置へ直接seekする別offline UIをオンライン因果pipelineへ混ぜない。

## 評価の要件候補

正確性 vs `t_stop/video_duration`、回答までの観測秒数、`t_first,t_last`と複数支持区間、frame decode count/RGB conversion count/model image tokens、model call count/prompt tokens/CPU・GPU時間、peak VRAM、working memory token、ledger bytes、見逃した証拠/早過ぎる回答率、質問型/動画長別の分布。最短十分prefixのannotationが無いdatasetなら、一部人手注釈または外部基準で定義し、最終正解ラベルやfull-video outputで停止時点を直接決めてはならない。

関連先行例: StreamReady (CVPR 2026) https://www.microsoft.com/en-us/research/publication/streamready-learning-what-to-answer-and-when-in-long-streaming-videos/ は回答可能時刻とタイミング評価、A.I.R. (ICLR 2026) https://proceedings.iclr.cc/paper_files/paper/2026/hash/1332893b662f655660c9abdf793230cf-Abstract-Conference.html はadaptive frame selection、`Towards Sparse Video Understanding and Reasoning` https://arxiv.org/abs/2602.13602 はsummary stateとearly stop。新規性はこれらとの差分調査が必要で未確定。

## 次の判断（今回まだspec化/コード変更しない）

早押しをどこまで要求するか: (a) 最初はreadinessを記録するだけ、(b) ゲートが停止する、(c) 次windowの長さ/枚数まで動的制御する。質問タイプでEOF依存を見分けるgateを必須とするか。メモリはイベント台帳を残し、working stateに全体変化＋質問関連証拠を保持する方向で継続。画面の「指定区間8枚」は、実行設定変更と、推論前の静止画確認を別操作として分ける。直接seekはonline実験と別のoffline preview境界。現行Step 10 UI応答性draftを本テーマのspecとして上書きしない。個人利用の前面serve＋Ctrl+C終了規則を守る。

## 2026-09-30 00:40 JST 追記：質問適応サンプリング、重要度基準、二つの閲覧形式と今週の実装候補

### 今回のユーザー案

質問文の意味からsampling interval（サンプル間隔）とwindow length（1回の観測秒数）を変え、観測中の重要度や不確実性から次のwindowの方針も更新する研究を検討する。Memoryに何を重要として残すかを説明できるようにする。Machine-readableなJSONLと、研究者が一目で読めるhuman-readableなテキスト/画面の双方がほしい。今週の実装スコープを現実的に選ぶ相談であり、この文書はexploratoryのまま、コード変更・spec昇格の許可ではない。

### 重要の意味（単一数値を初手で固定しない）

軸を分ける: (i) question_relevance（質問関連性）、(ii) state_change（人物・物体・場所/所持物の状態変化）、(iii) novelty（既存memoryとの差分）、(iv) uncertainty / unresolved（何が不明か）、(v) evidence_support（元frame/event/時刻への追跡可能性）。question relevanceが低くても大きな状態変化は捨てず、逆に関連が高くても画像から確認できないことを事実扱いしない。event_type、reason、source_frame_ids、time span、fact/inference/uncertain、updated entities等を別フィールドとして保存する。「保持対象か」はモデル候補→スキーマ検証→明示policyの結果と理由を分ける。正解ラベル/全動画後段は観測/選定に渡さない。後で基準を比較できるようにpolicy ID/hashとrunのresolved configを残す。

### JSONLと人間表示の二重化をどう扱うか

**正本はschema-version付きのappend-only JSONL**（既存memory.jsonl/stages.jsonl、関連するmemory.jsonの契約と互換検討）。machine-readableにrun_id、window_index、actual/target timestamps、frame/event IDs、stage/model/prompt/generation版、observed text、decision reasons、prev/next memory version、raw and validated output、error/elapsedを持つ。human-readableな「00:12 event-03 人物が冷蔵庫を開いた（観測事実）→ 00:34 event-04 飲み物を取った（変化）」の時系列timeline、現在の人物/物/場所state、質問関連の証拠、保留不確実性、prev→next memory差分は**同じJSONLから決定的に生成**する。別LLMで独立要約した第二正本を作らない。閲覧はWorkbenchの既存trace viewに統合/あるいはread-only markdown export。人間用画面で提示する文言もsource event IDsへ逆引き可能にする。

機械用モデルレコードの候補（現行schemaではない）:
~~~json
{"schema_version":"proposed-v1","kind":"event","event_id":"w0-e1","window_index":0,"start_seconds":1.2,"end_seconds":1.9,"text":"person opens refrigerator","evidence_frame_indices":[12,19],"question_relevance":"medium","state_change":{"entity":"refrigerator","before":"closed","after":"open"},"novelty":"new","uncertainty":"object contents not visible","retention_reason":["state_change","question_context"],"certainty":"fact"}
~~~

### 質問に適応したサンプリングの二段階

- 初期計画はquestion type（対象状態/順序/個数/最後/全体依存/時間幅不明）から推奨window_seconds、frames_per_window、目標時刻を出す。これは**仮説**であり、実装前に質問型とground-truth leakage境界を検討。
- 動画を読んだ後はvalidated observation＋working memory（変化、question evidence、未解決事項）から**次の未読windowのみ**のproposal（duration, frame count, reason, constraints）を生成する。現在/過去のframeの追加再取得はonline causal実験と分ける。preserve min/max/budget bounds、実際に採用したtarget/actual timestamps、sampling policy revision、CPU decode/RGB/model costを記録。
- 現行 `sequential_loader.TimeGridSamplingPolicy` は開始時に `target_windows()` で全動画分の固定区間・targetを構築し、`target_frame_stream`がその計画を消費する。WorkBench `configured_window_stream` はstatic `window_seconds` / `frames_per_window` を渡す。動的に変えるなら次window計画を受け取るreader APIと整合する新specが必要。今週は**shadow proposal**（提案を表示/保存、実readerに反映しない）で因果性/設定監査を先に検証し、正式なadaptive readerは次フェーズ。
- 通常区間でも状態変化を取り逃し得る。観測されなかった重要eventの検出はモデルだけでは保証不能。均一baseline / 適応版 / 異なる固定予算を分け、question type×evidence timing/spanでaccuracyとRGB/model call/token/wall timeを比較する。

### 今週（9/30〜10/2）に関する候補・ゲート

最小の通る成果物候補は**Agentと証跡の可読化＋4秒8frameの指定/表示＋shadow policy**（実行変更はせず設計・記録）。UI Step 10（初期タブ整理とブラウザ応答性）と研究用Agent基盤は別scopeとして優先度を調整し、実装する場合は現行WorkBench main/phase/ローダーの正本branchと作業木を再照合する。既存read-only history、run/turn POST境界、前面serve/Ctrl+C個人利用を維持する。

micro実装候補（全てユーザーがspec化を明示してGateを通過した後）:
1. **Agent definition / orchestration manifest**: Situation・Memory・Decision候補のname、role、model、prompt、input-output schema、generation、呼出し回数を一目で読み取る。ただしDecisionの早押しは未実装・旧EOF Answerをbaseline維持。既存pipeline/registryを破壊しない。
2. **Event schema & machine/human view**: machine正本のversioned JSONLにimportance軸とretention reason/source referencesを加える互換計画、決定的read-only human timeline/working-memory差分。fake test: source ID、時刻一致、古いrecordの読取、invalid reference停止/未確認表示。
3. **4秒8枚のread/preview**: `target_only` の採用frameとactual/target timestampを表示、4秒8枚の短いFake/合成実動画と既存turn viewerの回帰。推論前任意範囲previewを加える場合は明示的offline/inspect専用endpointと分離し、future情報をオンラインAgentへ混ぜない。
4. **Shadow sampling decision (optional/stretch)**: question+current validated stateに基づく次windowの提案・理由・制約・policy IDをtrace化。実readerのwindow幅/枚数は変更せず、性能や精度向上を主張しない。

今週の完了判定: Agentの処理順とQwen共有がソース上で明瞭、同じ根拠をJSONLと人間表示で辿れる、時刻と画像が一致、static 4秒8枚を確認、既存EOF/固定sampling挙動の回帰が通る。単発のFake/synthetic smokeまでは可否をspecで承認。GPU/Qwen full run、任意seekをonlineに混入、実adaptive scheduling、実stop gate、無断push/main統合、共有サーバーの高負荷は対象外。

### 次のユーザー判断とhandoff

「今週の正式scopeを可読化・追跡基盤に絞るか」「4秒8枚の推論前previewも今週に含めるか」「shadow adaptive proposalの表示まで含めるか」を決める。仕様化を明示依頼された場合、研究specでbranch/read-only current code、互換性、Gate、micro testと成果物を確定する。今週案は仮であり、自動TODO化やコード変更はしない。

## 2026-09-30 01:00 JST：研究specへの引き継ぎ

ユーザーから2026-09-30に、観測Agentへ前のテキストを渡す／渡さない複数モードの実装を進める意向と、新規spec・Codex向けプロンプト作成の依頼があった。研究specに初回scopeの草案を作成した（status: draft、コード実装未承認）。本brainstormの早押し・動的sampling・未来の多モード比較は依然exploratoryであり、新specへ自動昇格しない。

昇格先: [2026-09-30-workbench-agent-modes-and-readable-memory-spec](../../../lab/projects/agentic-streaming-videoqa/specs/2026-09-30-workbench-agent-modes-and-readable-memory-spec.md)
