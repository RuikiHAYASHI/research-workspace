---
date: 2026-10-14
project: agentic-streaming-videoqa
source_todo: "2026-10-14 2回目MTG: Memory保持以外の観点を2〜3個整理する（観点1：Agentの役割）"
topic: agent-role-classification-round1
status: exploratory
tags: [brainstorm, literature-review, agent, taxonomy, classification, task, streaming-videoqa]
---

# Agentの役割の分類：1回目の当てはめ（44本）

## 位置づけ

- 観点の優先度1位「Agentの役割」について、AGT分類（A〜G）を、Memory分類で扱った全44本に当てはめた1回目の結果。
  - 対象：[Memory分類の2回目当てはめ](2026-10-14-memory-classification-round2.md)の41本と、そこで「Memoryの定義外」とした3本（[VideoTree]★、[VideoAgent-Wang]★、[VideoINSTA]★）。この3本はAgent型の手法なので、Agentの観点では対象に含めた。
- 当てはめはAIが一次資料（arXiv HTML版、学会公式ページ、学会proceedings）を読んで行った。**林が原文で確認したものではない**。
- コードは、観点を表す接頭辞を付けて `AGT-A1` のように書く（Memory分類は `MEM-`）。表の中では接頭辞を省略する。
- 付け方の規則：
  - A（判断する対象）とC（判断の根拠）は複数のコードを付けてよい。B・D・E・F・Gは主なもの1つだけ。
  - A0（判断しない）の論文は、B〜Gを付けない（`—`）。
- 表記：
  - `★`：offlineの論文（動画全体を見られる設定）。
  - `?`：判定が境界にあるもの（第6節）。
  - 記述は「著者の主張」「実験で示されたこと」「私たちの推論（推論と明記）」「未確認」を区別する。
- 論文名のリンクは学会公式ページを優先し、無い場合はarXivとした。全論文の公式URLとarXivのURLは付録Aにまとめた。

### 「判断」として数えるもの（共通の前提）

「Agentを置くこと」と「Agentが実際に判断すること」は別、という区別（[重要な問いのメモ](2026-10-14-critical-literature-review-questions.md)のCritical 3）にもとづく。

- 数える：推論時に、モデル（LLM、VLM、学習した専用モジュール）が入力に応じて処理の分岐を選ぶこと。
- 数えない：類似度の閾値・FIFO・top-kなど、**固定の規則だけ**で決まるもの。
- 数えない：VLMやLLMが毎回必ずcaptionやnoteを書くこと（知覚・記述）。

## 1. 分類A：判断する対象（複数可）

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| A0 | 判断しない | 処理の流れが固定で、規則だけで動く | [Lando et al.], [Think While Watching]?, [StreamForest], [VideoLLaMB]★, [MuKV], [StreamMem], [Flash-VStream], [ProVideLLM], [Lando Edge], [MEMO], [LiveVLM], [StreamChat], [ReKV], [SAVEMem], [MovieChat], [MA-LMM], [QueryStream], [video-SALMONN S], [ProtoKV] | 19 |
| A1 | 観測 | どのframe・区間・解像度を見るか、追加で見に行くかを選ぶ | [StreamAgent], [EventMemAgent], [VideoAgent-Fan]★, [VideoMultiAgents]★, [OmAgent]★, [ReWind]★?, [TraveLER]★, [VideoTree]★, [VideoAgent-Wang]★, [CogStream]? | 10 |
| A2 | 書き込み | 何を残す／残さないか、何を記録するかを選ぶ | [OneStreamer], [SVMemAgent], [StreamArena], [Memento]?, [M3-Agent], [TraveLER]★ | 6 |
| A3 | 更新・削除 | 統合・書き直し・入れ替え・捨てるを選ぶ | [SVMemAgent], [Watch-Think-Interact], [Memento]?, [TraveLER]★ | 4 |
| A4 | 読み出し | 何を検索するか、どの記録・ツールで取り出すかを選ぶ | [EventMemAgent], [OASIS], [VideoAgent-Fan]★, [VideoMultiAgents]★, [Watch-Think-Interact], [VideoStreaming]?, [OmAgent]★, [CogStream], [StreamArena], [Memento]?, [M3-Agent], [VideoAgent-Wang]★, [VideoINSTA]★ | 13 |
| A5 | 回答のタイミング | 今答えるか黙るか、重いLLMを呼ぶかを選ぶ | [StreamAgent], [OneStreamer], [Response-G1], [Watch-Think-Interact], [ThinkStream], [StreamingVLM]?, [StreamMind], [R3-Streaming], [StreamArena], [Em-Garde]?, [Memento] | 11 |
| A6 | 計画 | 質問の分解、サブタスク・ツール使用の計画を作る | [StreamAgent], [VideoAgent-Fan]★, [OmAgent]★, [StreamArena], [Em-Garde], [M3-Agent], [TraveLER]★ | 7 |

備考：
- [CogStream]：「テキストだけで答えられるか」のflagで映像を入力しないことがあり、これを「映像を見るかどうか」の判断と読んでA1を付けた（推定）。
- [StreamAgent]：KVの取り出し（Selective Recall）はattentionの規則なので、A4に数えていない。
- [Em-Garde]：A6は、質問から「見つけるべき視覚手がかり」の候補文を作る処理を計画とみなしたもの（推定）。

## 2. 分類B：構成（A0以外の25本）

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| B1 | 1つのモデル | 回答と同じモデル、または単一のLLMが判断する | [OneStreamer], [EventMemAgent], [OASIS], [VideoAgent-Fan]★, [Response-G1], [Watch-Think-Interact], [ThinkStream], [StreamingVLM], [CogStream], [VideoTree]★, [VideoAgent-Wang]★, [VideoINSTA]★ | 12 |
| B2 | 複数のLLM Agent | 役割を分けた複数のLLMが判断する | [StreamAgent]?, [VideoMultiAgents]★, [OmAgent]★, [StreamArena], [Em-Garde], [M3-Agent], [TraveLER]★ | 7 |
| B3 | 専用の学習モジュール | 方策ネットやgateなど、判断専用に学習した部品 | [SVMemAgent], [VideoStreaming], [StreamMind], [ReWind]★ | 4 |
| B4 | 複合 | LLMと学習モジュールを組み合わせる | [R3-Streaming], [Memento] | 2 |

