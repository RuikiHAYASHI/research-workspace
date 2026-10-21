---
date: 2026-10-21
project: agentic-streaming-videoqa
topic: 先行研究のイベント書き起こしAgentは、何を・いつ・どの形式で書いているか（記録プロンプトの見直しのため）
status: investigated
tags: [literature, event-log, recording-agent, prompt, text-memory]
---

# 先行研究のイベント書き起こしAgentの出力形式

- 経緯: 林の指摘（2026-10-21）「イベント書き起こしAgentを作ろうという話だったはず。過去論文のイベントをテキストに起こすAgentは何をしているのか。そこを参考にプロンプトを見直した方がいい」。v5は場面・人・物・文字を細かく列挙する「場面の目録」に寄っていた（[プロンプトの変遷](../../../lab/projects/agentic-streaming-videoqa/experiments/2026-10-21-record-prompt-evolution.md) 第22節）。
- 調べ方: AIの調査役が各論文のPDFをarXivから取得し、本文と付録を読んだ（2026-10-21）。「」は論文からの逐語引用。【確認済】は本文で確認、【推測】は調査役の解釈。
- 調査役の作業メモ: `/tmp/claude-1129/eventlit/notes.md`、取得したPDF: `/tmp/claude-1129/eventlit/pdfs/`（一時フォルダ）。
- 見つからなかったもの: StreamMindの記録係のプロンプト本文、OneStreamerの「fact-recording prompt」の本文（どちらも論文に載っていない）。

各表の行: (a) 書く単位ときっかけ (b) 出力の形式 (c) 何をどの細かさで (d) プロンプト (e) 報告された失敗・設計の理由 (f) モデルと学習の有無

## 1. OneStreamer（arXiv 2610.01762）

| 項目 | 内容 |
|---|---|
| (a) | モデル自身が制御トークンで決める。`</Observe>`（短い区間の局所キャプション）、`</Summary>`（イベントや区間が終わったときの要約）、`</Silence>`（何も書かずに観察を続ける）。学習データでは、局所キャプションは根拠区間の終わりに、区間キャプションは区間の境界に置かれる（§3.2、§4.1、B.2）【確認済】 |
| (b) | `</Observe> [0s-6s] 自由文` と `</Summary> [0s-48s] 自由文`。時刻範囲が先頭に付く（図7〜9） |
| (c) | Observe は「observed objects, actions, scenes, and state changes」。例ではスコアボードの数字や画面上の文字、具体的な動作が中心。Summary は1〜2文で区間をまとめる |
| (d) | 推論時のプロンプトは載っていない。教師データは Gemini3.1Pro と Seed2.1Pro に、フレーム/クリップ、区間、動画全体の3段階でキャプションを書かせて作る |
| (e) | 表17: キャプション学習なしで同じ「proactive fact-recording prompt」を使うと、FIFOとの差は −0.1 / +0.3 ポイント。著者の結論「inference-time prompting alone does not reproduce the memory gains」。表18: Observeのみ 71.7、Summaryのみ 71.2、両方 72.1（OVOBench） |
| (f) | Qwen3-VL-4B-Instruct を SFT（学習あり） |

## 2. DeltaStreamer（arXiv 2610.19849）

