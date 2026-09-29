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