備考：
- [StreamAgent]：§3.1は「単一の軽量MLLM」と書くが、実装（§4.1）では計画用と対話用の2モデルを使う。
- [OmAgent]★：役割（Conqueror / Divider / Rescuer）は分かれているが、別々のLLMか同じLLMかは明記されていない（推定でB2）。
- [StreamArena]：役割の違う複数のworkerが、同じLLMのendpointを共有している（明記）。

## 3. 分類C：判断の根拠（複数可、A0以外の25本）

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| C1 | 現在の観測 | 今見ているframe・区間 | [StreamAgent], [OneStreamer], [EventMemAgent], [OASIS], [SVMemAgent], [Response-G1], [Watch-Think-Interact], [ThinkStream], [StreamingVLM], [StreamMind], [StreamArena], [Em-Garde], [Memento], [M3-Agent], [TraveLER]★, [VideoTree]★, [VideoINSTA]★ | 17 |
| C2 | Memory | 過去の記録 | [StreamAgent], [OneStreamer], [EventMemAgent], [OASIS], [SVMemAgent], [VideoAgent-Fan]★, [VideoMultiAgents]★, [Response-G1], [Watch-Think-Interact], [ThinkStream], [StreamingVLM], [VideoStreaming], [OmAgent]★, [CogStream], [R3-Streaming], [StreamArena], [Memento], [ReWind]★, [M3-Agent], [TraveLER]★, [VideoAgent-Wang]★ | 21 |
| C3 | 質問 | 実際の質問・指示 | [SVMemAgent]と[StreamingVLM]以外の23本 | 23 |
| C4 | 予測した未来 | これから起きることの予測 | [StreamAgent] | 1 |
| C5 | 確信度・自己評価 | 自分の答えや情報の十分さの評価 | [VideoMultiAgents]★, [R3-Streaming]?, [StreamArena], [TraveLER]★, [VideoAgent-Wang]★, [VideoINSTA]★ | 6 |

備考：
- [SVMemAgent]は質問を見ずに、何を残すかを決める（質問も未来のframeも見えない設定、明記）。
- [StreamMind]：現在のframeの特徴は状態空間モデルの状態なので、過去の情報も暗に含む。

## 4. 分類D〜G（A0以外の25本）

### 分類D：判断のタイミング

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| D1 | 毎frame | frameが届くたびに判断する | [SVMemAgent], [Response-G1], [StreamingVLM], [StreamMind], [Memento] | 5 |
| D2 | 一定間隔 | clipごと・数秒ごとに判断する | [StreamAgent], [OneStreamer], [Watch-Think-Interact], [ThinkStream] | 4 |
| D3 | 切れ目・容量超過時 | イベントの切れ目や、容量を超えたときに判断する | （主なタイミングとしては該当なし） | 0 |
| D4 | 質問時のみ | 質問が届いたとき・回答するときだけ判断する | [EventMemAgent], [OASIS], [VideoAgent-Fan]★, [VideoMultiAgents]★, [VideoStreaming], [OmAgent]★, [CogStream], [Em-Garde], [ReWind]★, [TraveLER]★, [VideoTree]★, [VideoAgent-Wang]★, [VideoINSTA]★ | 13 |
| D5 | 複合 | 書き込みは一定間隔、検索は質問時など、判断ごとにタイミングが違う | [R3-Streaming], [StreamArena], [M3-Agent] | 3 |

備考：[Watch-Think-Interact]はMemoryの書き直しだけ区切りごと（D3）に行う。

### 分類E：行動の形式

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| E1 | 決まった選択肢 | 離散のaction・特殊token・段階評価 | [OneStreamer], [Response-G1], [Watch-Think-Interact], [ThinkStream], [StreamingVLM], [CogStream], [StreamMind], [R3-Streaming], [Memento], [VideoTree]★, [VideoINSTA]★ | 11 |
| E2 | ツール呼び出し | ツールの選択と引数 | [EventMemAgent], [OASIS], [VideoAgent-Fan]★, [VideoMultiAgents]★, [OmAgent]★, [StreamArena], [M3-Agent] | 7 |
| E3 | 自由な文章 | 計画文・検索クエリ文・候補文 | [StreamAgent], [Em-Garde], [TraveLER]★, [VideoAgent-Wang]★ | 4 |
| E4 | 数値 | スコア・確率・重みにtop-kや閾値をかける | [SVMemAgent], [VideoStreaming], [ReWind]★ | 3 |

### 分類F：繰り返し

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| F0 | 1回で終わる | 判断は1回で、やり直さない | [OneStreamer], [SVMemAgent], [Response-G1], [ThinkStream], [StreamingVLM], [VideoStreaming], [CogStream], [StreamMind], [R3-Streaming], [Em-Garde], [Memento], [ReWind]★ | 12 |
| F1 | 足りなければ追加 | 情報が足りなければ、追加で観測・検索する | [StreamAgent], [EventMemAgent], [OASIS], [VideoAgent-Fan]★, [VideoMultiAgents]★, [Watch-Think-Interact], [OmAgent]★, [StreamArena], [M3-Agent], [TraveLER]★, [VideoTree]★, [VideoAgent-Wang]★, [VideoINSTA]★ | 13 |
| F2 | 自分で検証して直す | 自分の答えや計画を検証して直す | （該当なし） | 0 |

備考：[TraveLER]★のEvaluatorは計画どおり進んだかも検査するのでF2の要素もあるが、主な働きは追加の観測なのでF1にした。

