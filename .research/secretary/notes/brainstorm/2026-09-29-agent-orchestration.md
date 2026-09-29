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

## 2026-09-29 23:57 JST 追記：3 Agentの責務、テキスト記憶、クラスから分かる運用

### ユーザー追加要件

Agentが情報を**テキストとして蓄積**し、次の動画区間へ引き継げる構成を詳しく検討する。参照したオーケストレーションのサンプル同様に、コード上でAgentクラス・設定を見れば担当役割、モデル、入出力、実行順序がひと目で分かる形を優先する。まず3 Agentの責務から設計する。この段階はexploratoryであり、新しいAgent classやschemaの実装許可ではない。

### 責務案（3 Agentを維持）

1. **Situation Agent（状況理解）**: 現在windowの選択済みframe、実timestamp、質問を受け、フレームごとの見える対象・行為・変化、関連度、観測不能・不確実性を構造化テキストとして返す。選択肢、過去の全文脈、未来window、最終回答は入力・生成対象にしない。全frame被覆のvalidationに失敗したら次段階へ黙って渡さない。
2. **Memory Agent（情報集約と記憶更新）**: 検証済み現在観測と直前の明示的なtext memoryを入力とし、イベントの時刻・説明・frame参照・重要性理由・不確実性と、新版の時系列text narrativeを返す。過去と矛盾する記述は黙って上書きせず更新根拠を残す。全観測・全イベント・全memory版をappend-only保存する一方、次windowへ渡すのは現在版のbounded working memoryと必要な章参照。質問関連度と将来の状況理解に重要な状態変化は別に考える。選択肢/最終回答は原則渡さない。
3. **Answer Agent（最終回答）**: EOF後に初めて質問・選択肢・最終text memoryと根拠イベント/時刻を受け取って回答、参照event/frame/time、未確実事項を返す。原動画の再decodeや未来情報へのアクセスはしない。

**オーケストレータは4番目の推論Agentではなく、Pythonの決定的な進行管理役。** 1windowのread→Situation→validation→Memory→validation→commit、EOF→Answerを進め、stage status/記録/cancel/モデル呼出しを統制。個別Agentへ生の全会話履歴を暗黙転送せず、型付き入力で渡す。Microsoft Agent FrameworkのSequentialBuilder/Agentの定義方式は可読性の参考とするが、フレームワーク導入は未決。ドキュメント https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/sequential

### 重要なmemory stateの分離

- **一次記録／observations**: 時刻・frame ID・観測テキスト。全件追記、削除せず検証可能にする。
- **event ledger**: 変化や出来事、証拠frameと重要性／不確実性。全件追記、重要なものをworking memoryの前面に採用するか分ける。
- **working text memory**: 前版＋新イベントを明示的に更新した最新の人が読める時系列文章。現在何が起きているか、過去の重要な状態変化、未解決事項、根拠ID、対象時刻・versionを持つ。
- **chapters/archive**: budget超過時だけ古い範囲を根拠IDつきで章へ整理する。原記録は消さない。現行の単純単語切断を知的な記憶選別と混同しない。

各windowで、prev memory versionを読込み、validated observationからeventsを得て、Memory Agentがnext textを書き、schemaと参照を検証してsnapshotとappend-only版を保存する。失敗時は直前の正常版を維持し、run/stageにerrorを残す。過去の長文を毎回全文連結して入力しない。

### 可読なコード構成候補（疑似コード）

~~~python
model = Qwen3VLAdapter(model_id=model_id)
agents = {
    "situation": SituationAgent(model=model, config=config.situation),
    "memory": MemoryAgent(model=model, config=config.memory, memory_store=store),
    "answer": AnswerAgent(model=model, config=config.answer),
}
orchestrator = VideoQAOrchestrator(**agents)
~~~

これは実装済みAPIではない。Agent定義にname/role、prompt ID/hash、model adapter、generation、input/output schema、validation、memory read/write、editable settingsを見える形で揃え、設定はrun開始時にsnapshot化する。Qwenは共通lazy-loaded adapterで1 instanceを共有し、Agent classごとに重みを3個ロードしない。Webは構成・traceを表示し、Qwen呼出しはPythonだけが行う。

### Memory Agent内部の比較候補

- A: 1呼出しでevents＋narrative（現行baselineに近い。1windowあたりSituation1＋Memory1）。
- B: 同じMemory Agentの内部でevent extraction/selectionとtext memory updateを別々にモデル呼出し（1windowあたりSituation1＋Memory2）。責務を見える化できる一方、latency/token/VRAMが増える。第4 Agentへ責務変更したのではなく、1 Agent内の2 stageとして実装可能。
- 一次記録は常に追記。A/Bの比較では入力frame、window、Qwen版、prompt、question、memory budget等をできる限り固定し、評価は根拠整合・重要情報保持・最終精度・速度/コストの区別とする。

### 未決・spec handoff候補

1. Memory Agentの重要イベント基準: 質問関連のみか、質問とは直接関係なく人物・物体・場所の状態変化も保存するか。
2. working memoryの書式: 自由な物語文だけか、文章＋イベント参照＋未解決項目を持つ構造化stateか。
3. Memory Agent内部はAをbaselineにBを比較追加する方向が有力だが、実装順はspec化時に承認する。
4. Agentの設定選択UIとコードの定義範囲は、今回の可読性目標を満たす最小契約から決める。初回からグラフエディタ/非同期分散実行は不要。
5. 動画ネイティブ入力と複数画像入力の比較はAgent責務分離と別実験軸にする。Codex/Workbenchの個人用前面起動・Ctrl+C終了はCompany README既存指示を維持する。
