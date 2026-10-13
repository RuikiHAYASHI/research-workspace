---
date: 2026-10-14
project: agentic-streaming-videoqa
source_todo: "2026-09-11 MTG: Agent系Streaming VideoQAとMemory表現・未解決点の関連研究調査"
topic: streaming-videoqa-literature-review-plan
status: exploratory
tags: [brainstorm, literature-review, streaming-videoqa, memory, agent, anticipation, research-plan]
---

# Streaming VideoQA 関連研究：問い・抽出事項・実行順序

## 立脚する確定事項と留保
- 2026-09-11 MTG: Agent系の既存手法ができること/できないことを幅広く調べ、Memoryのtext/KV/feature等を区別し、動的chunk・multi-timescale・予兆Memory・未来予測などを探索する方針。Query=t0既知、future chunkなしのchunk-level causalを当面の研究設定とする。
- 2026-10-02 MTG: Agentの責務・入出力を自分で理解することを優先。これと今回の文献調査の達成条件を混同しない。
- 2026-10-09実験/brainstorm: 現行のSituation -> Summary -> Answerでは、Summary_t=LLM(Summary_{t-1}, Situation_t) の累積書換えで古い事実が脱落・重複する可能性がある。ただし原因・QAへの影響の確定ではない。
- 2026-10-14のユーザー選択: 忘却A、選択B、予測Cのどれにも研究テーマを絞らず、それぞれが既存研究でどこまで実現されているか調べてから翌MTGで議論したい。
- 上記はCompany README/MTGのAuthorityとexploratory brainstormの区別を維持する。今回の調査計画自体は未承認の提案であり、採用spec・実装許可ではない。

## 目的と成功条件
**中心問い:** Streaming VideoQAで将来の回答に必要な動画情報を、どのように観測し、何を保存し、どう維持・検索して使うか。そのうちAgentがどの意思決定を行えるか。
**今回の成果:** 主要な既存の仕組み、論文が実証した機能、未確認の論点、次に深掘りする理由が説明できる。論文本数、新規性の断定、網羅サーベイ、実装レベル理解を成功条件にしない。

## 調査する問い（優先順位）
### 共通Gate：研究設定
- future framesへのアクセスの有無。pseudo-streaming prefix評価かtrue incremental処理かを区別する。
- Queryが開始時既知/途中到着/未知。過去rawを再読み込みするか。処理単位（frame/clip/chunk）。
- 同条件なら直接比較候補、異条件でも機構が有用なら周辺研究。絶対的な除外条件にしない。

### Q1. Memoryはどんな形式・構造で保存されるか？（高）
- text summary / text event record、visual feature/token、KV cache、frame/raw、latent、hybrid。
- 記憶の単位: frame、window、event、chapter。長期/短期、階層、上限budget。
- 「通常推論中にKVがある」と「保持・再検索の長期KV memory」は区別。

### Q2. 何を残すかは誰がどう決める？（高）
- 全記録か選択記録か、重要度（類似度、時間、Query relevance、event boundary、Agent policy、予測）。
- action: write、keep、replace、discard、skip。観測対象を選ぶAgentと保存を選ぶAgentは別。
- Questionが与えられた段階で選択するか、未知でも先に残すか。

### Q3. 古い情報をどう保持・更新する？（高）
- append-only、recurrent rewrite、edit、merge、compress、prune、hierarchy、retrieve、revisit。
- 忘却・矛盾・順序・詳細保持とtoken/VRAM/latencyのtrade-off。
- 劣化を改善した主張と、そのablation/evidenceがあるかを分ける。

### Q4. 予測・Agent判断はどの操作を変える？（中〜高）
- future-event anticipation（次の場所・対象・時間の予測）とfuture-query prior（将来尋ねられそうなことの予測）を区別。
- Agentの決定出力と実際のactionが一致するか：crop、追跡、sampling、次chunk長、Memory write/delete、retrieve、answer timing。
- 単にLLMを複数使う方式はdecision policyとは区別。

### Q5. 保存情報をどう検索してQAへ使う？（中）
- global summary一括渡し、検索、event/時間帯の選択、保存視覚特徴やrawへの再アクセス。
- 保存できなかった vs 保存中に失った vs 取り出せなかった vs Answerで活用できなかった、を分ける。

