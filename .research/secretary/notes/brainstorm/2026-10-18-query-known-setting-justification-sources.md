# 「質問を最初から与える」設定の根拠になりそうな論文

- 日付：2026-10-18
- プロジェクト：agentic-streaming-videoqa
- 経緯：QueryStream（ICLR 2026）の本文には、質問を先に知る設定そのものの正当化がなかった（[引用の追跡](2026-10-18-query-known-online-video-citation-trace.md)の5節）。そこで、根拠に使えそうな論文を探した。
- 根拠の確かさ：TSGSVとInfiniPotは、PDFをテキストにして該当箇所の原文を読んだ。それ以外はarXivのページやWeb検索の要約による。引用する前に原文で確認する。

## 1. 結論

QueryStream以外にも、根拠の候補は4つの方向で見つかった。

1. **動画で、質問（文）を先に与えて、届く順に処理する課題がすでに定義されている**：TSGSV（ACM MM 2023）、OnVTG（ICCV 2025）。いずれも監視・ライブ配信で「指定した出来事を、起きた瞬間に見つける」ことを動機にしている。特にTSGSVは、**質問を使って過去のフレームを圧縮する**（質問に関係するフレームを強める）ので、私たちの「質問を使って何を残すか決める」に最も近い。
2. **Streaming VideoQAで、質問が証拠より先に来る設定がある**：StreamReady（arXiv 2603.08620）、OVO-BenchのForward Active Responding。動機は「早すぎる回答は推測、遅すぎる回答は遅延」。
3. **LLMの長文処理で、メモリ上限のもと質問を先に使う設定が正当な変種として扱われている**：InfiniPot（EMNLP 2024）、Beyond RAG（arXiv 2503.04973）。
4. **人間の学習の研究で、動画の前に質問を与えると、その情報をよく覚える**：Carpenter & Toftness（2017）、Toftness et al.（2018）。動機付けの比喩として使える程度。

ただし、1と2はどれも「出来事が起きたら答える（監視・能動的な応答）」という用途で説明している。私たちのように「最後に答える多肢選択VQA」で質問を先に与える設定を、そのまま正当化しているものは見つかっていない。

## 2. 論文ごとのメモ

### TSGSV：Temporal Sentence Grounding in Streaming Videos（[arXiv 2308.07102](https://arxiv.org/abs/2308.07102)、ACM MM 2023）
- 設定：文の質問を与え、未来のフレームを見ずに、今が該当の出来事の始まり・途中・終わりかを各時刻で推定する。例は「台風で何かが通りに飛ばされる」。
- 動機（1節）："there are more than one billion surveillance cameras operating worldwide"、"the development of algorithms capable of detecting the exact moment a queried event occurs in real-time video streams has become paramount"。オフラインのgroundingは "necessitate the availability of the entire video in advance" なので使えない、と述べる。
- **質問を使った圧縮**（1節）："Existing compression method for streaming video [6] has not take sentence query into consideration, resulting in query-irrelevant information"。提案するLFCは "compresses historical frames under the guidance of a sentence query"。
- 私たちへの使い方：「質問を先に与え、質問に合わせて過去を圧縮する」ことには、2023年に先例がある。根拠として最も直接的。

### OnVTG：Hierarchical Event Memory for Accurate and Low-latency Online Video Temporal Grounding（[arXiv 2508.04546](https://arxiv.org/abs/2508.04546)、ICCV 2025）
- 設定："locate events related to a given text query within a video stream"、"without observing future frames"。全履歴を保存するのは非現実的なので、出来事ごとの階層メモリを使う。
- 質問がストリームの前に与えられるかは、要旨には明記なし（課題の性質上そう読める。本文で要確認）。

### StreamReady（[arXiv 2603.08620](https://arxiv.org/abs/2603.08620)、採録の記載なし）
- 設定："future-dependent (proactive) reasoning, where the question appears before the supporting evidence"。
- 動機："responding too early, even if correct, indicates unsupported speculation; responding too late causes unwanted delay"。用途に "surveillance, sports analytics, robotics, and assistive systems" を挙げる。
- 評価：自作のProReady-QA（Ego4D、MovieNetの長い動画）。ほかにStreamingBench、OVO-Bench、OVBench、VStream-QA。

### OVO-Bench Forward Active Responding（[arXiv 2501.05510](https://arxiv.org/abs/2501.05510)、CVPR 2025）
- 要旨："delay the response until sufficient future information becomes available to answer the question accurately"。質問が先に来て、答えられるまで待つ設定と読める。
- 主要ベンチマークの1区分として、質問が先に来る設定がある、という根拠になる。