| 項目 | 内容 |
|---|---|
| (a) | 1fpsのフレームごとに、直前と現在の2枚をVLMに渡して観察を書く。イベントの境界は (1) モデルが意味的な境界と判断して `<Recap>` を出す、(2) ルール側で BOCPD（観察テキストのハッシュベクトルで変化点検出）。ただし「scene descriptions match and … actor counts agree」なら分割しない（A.2.1） |
| (b) | 7フィールド: description / actors / objects / actions / ocr / scene / delta。Recap は `<Recap t0= t1= kind=<event_end\|scene_change\|actor_enter\|actor_exit\|actor_change\|object_change\|milestone> state=<finished\|started\|in_progress\|aborted>>` |
| (c) | 毎フレーム全フィールドを網羅（「Re-list ALL actors every frame」）したうえで、delta を最重要とする。新規性スコアの重みは delta 0.35、actions 0.25、actors 0.15、objects 0.10、ocr 0.10、scene 0.05 |
| (d) | 付録E.1 図6（抜粋）:「delta: what CHANGED from the PREVIOUS frame. This is the MOST IMPORTANT field」「Format: <subject> <verb/delta> <detail>」「BAD: "delta: no change" (NEVER allowed)」「actions: <actor> <verb> <target> [STATE] … [STARTING] / [IN-PROGRESS] / [FINISHED] / [ABORTED]」「For persisting actions, use still ... or continues to ... instead of re-describing.」「If uncertain … write [uncertain: <detail>]」。Recap:「If THIS frame marks a semantic boundary — an event you were narrating just FINISHED, a SCENE CHANGE happened, an ACTOR ENTERED / LEFT / visibly CHANGED, or a KEY OBJECT appeared/disappeared/changed state」 |
| (e) | 表3: 1枚・差分なし 58.87、1枚で前回テキストと比べる 63.19、2枚・差分なし 61.12、2枚の画像を比べて差分を書く 66.07。平坦なメモリ 61.25（階層あり 66.07）。動機「records primarily capture what is present while leaving what is changing implicit」 |
| (f) | Qwen3.6-27B、学習なし（エージェント構成） |

## 3. TaskMem（arXiv 2605.31075）

| 項目 | 内容 |
|---|---|
| (a) | 10秒クリップごとに必ず1件。入力は直近 k=4 クリップと、そのうち前3件のメモリ（§2.1、§4） |
| (b) | JSON `{"description": "..."}`。メモリ上では `00:00:00--00:00:10` の見出しの下。人物は `[face_1]` などの全体ID |
| (c) | 人物の外見、動作、発話、文脈上の振る舞い。1〜2文 |
| (d) | 表19（抜粋）:「If a character has an associated face ID in the video, refer to them ONLY using that face ID.」「Ensure the continuity and uniformity of content between adjacent descriptions.」「Generate subsequent descriptions not covered in [Description of the preceding part], maintain coherence with it, and avoid any repetition of similar information.」「Generate the description briefly in one or two sentences.」。IDはモデルが推定するのではなく、顔検出の枠とID番号をフレームに描き込み、話者ID付きの字幕も重ねる（§2.1、App.A） |
| (e) | 冗長さの評価（表22）:「repeats any atomic fact already present in the [Context]」なら不合格。正確さの報酬だけだと正しいが中身のない出力になる（報酬ハッキング、表15）ので豊富さの報酬を足した。失敗例: 細かい根拠の抜け（口紅の番号）、誤った情報、関係や時間の統合の失敗。タスク例を足しただけのプロンプト（表20）は改善するが学習版に届かない（表3） |
| (f) | Qwen3-VL-30B-A3B を GSPO と DPO で学習 |

## 4. Imprint（arXiv 2607.00696）

| 項目 | 内容 |
|---|---|
| (a) | 区間ごとに EgoGPT がキャプションを書き、LLMが1件以上のインタラクション記録に分解する |
| (b) | f=(人, 行為, 対象, 開始時刻, 終了時刻)（式1）。抽出用JSON: `persons, action, object, tool, app, source_location, target_location, speech_content, attributes` |
| (c) | 人と物のインタラクションのみ。「Create ONE FIO per distinct interaction」 |
| (d) | キャプション（図11）:「Imagine you are the character in the video, describing from a first-person perspective what you saw, and everything that happened over time. Use I as the subject.」。64個の質問テンプレートを「hidden guidance」として与え、「produce a smooth, natural, and continuous story-like caption」。抽出（図12）:「extract ALL distinct human interactions」「"persons" MUST list ALL named persons」「"speech_content" MUST include exact words」「Do NOT invent information」 |
| (e) | 要約ではなくインタラクション記録で検索すると GA 10.8 → 41.5 だが、正答率は 31.0 → 28.4 に下がる。原因「substantial redundancy, retrieval noise, and competition among repeated observations」。統合と重要度による圧縮で解消。質問テンプレート付きのキャプションで GA 5.41 → 64.80 |
| (f) | EgoGPT（既製）と Qwen2.5-7B-Instruct。Imprint自体は学習なし |