### Q6. 何を実験で確認した？（全論文）
- benchmark、同条件のbaseline、改善指標（accuracy、fact retention、memory budget、latency）、ablation。
- 「著者がlimitationと認めた」「論文で未評価」「自分が未読」を3種類に分ける。

## 読む範囲・開始候補（全て入口の候補、網羅調査済みではない）
- text蓄積基礎: Lando et al. https://arxiv.org/abs/2506.16450
- text構造化: LangRepo https://arxiv.org/abs/2403.14622 （現在研究と同じstreaming条件か要確認）
- eventテキストとrecent visual: OneStreamer https://arxiv.org/abs/2610.01762
- 視覚event階層: StreamForest https://arxiv.org/abs/2509.24871
- 視覚KV容量: StreamMem https://arxiv.org/abs/2508.15717
- text+KV/未来観測: StreamAgent https://arxiv.org/abs/2508.01875
- agentによるkeep/replace/discard: SVMemAgent https://arxiv.org/abs/2609.18540 （Query未知、前提違い）
- event memoryからretrieve: EventMemAgent https://arxiv.org/abs/2602.15329
周辺追加候補: SAVEMem https://arxiv.org/abs/2605.07897 （future query prior / pseudo-streaming評価の留保）、Watch-Think-Interact https://arxiv.org/abs/2609.37035 （過去raw再アクセス）、MovieChat https://arxiv.org/abs/2307.16449（short/long visual memory）。
- AgentのオフラインRelated Workを全面精読することは保留。write/retrieve/anticipationなど関連mechanismがあるものは部分参照。

## 調査手順（MTG前の現実的な提案）
### STEP 0：調査ノートの準備（10分）
- 既存Company候補の重複確認。新しい論文数を増やすより新しい「仕組み」か「反例」を発見することを評価。
- 縦に論文、横に6つの問い、行外に「前提の違い」を書く。全セルを埋めることは要求しない。

### STEP 1：幅広い一次探索（45〜60分程度）
- 候補8本の中から約6〜8本をScan。1本5〜8分を上限目安にAbstract、中心図、Introductionの問題設定、Conclusionだけ読む。
- 最小記録: （1）論文名/URL（2）解決対象とMethodを各1行（3）Memory形式/更新（4）Agentの判断対象（5）自研究との接点・疑問点、未確認があればそのまま。
- スクリーニングでは正確な実装数式を調べず、次に読む理由が生まれなければ保留。

### STEP 2：問いベースの追加探索（20〜40分程度）
- 論文間の隙間を問いに言語化して探す。例：text event summaryと累積rewriteの比較研究？ Agentが観測と保存を両方変える研究？ Q=t0で記憶選択する研究？ 未来を見ずにraw再読込なしのretrieval？
- 全てのRelated Workを順に辿らず、欠けた問いに関係する引用や引用元を各方向1〜2本拾う。
- 議論に不可欠な2〜3本だけ本文Method/Experiments/Ablationの該当箇所を10〜15分程度読む。

### STEP 3：横断的なまとめ（20〜30分程度）
- 5つの問いごとに「既存研究の実例」「確認した達成事項」「設定の違い」「未確認/疑問」「次に読む必要」を1〜3文で整理。
- MTG持参物は(1)説明できる既存メカニズム3〜5種(2)直接比較候補2〜3本(3)要追加調査の問い2〜3件(4)先生への意思決定相談1件。
- 調査した論文の本数より、既存手法の位置付けと未確認点を言えることを重視する。

### MTG後
- 先生と研究目的、前提、深く読むべき観点を優先化してから主要3〜5本をLevel 2（Method + Experiments）、必要な1〜2本だけLevel 3（詳細式・コード）へ。
- 調査結果だけで「存在しない」と言わない。研究差分の成立は文献とEvidenceで後から判定。

## 1本ごとの記録フォーマット
### 1周目（短く）
- 論文名/URL
- 解決したい問題：一言
- 中心手法：一言（Memory形式・書込/更新、Agent action）
- 今回の研究との接点：どの問いか
- わからないこと・次に読む理由：1行

### 2周目（重要論文だけ）
- 設定: future、Query timing、raw past revisit、処理単位
- Memory: representation / unit / update / capacity
- Decision: rule or Agent、実際の行動
- Evidence: benchmark / baseline / ablation / 効果の指標と論文内の根拠位置
- 既存研究が「実現済み」と明記できること
- 著者が述べる制約、未評価、読者側未確認の区別
- 自研究との比較条件と次の検索問い

