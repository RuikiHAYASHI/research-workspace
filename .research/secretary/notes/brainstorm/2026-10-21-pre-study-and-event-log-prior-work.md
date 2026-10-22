---
date: 2026-10-21
project: agentic-streaming-videoqa
topic: 「予習」と「イベントの書き起こし」を同時に行う先行研究はあるか
status: investigated
tags: [literature, pre-study, event-memory, novelty]
---

# 「予習」と「イベントの書き起こし」を同時に行う先行研究

- 経緯: [2026-10-19 MTG](../../../lab/projects/agentic-streaming-videoqa/meetings/2026-10-19-mtg.md) で、教授が「なぜイベントを書き起こす手法に予習させないのか。本当にないか確認すること」と述べた。
- 調べ方: AIの調査役によるWeb検索（約15の検索語）と、arXiv本文の確認。Imprintは本文を直接確認した（2026-10-21）。
- 条件:
  - (A) 予習: 実際の質問を知らないまま、どんな質問が来そうかという知識（質問の分布、質問タイプ、仮の質問など）を使って、何を見て何を記録するかを決める。
  - (B) イベントの書き起こし: 見ながら、イベントを時刻付きでテキストなどの記録に書き、あとからその記録で答える。
  - 実際の質問は、動画のあとに来る。

## 結論

- **(A)と(B)をはっきり両方行う論文が2本あった: Imprint（arXiv 2607.00696、2026-07）と TaskMem（arXiv 2605.31075、2026-05。下の追加調査を参照）。** Imprintの対象は一人称視点の長期ライフログQA。TaskMemはVideoMME・EgoLife・EgoTempoを、動画の後に質問が来る形で評価している。
- 最初の調査では「ストリーミングVideoQAでは見つからない」としたが、追加調査でTaskMemが見つかったため、この結論は取り下げる。
- 新規性の主張は「組み合わせ自体が初めて」とは言えない。ImprintとTaskMemとの違いを言う形にする必要がある。

## Imprint（本文で確認）

- 書誌: Kousik Das, Debaditya Roy（IIT Kharagpur）. Imprint: Online Memory Compression for Long-Horizon Egocentric QA. arXiv 2607.00696v1. https://arxiv.org/abs/2607.00696
- (A): EgoLifeQAをもとに、64個のメタ質問を5カテゴリ（Episodic, Social, Behavioral, Temporal, Goal-Oriented）に整理し、キャプション生成のプロンプトに入れる。
  - 原文: "we define set of meta-questions based on EgoLifeQA" / "Use these meta-questions only as hidden guidance to make your narration more detailed and complete."
  - メタ質問をEgoLifeQAのどの分割から作ったかは書かれていない。評価問題に近いもの（リーク）かどうかは判断できない。
- (B): キャプションを (person, action, object, start time, end time) の記録（Interaction Record）に変換し、オンラインで統合・圧縮する。ただし、抽出の形式（付録B）に時刻の欄がなく、時刻をどこから得ているかは明確でない。
- 質問のタイミング: メモリを作ったあとの質問時刻（"At query time, candidate memory entries are retrieved from the compressed memory."）。
- メタ質問の効果: 付録A.3で "Query-aware captioning consistently enhances downstream QA performance" とし、Grounded Accuracy が 5.41% → 64.80% と報告している。QAの正答率の数値は本文に書かれていない（図10のみ）。
- 処理の流れ（本文で確認、2026-10-21 追記）:
  1. キャプション: EgoGPT（EgoRAGと同じもの）が、メタ質問を「hidden guidance」としてプロンプトに入れた状態で、一人称（"I"）の語りを書く。メタ質問そのものには答えさせない。
  2. 記録への変換: Qwen2.5-7B-Instruct が、キャプションを1つのやり取りにつき1件の記録 (person, action, object, start, end) に変換する。補助として、道具・アプリ・場所・発話・属性も持つ。
  3. 集約（Algorithm 1、LLMではなく埋め込みの類似度と閾値で行う）:
     - action と object を埋め込み、直前の5件と合わせて文脈つきの埋め込みにする。
     - 「イベントの型（prototype）」に割り当てる（類似度 > 0.75。なければ新しく作る。上限300個）。型は検索には使わず、繰り返しの回数と最後に見た時刻を数えるためのもの。
     - 重要度 w = 頻度 × 新しさ × 珍しさ の形で計算し、0.2 未満の記録は捨てる。
     - 残った記録は、action・object が一致し、文脈つきの埋め込みも近ければ（cos > 0.75）既存の記録にまとめる。そうでなければ新しく足す。
     - 操作は「捨てる・まとめる・足す」の3つ。階層や時間スケールはない（平らな構造）。
  4. 回答: LLMが質問を JSON（人、動作、物体、意図、時間の関係 first_time / last_time / before / after など）に分解する。質問時刻より前の記録だけを対象に、物体・動作の類似度と重要度で上位5件を取り出し、Qwen2.5-7B-Instruct が答える。回数を数える質問などは規則で先に処理する。
  - 数字: メモリ 267MB → 109MB（EgoRAGは254.2MB）、検索 20.1 → 1.7 秒/質問（EgoRAG比）、QA正答率 31.0% → 35.8%、Grounded Accuracy 10.8% → 64.8%（いずれもEgoRAG比）。