### InfiniPot（[arXiv 2410.01518](https://arxiv.org/abs/2410.01518)、EMNLP 2024）
- 設定：固定のメモリ上限で、長文を順に読みながら圧縮する（未来の文脈は見ない）。
- 4.4.1節："In QA tasks where specific queries are predefined, incorporating the question into the CaP prompt leads to additional performance improvements (from 30.54 to 35.71)"、"In general long context scenarios where queries are not pre-accessible, CaP-G still effectively achieves query-agnostic context compression"。**表1の主結果でも、QAでは質問を使う版（CaP-Q）を使っている。**
- 私たちへの使い方：メモリ上限つきの逐次処理で「質問が先に分かる場合は使う」ことが、正当な設定として主結果に入っている先例。

### Beyond RAG：Task-Aware KV Cache Compression（[arXiv 2503.04973](https://arxiv.org/abs/2503.04973)）
- タスクの指示（zero-shot）や例（few-shot）を先に与えて知識を圧縮し、後の質問に使う。質問そのものではなく「タスク」を先に知る設定。正当化の文は未確認。

### StreamMem（[arXiv 2508.15717](https://arxiv.org/abs/2508.15717)）
- 本体は質問を知らない設定だが、ablationで正解の質問を使ってKVを圧縮すると、特に細部を問う課題で有利と報告している（[2026-09-10のメモ](2026-09-10-causal-granularity-query-pregiven.md)）。質問を先に知る設定は「上限」として扱われている。

### 人間の学習：prequestion（事前質問）
- Carpenter & Toftness（2017, Journal of Applied Research in Memory and Cognition）：短い動画の各区間の前に質問を与えると、事後テストの成績が上がった（[BPSの紹介記事](https://bps.org.uk/research-digest/heres-simple-way-boost-your-learning-videos-prequestion)）。
- Toftness et al.（2018、同誌）：20分を超える実際の講義動画では、事前に問われた情報だけがよく覚えられ、それ以外はほぼ差がなかった（[PDF](https://pure.royalholloway.ac.uk/files/30437641/JARMAC_Toftness_et_al.pdf)）。
- 2017年の論文の書誌情報（DOI）は未確認。

## 3. 私たちの推論

- 用途の説明は、TSGSVやStreamReadyのように「**指定した条件を見張る**（監視、ライブ配信、ロボット、支援）」に寄せるのが最も根拠をそろえやすい。最後に答えるVQAで質問を先に与えるのは、その「見張りの内容を言葉で指定する」場合の評価の形、と位置づけられる可能性がある。
- 「質問を知らない設定より簡単すぎる」という反論には、InfiniPotやStreamMemのように「質問が分かる場合は使うのが自然で、質問を知らない設定の上限にもなる」という整理で答えられる可能性がある。オフラインとの違い（過去を見直せない、未来を見ない、メモリ上限）は[引用の追跡](2026-10-18-query-known-online-video-citation-trace.md)の7節の通り。
- 人間の事前質問の研究は、「質問を先に知ると、関係する情報に注意が向き、それ以外は残りにくい」という点で、質問に合わせて残す設計の比喩になる。ただし根拠としては弱い。

## 4. 次の判断・未確認

- [ ] OnVTGで、質問がストリームの前に与えられるかを本文で確認する
- [ ] TSGSV・OnVTGを引用している論文から、質問を先に与える動画の手法をさらに探す
- [ ] Beyond RAGで、タスクを先に知る設定をどう正当化しているかを読む
- [ ] StreamingBenchのProactive Outputで、質問が先に与えられるかを確認する
- [ ] Carpenter & Toftness（2017）の書誌情報を確認する

## 出典

- [TSGSV (arXiv 2308.07102)](https://arxiv.org/abs/2308.07102)
- [OnVTG (arXiv 2508.04546)](https://arxiv.org/abs/2508.04546)、[ICCV 2025のページ](https://iccv.thecvf.com/virtual/2025/poster/2259)
- [StreamReady (arXiv 2603.08620)](https://arxiv.org/html/2603.08620)
- [OVO-Bench (arXiv 2501.05510)](https://arxiv.org/abs/2501.05510)
- [InfiniPot (arXiv 2410.01518)](https://arxiv.org/abs/2410.01518)
- [Beyond RAG (arXiv 2503.04973)](https://arxiv.org/abs/2503.04973)
- [StreamMem (arXiv 2508.15717)](https://arxiv.org/abs/2508.15717)
- [BPS Research Digest（Carpenter & Toftness 2017の紹介）](https://bps.org.uk/research-digest/heres-simple-way-boost-your-learning-videos-prequestion)、[Toftness et al. 2018 (PDF)](https://pure.royalholloway.ac.uk/files/30437641/JARMAC_Toftness_et_al.pdf)