## 調査の終了条件
- Text系、visual/KV系、Agentの観測・保存選択系の各方向について少なくとも代表手法を説明できる（網羅性の証明ではない）。
- Memoryの媒体とMemory更新政策、Agentのactionを混同せず説明できる。
- 直接比較できそうな手法と、設定が違うが参考になる手法を区別できる。
- 次のMTGで決めたい優先調査問いを2〜3件持てる。
- 追加論文で新しい機構や不明点が増えなければ一旦止め、技術的詳細を無限に掘らない。

## 未採用・注意
- 研究テーマA/B/Cを今決定しない。Text memoryのみ、Visual memoryのみ、予測のみへ限定しない。
- 累積Summary劣化は観測・書込み・更新・検索・回答のどこに原因があるか未切分け。保存形式が直接原因とは断定しない。
- 「重要イベント記録」「階層化」「Agent利用」は既存例があり、それらをするだけでは新規性にならない。
- 計画はexploratory。TODO、README、spec、研究コードの作成・変更はしない。

## 根拠のCompany文書
- .research/lab/projects/agentic-streaming-videoqa/README.md
- .research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-11-mtg.md
- .research/lab/projects/agentic-streaming-videoqa/meetings/2026-10-02-mtg.md
- .research/secretary/notes/brainstorm/2026-10-14-critical-literature-review-questions.md
- .research/secretary/notes/brainstorm/2026-10-14-memory-literature-review-tree-strategy.md
- .research/secretary/notes/brainstorm/2026-10-14-anticipation-and-text-memory-literature.md
- .research/secretary/notes/brainstorm/2026-10-09-summary-memory-degradation-countermeasures.md


## 2026-10-14 追記：10/09議事録復元後の調査優先順位の修正

### 新たに確認したAuthority
- 2026-10-09 MTG議事録（10/14に遡及作成）を確認。指導では「過去のイベントを他の手法はどう保持しているか」など一つの観点を絞って10〜20本程度を調べ、代表論文（StreamAgent等）のRelated Workを手がかりに探索し、他方式との比較を始めることが勧められている。
- 来週までの重点は「Prompt改善」「Memory / Event / 予習の文献説明」「Summaryと別にEventを記録する小さな試作」の3つ。関連研究調査はそのうち一部であり、全部を並列の文献サーベイトラックに展開する必要はない。
- 現行baselineはSituation -> Summary -> Answerであり、Summary全文を各chunkで繰返し更新するため古いイベントの脱落が疑われる。ただし情報落ちの原因、実際のQAへの影響は未証明。

### 調査計画の修正（探索の最有力案）
従来のQ1～Q6のうち、全方向を同時に独立調査する案は**今のMTGの一次要求としては広すぎるため保留**する。研究テーマをどれかに確定させることは引き続き保留。

まず一つの調査問いに焦点を当てる：
**「Streaming VideoQAでは、過去の出来事（event）を、どんな媒体・単位で保存し、長尺化・要約・圧縮で失わないためにどう管理し、最終QAでどう利用するのか？」**

この問いから、各論文では必要最小限の共通事項を確認する。
1. 論文名・URL・解決しようとする問題
2. 記憶の表現: text / visual feature / raw frame / KV / hybrid。形式と実際の保存の構造（frame / event / chunk / chapter）を区別する。
3. 過去イベントの扱い: append / recurrent summary rewrite / merge-compress / keep-discard / retrieval。何を消すか、誰が判断するか（規則、類似度、Agent、Query）。
4. 保存した情報をAnswerで利用するか、raw-video再取得するか。
5. Setting: 未来frame先読みの有無、Questionを知る時点、過去映像再アクセスの可否。直接比較できるか。
6. 確認できた機能、著者の明示した限界、未評価、未読の区別。初回は論文の図/Abstract程度で空欄を許す。

特に「eventを別枠に保存する既存例」「単一累積text summaryの限界」「Agentがイベントの保存選択を行う既存例」を比較の起点にする。Anticipationは会議で言及された追加関心だが、一次Memory調査から切り離し、**予習により何を記憶するかが変わる研究があるか**の短い周辺調査とする。

