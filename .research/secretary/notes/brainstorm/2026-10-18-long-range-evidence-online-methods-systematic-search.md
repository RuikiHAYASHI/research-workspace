# 離れた証拠が必要なベンチマークで評価したオンライン手法の体系的な調査

- 日付：2026-10-18（調査もこの日に実施）
- プロジェクト：agentic-streaming-videoqa
- 経緯：[2026-10-18 長時間離れた証拠のベンチマーク](2026-10-18-long-range-evidence-benchmark-online-methods.md)で「離れた証拠を保証したベンチマークを主な評価にしたオンライン手法は見つからない」という仮説が出た。LongVideoBenchで「報告なし」と誤って書いた反省から、基準と手順を決めて数え直した。
- 根拠の確かさ：判定は、arXiv HTML（一部PDF）の本文をcurlで取得し、該当箇所の原文を読んで行った。本文の読み取りは分担して行い、(b)=yesとした論文の根拠の文は、この記録を書く前に原文で照合した（表5-1）。表の数値は、HTMLをテキストにした際に列がずれている可能性があるので、引用する前に原表で確認する（**要確認**）。

## 1. 結論（2026-10-18時点）

**この手順で探して、該当は9本（強い該当0本、弱い該当9本）。オンラインかどうかが本文から判断できない「不明」が17本。**

- 9本はすべて **LongVideoBench** の全体正答率だけを報告したもの。他の7つのベンチマーク（EgoProbe、EGOSTREAM、TeleEgo、EgoMemReason、EgoMonth、S-EMBER、HERBench）で結果を報告しているオンライン手法の論文は **0本** だった。
- **離れた証拠についての結果を分けて出しているオンライン手法は0本**。LongVideoBenchのReferring Reasoning（17カテゴリ）別に結果を出した論文は、オンライン・オフラインを問わず見つからなかった。最も近いのは次の3本で、いずれも該当ではない。
  - KeyRec（オンライン）：動画の長さ（900〜3600秒）の群だけで結果を図示。証拠からの間隔ではない。
  - LongVU-TTT（**オフライン**）：LongVideoBenchの時間関連の問題を、証拠と質問の時間差（0〜25%、…、75〜100%）で分けて報告している。
  - LazySloth（**オフライン**）：LongVideoBenchを質問の種類（T2O、SOS、TOSなど）別に報告している。
- したがって「**離れた証拠を保証したベンチマークを主な評価にし、離れた証拠の結果を分けて示したオンライン手法**」は、この手順の範囲では見つからなかった。前回の仮説は、この手順でも支持された。
- ただし、LongVideoBenchをオンライン処理で解き、全体の正答率を報告した手法は少なくとも9本あり、増えている（9本中8本が2026年以降のarXiv）。「LongVideoBenchでオンライン手法と比べる」こと自体は新しくない。

## 2. 判定の基準

該当＝(a)(b)(c)をすべて満たすもの。

| 基準 | 内容 |
| --- | --- |
| (a) 手法の提案 | 手法を提案している。ベンチマーク・サーベイ・分析だけの論文は除く。汎用の基盤モデルの技術報告（MiniCPM-o 4.5、InfiniteVLなど）も手法の提案とは数えず、境界として記録した |
| (b) オンライン処理 | フレームを届く順に処理し、未来の映像を見ない。**対象ベンチマークでの評価方法**を本文で確認する。「オフライン評価として動画全体を入力」とあれば満たさない。手法がオンライン向けでも、対象ベンチマークでどう入力したかの記載がなければ「不明」 |
| (c) 対象ベンチマーク | EgoProbe (2610.17128)、EGOSTREAM (2605.31557)、TeleEgo (2510.23981)、EgoMemReason (2605.09874)、EgoMonth (2608.13113)、S-EMBER (2607.02689)、LongVideoBench (2407.15754)、HERBench (2512.14870) のどれかで結果を報告している（引用しているだけは除く） |
| 強い／弱い | 強い：離れた証拠についての結果を分けている（証拠と質問の間隔別、LongVideoBenchのReferring Reasoningのカテゴリ別など）。弱い：全体の正答率だけ。**動画の長さ別だけの場合は「弱い」とした**（長さは間隔の代わりにならないため） |
| 質問を事前に知るか | query-aware（質問を先に与えて処理する）／query-agnostic（質問を知らずにメモリを作る）／不明 |

