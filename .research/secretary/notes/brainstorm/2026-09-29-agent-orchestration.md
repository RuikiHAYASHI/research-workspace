---
date: 2026-09-29
project: agentic-streaming-videoqa
source_todo: "2026-09-25 MTG: Agent責務・イベントJSON・複数frame入力とオーケストレーションの調査"
topic: agent-orchestration
status: exploratory
tags: [brainstorm, agent, orchestration, model-call, workbench, streaming-videoqa]
---

# Agent運用計画とQwen3-VL呼出しオーケストレーションの壁打ち

## 出発点・Authority・現在地

2026-09-25 MTGの明示決定: 状況理解・情報集約・最終回答の責務と編集点をコード/UIで可視化する。気になるイベントを時刻・観測情報・集約情報を含むJSONへ残す。Qwen3-VLの複数frameを動画入力にする方法と、複数Agentのオーケストレーション実装例を調査する。フレームワーク採用自体は目的にしない。2026-09-18 MTGでは操作時に1単位ずつAgentを動かしprompt/入力条件を比較するデモを求めた。

GitHub上の研究コード `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` の調査時HEADは `a491757cabb8ed897a2d752da73325fe15f48884`。実サーバの未commit/未push変更と実GPU・実動画の性能はGitHubでは確認できない。次のUI改善Step 10 draftと本Agent設計は別の論点であり、既存Step 10を本brainstormで改番/実装しない。

## 現行実装から直接確認した事実

- `agent/pipeline.py`: windowごとに `run_chunk_understanding` → `run_evidence_aggregation`、EOF後に `run_final_answer`。前段は当該windowの画像列と質問、集約は前のevidenceと現在観測のtext、最終回答は証拠と初めて選択肢を受け取る。target_onlyでは各frameの観測JSONを完全被覆検証し、情報集約出力から窓イベントと物語を保存する。
- `core/contracts.py` の3 `StageName`、`ModelRequest(stage,prompt,images,generation)`、`core/protocols.py` の共通 `ModelAdapter.generate` を使用。複数のAgent役割は同一Qwenインスタンスに別promptで順次要求することで表現される。
- `model/qwen3vl.py` は `generate` / `count_text_tokens` の初回にlazy loadする。現行の観測入力は複数の `type:image` を列挙し、frame indexとtimestampはprompt中のmanifest。ネイティブ `type:video` と時刻metadataを使う経路は未実装。
- `agent/events.py` のイベントJSONは `event_id,start_seconds,end_seconds,description,evidence_frame_indices,certainty`。同一のaggregation呼出しが `events` と `narrative` を返すため、独立したEvent Agentのモデル呼出しは現時点ではない。元観測・イベントの追記台帳、story/chapterと根拠追跡の既存成果物は維持対象。
- `agent/memory.py` の予算超過時の章圧縮は現行実装では決定的なテキスト縮約で、別のQwen要約呼出しではない。研究品質や参照保持は別途検証対象。
- `interfaces/server.py`: 明示的な「次turn」でwindowを1つ進め、session lockとcancel requestedを持つ。閲覧とrun開始は別操作。既存runを無断で進めない。モデルの実ロードはserve直後ではなく初回実要求時である。

## 中心の問い

同じQwenを何回・どの入力形式で・誰の責務として呼び、因果性、イベント証跡、比較可能性、単一ユーザーGPU資源の制約を両立させるか。

## 比較案

| 案 | 1 windowの呼出し | 特徴と失敗要因 | 位置づけ |
| --- | --- | --- | --- |
| A. 現行の決定的逐次 | 観測(VLM)1→イベント＋物語更新(text)1、EOF後最終1 | 現行契約と比較可能。イベント抽出と記憶更新が同一出力で混ざり、重要イベントの選定理由が不鮮明 | **まず保つbaseline候補** |
| B. 責務分離 | 観測(VLM)1→イベント選別(text)1→記憶更新(text)1、EOF後最終1 | 入力・出力・コストを分離し、重要イベントの理由を検証できる。1 window当たり追加1呼出し・遅延増 | **次の比較候補** |
| C. 条件分岐/自律選択 | 観測の不確実性等から次Agent呼出しを可変にする | call費を抑えうるがrouting判断自体の比較と再現性を要する | 後続保留 |

AとBで同一動画・question・window境界・frame選択・モデル版・generation・prompt版を固定し、差分を「独立イベント選別の有無」に絞る。比較軸: event evidence参照整合、unsupported event率、重要イベント保持、質問最終正解、1 window latency/token/VRAM、失敗と再試行。実測がない段階で精度・速度の優位を主張しない。