- 補足（本文で確認、2026-10-21 追記）:
  - メタ質問は64個すべてをプロンプトに入れている（Figure 11）。物体などは穴埋めの形（例: "Who used the [object]?", "Where was the [object]?", "What was in the [container]?"）。
  - EgoGPTを使う理由として本文にあるのは、EgoRAGと同じキャプションにして公平に比べるため（"performance differences arise from memory representation and retrieval design rather than caption quality"）。記録への変換は、照合に人・動作・物体・時刻の欄が要るため。
  - 集約をLLMでなく閾値で行う理由は、本文に明記されていない。文脈からは、記録が届くたびのオンライン処理、重複の削減、メモリの増え方を抑えること、が読み取れる。限界として、キャプションの誤りが記録に伝わること、重要度が経験則であること（学習する方式は今後の課題）、型の上限が小さいと別のパターンが1つの型にまとめられることを挙げている。
  - EgoRAG（EgoLifeの論文で提案）: クリップごとのキャプションを、分・時間・日の階層の要約にまとめて保存し、検索して答える。Imprintは「要約すると繰り返しのやり取りが粗い記述に吸収され、長期の集計に弱い」と批判している。元のEgoRAGはGPT-4oで答えるが、Imprintは公平に比べるためQwen2.5-7B-Instructで再現している。
- 私たちとの違い（推論）:
  - Imprintの予習は「キャプションの書き方」にだけ効く。集約は埋め込みの閾値による規則で、予習の観点は使っていない。私たちは、予習した観点で集約の仕方も変えることを想定している（例：回数を聞かれそうなら数えておく）。
  - Imprintの集約には時間スケールの階層がない。
  - Imprintは長期ライフログ（EgoLife）が対象。私たちはLongVideoBenchなどのVideoQAで、オンライン処理として評価する。
  - Imprintは手作りのメタ質問を固定で使う。私たちはデータセットの質問の傾向から予習する予定（方法は未定）。
  - 私たちは、似たイベントのまとめ（NMSのような集約）、時間スケールごとのまとめ、小さいモデル群での分割統治を想定している。Imprintにも統合・圧縮はあるので、どこが違うかは要確認。

## ほぼ該当（予習が暗黙的・弱い）

| 論文 | 内容 | 確認範囲 |
| --- | --- | --- |
| VST（arXiv 2603.12262） | 質問を見ずに、時刻付きのテキストの「思考」をメモリに書く。最終回答の正誤を報酬にしたRLで学習するので、質問の傾向を暗に学んでいるとも読める。論文は予習とは位置づけていない | 調査役が本文で確認 |
| EGSD（arXiv 2609.36803） | studentがクリップごとにテキストのメモリを書く。teacherだけが質問を見る蒸留。予習はほぼない | 調査役が本文で確認 |

## 近いが条件が違う

| 論文 | 違い |
| --- | --- |
| SAVEMem（2605.07897） | 固定の仮の質問5つで予習するが、残すのは視覚token |
| SVMemAgent（2609.18540） | RLで質問の傾向を学ぶが、残すのはフレーム |
| OneStreamer（2610.01762）、DeltaStreamer（2610.19849）、FOLIO（2607.13298） | 時刻付きのテキストや構造化記録を書くが、予習はない（DeltaStreamerは「後で何が重要か知らないまま記録する」と明言） |
| HiCrew（2604.21444）、Vinci2（2607.11523）、Query-Guided Captioning（2601.09350）、VideoRAG（2502.01549）、QueryStream | 実際の質問を見てから、キャプションや記録を作る |
| LifelongMemory（2312.05269） | 質問に合わせたキャプションは偽陽性を増やし、検索精度を下げると報告。予習の悪い面として参考になる |