## 3. 手順

| # | 手順 | 手段 | 日付 |
| --- | --- | --- | --- |
| 1 | 8つのベンチマークを引用している論文を全件取得 | Semantic Scholar Graph API `paper/arXiv:<id>/citations?fields=title,abstract,externalIds,year,venue,publicationDate&limit=500&offset=…`（Bashのcurlで取得。今回はサンドボックス内から外部に出られた） | 2026-10-18 |
| 2 | 絞り込み | LongVideoBench：タイトルと要旨に、正規表現 `\bstream(ing\|s\|ed)?\b`、`\bonline\b`、`\breal[- ]?time\b`、`\bmemory\b`、`\bmemories\b` のどれかを含むもの。さらにタイトルと要旨を読み、オンライン・ストリーミング・逐次メモリの手法と思われるものを本文確認に回した。要旨がない37件はタイトルで判断した。新しい7つのベンチマーク：全件を要旨で確認し、ベンチマーク・サーベイ以外はすべて本文確認に回した | 2026-10-18 |
| 3 | 本文で(a)(b)(c)を判定 | arXiv HTMLをcurlで取得し、ベンチマーク名と "offline"・"online"・"streaming"・"chronologically" などで検索して、該当箇所を読んだ。HTMLがない場合はPDF | 2026-10-18 |
| 4 | キーワード検索で補う | arXiv API（タイトルと要旨が対象）：`abs:LongVideoBench AND (abs:streaming OR abs:online)`、`abs:LongVideoBench AND abs:memory`、`abs:LongVideoBench`、`all:<各ベンチマーク名>`。WebSearch：23件の検索語（例："streaming video long-term memory question answering LongVideoBench"、"EgoMemReason streaming method"、"TeleEgo proposed method streaming memory outperforms"、"online streaming video method HERBench results table"）。検索語は全部で34件 | 2026-10-18 |
| 5 | 手元のメモと突き合わせる | [分類メモ（2回目）](2026-10-17-agent-role-classification-round2.md)の4.3節でLongVideoBenchを使う7本を必ず含めた | 2026-10-18 |

## 4. 件数の流れ

### 4-1. 引用の前向き追跡（Semantic Scholar、2026-10-18取得）

| ベンチマーク | 被引用（取得件数） | 絞り込み後 | 本文確認 | (c)を満たす手法 | 該当（(b)=yes） | (b)=不明 |
| --- | --- | --- | --- | --- | --- | --- |
| EgoProbe | 0（公開が2026-10-12で、まだ引用がない） | 0 | 0 | 0 | 0 | 0 |
| EGOSTREAM | 4 | 全件 | 1（残りはベンチマーク） | 0 | 0 | 0 |
| TeleEgo | 10 | 全件 | 5 | 0 | 0 | 0 |
| EgoMemReason | 13 | 全件 | 6 | 0 | 0 | 0 |
| EgoMonth | 2 | 全件 | 0（2本ともベンチマーク） | 0 | 0 | 0 |
| S-EMBER | 2 | 全件 | 0（2本ともベンチマーク） | 0 | 0 | 0 |
| HERBench | 4 | 全件 | 3 | 3（いずれもオフライン。うちHERBenchの結果は2本、TRACEはLongVideoBench） | 0 | 0 |
| （新しい7つの合計、重複除く） | 33 | 33 | 15 | 4（すべてオフライン。LazySlothを含む） | 0 | 0 |
| LongVideoBench | 826 | 225（キーワード）→59（タイトル・要旨で選択） | 59 | 45（うち基盤モデルの報告5） | 8 | 15 |