### 開始候補と調査順
- 主軸: StreamAgent (text m_t + KV recall)、OneStreamer (temporal event text summaries)、StreamForest (visual event forest)。いずれも既存brainstormで検討済みの候補で、厳密なMethodを理解したという意味ではない。
- 広げる: LangRepo / Lando (text memory) や StreamMem / MovieChat (visual/KV) を、主軸の「記憶の残し方」を比較するために必要なときだけ参照。
- Agentによるkeep/replace/discardに関係するSVMemAgent、未来の質問分布を扱うSAVEMemは周辺として調べる。質問既知/未知の設定差に注意。
- Related Workをすべて読むのではなく、イベント保存・要約保持・メモリ更新・検索に関わる引用を優先し、1本5〜10分のスクリーニングから始める。
- 10〜20本は会議で示された調査範囲の目安であり、**1回の深夜作業で網羅または精読せよというノルマではない**。

### 報告の形（候補）
- 冒頭: 「過去のイベント保持」に絞った理由。現行Summaryが過去情報を失う懸念とイベント別保存案が背景である。
- 代表例3〜5本について、同じ問いで1行〜数行比較。最低でもtext/visual/KVまたはhybrid、更新・保持の工夫、明らかな設定差。
- 各手法が何を解決すると主張し、どの結果が実証で、何が未確認か。
- 次に調べるべき不足点と、先生に確認したい深掘り方向（イベント保存の選択か、保持・劣化か、予習か）。
- イベント別保存や予習Agentの新規性が確認されたわけではない。MTG後に深掘り優先を判断する。

### 保留・反例・次に決めること
- 「イベント保持」だけでは予習Agentの設計そのものの比較が十分でない可能性がある。別途、補助的に1〜2本でも予習に近い先行例を確認しておく案。
- イベント台帳とvisual event forestは形式と機構が違う。イベントの名称が一致しているだけで同一手法とみなさない。
- 直接比較候補のstreaming protocolが同じとは限らない。Question timing/future/revisitに注意。
- MTGでのResearch gap発見と今のbaseline実装の改良順序は未決。現時点で一つの研究手法を正式採用しない。

関連: [2026-10-09 MTG](../../lab/projects/agentic-streaming-videoqa/meetings/2026-10-09-mtg.md)


## 2026-10-14 追加壁打ち：主題は過去映像情報のMemory維持へ

ユーザーは「イベント」に限定するとStreamAgentのような累積Text Memoryが外れ、比較が歪むと指摘。中心問いを「過去の映像情報をどうMemoryとして維持するか」に置き直す。イベント記憶は、その下位で必要に応じて集中調査する候補。現時点では研究方向をイベント保存のみに絞っていない。

公開論文のAbstract・手法説明を検索し、Streaming動画理解/QAで過去情報をイベント単位の明示的Memoryとして保持する候補を7本確認した（網羅数ではなく今回見つけた下限的候補）。
- StreamForest: https://arxiv.org/abs/2509.24871 — 視覚特徴のevent tree。
- VideoScaffold: https://arxiv.org/abs/2512.22226 — event segmentationと階層的統合。
- Event-VStream: https://arxiv.org/abs/2601.15655 — 状態変化ごとのevent embeddingをpersistent bankへ。
- EventMemAgent: https://arxiv.org/abs/2602.15329 — eventごとのcaption、視覚手掛かり等を保存。
- OASIS: https://arxiv.org/abs/2604.17052 — 階層的event記憶の要求時検索。
- KeyRec: https://arxiv.org/abs/2609.32182 — 視覚event bankへのadd/merge/evict。
- OneStreamer: https://arxiv.org/abs/2610.01762 — 完了したeventのtext summaryと局所caption。

隣接するOnline Video Temporal Grounding（QAではなくイベント時刻特定）で1本: https://arxiv.org/abs/2508.04546 。したがって今回の確認候補は計8本。OfflineのMemoryCard https://arxiv.org/abs/2606.05917 は数えない。実時間処理や質問到着条件が全論文で一致するわけではなく、これらの件数は網羅的な調査結果ではない。

整理の核心：Text/Visual/KVは保存媒体、event/frame/chunkは保存単位、append/rewrite/merge/searchはMemory操作。これらを別々に記録する。StreamAgentは明示的イベント記憶の7本には含めず、text+KVの比較基準として残す。

次は各論文について、Memoryの形式・単位・書込更新・重要情報選択・QA時の読出し・future/Query条件を浅く調査する。Text一体要約方式とEvent方式の違いを確認してから、イベント保持へ範囲を絞るべきか判断する。新TODO、spec、研究コードの変更は行わない。