### 分類G：判断部分の学習

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| G0 | 学習なし | promptや既存モデルだけで判断する | [StreamAgent], [OASIS], [VideoAgent-Fan]★, [VideoMultiAgents]★, [Response-G1], [OmAgent]★, [StreamArena], [TraveLER]★, [VideoTree]★, [VideoAgent-Wang]★, [VideoINSTA]★ | 11 |
| G1 | 教師あり学習 | SFTなどで判断を学習する | [OneStreamer], [StreamingVLM], [VideoStreaming], [CogStream], [StreamMind], [Memento], [ReWind]★ | 7 |
| G2 | 強化学習 | 強化学習で判断を学習する（SFTの後にRLを含む） | [EventMemAgent], [SVMemAgent], [Watch-Think-Interact], [ThinkStream], [R3-Streaming], [Em-Garde], [M3-Agent] | 7 |

## 5. タスク別の論文（全44本）

論文が評価に使ったタスクで分けた。1本の論文が複数のタスクに入る。

| コード | タスク | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| T1 | 多肢選択VQA | 選択肢から答えを選ぶ質問応答 | [StreamAgent], [OneStreamer], [Lando et al.], [Think While Watching], [StreamForest], [EventMemAgent], [OASIS], [VideoLLaMB]★, [MuKV], [StreamMem], [Flash-VStream], [SVMemAgent], [VideoAgent-Fan]★, [VideoMultiAgents]★, [Response-G1], [Lando Edge], [Watch-Think-Interact], [ThinkStream], [MEMO], [StreamingVLM], [LiveVLM], [VideoStreaming], [ReKV], [SAVEMem], [OmAgent]★, [R3-Streaming], [Em-Garde], [QueryStream], [M3-Agent], [video-SALMONN S], [ProtoKV], [TraveLER]★, [VideoTree]★, [VideoAgent-Wang]★, [VideoINSTA]★ | 35 |
| T2 | 自由記述VQA | 文章で答え、GPTなどで採点する質問応答 | [StreamAgent], [OASIS], [MuKV], [StreamMem], [SVMemAgent]?, [VideoAgent-Fan]★, [LiveVLM], [StreamChat], [VideoStreaming], [ReKV], [MovieChat], [MA-LMM], [CogStream], [StreamArena], [Memento], [ReWind]★, [M3-Agent], [ProtoKV], [VideoINSTA]★ | 19 |
| T3 | リアルタイム・能動的応答 | いつ答えるかを含めて評価する（OVO-BenchのForward Active Respondingなど） | [StreamAgent]?, [OneStreamer], [Think While Watching], [StreamForest]?, [EventMemAgent]?, [Response-G1], [Watch-Think-Interact], [StreamMind], [R3-Streaming], [StreamArena], [Em-Garde], [Memento], [QueryStream]? | 13 |
| T4 | 複数ターンの対話 | 同じ動画について続けて質問する | [Think While Watching], [ProVideLLM]（補助）, [StreamChat], [CogStream], [StreamArena] | 5 |
| T5 | 行動予測・手順理解 | 次の行動や手順を予測・認識する | [VideoLLaMB]★, [ProVideLLM], [MA-LMM], [StreamMind] | 4 |
| T6 | 実況・キャプション生成 | 動画の説明文や実況を生成する | [VideoLLaMB]★（定性評価のみ）, [ProVideLLM]（補助）, [StreamingVLM], [MA-LMM], [StreamMind] | 5 |
| T7 | 時間的grounding | 質問に対応する区間を答える | [VideoAgent-Fan]★, [VideoStreaming], [OmAgent]★, [ReWind]★ | 4 |
| T8 | その他 | 上記以外 | [VideoLLaMB]★（長い映像に埋めた情報を探すNIAVH）, [MA-LMM]（長期動画の分類）, [OmAgent]★（コード生成・知識QA）, [StreamArena]（外部検索を使う質問） | 4 |

備考：
- T3の`?`は、OVO-BenchのForward Active Respondingを含むことからの推定。[SAVEMem]と[ThinkStream]はForwardを評価していないので、T3に入れていない。
- [Think While Watching]は、StreamingBenchとOVO-Benchを単一ターンと複数ターンの両方で評価している。

### 参考：主なベンチマーク別の論文

| ベンチマーク | 該当論文 | 本数 |
| --- | --- | --- |
| StreamingBench | [StreamAgent], [OneStreamer], [Think While Watching], [StreamForest], [EventMemAgent], [OASIS], [MuKV], [Response-G1], [Watch-Think-Interact], [ThinkStream], [MEMO], [LiveVLM], [SAVEMem], [R3-Streaming], [Em-Garde], [QueryStream], [video-SALMONN S], [ProtoKV] | 18 |
| Video-MME | [StreamAgent], [StreamForest], [VideoLLaMB]★, [MuKV], [StreamMem], [Flash-VStream], [SVMemAgent], [Watch-Think-Interact], [ThinkStream], [StreamingVLM], [LiveVLM], [R3-Streaming], [QueryStream], [M3-Agent]（long）, [video-SALMONN S], [ProtoKV], [VideoTree]★ | 17 |
| OVO-Bench | [StreamAgent], [OneStreamer], [Think While Watching], [StreamForest], [EventMemAgent], [OASIS], [Response-G1], [Watch-Think-Interact], [ThinkStream], [MEMO], [StreamingVLM], [SAVEMem], [R3-Streaming], [Em-Garde], [QueryStream], [ProtoKV] | 16 |
| EgoSchema | [StreamAgent], [VideoLLaMB]★, [MuKV], [StreamMem], [Flash-VStream], [SVMemAgent], [VideoAgent-Fan]★, [VideoMultiAgents]★, [VideoStreaming], [ReKV], [TraveLER]★, [VideoTree]★, [VideoAgent-Wang]★, [VideoINSTA]★ | 14 |
| MLVU | [StreamAgent], [StreamForest], [MuKV], [StreamMem], [Flash-VStream], [Watch-Think-Interact], [LiveVLM], [ReKV], [R3-Streaming], [ProtoKV], [VideoTree]★ | 11 |
| LongVideoBench（私たちのbaselineで使用中） | [StreamAgent], [SVMemAgent], [Watch-Think-Interact], [ThinkStream], [StreamingVLM], [LiveVLM], [QueryStream] | 7 |
| RVS-Ego / RVS-Movie | [StreamAgent], [MuKV], [StreamMem], [SVMemAgent]（RVS-Egoのみ）, [LiveVLM], [ReKV], [ProtoKV] | 7 |
| QAEgo4D | [Lando et al.], [Lando Edge], [ReKV] | 3 |