## 呼出し契約の有力候補

- **オーケストレータはLLMではなくPythonの決定的state machine**。モデルは同一のlazy-loaded `ModelAdapter` を通じて段階別に直列呼出しし、段階ごとにrole/prompt/generation/input-schema/output-schema/検証/保存を明示。モデル本体をAgentごとに3つロードしない。
- 事前にdataset/video/questionとimmutable run設定を確定し、明示「実行」1回で1 window処理。stage間で成功した構造化結果だけを渡す。失敗したJSONを黙って次段階に渡さない。retryは0回の既定を保持し、変更時は設定/成果物に記録。途中cancelは安全なwindow/呼出し境界。
- Agent別にinput manifest（window index、実frame index/timestamp、prompt ID/hash、model ID、generation）、output raw/validated、elapsed、stage status/error、依存event IDを残す。正解ラベルは最終評価以外へ漏らさない。観測には選択肢を渡さず、finalだけ選択肢を与える。
- 既存イベント項目は維持しつつ、「重要イベント」を定義するための候補は `question_relevance`、`importance_reason`、`evidence_frame_indices`、事実/推論/不確実の区別。スキーマ拡張は既存artifact読取互換とversionを考慮してspecで確定する。全イベントは台帳に残し、重要イベントだけmemoryの前面に採用するかを比較可能にする。
- Web UIはAgentの順序・出力・選択中段階・prompt編集・model call回数・実行時間を表示するだけで、browser側が直接Qwenへ送信しない。閲覧とrun POSTの境界を維持する。
- **動画入力は別比較軸**: baselineの複数image（text timestamp manifestあり）と、公式Qwen3-VLが公開する `type:video` のframe列・時刻を使う経路を別run設定で比較する。学習済みモデル内の時間表現・samplingが変わるため、Agent分離と同じ実験で同時に変更しない。原video pathを渡して再samplingさせる方式は逐次読取条件に反するため、既に到着済みの選択frameと実timestampだけを渡す。Qwen版/processor実装対応は小さいfake test・少数frameでread-only/許可後に検証する。

参考: https://github.com/QwenLM/Qwen3-VL/blob/main/README.md （複数画像とvideo入力例）、https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/sequential （順次orchestration）、https://www.langchain.com/langgraph （stateful graph）、https://microsoft.github.io/autogen/dev/user-guide/agentchat-user-guide/tutorial/teams.html （multi-agent team）。

## Codexへの共通Workbench運用条件（ユーザー確定）

このプロジェクトREADMEの「Workbench個人利用の起動・終了運用」を参照。個人利用・必要時のみ前面起動、同じ端末のCtrl+Cで終了、常駐化・nohup・background・systemdは別明示依頼なしに採用しない。共有サーバーの他者プロセス/GPU/ストレージに影響しない。ChatGPT上のプロジェクトMemoryは無効なので、今後のCodex依頼ではCompany READMEを読み込む。

## 保留・反例・次に決めること

- Event Agentを独立した3回目のQwen呼出しにするか、当面Aのaggregation出力内で重要eventを構造化するか（**最重要**）。
- `target_only`をbaselineとして固定するか、`full_rgb`との互換性をどこまで残すか。どちらのモードも黙って意味を変更しない。
- 「重要」の定義を質問関連度中心にするか、質問に無関係でも将来の文脈理解に必要な状態変化も含めるか。
- 動画入力は同一frame・timestampの2経路比較から始めるか。実モデルの追加メモリ・GPU使用は別許可。
- 最初のStepは「役割とstage traceを見える化する・現行Aを非回帰」と「独立Event Agent Bの比較」を別micro/別runに分ける。Agentの研究specはユーザーがspec化を明示するまで作らず、次のUI改善Step 10 draftの番号と混同しない。

## Research Spec Handoff候補（未承認）

- 目的: Qwen一つに複数Agent役割を明示して順次呼び、重要イベント・因果性・説明可能性を強める。
- 現行baseline: 1 windowで観測1＋集約1、EOF後最終1。第4Agentはまだ未実装。
- 対象候補: Pythonオーケストレータ、roleごとの入出力/可視化、イベントJSONの重要度、image/video入力比較、fake test/短時間smoke。
- 対象外: 自律分散Agent導入、Webが直接モデル呼出し、モデルのstage別多重ロード、無許可GPU実験・dataset download・push・main統合。
- 主な未決: event call分離/重要度の定義、baseline mode、Qwen video入力メタデータとprocessor対応、比較用動画/評価。