## 5. MemLife（arXiv 2609.40195）

| 項目 | 内容 |
|---|---|
| (a) | 30秒の区間ごとに1件。8フレーム（704px）と音声の書き起こしを入力し、前の区間とは独立に書く（B.1） |
| (b) | 一人称の段落1つ（約450トークンまで）。「No JSON, no bullets, no headers」 |
| (c) | 見たもの（人、行為、扱った物、ブランド名、文字、場所）と聞いたもの（誰が何を言ったか、決定、数、時刻）を同じ重みで |
| (d) | 図6:「This entry is the only record of this moment that a later question-answering system will see, so capture the concrete, factual details it might be asked about.」「Refer to any OTHER person by name when they are a named speaker in the transcript … add stable visual attributes (clothing, hair, glasses) as a complement to the name, and use visual attributes alone only when no name is available.」「Describe only this segment; do not speculate beyond the evidence.」 |
| (e) | 付録I: 前の区間の文脈を渡すと、時系列の再構成と物の位置の記憶が下がり、全体の精度も上がらない。そのため独立に書く（エラーの伝播も避けられる） |
| (f) | Qwen3.5-9B。基本形は学習なし（MemOptで書き手を強化学習すると上積み） |

## 6. VST（arXiv 2603.12262）

| 項目 | 内容 |
|---|---|
| (a) | 視覚トークンが一定量たまるごと（実測16〜32秒間隔）に「thought」を1件。メモリはFIFO |
| (b) | タイムスタンプと自由文 |
| (c) | 進行（delta）だけ |
| (d) | 推論時は「You are a Streaming Video Analyst. {Memory} {TimeStamp} {VideoClip}」だけ（表7）。学習データ生成のプロンプト（表8）:「Provide a incremental update of the visual scene/action/details in this segment. Focus on Progress (Delta)」「If the scene is static, be very concise.」「NO restate: Do NOT restate the action/scene/details from the previous segment's end. Skip the action stated previously or state the changes. NEVER repeat.」。知識グラフ生成は `{"events":[{"subject","relation","object","description"}]}` と Entity Registry |
| (e) | 学習なしで書き方を変えるのではなく、このプロンプトで作ったデータで学習 |
| (f) | Qwen2.5-VL-7B を SFT と GRPO |

## 7a. Think While Watching（arXiv 2603.11896）

| 項目 | 内容 |
|---|---|
| (a) | セグメントごとに「exactly one memory note」（§4.1） |
| (b) | データ生成時の形式: `[SEG k THINK] Focus / Evidence from this segment (2-5 sentences) / State update (1-3 sentences)` |
| (c) | 「key entities and attributes, salient actions and interactions, scene changes, and short-range temporal relations」 |
| (d) | 付録:「If no task-relevant change occurs, explicitly state that the scene, action, or tracked state remains stable.」「Emphasize continuity, change, or boundary cues (start / end / ongoing).」「Update internal task-specific state clearly and conservatively.」 |
| (e) | 大まかなイベントの流れは残るが、序盤の細かい属性（どの物、どちら側、どの人物）を忘れる。証拠不足のまま早く断定する。目立つが無関係な区間に引きずられる |
| (f) | Qwen3-VL-2B/4B/8B を SFT |

## 7b. StreamArena / StreamMind（arXiv 2608.05703）