- 新しい7つの合計の内訳：33本のうち18本は、タイトルと要旨からベンチマーク・サーベイ・分析と判断して除いた（STORM-Bench、APM-Bench、EgoProbe、EXPLORE-Bench、MyEgo、EgoMemReason、SIMLIFE、EMBER-Bench、ICM-Bench、CapMem、スマートグラスのサーベイ、EmbodiedMemory-Bench、MemTransfer、Beyond3D、EgoGears、NextMe-800、TRACE（評価の監査）、EG-VQA）。残りの15本は本文を確認した（Ledgerを含む）。
- LongVideoBenchの「(c)を満たす」45本は、本文確認した59本から、LongVideoBenchを引用しているだけ・表に載せているだけの14本（サーベイ1本、ベンチマーク1本を含む）を除いた数。基盤モデルの報告5本は(c)に数えたが、該当の判定からは外した。
- LongVideoBench 59本には、VST（2603.12262）を含む。VSTは既存メモで確認済みとして最初の分担から外していたが、キーワード検索で再び見つかり、本文の表5で評価方法を確認した。

### 4-2. Semantic Scholarに無かったもの（手元のメモから追加）

手元の4.3節の7本のうち、StreamingVLM（2510.09608）、SVMemAgent（2609.18540）、QueryStream（ICLR 2026、arXivなし）の3本は、LongVideoBenchの被引用リストに **入っていなかった**。Semantic Scholarの引用データは完全ではない。3本とも本文（QueryStreamは既存メモ）で判定に含めた。

### 4-3. キーワード検索（2026-10-18）

- 新しい候補26本を本文で確認した。20本は、8つのベンチマークの名前が本文に一度も出てこなかった（(c)=no）。残り6本のうち、VSTは該当（4-1に計上）。LiViBench、CASE、DynaTok、One Token per Highly Selective Frame、Video-X2Lの5本はLongVideoBenchを報告していたが、どれもオフラインだった（(b)=no）。
- 新しい7つのベンチマークの名前でarXiv APIを検索すると、ヒットはそれぞれのベンチマーク論文自身だけだった（S-EMBERは0件）。

### 4-4. まとめ

| 段階 | 本数 |
| --- | --- |
| 取得した被引用（8ベンチマーク、延べ） | 861 |
| 本文を確認した | 103（被引用74、手元から追加3、キーワード検索26） |
| (a)(c)を満たす手法（基盤モデルの報告を除く） | 52（被引用のLongVideoBench 40、新しいベンチマークの被引用4、手元から追加3、キーワード検索5） |
| **該当：(a)(b)(c)を満たす** | **9（強い0、弱い9）。被引用から8、手元から追加1（SVMemAgent）** |
| (b)が不明 | 17（被引用から15、手元から追加2（StreamingVLM、QueryStream）） |

## 5. 該当論文

### 5-1. 該当（(b)=yes）：9本、すべて弱い該当