## 6. 境界例（方針を決めたい点）

今回は次の方針で判定した。変えると、該当する論文のコードが変わる。

| # | 迷った点 | 今回の扱い | 該当論文 |
| --- | --- | --- | --- |
| K1 | 学習したモジュールのスコアに、固定のtop-kや閾値をかけて選ぶ | 判断あり（`?`付き） | [VideoStreaming], [ReWind]★, [Memento] |
| K2 | 既存モデルのattentionやCLIP類似度に、固定のtop-kや閾値をかけて選ぶ | 判断なし（A0） | [ReKV], [video-SALMONN S], [QueryStream], [MuKV] |
| K3 | 毎回必ず書くnote・推論文・要約の中身 | 記述として判断に数えない（A0、またはA2を付けない） | [Think While Watching]（数えるならA2 / B1 / C1 / D2 / E3 / F0 / G1）, [ThinkStream], [OASIS]（統合後の要約） |
| K4 | 判断用の部品はなく、学習で「黙る」出力を身につけただけ | A5（`?`付き） | [StreamingVLM] |
| K5 | 「答えるか、もっと探すか」の選択 | A5ではなくF1として扱う | [OASIS], [M3-Agent], [VideoAgent-Wang]★ |
| K6 | 応答を固定規則で発火させた後、別のモデルが応答してよいか検証する | A5（`?`付き） | [Em-Garde] |

- 応答の主な仕組みが書かれていない論文は、A5を付けなかった：[ProVideLLM]（§4.4に「黙るよう学習」とあるだけ。厳しめに数えるならA5 / B1 / G1）。

## 7. 当てはめから見えたこと（私たちの推論）

1. **44本中19本はAgentの判断を持たない（A0）。** KVや視覚特徴のMemoryを圧縮する論文の多くはここに入る。Memoryの研究とAgentの研究は、かなりの部分で別の流れになっている。
2. **Agentが判断するのは「読み出し」（13本）と「回答のタイミング」（11本）が多い。** 「何を書き込むか」（A2：6本）と「どう更新・削除するか」（A3：4本）をモデルが判断する論文は少ない。
   - streamingでLLMが書き込みを判断するのは、[StreamArena]、[M3-Agent]、[OneStreamer]、[Memento]?。[SVMemAgent]は学習した方策で判断する。
   - 私たちの関心である「Memoryに何を残すかをAgentが決める」は、比較的少ない領域と言える（今回の44本の範囲で）。
3. **予測した未来を判断の根拠にする（C4）のは[StreamAgent]だけ。** 観点2「先読み・予習」と直接つながる。先読みを観測や回答以外（例えば書き込み）に使う論文は、今回の範囲では見つからなかった（未確認）。
4. **offlineとstreamingで判断の作り方が違う。**
   - offline★の論文はほとんどが「質問を受けてから（D4）、ツールを呼び（E2）、足りなければ探し直す（F1）」形で、学習なし（G0）。
   - streamingの論文は「毎frameか一定間隔で（D1・D2）、特殊tokenで（E1）」判断する形が多く、学習して身につける（G1・G2）。強化学習の7本はすべてstreaming。
5. **自分で検証して直す（F2）論文は0本。** 判断を繰り返す論文はあるが、どれも「足りなければ追加で見る」形だった。
6. **私たちの3-Agent baseline（Situation → Summary → Answer）の位置**：役割を分けた複数Agent（B2）の構成だが、処理の流れは固定で、Summaryは毎回必ず書き直す。今回の基準ではA0に近い（K3と同じ扱い）。「何を残すか」をAgentに判断させれば、A2・A3に入る。
7. **タスクは多肢選択VQA（T1：35本）に偏っている。** 質問を最初から知っているstreaming論文（[Em-Garde]、[QueryStream]）は、どちらもT3（能動的応答）で評価している。私たちのLongVideoBenchを使った論文は7本。

## 8. 未確認・要確認

- [SVMemAgent]、[StreamMem]：OpenReviewのページがbot認証で開けず、URLが同じ論文を指すかを確認できなかった。ブラウザで手動確認する。arXivのURLは付録Aにある。
- [QueryStream]：本文を読めていない（OpenReviewが開けなかった）。手法の閾値などは、公式GitHubのREADMEと第三者の論文解説ページによる判定（推定）。
- [OneStreamer]、[Think While Watching]、[CogStream]：本文の末尾（約1割）を読めていない。
- [Em-Garde]：応答するモデル（responder）のモデル名と判断方法が書かれていない。HTML版の「ICML」表記がテンプレート由来かどうかも未確認。
- [Memento]：付録の「dynamic correction strategy」を読めていない。gateの学習方法（end-to-endか）が明記されていない。
- [Watch-Think-Interact]：題名に「Multi-Turn」とあるが、複数ターンのベンチマークは確認できなかった（T4は付けていない）。
- [SVMemAgent]のRVS-Egoが自由記述かどうか（T2の`?`）。
- 論文中の不整合（参考）：[MuKV]はk_gの値が本文中で2通りある。[VideoStreaming]は学習サンプル数が§3.4と付録Aで食い違う。[MovieChat]は注釈数がabstractと本文で食い違う。

## 9. Memory分類のメモへの反映候補（未反映）

今回の確認で、次の点がMemory分類のメモ（1回目・2回目）と食い違っている。反映するかはユーザーと決める。