- この表の多くは、調査役が検索結果またはabstractで確認したもの。引用する前に原文を確認する。

## 追加調査（2026-10-21、穴埋め）

### 新たに見つかった該当: TaskMem（arXiv 2605.31075、2026-05-29。Imprintより前）

- 書誌: Tao Zou, Yichen He, Tian Qiu, Yuan Lin, Hang Li. *Task-Focused Memorization for Multimodal Agents*. https://arxiv.org/abs/2605.31075
- 本文で確認したこと:
  - 質問のタイミング: "The corresponding question is revealed only after the video has been processed." 答えるときは記録だけを使い、元の動画は見られない。
  - 予習: "the agent leverages recent tasks to model the likely distribution of future tasks"。直近に来た実際のタスク（質問）から、これから来そうな質問の分布を推し量る。
  - 記録: 10秒ごとの時刻付きテキスト（例 "00:00:00–00:00:10"）。人物に [face_1] のようなIDを付ける。
  - 学習:
    - Phase One: 形式・長さ・質（Gemini-2.5-Flash、GPT-4oで採点）・豊かさの報酬で、GSPOにより記録の書き方を学ぶ。
    - Phase Two（運用後）: 報酬モデルが「例のタスク」と2つの記録を見て、どちらがタスクに合うかを判定し、その好みのデータでDPOを行う。更新するのは第22層に足した2,048次元のadapterだけ。
  - ベースライン「+ Task Prompt」: 同じ直近のタスクをQwen3-VL-30B-A3Bに渡し、タスクに合う記録を書かせる（Imprintとほぼ同じ形の予習）。プロンプトの全文と例の質問の数は、HTMLで表が表示されず未確認（調査役の報告では "Your generated memory will be used to answer questions of the same type as those below." という文があるとのこと。PDFで要確認）。
  - 正答率（VideoMME / EgoLife / EgoTempo）: 元のモデル 61.6 / 38.4 / 22.3、+Task Prompt 64.2 / 40.0 / 24.5、Phase Oneのみ 64.4 / 39.6 / 23.7、TaskMem 67.9 / 45.4 / 27.6。
- 私たちとの違い（推論）:
  - TaskMemの予習の元は「その環境で直近に来た実際の質問」。私たちは「データセットの質問の傾向」。
  - TaskMemの本体は学習（報酬モデル＋DPO）。私たちの第1版は学習なし。
  - TaskMemは10秒ごとに必ず記録を書き、集約（似たイベントのまとめ、時間スケール）や分割統治の回答は見当たらない（本文の後半は未読）。
  - 「予習の観点を、プロンプトに入れて記録を書かせる」は、TaskMemでは**ベースライン**として扱われている。私たちの第1版（手書きのプロンプトで予習を代用）は、このベースラインとほぼ同じになる。

### 該当しなかったもの（調査役が本文で確認）

- FOLIO（2607.13298）: 質問タイプの分類表（付録D.9）は回答時に使う。記録を書くときは質問の種類を使わない。
- StreamingClaw（2603.22120）: 記録は動画中心の多モーダルなメモリ。質問の傾向は使わない。
- StreamEMS（2608.27881）: clip単位の視覚特徴の記録。テキストも予習もない。
- Harnessing Streaming Video in the Wild（2606.08615）: テキスト要約とタイムラインを持つが、予習はない。
- MemLife（2609.40195）: 時刻付きテキストを書くが、"leaving the writer question-independent" と明記。
- MemEvo（2609.36581）: 開発用データの正答率で記録の仕組みを探索する。質問の傾向が間接的に入るだけ（弱い準該当）。
- EgoGPT（EgoLife、arXiv 2503.03803）: 一人称視点のデータで学習した、音声も扱うキャプション用のモデル。質問の傾向は使わない。

### 被引用

- Imprintを引用している論文: Semantic Scholarで0件（公開から約3か月）。
- SAVEMemを引用している8本、SVMemAgentを引用している1本（DeltaStreamer）: どれも該当しない。

## 限界

- Google Scholarの被引用とarXivの全文検索は使えなかった。Semantic Scholarが拾い漏らしている可能性がある。
- TaskMemの本文の後半（付録のプロンプトなど）は、一部しか確認できていない。
- 2026年10月の最新のプレプリントは、検索に出ていない可能性がある。