| 論文 | 採録先 | 対象ベンチマーク | オンライン処理か（根拠の本文） | 質問を事前に知るか | 離れた証拠の結果 |
| --- | --- | --- | --- | --- | --- |
| [SVMemAgent](https://arxiv.org/abs/2609.18540) | ECCV 2026 Workshop（手元のメモによる。OpenReviewは開けず未確認） | LongVideoBench（表2、表3、表6） | yes。"Offline benchmarks pose the query after the stream ends ... During evaluation, SVMemAgent processes videos strictly in an online manner at 1 FPS, without access to future frames, the total video duration, or the user query during frame selection"（4節） | agnostic | なし（全体のみ） |
| [VST: Video Streaming Thinking](https://arxiv.org/abs/2603.12262) | ECCV 2026（arXivのcomments） | LongVideoBench（表3、表5） | yes。表5に "All results in this table are obtained with the VST inference pipeline"。6.2節 "Prior to receiving the user query, we conduct a streaming thinking process for each video clip"。ただし表3は、評価方法の注記がないので「おそらくyes」 | agnostic | なし |
| [CausalMem（Dynamic and Fixed-budget Memory Bank）](https://arxiv.org/abs/2606.25658) | 不明 | LongVideoBench（表2） | yes。"For offline evaluation, CausalMem still follows the streaming processing setting under strict causality, where frames are unknown to future information."（4.3節） | agnostic | なし |
| [PReM](https://arxiv.org/abs/2609.23601) | 不明 | LongVideoBench（表1、表2） | yes。"evaluation ingests a question-agnostic 1 FPS stream ... streaming mode ingests two-frame chunks carrying state and answers at stream end"（4.1節）。オフラインのモードの結果も別に報告している | agnostic | なし（付録に「LongVideoBenchにはタスク区分がない」とある。要確認） |
| [DeltaS](https://arxiv.org/abs/2609.27470) | 不明 | LongVideoBench（表1、表2） | yes。"Each video is prefilled chronologically, chunk by chunk, and the question is provided only after the final chunk has been processed."（4節） | agnostic | なし |
| [Mosaic](https://arxiv.org/abs/2604.10060) | 不明 | LongVideoBench（表III、表IV、図7） | yes。"In all experiments, videos are processed sequentially to simulate a streaming setting and are sampled at 0.5 FPS."（VIII節） | agnostic（質問が来た時にKVキャッシュを検索） | なし |
| [EGSD](https://arxiv.org/abs/2609.36803) | 不明 | LongVideoBench（表2） | yes（根拠はやや弱い）。"Under the streaming protocol ... All methods are evaluated under this same streaming protocol."（4.1節）。表2ではLongVideoBenchを "offline benchmarks" と呼んでいる | agnostic | なし |
| [KeyRec](https://arxiv.org/abs/2609.32182) | 不明 | LongVideoBench（表1、表2、表4、図3） | yes（要確認）。"64 frames from each complete long video, processing frames chronologically."（3.1節）。届く順に処理しているが、64フレームは動画全体から抜き出しており、全長を知っている前提 | agnostic（書き込み）。読み出しは質問に合わせる | 長さ別のみ（図3：900〜3600秒の群）→弱い |
| [StreamingTOM](https://arxiv.org/abs/2510.18269) | 不明 | LongVideoBench（付録の表5のみ） | yes（根拠は弱い）。表5の設定は "0.5 FPS" のみ。本文全体では "streaming-designed methods, by processing frames causally" と書いているが、LongVideoBenchで届く順に処理したという直接の記載はない | agnostic（推定） | なし |

### 5-2. (b)が不明：17本

手法はオンライン向けだが、LongVideoBenchでどう入力したかが本文に書かれていないもの。すべてLongVideoBenchの全体正答率のみ（弱い）。

| 論文 | 採録先 | LongVideoBenchの結果 | 記載 | 質問を事前に知るか |
| --- | --- | --- | --- | --- |
| [StreamingVLM](https://arxiv.org/abs/2510.09608) | ICLR 2026 | 表3 | 入力方法と質問の時刻の記載なし | 不明 |
| [LiveVLM](https://arxiv.org/abs/2505.15269) | arXiv（本文にDAC '26の記載） | あり | 「オフライン評価」と記載。動画全体を入力したかは書かれていない（既存メモの表3-2） | 届いた後に質問 |
| QueryStream（[ICLR 2026](https://iclr.cc/virtual/2026/poster/10011335)） | ICLR 2026 | 表番号は未確認 | オフラインのベンチマークとして記載。質問の時刻は記載なし（[引用の追跡メモ](2026-10-18-query-known-online-video-citation-trace.md)による。今回OpenReviewのPDFは403で読めず） | aware |
| [Watch-Think-Interact](https://arxiv.org/abs/2609.37035) | arXiv（採録未確認） | 表3 | "offline long-video benchmarks"。入力方法の記載なし | 不明 |
| [ThinkStream](https://arxiv.org/abs/2603.12938) | arXiv（採録未確認） | 表3 | "standard offline video benchmarks"（6.1節） | 不明 |
| [StreamChat（Chatting with Streaming Video）](https://arxiv.org/abs/2412.08646) | 不明 | 表2 | LMMs-Evalで評価。オフラインの可能性が高い | 不明 |
| [Streamo（Streaming Video Instruction Tuning）](https://arxiv.org/abs/2512.21334) | CVPR 2026 | 表3、付録の表12 | "The offline evaluation used ... VideoMME and LongVideoBench" | 不明 |
| [VideoChat-Online](https://arxiv.org/abs/2501.00584) | CVPR 2025 | 表3 | オフラインのベンチマークとして記載 | 不明 |
| [VideoScan](https://arxiv.org/abs/2503.09387) | 不明 | 表1 | "offline video question-answering benchmarks" | agnostic |
| [InfiniPot-V](https://arxiv.org/abs/2506.15745) | NeurIPS 2025 | 表1、図4、表A5 | 表1がメモリ上限つきの継続処理で評価したか記載なし | agnostic |
| [FluxMem](https://arxiv.org/abs/2603.02096) | 不明 | 表2 | "For the offline evaluation, we choose VideoMME, MLVU, and LongVideoBench"。1 fps、最大1024フレーム | agnostic寄り |
| [Thinking-QwenVL（Progressive Online Video Understanding）](https://arxiv.org/abs/2604.18459) | 不明 | 表3 | "Videos are divided into 16-frame clips"。順に処理したかは記載なし | 不明 |
| [D-HSM（Dynamic Hub-and-Spoke Memory）](https://arxiv.org/abs/2608.30294) | 不明 | 表3 | オフラインのベンチマークとして記載。入力方法の記載なし | 質問時に検索 |
| [CoFiE](https://arxiv.org/abs/2609.03675) | 不明 | 表3 | "offline long-video results ... under the 0% drop setting" | 不明 |
| [LatentStream（Beyond Retrieval）](https://arxiv.org/abs/2609.04131) | 不明 | 表2 | メモリは "constructed entirely online before the query arrives" と手法で説明。オフラインのベンチマークでの入力方法は記載なし | agnostic |
| [VideoMem](https://arxiv.org/abs/2512.04540) | 不明 | 表1、表5、図5 | クリップを順に入れるが、質問を毎回入力する。ストリーミング評価とは書いていない | aware |
| [Video Detective](https://arxiv.org/abs/2512.17229) | 不明 | 表1 | 区間を順に処理し、質問を各区間に入れる。ストリーミング評価の記載なし | aware |

### 5-3. 既存のオンライン手法を評価しているベンチマーク論文（別欄）

前回のメモ（表3-1）で確認したもの。今回の被引用リストからは新たに見つからなかった。

| ベンチマーク | 評価したオンライン手法 | 離れた証拠の結果 |
| --- | --- | --- |
| [EgoProbe](https://arxiv.org/abs/2610.17128) | StreamForest、VST、OASIS、MEMOなど10本 | 間隔別（3分未満〜12時間以上） |
| [EGOSTREAM](https://arxiv.org/abs/2605.31557) | StreamMem、InfiniPot-V、StreamingTOM、ReKVなどのメモリ管理を比較 | 間隔別（7段階） |
| [TeleEgo](https://arxiv.org/abs/2510.23981) | MiniCPM-o（ほかは擬似的なStreaming） | 間隔そのものの集計はなし |
| [EgoMemReason](https://arxiv.org/abs/2605.09874) | StreamingVLM（評価自体はオフライン） | 平均約26時間さかのぼる問題のみ |

## 6. 該当しなかったが境界の論文

| 論文 | 対象ベンチマーク | 外した理由 |
| --- | --- | --- |
| [LongVU-TTT](https://arxiv.org/abs/2608.25729) | LongVideoBench（表1〜4） | **離れた証拠を分けた唯一の例**（表4：証拠と質問の時間差の4区分）。ただし "the final fixed-budget frame selection are performed after the full video has been processed" で、(b)=no |
| [LazySloth](https://arxiv.org/abs/2609.37426) | LongVideoBench（表2、表3、表10） | 表10で質問の種類別（T2O、SOS、TOSなど）に報告。動画全体と質問から木を作るオフライン手法 |
| [Elephant in the Fridge（FramePack-U）](https://arxiv.org/abs/2610.16118) | LongVideoBench（表1〜6） | 長さ別（15秒〜3600秒）に報告。"we sample all frames in an offline way for the benchmarking experiments"。query-aware |
| [Proact-VL](https://arxiv.org/abs/2603.03447)（ICML 2026） | LongVideoBench（付録の表20） | 長さ別に報告。8フレームのオフライン評価 |
| [HiMu](https://arxiv.org/abs/2603.18558) | LongVideoBench、HERBench-Lite（表2、表3） | 動画全体から質問に合わせて16フレームを選ぶオフライン手法 |
| [Target-Checked Reliability Score Refinement](https://arxiv.org/abs/2609.13288) | HERBench Lite-v2（表6、7、11など） | タスク別に報告（間隔別ではない）。逆順を含む動画全体の見え方を使うオフライン手法 |
| [TRACE（Temporal Retrieval with Anchored and Convergent Evidence）](https://arxiv.org/abs/2608.22516) | LongVideoBench（表1） | "Each method receives the full video, question, and four options."（オフライン） |
| [StreamAgent](https://arxiv.org/abs/2508.01875) | LongVideoBench | 「オフラインでは動画全体を入力する」と記載（既存メモの表3-2） |
| [TimeChat-Online](https://arxiv.org/abs/2504.17343) | LongVideoBench（表3） | "In the offline setting, the entire video is provided as input" |
| [MMDuet2](https://arxiv.org/abs/2512.06810)、[AURA](https://arxiv.org/abs/2604.04184)、[LiveStarPro](https://arxiv.org/abs/2606.17798)、[StreamOPD](https://arxiv.org/abs/2608.16320)、[EvoStreaming](https://arxiv.org/abs/2605.10343)、[LyraV（Don't Pause）](https://arxiv.org/abs/2606.06991)、[StreamBridge](https://arxiv.org/abs/2505.05467)、[QuickVideo](https://arxiv.org/abs/2505.16175)、[FlexMem](https://arxiv.org/abs/2603.29252)、[Tempo](https://arxiv.org/abs/2604.08120)、[QASLR](https://arxiv.org/abs/2610.04864) | LongVideoBench | オンライン向けの手法だが、LongVideoBenchは標準のオフライン評価（動画全体から一様に抜き出す、lmms-evalで評価、など）と明記 |
| [VideoXAgent（Online Video Agent Harness）](https://arxiv.org/abs/2609.12818) | LongVideoBench（表1、表3） | 「オンライン」は事前に索引を作らないという意味で、届く順の処理ではない |
| [MiniCPM-o 4.5](https://arxiv.org/abs/2604.27393)、[InfiniteVL](https://arxiv.org/abs/2512.08829)、[JoyAI-VL-Interaction](https://arxiv.org/abs/2606.14777)、[Mage-VL](https://arxiv.org/abs/2607.24904)、[MOSS-Video-Preview](https://arxiv.org/abs/2606.07639) | LongVideoBench | 基盤モデルの報告。LongVideoBenchはオフライン、または入力方法の記載なし |
| [ReMem](https://arxiv.org/abs/2610.05940) | なし | オンライン手法だが、LongVideoBenchは参考文献にあるだけ（前回のメモの通り、評価先はStreamingBenchとOVO-Bench） |
| [Ledger（Never Look Back）](https://arxiv.org/abs/2610.10538) | なし | TeleEgoの動画を含むUCS-Benchで評価しており、TeleEgoそのものではない。"Construction is offline, so filtering records by question time does not establish causal online memory" |
| [StreamPro](https://arxiv.org/abs/2605.16381) | なし（要確認） | 本文はLongVideoBenchと書くが、表4の列はLVBench。名前の取り違えの可能性あり。付録は未精読 |

## 7. 本文を読めなかった・確認が不十分な論文

| 論文 | 状態 | 理由 |
| --- | --- | --- |
| QueryStream | 今回は読めず | OpenReviewのPDFが403。既存の[引用の追跡メモ](2026-10-18-query-known-online-video-citation-trace.md)とGitHubのREADMEで判定 |
| CITR: Efficient Long Video Understanding Needs Causal Importance | 未確認 | arXiv IDがなく、要旨もなかったので、タイトルだけで除外した。"Causal" を含むので、オンライン手法の可能性がある |
| 要旨がない37件 | タイトルのみ | Semantic Scholarに要旨がなかった。タイトルからはオンライン手法と思われるものはなかった |
| KeyRec、EGSD、StreamingTOM | 本文は読めた | (b)=yesの根拠の文がLongVideoBench専用ではない、または弱い（表5-1に記載） |
| StreamForest、Dispider | 本文は読めた | VSTの表3にLongVideoBenchの数値（61.4、57.2）が載っているが、両論文の本文にはLongVideoBenchが出てこない。VST側が測った数値と思われる |
| 採録先 | 多くが不明 | arXiv HTMLにcommentsが無いため。手元のメモとarXivのcommentsで分かったものだけ記載 |

## 8. 結論と限界

### 結論
- 2026-10-18時点で、この手順（Semantic Scholarの被引用の全件取得、キーワードとタイトル・要旨による絞り込み、本文での判定、arXiv APIとWeb検索による補い）で探した結果、該当は **9本（強い0本、弱い9本）**、オンラインかどうか不明が **17本** だった。
- 9本も17本も、すべてLongVideoBenchの全体正答率だけで、離れた証拠を分けた結果は出していない。新しい7つのベンチマーク（EgoProbe、EGOSTREAM、TeleEgo、EgoMemReason、EgoMonth、S-EMBER、HERBench）で結果を報告したオンライン手法は0本だった。
- 「離れた証拠についての結果を分けて示すオンライン手法」という位置は、この調査の範囲では空いている。一方で、LongVideoBenchの全体正答率でオンライン手法と比べること自体は、すでに9本以上が行っている。

### 限界（取りこぼしの可能性）
1. **Semantic Scholarの引用データは完全ではない。** 手元の7本のうち3本（StreamingVLM、SVMemAgent、QueryStream）が、LongVideoBenchの被引用リストに入っていなかった。同じように抜けている論文がある可能性が高い。
2. **LongVideoBenchの絞り込みはタイトルと要旨が対象。** 本文の表だけでLongVideoBenchを使い、要旨にstream/online/memory/real-timeを含まない論文は拾えていない。225件から59件を選んだ段階も、タイトルと要旨だけで判断している（除外した166件は付録A）。
3. **arXiv APIの検索もタイトルと要旨だけ。** 新しいベンチマークの名前で検索しても、ヒットはベンチマーク論文自身だけだった。本文の表だけで使っている論文は拾えない。
4. **新しいベンチマークはまだ引用が少ない**（EgoProbeは0件）。これから手法が出てくる時期なので、時間がたてば結果は変わる。
5. **(b)の判定は本文の記載に依存する。** 「不明」の17本には、実際はオンラインで評価したものも含まれうる。逆に、(b)=yesのうちKeyRec、EGSD、StreamingTOMは、LongVideoBench専用の記載ではないので、厳しく見れば不明に移る（その場合、該当は6本）。
6. 本文の判定は、作業を分担して読み取った結果をまとめた。(b)=yesの9本は根拠の文を原文で照合したが、(b)=no・不明の判定は分担した読み取りのままで、照合していない。

## 9. 次の判断・未確認

- [ ] (b)=不明の17本のうち、比較相手になりそうなもの（StreamingVLM、ThinkStream、Watch-Think-Interact、QueryStream）は、コードや著者への問い合わせで、LongVideoBenchの入力方法を確認する
- [ ] LongVU-TTTの「証拠と質問の時間差」による分け方（表4）を、私たちの評価の設計の参考として読む
- [ ] 手順を同じにして、1〜2か月後に再実行する（特にEgoProbe、EGOSTREAMの被引用）
- [ ] Google Scholarの「被引用」でも同じ追跡をして、Semantic Scholarとの差を確認する

## 出典

- Semantic Scholar Graph API（`https://api.semanticscholar.org/graph/v1/paper/arXiv:<id>/citations`）、2026-10-18取得
- arXiv API（`http://export.arxiv.org/api/query`）、2026-10-18検索
- 各論文のarXiv HTML（表5〜6のリンク先）
- [2026-10-18 長時間離れた証拠のベンチマーク](2026-10-18-long-range-evidence-benchmark-online-methods.md)
- [2026-10-18 引用の追跡（質問を最初から知るオンライン手法）](2026-10-18-query-known-online-video-citation-trace.md)
- [2026-10-17 分類メモ（2回目）](2026-10-17-agent-role-classification-round2.md)

## 付録A：LongVideoBenchのキーワード候補225件のうち、タイトル・要旨で除外した166件

主な理由：オフラインの手法（フレーム選択、トークン削減、動画全体を見るAgent・検索）、ベンチマーク、サーベイ、効率化の一般手法、動画QA以外の課題。

2406.08035, 2408.10188, 2409.02889, 2409.20018, 2410.07177, 2410.13166, 2411.16173, 2412.20504, (arXivなし) Sharper and Faster mean Better, 2501.05179, 2501.12386, 2503.11579, 2504.10739, 2506.00993, 2506.04953, 2506.05332, 2506.19225, 2507.02946, 2508.01548, 2508.03351, 2508.09981, 2508.16201, 2508.17243, 2509.18154, 2510.10991, 2510.12299, (arXivなし) Visual Context Window Extension（2409.20018と重複）, 2511.12027, 2511.12201, 2511.17945, 2512.01949, 2512.12360, 2601.22959, 2602.08005, 2603.04349, 2603.05484（TeleEgoの被引用として本文確認済み）, 2603.10335, (arXivなし) SELongVLM, 2603.17948, 2603.19217, 2603.21957, 2603.22911, 2603.27259, 2603.27650, 2603.28696, 2603.29494, 2604.00677, 2605.00891, 2605.05848, 2605.09874, 2605.12954, 2605.22907, 2605.26584, 2606.06532, 2606.05917, 2606.13392, 2606.19338, (arXivなし) Frame Skipping Architecture, 2606.24187, 2607.24794, 2607.28678, 2607.28156, 2608.01644, 2608.04132, 2608.13113, 2609.00103, (arXivなし) EVA, 2609.04438, (arXivなし) A Survey of Multi-Model Collaboration, 2609.09985, 2609.19610, 2609.31713, 2609.38119, 2610.04225, 2610.05013, 2610.05526, 2610.06672, 2610.11171, 2610.15389, 2501.00574, 2501.05510, 2503.13016, 2503.18943, 2503.22952, 2503.24008, 2504.10049, 2505.02064, 2505.22654, 2506.01274, 2506.05349, 2506.06144, 2508.02134, 2508.03039, 2508.18265, 2510.02778, 2511.00279, (arXivなし) CHEF-VL, 2512.19107, 2601.13719, 2601.15016（キーワード検索で本文確認、オフライン）, 2602.00523, 2602.08882, 2602.15318, 2602.16412, 2602.23553, 2603.00490, 2603.00983, (arXivなし) SmoothDiffusion-VE, 2603.12703, 2604.08703, 2604.17422, 2605.05225, 2605.06537, 2605.08412, 2605.17360, 2605.26232, 2605.26485, 2605.29643, 2606.02443, 2609.05596, 2606.03890, 2606.03920, 2606.09547, 2606.11913, 2606.13707, 2606.19706, 2606.23256, 2606.24422, 2607.01751, 2607.13681, 2607.14935, 2607.16107, 2608.07585, 2608.15045, 2608.20958, 2608.22279, 2608.27929, (arXivなし) A scalable and semantic pipeline, 2609.13814, 2609.30670, 2609.30981, 2609.32280, 2609.35416, 2609.36691（EgoMemReasonの被引用として本文確認済み）, 2610.05400（キーワード検索で本文確認、オフライン）, 2412.19442, 2501.02430, 2505.21487, 2509.19115, (arXivなし) Towards training-free long video understanding, (arXivなし) CITR, (arXivなし) Constraint-Driven Evolution, 2603.03985, 2603.09827, 2604.05546, 2604.11627, 2605.06185, 2605.10936, 2605.19322（キーワード検索で本文確認、オフライン）, 2607.11312, 2608.03979, 2608.08612, 2609.10355, 2609.11899, 2610.10183, 2610.17355