- 発表先の確認：[ProtoKV]はICML 2026の公式ページが見つかった。[TraveLER]★はEMNLP 2024（Main）の公式ページが見つかった。[QueryStream]はICLR 2026の公式ページが見つかった。
- リンクの修正：[VideoStreaming]と[ReKV]はPDFへの直リンクだったので、Abstractページに変えた。
- 処理設定の注記：[VideoLLaMB]★は構造がstreaming型で、評価はoffline。[Flash-VStream]、[VideoStreaming]、[MovieChat]は逐次に処理するが、評価や回答は動画を最後まで見てから行う。
- 名前の衝突：[StreamArena]が提案するAgentも「StreamMind」という名前で、ICCV 2025の[StreamMind]とは別物。
- 2回目メモのリンク崩れ：`[MovieChat][新]`のように、リンクの直後に`[新]`を続けて書いたため、Markdownが「新」という名前のリンク定義を探してしまい、リンクにならなかった。

## 付録A：論文の公式URLとarXiv

「確認」の列は、今回URLを開いて題名が一致したかどうか。

| 論文 | 正式な題名（略称と違う場合） | 発表先 | 公式ページ | arXiv | 確認 |
| --- | --- | --- | --- | --- | --- |
| [StreamAgent] | StreamAgent: Towards Anticipatory Agents for Streaming Video Understanding | arXiv（採録未確認） | — | [2508.01875](https://arxiv.org/abs/2508.01875) | OK |
| [OneStreamer] | — | arXiv（採録未確認） | — | [2610.01762](https://arxiv.org/abs/2610.01762) | OK |
| [Lando et al.] | How Far Can Off-the-Shelf Multimodal Large Language Models Go in Online Episodic Memory Question Answering? | ICIAP 2025（著者ページの記載のみ） | — | [2506.16450](https://arxiv.org/abs/2506.16450) | OK |
| [Think While Watching] | — | arXiv（採録未確認） | — | [2603.11896](https://arxiv.org/abs/2603.11896) | OK |
| [StreamForest] | — | NeurIPS 2025 | [NeurIPS](https://papers.neurips.cc/paper_files/paper/2025/hash/6dd91fec726dbed8915a1fbadd91d1d2-Abstract-Conference.html) | [2509.24871](https://arxiv.org/abs/2509.24871) | OK |
| [EventMemAgent] | — | arXiv（採録未確認） | — | [2602.15329](https://arxiv.org/abs/2602.15329) | OK |
| [OASIS] | — | CVPR 2026 | [CVF](https://openaccess.thecvf.com/content/CVPR2026/html/Liang_OASIS_On-Demand_Hierarchical_Event_Memory_for_Streaming_Video_Reasoning_CVPR_2026_paper.html) | [2604.17052](https://arxiv.org/abs/2604.17052) | OK |
| [VideoLLaMB]★ | Long Streaming Video Understanding with Recurrent Memory Bridges | ICCV 2025 | [CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Wang_VideoLLaMB_Long_Streaming_Video_Understanding_with_Recurrent_Memory_Bridges_ICCV_2025_paper.html) | [2409.01071](https://arxiv.org/abs/2409.01071) | OK |
| [MuKV] | — | CVPR 2026 | [CVF](https://openaccess.thecvf.com/content/CVPR2026/html/Xiao_MuKV_Multi-Grained_KV_Cache_Compression_for_Long_Streaming_Video_Question-Answering_CVPR_2026_paper.html) | [2605.22269](https://arxiv.org/abs/2605.22269) | OK |
| [StreamMem] | — | CVPR 2026 Workshop | [OpenReview](https://openreview.net/forum?id=siAEqckmUs) | [2508.15717](https://arxiv.org/abs/2508.15717) | OpenReviewは開けず未確認 |
| [Flash-VStream] | — | ICCV 2025 | [CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Zhang_Flash-VStream_Efficient_Real-Time_Understanding_for_Long_Video_Streams_ICCV_2025_paper.html) | [2506.23825](https://arxiv.org/abs/2506.23825) | OK |
| [SVMemAgent] | — | ECCV 2026 Workshop | [OpenReview](https://openreview.net/forum?id=E0LVxLc5Pw) | [2609.18540](https://arxiv.org/abs/2609.18540) | OpenReviewは開けず未確認 |
| [VideoAgent-Fan]★ | VideoAgent: A Memory-augmented Multimodal Agent for Video Understanding（Fan et al.） | ECCV 2024 | [ECVA](https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/3241_ECCV_2024_paper.php) | [2403.11481](https://arxiv.org/abs/2403.11481) | OK |
| [VideoMultiAgents]★ | — | arXiv（採録未確認） | — | [2504.20091](https://arxiv.org/abs/2504.20091) | OK |
| [Response-G1] | — | ACL 2026（Long） | [ACL Anthology](https://aclanthology.org/2026.acl-long.2042/) | [2605.07575](https://arxiv.org/abs/2605.07575) | OK |
| [ProVideLLM] | Streaming VideoLLMs for Real-Time Procedural Video Understanding | ICCV 2025 | [CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Chatterjee_Streaming_VideoLLMs_for_Real-Time_Procedural_Video_Understanding_ICCV_2025_paper.html) | [2504.13915](https://arxiv.org/abs/2504.13915) | OK |
| [Lando Edge] | Exploring Multimodal LMMs for Online Episodic Memory Question Answering on the Edge | VISAPP 2026（研究室ページの記載のみ） | — | [2602.22455](https://arxiv.org/abs/2602.22455) | OK |
| [Watch-Think-Interact] | — | arXiv（採録未確認） | — | [2609.37035](https://arxiv.org/abs/2609.37035) | OK |
| [ThinkStream] | Thinking in Streaming Video | arXiv（採録未確認） | — | [2603.12938](https://arxiv.org/abs/2603.12938) | OK |
| [MEMO] | MEMO: Multi-Level Entity-Aware Memory for Streaming Video Understanding | ACM MM 2026（arXivのコメントのみ） | — | [2609.38900](https://arxiv.org/abs/2609.38900) | OK |
| [StreamingVLM] | — | ICLR 2026 | [ICLR](https://iclr.cc/virtual/2026/poster/10008145) | [2510.09608](https://arxiv.org/abs/2510.09608) | OK |
| [LiveVLM] | — | arXiv（本文にDAC '26の記載） | — | [2505.15269](https://arxiv.org/abs/2505.15269) | OK |
| [StreamChat] | Streaming Video Understanding and Multi-round Interaction with Memory-enhanced Knowledge | ICLR 2025 | [ICLR](https://proceedings.iclr.cc/paper_files/paper/2025/hash/ad2fa437f7c23e4e9875599c6065d18a-Abstract-Conference.html) | [2501.13468](https://arxiv.org/abs/2501.13468) | OK |
| [VideoStreaming] | Streaming Long Video Understanding with Large Language Models | NeurIPS 2024 | [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2024/hash/d7ce06e9293c3d8e6cb3f80b4157f875-Abstract-Conference.html) | [2405.16009](https://arxiv.org/abs/2405.16009) | OK（PDF直リンクから変更） |
| [ReKV] | Streaming Video Question-Answering with In-context Video KV-Cache Retrieval | ICLR 2025 | [ICLR](https://proceedings.iclr.cc/paper_files/paper/2025/hash/67a9b444cbcd647572c88194619f72d5-Abstract-Conference.html) | [2503.00540](https://arxiv.org/abs/2503.00540) | OK（PDF直リンクから変更） |
| [SAVEMem] | Semantic-Aware Adaptive Visual Memory for Streaming Video Understanding | arXiv（採録未確認） | — | [2605.07897](https://arxiv.org/abs/2605.07897) | OK |
| [MovieChat] | — | CVPR 2024 | [CVF](https://openaccess.thecvf.com/content/CVPR2024/html/Song_MovieChat_From_Dense_Token_to_Sparse_Memory_for_Long_Video_CVPR_2024_paper.html) | [2307.16449](https://arxiv.org/abs/2307.16449) | OK |
| [MA-LMM] | — | CVPR 2024 | [CVF](https://openaccess.thecvf.com/content/CVPR2024/html/He_MA-LMM_Memory-Augmented_Large_Multimodal_Model_for_Long-Term_Video_Understanding_CVPR_2024_paper.html) | [2404.05726](https://arxiv.org/abs/2404.05726) | OK |
| [OmAgent]★ | — | EMNLP 2024 | [ACL Anthology](https://aclanthology.org/2024.emnlp-main.559/) | [2406.16620](https://arxiv.org/abs/2406.16620) | OK |
| [CogStream] | CogStream: Context-guided Streaming Video Question Answering | AAAI 2026 | [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/38336) | [2506.10516](https://arxiv.org/abs/2506.10516) | OK |
| [StreamMind] | StreamMind: Unlocking Full Frame Rate Streaming Video Dialogue through Event-Gated Cognition | ICCV 2025 | [CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Ding_StreamMind_Unlocking_Full_Frame_Rate_Streaming_Video_Dialogue_through_Event-Gated_ICCV_2025_paper.html) | [2503.06220](https://arxiv.org/abs/2503.06220) | OK |
| [R3-Streaming] | An Efficient Streaming Video Understanding Framework with Agentic Control | arXiv（採録未確認） | — | [2605.17921](https://arxiv.org/abs/2605.17921) | OK |
| [StreamArena] | StreamArena: Toward Continuous, Interactive, and Long-Horizon Agentic Streaming Video Understanding | arXiv（採録未確認） | — | [2608.05703](https://arxiv.org/abs/2608.05703) | OK |
| [Em-Garde] | — | arXiv（採録未確認） | — | [2603.19054](https://arxiv.org/abs/2603.19054) | OK |
| [Memento] | — | ICLR 2026 | [ICLR](https://proceedings.iclr.cc/paper_files/paper/2026/hash/3b5f4587a0bdb81ecc6ce9d82320a5c2-Abstract-Conference.html) | 見つからず | OK |
| [QueryStream] | — | ICLR 2026 | [ICLR](https://iclr.cc/virtual/2026/poster/10011335) | 見つからず（[OpenReview](https://openreview.net/forum?id=738HjJEbml)） | OK（OpenReviewから変更） |
| [ReWind]★ | — | CVPR 2025 | [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Diko_ReWind_Understanding_Long_Videos_with_Instructed_Learnable_Memory_CVPR_2025_paper.html) | [2411.15556](https://arxiv.org/abs/2411.15556) | OK |
| [M3-Agent] | Seeing, Listening, Remembering, and Reasoning: A Multimodal Agent with Long-Term Memory | ICLR 2026 | [ICLR](https://iclr.cc/virtual/2026/poster/10009685) | [2508.09736](https://arxiv.org/abs/2508.09736) | OK |
| [video-SALMONN S] | — | ICML 2026 | [ICML](https://icml.cc/virtual/2026/poster/61140) | [2510.11129](https://arxiv.org/abs/2510.11129) | OK |
| [ProtoKV] | — | ICML 2026 | [ICML](https://icml.cc/virtual/2026/poster/63663) | [2606.26762](https://arxiv.org/abs/2606.26762) | OK（arXivから変更） |
| [TraveLER]★ | — | EMNLP 2024 | [ACL Anthology](https://aclanthology.org/2024.emnlp-main.544/) | [2404.01476](https://arxiv.org/abs/2404.01476) | OK（arXivから変更） |
| [VideoTree]★ | — | CVPR 2025 | [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Wang_VideoTree_Adaptive_Tree-based_Video_Representation_for_LLM_Reasoning_on_Long_CVPR_2025_paper.html) | [2405.19209](https://arxiv.org/abs/2405.19209) | OK |
| [VideoAgent-Wang]★ | VideoAgent: Long-form Video Understanding with Large Language Model as Agent（Wang et al.） | ECCV 2024 | [ECVA](https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/10325_ECCV_2024_paper.php) | [2403.10517](https://arxiv.org/abs/2403.10517) | OK |
| [VideoINSTA]★ | — | Findings of EMNLP 2024 | [ACL Anthology](https://aclanthology.org/2024.findings-emnlp.384/) | [2409.20365](https://arxiv.org/abs/2409.20365) | OK |

- CVFのページはWebFetchでは開けなかったが、curlで開いて題名・著者が一致した。

## 付録B：判断がある25本の判定根拠（要点）

- **[StreamAgent]**：toolで入力frameの一部を切り出す・追跡する（A1、Eq.3）。決定関数で「待つか答えるか」を選ぶ（A5）。3つの見通し（直後・少し先・遠い先）から計画候補を作って1つ選ぶ（A6、Eq.2）。予測した未来の出来事を根拠に使う（C4）。
- **[OneStreamer]**：制御tokenで、captionを書く・出来事の要約を書く（A2）、黙る・保留する・答える（A5）を選ぶ。SFTのみ。
- **[EventMemAgent]**：情報が足りないときだけ、Agentが時間・意味の検索を呼ぶ（A4）。OCRや物体検出で追加で見る（A1）。ReAct形式。GRPOで学習し、報酬は最終回答の正誤。
- **[OASIS]**：粗い推論で直接答えるか、検索するかを選ぶ（A4）。検索は最大1回（F1）。学習なし。
- **[SVMemAgent]**：新しいframeごとに、捨てるか、Memoryの枠（16枠）のどれと入れ替えるかを方策が選ぶ（A2・A3）。質問は使わない。SFTの後にGRPO。
- **[VideoAgent-Fan]★**：GPT-4がツール（caption検索・区間の特定・VQA・物体Memoryの検索）を選び、質問を分解する（A1・A4・A6）。Memoryは決まった処理で作る。
- **[VideoMultiAgents]★**：Text・Video・GraphのAgentが、それぞれツールを繰り返し呼ぶ（A1・A4）。Organizerが答えをまとめる。
- **[Response-G1]**：質問の後、毎時刻に「黙る／答える」をYes / Noのtokenで選ぶ（A5）。scene graphの検索は類似度top-Kの規則。
- **[Watch-Think-Interact]**：区間ごとに「黙る／答える／過去の映像を呼び出す」を選ぶ（A4・A5）。区切りごとにテキストMemoryを書き直す（A3）。呼び出した後、同じ時刻でもう一度判断する（F1）。SFTの後にRL。
- **[ThinkStream]**：区間ごとに推論文の後、黙るか答えるかを特殊tokenで出す（A5）。推論文を残す仕組みは固定の規則。SFTの後にGRPO。
- **[StreamingVLM]**：実況のない秒に「...」を入れて学習し、いつ話すかを身につける（A5?、K4）。KV cacheは固定の規則。
- **[VideoStreaming]**：質問から作った指標と各clipの指標の類似度で、clipのMemoryを選ぶ（A4?、K1）。指標は学習済み。
- **[OmAgent]★**：課題を分類して部分課題の木に分解する（A6）。ツールを選び、元の動画の区間を見直す（A1・A4）。
- **[CogStream]**：LLMが、現在の質問に関連する過去のQAを選ぶ（A4）。同時に「テキストだけで答えられるか」のflagを出す（A1?）。検索用のLoRAをSFT。
- **[StreamMind]**：専用のgateが毎frame、LLMを呼ぶか（答えるか）を特殊tokenで決める（A5、B3）。
- **[R3-Streaming]**：readinessの部品が答えるか保留するかを決め、速いVLMが重いモデルへ回すかを決める（A5）。Memoryの管理は規則。SFTの後にRL。
- **[StreamArena]**：Memory Writer（LLM）が4秒ごとにイベントの境界と記録を出す（A2）。Routerが検索ツールを選び、部分課題に分ける（A4・A6）。Front WorkerとMonitorが答えるタイミングを決める（A5）。学習なし。
- **[Em-Garde]**：質問から「見つけるべき視覚手がかり」の候補文を作る（A6）。発火は固定規則で、その後の応答を別のモデルが検証する（A5?、K6）。SFTの後にGRPO。
- **[Memento]**：gateが「直前の記録に統合／全体を更新／新しく追加」を選ぶ（A2?・A3?、K1）。質問との関連度で記録を選ぶ（A4?）。frameごとに黙るか答えるかを出す（A5）。
- **[ReWind]★**：全体を処理した後、指示文とMemoryのattentionで見直すframeを選び、高解像度で見る（A1?、K1）。
- **[M3-Agent]**：記憶用のMLLMがclipごとに何を書くかを生成する（A2）。制御用の方策が検索文を書き、検索ツールを選ぶ（A4）。最大5回まで繰り返す（F1）。記憶用はSFT、制御用はRL。
- **[TraveLER]★**：Plannerが計画を作り、Retrieverが次に見る時刻を選び、Extractorが質問を作って答えを記録し、Summarizerが記録を書き直す（A1・A2・A3・A6）。Evaluatorが情報の十分さを評価する（C5）。
- **[VideoTree]★**：LLMが各クラスタと質問の関連度を1〜3で採点し、それに応じて深く分けて追加のframeを見る（A1）。
- **[VideoAgent-Wang]★**：LLMがどの区間を探すかを選び、検索文を書いてCLIPでframeを取り出す（A1・A4）。確信度が足りなければ追加で探す（F1）。
- **[VideoINSTA]★**：LLMが各イベントの情報量を採点し、上位から使う（A4）。確信度が最高でなければ次のclipを足して答え直す（F1）。

## 修正履歴

| 日時 | 変更 | 理由 |
| --- | --- | --- |
| 2026-10-14 | 初版作成：AGT分類（A〜G）を44本に当てはめ、タスク別・ベンチマーク別の表と公式URLの一覧を作った | ユーザー指示（全論文を今の分類案で分類し、offlineに★、URLを確実に載せ、タスク別の表を別枠で作る） |

## 関連文書

- [Memory分類の判定基準](2026-10-14-memory-retention-classification-criteria.md)
- [Memory分類の1回目当てはめ](2026-10-14-memory-classification-round1.md)
- [Memory分類の2回目当てはめ](2026-10-14-memory-classification-round2.md)
- [文献調査の重要な問い](2026-10-14-critical-literature-review-questions.md)
- [2026-10-14 MTG議事録（2回目）](../../../lab/projects/agentic-streaming-videoqa/meetings/2026-10-14-second-mtg.md)

[StreamAgent]: https://arxiv.org/abs/2508.01875
[OneStreamer]: https://arxiv.org/abs/2610.01762
[Lando et al.]: https://arxiv.org/abs/2506.16450
[Think While Watching]: https://arxiv.org/abs/2603.11896
[StreamForest]: https://papers.neurips.cc/paper_files/paper/2025/hash/6dd91fec726dbed8915a1fbadd91d1d2-Abstract-Conference.html
[EventMemAgent]: https://arxiv.org/abs/2602.15329
[OASIS]: https://openaccess.thecvf.com/content/CVPR2026/html/Liang_OASIS_On-Demand_Hierarchical_Event_Memory_for_Streaming_Video_Reasoning_CVPR_2026_paper.html
[VideoLLaMB]: https://openaccess.thecvf.com/content/ICCV2025/html/Wang_VideoLLaMB_Long_Streaming_Video_Understanding_with_Recurrent_Memory_Bridges_ICCV_2025_paper.html
[MuKV]: https://openaccess.thecvf.com/content/CVPR2026/html/Xiao_MuKV_Multi-Grained_KV_Cache_Compression_for_Long_Streaming_Video_Question-Answering_CVPR_2026_paper.html
[StreamMem]: https://openreview.net/forum?id=siAEqckmUs
[Flash-VStream]: https://openaccess.thecvf.com/content/ICCV2025/html/Zhang_Flash-VStream_Efficient_Real-Time_Understanding_for_Long_Video_Streams_ICCV_2025_paper.html
[SVMemAgent]: https://openreview.net/forum?id=E0LVxLc5Pw
[VideoAgent-Fan]: https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/3241_ECCV_2024_paper.php
[VideoMultiAgents]: https://arxiv.org/abs/2504.20091
[Response-G1]: https://aclanthology.org/2026.acl-long.2042/
[ProVideLLM]: https://openaccess.thecvf.com/content/ICCV2025/html/Chatterjee_Streaming_VideoLLMs_for_Real-Time_Procedural_Video_Understanding_ICCV_2025_paper.html
[Lando Edge]: https://arxiv.org/abs/2602.22455
[Watch-Think-Interact]: https://arxiv.org/abs/2609.37035
[ThinkStream]: https://arxiv.org/abs/2603.12938
[MEMO]: https://arxiv.org/abs/2609.38900
[StreamingVLM]: https://iclr.cc/virtual/2026/poster/10008145
[LiveVLM]: https://arxiv.org/abs/2505.15269
[StreamChat]: https://proceedings.iclr.cc/paper_files/paper/2025/hash/ad2fa437f7c23e4e9875599c6065d18a-Abstract-Conference.html
[VideoStreaming]: https://proceedings.neurips.cc/paper_files/paper/2024/hash/d7ce06e9293c3d8e6cb3f80b4157f875-Abstract-Conference.html
[ReKV]: https://proceedings.iclr.cc/paper_files/paper/2025/hash/67a9b444cbcd647572c88194619f72d5-Abstract-Conference.html
[SAVEMem]: https://arxiv.org/abs/2605.07897
[MovieChat]: https://openaccess.thecvf.com/content/CVPR2024/html/Song_MovieChat_From_Dense_Token_to_Sparse_Memory_for_Long_Video_CVPR_2024_paper.html
[MA-LMM]: https://openaccess.thecvf.com/content/CVPR2024/html/He_MA-LMM_Memory-Augmented_Large_Multimodal_Model_for_Long-Term_Video_Understanding_CVPR_2024_paper.html
[OmAgent]: https://aclanthology.org/2024.emnlp-main.559/
[CogStream]: https://ojs.aaai.org/index.php/AAAI/article/view/38336
[StreamMind]: https://openaccess.thecvf.com/content/ICCV2025/html/Ding_StreamMind_Unlocking_Full_Frame_Rate_Streaming_Video_Dialogue_through_Event-Gated_ICCV_2025_paper.html
[R3-Streaming]: https://arxiv.org/abs/2605.17921
[StreamArena]: https://arxiv.org/abs/2608.05703
[Em-Garde]: https://arxiv.org/abs/2603.19054
[Memento]: https://proceedings.iclr.cc/paper_files/paper/2026/hash/3b5f4587a0bdb81ecc6ce9d82320a5c2-Abstract-Conference.html
[QueryStream]: https://iclr.cc/virtual/2026/poster/10011335
[ReWind]: https://openaccess.thecvf.com/content/CVPR2025/html/Diko_ReWind_Understanding_Long_Videos_with_Instructed_Learnable_Memory_CVPR_2025_paper.html
[M3-Agent]: https://iclr.cc/virtual/2026/poster/10009685
[video-SALMONN S]: https://icml.cc/virtual/2026/poster/61140
[ProtoKV]: https://icml.cc/virtual/2026/poster/63663
[TraveLER]: https://aclanthology.org/2024.emnlp-main.544/
[VideoTree]: https://openaccess.thecvf.com/content/CVPR2025/html/Wang_VideoTree_Adaptive_Tree-based_Video_Representation_for_LLM_Reasoning_on_Long_CVPR_2025_paper.html
[VideoAgent-Wang]: https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/10325_ECCV_2024_paper.php
[VideoINSTA]: https://aclanthology.org/2024.findings-emnlp.384/