| 項目 | 内容 |
|---|---|
| (a) | 記録係が4秒ごとに30フレームと直近15秒の音声書き起こしを読み、イベント境界かを判定。micro イベントは境界予測・6回の読み取り・30秒のいずれかで閉じる。macro は micro 5件か180秒、super は macro 4件か900秒（C.5） |
| (b) | micro イベントの記録、エンティティの更新、関係のエッジ、キーフレーム |
| (c) | 階層化したイベントと、エンティティの関係グラフ。人物名の統合はしきい値0.85 |
| (d) | 記録係のプロンプトは載っていない |
| (e) | 「workers require reliable instruction following for structured memory construction」ので大きなモデルを使う |
| (f) | Qwen3.5-397B-A17B、学習なし |

## 8. Lando ら（ICIAP 2025, arXiv 2506.16450）

| 項目 | 内容 |
|---|---|
| (a) | 固定長のクリップごとに1件。30 / 15 / 5秒を比較 |
| (b) | 一人称の文章。1文に1つの行為 |
| (c) | 行為、物の位置、自分の居場所 |
| (d) | 図3:「Describe each action you perform in the video using first-person narration」「One action per sentence to maintain clarity and granularity」「Prioritize: The action performed … The description of objects (e.g., "on the table," "to the left of the motorcycle") … Your position in space」。質問テンプレート「Where is object X before / after event Y? / Where is object X? / What did I put in X?」 |
| (e) | 前のクリップの記述を渡すと精度が下がる（外すと Gemini 51.6 → 56.0、LLaVA-OV-7B 47.9 → 51.9）。「hallucination snowballing」。質問テンプレートを外すと LLaVA-OV-7B は 51.9 → 32.2。小さなモデルの最適なクリップ長は15秒（30秒 37.0、5秒 45.7） |
| (f) | Gemini 2.0 Flash Thinking と LLaVA-OneVision-7B。回答は DeepSeek R1。学習なし |

## 9. EgoLife / EgoRAG（arXiv 2503.03803）と LifelongMemory（arXiv 2312.05269）

| 項目 | 内容 |
|---|---|
| (a) | EgoGPT は30秒ごとに映像と音声からキャプション。LifelongMemory は2秒ごとに LaViLa のキャプションを1行 |
| (b) | EgoLife は一人称の文章で発話を引用（例「Jake said, "Here is a stopwatch."」）。上位に1時間・1日ごとの要約 |
| (c) | EgoLife の正解データは平均2.65秒ごとの人手の口頭記述。「When no specific action was occurring, annotators described the participant's focus and prominent features in the surroundings」 |
| (d) | LifelongMemory の Caption Digest:「merge a list of captions into a single, concise caption. Focus on clarity and brevity while ensuring no critical details are lost」。その前に情報のないキャプション（「looks around」）を除き、似た連続キャプションをまとめる |
| (e) | 質問を条件にした LLaVA の長いキャプションは LaViLa より大きく劣る。最も良いのは人手の Ego4D ナレーション（1分あたり13.2文で件数は少ない。「focuses on the core activity」）。LaViLa は存在しないものを書く誤りが出る |
| (f) | EgoGPT は LLaVA-OV-7B を学習。LifelongMemory は学習なし |

## 10. FOLIO（arXiv 2607.13298）と Harnessing Streaming Video in the Wild（arXiv 2606.08615）

| 項目 | FOLIO | Harnessing |
|---|---|---|
| (a) | 8秒のセグメントごと（既定。32秒では −6.0 ポイント） | 200秒のチャンクごとに中期の要約、5件で長期の要約。ナレーションは「emits a description only when such events occur」 |
| (b) | JSON の `detailed_objects`（location, holder, state, relations, interactions, state_change, evidence_frames, confidence）、`compact_objects`、`events`（event_type, summary, participants, changed_objects） | 長期の要約は「organizing causally related events into a coherent timeline」。応答は `</silence>` か `</response>`＋1文 |
| (c) | 注目する物は詳しく、周辺の物は「brief」。`state_change`:「what changed since previous segment, or stable」 | 重要な瞬間だけ |
| (d) | K.1:「Do not duplicate the same physical object」「Only list visible or partially visible objects」 | B.1:「Use </silence> when no user query is active or when there is no useful new response」「Do not invent names, scores, labels, or facts」 |
| (e) | 細かい状態やOCR・スコアの取りこぼし。「書いたが検索できなかった」誤りは0件 | 既製のモデルは「over-narrate in a dense captioning style」。小さなモデルは「frequently hallucinate, misreport critical outcomes, repeat templated phrases, and miss key events」 |
| (f) | Qwen2.5-VL-7B と Qwen3-VL-8B。学習なし | Qwen3-VL-8B を学習 |

## まとめ（調査役の整理）

### 論文で確認できた事実

1. **書く単位は2種類が主流。** 固定の時間窓（8〜30秒）ごとの記録と、イベントの境界で書く完了イベント要約（OneStreamer の Summary、DeltaStreamer の Recap、StreamMind の micro/macro）を併用。境界の判定は、学習したモデル、ルールと変化点検出、大きなモデルのいずれか。
2. **変化を明示的に書くと効く。** DeltaStreamer の 58.87 → 66.07、VST と FOLIO の「Delta」「state_change ... or stable」。「何があるか」より「何が変わったか」。
3. **網羅的に書くと害がある。** 冗長な記録が検索で競合して正答率が下がる（Imprint）。情報のないキャプションは除くべき（LifelongMemory）。既製のモデルは書きすぎる（Harnessing）。前の記述の繰り返しは不合格（TaskMem）。例外の DeltaStreamer は毎フレーム全項目を書かせるが、27Bのモデルで、変化のない記録はルール側で抑えている。
4. **前の記録を文脈に渡すかは結論が割れている。** Lando と MemLife は「渡すと悪化、または効果なし」（ハルシネーションの連鎖）。TaskMem と VST は「渡して繰り返しを禁じる」だが、どちらも学習が前提。
5. **人物のIDはモデル任せにしていない。** 顔の枠とIDを画像に描き込む（TaskMem）、話者名・装着者名を外から与える（MemLife、Imprint）、名前・別名・類似度で照合する（FOLIO、StreamMind）。
6. **小さなモデルにプロンプトだけで書かせることには限界がある。** OneStreamer の表17、StreamMind が大きなモデルを使った理由の記述。

### 調査役の改訂案（推測。研究上の判断として扱う）

- 1行の形: `[開始秒-終了秒] 主体 | 行為（動詞） | 対象 | 状態（開始・継続・完了・中断） | 根拠（見える手がかり、OCR、発話）`。Imprint の (人, 行為, 対象, 時刻) と DeltaStreamer の状態タグの組み合わせ。SCENE型とOBJECT型の行はやめ、物は行為の対象か状態が変わったときだけ書く。
- 書くか書かないか: 「新しい行為・状態変化・入退場・文字の変化」が0件なら `NO_CHANGE` の1行だけ（TWW、FOLIO にならう。DeltaStreamer は「no change」を禁じているが、毎フレームの差分が前提で20秒の窓には当てはまりにくい）。
- SCENE は場面が切り替わったときだけ1行（DeltaStreamer の Recap kind=scene_change）。
- 継続中の行為は「continues/still」の短い行、完了した窓では `state=finished`（DeltaStreamer）。
- 前の窓の自由文は渡さない（Lando、MemLife）。代わりに「現在進行中の行為の一覧」と「人物IDの一覧（`P1: 赤いシャツの男性`）」だけを渡す。照合はプログラム側で後から補正するのが安全。
- ベンチマークの質問の型を「hidden guidance」として入れる価値は高い（Lando、Imprint で大きく効いた）。
- 窓の長さは 15秒 ≤ 窓 ≤ 30秒 が妥当（Lando）。8秒（FOLIO）の方が細かい状態を取りこぼしにくい可能性もある。
