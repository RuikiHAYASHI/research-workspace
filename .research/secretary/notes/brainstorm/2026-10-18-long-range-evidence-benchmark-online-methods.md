# 長時間離れた証拠が必要なベンチマークと、それをオンライン処理で解いている論文

- 日付：2026-10-18
- プロジェクト：agentic-streaming-videoqa
- 問い：「長時間離れた証拠がないと解けない問題」を集めたベンチマークを、オンライン処理で解いている論文はあるか。
- 根拠の確かさ：Web検索の要約と、arXiv HTMLを要約ツールで読んだ結果による。原文での確認はまだしていない。数値やモデル名は原文で確認し直す必要がある。

## 1. 結論（2026-10-18時点）

- **ベンチマークを作り、既存のオンライン手法を評価している論文はある**：EgoProbe（arXiv 2610.17128）とEGOSTREAM（arXiv 2605.31557）。どちらも証拠から質問までの間隔を意図して分けて作っており、質問をその時刻に初めて見せる形で評価している。EgoProbeはStreamingモデル（StreamForest、VST、OASISなど）、EGOSTREAMはメモリの管理方法（StreamMem、InfiniPot-V、ReKVなど）を比べている（2026-10-18追記：EGOSTREAMは当初未確認だった）。
- **自分の手法を提案し、離れた証拠が必要なベンチマークで評価しているオンライン手法**として見つかったのは、ReMem（arXiv 2610.05940）だけだった。ただし、使っているのはStreamingBenchの文脈理解の一部とOVO-BenchのBackward Tracingで、どちらも「過去を思い出す」ことは必要だが、**離れていることを保証して作られたベンチマークではない**。
- **離れた証拠を保証したオフラインのベンチマーク**（HERBench、EgoMemReason）を、オンライン処理で解いた論文は見つからなかった。EgoMemReasonは、Streaming評価を今後の課題としている。
- **訂正（2026-10-18）：** 当初「LongVideoBenchをオンライン処理で解いた論文は見つからない」と書いたが誤り。手元の[分類メモ（2回目）](2026-10-17-agent-role-classification-round2.md)の4.3節で、Streaming系の論文7本がLongVideoBenchの結果を報告している。ただし、確認した3本はいずれもLongVideoBenchを「オフライン評価」と位置づけ、届く順に処理したかを書いておらず、Referring Reasoningや動画の長さ別の結果も出していない（表3-2）。

## 2. ベンチマーク一覧（2026-10-18更新）

- リンク先：会議に採録されたものは会議の論文ページ、採録が確認できないものはarXivのページ。
- 「質問の出し方」：Streaming＝質問の時刻までの映像だけを見せ、質問はその時刻に初めて見せる。オフライン＝抜き出したフレームをまとめて見せる。

| ベンチマーク | 採録先 | 動画の規模 | 証拠と質問の間隔 | 質問の出し方 | Streamモデルの評価 |
| --- | --- | --- | --- | --- | --- |
| [EgoProbe](https://arxiv.org/abs/2610.17128) | 採録の記載なし（arXiv、2026-10-12） | Ego4DとEgoLifeが元 | **意図して設定**：3分未満／3〜30分／30分〜12時間／12時間以上。約24%が30分以上。最大約139時間 | Streaming | あり（10本。表3-1） |
| [EGOSTREAM](https://arxiv.org/abs/2605.31557) | 採録の記載なし（arXiv、2026-05-29） | 2,250問（8,528評価） | **意図して設定**：0秒〜8時間超を7段階（30分〜8時間が長期、8時間超が超長期） | Streaming。メモリは質問を知らずに作る | あり（20構成。表3-1） |
| [TeleEgo](https://arxiv.org/abs/2510.23981) | 採録の記載なし（arXiv、2025-10-28） | 1人あたり約14時間。3,291問。音声も含む | 超長期の記憶の質問は、証拠が10〜60分にわたる。間隔そのものの保証は書かれていない | Streaming（証拠の終わりの時刻に質問。5秒以内に答える） | あり（2本。表3-1） |
| [S-EMBER](https://arxiv.org/abs/2607.02689) | 採録の記載なし（arXiv、2026-07-02） | 3,141本、約388時間。1本は平均7.4分 | 結果を0〜30秒から8分超まで間隔別に集計。長時間ではない | 質問時刻までの映像だけを見せる | なし（一般のMLLMのみ） |
| [EgoMemReason](https://arxiv.org/abs/2605.09874) | COLM 2026（会議の論文ページは見つからず、arXivにリンク） | 1週間分の一人称動画。500問 | 1問あたり平均5.1区間、平均約26時間さかのぼる | オフライン（質問時刻までから1024フレームを抜き出す） | 1本のみ（StreamingVLM。表3-1） |
| [EgoMonth](https://arxiv.org/abs/2608.13113) | 採録の記載なし（arXiv、2026-08-13） | 1人20〜120日、300時間以上。1,443問 | 証拠が別の日の動画にまたがる場合がある。間隔の集計はない | オフライン | なし |
| [HERBench](https://openaccess.thecvf.com/content/CVPR2026/papers/Ami_HERBench_A_Benchmark_for_Multi-Evidence_Integration_in_Video_Question_Answering_CVPR_2026_paper.pdf) | CVPR 2026 | 26,806問 | 1問に、別の区間から3つ以上の手がかりが必要。**時間の隔たりの保証は弱い**（一部の手がかりで30フレーム以上のみ） | オフライン（16フレーム） | なし |
| [LongVideoBench](https://neurips.cc/virtual/2024/poster/97862) | NeurIPS 2024（Datasets and Benchmarks） | 最大1時間。6,678問 | 質問が動画の特定の区間を指す（Referring Reasoning）。間隔の保証は未確認 | オフライン | 原論文は未確認（表3-3）。Streaming系の手法7本が結果を報告（表3-2） |
| [OVO-Bench](https://openaccess.thecvf.com/content/CVPR2025/papers/Niu_OVO-Bench_How_Far_is_Your_Video-LLMs_from_Real-World_Online_Video_CVPR_2025_paper.pdf)（参考） | CVPR 2025 | 644本（arXiv版） | Backward Tracingは過去を思い出す。間隔の数値はなく、一部の質問を動画の最後に置いて間隔を広げているだけ | Streaming | あり（3本。表3-1） |
| [StreamingBench](https://arxiv.org/abs/2411.03628)（参考） | 採録の記載なし（arXiv） | 900本、4,500問 | 文脈理解の課題は過去を使うが、間隔の数値はない | Streaming | あり（2本。表3-1） |

## 3. Streamモデルを使った評価

### 3-1. ベンチマークの論文が、既存のStreamモデルを評価しているもの

| 論文 | 評価したStreamモデル | 結果の要点（要約ツールの読み取り。要確認） |
| --- | --- | --- |
| [EgoProbe](https://arxiv.org/abs/2610.17128) | SimpleStream、StreamingVLM、HERMES、StreamForest、OASIS、EventMemAgent、MEMO、ObjectStream、VST、JoyAI-VL-Interaction | 全体ではStreamForestが最高（50.66%）。30分〜12時間では38.7〜48.2%、12時間以上では28〜40%（MEMOが40%で最高）。4択なので偶然は25% |
| [EGOSTREAM](https://arxiv.org/abs/2605.31557) | 同じQwen3-VLに、メモリの管理方法だけを入れ替えて比較：FIFO、StreamVLM、CaM系の統合、StreamMem、InfiniPot-V、StreamingTOM、ReKV（退避あり／量子化して退避）など | 短い間隔では多くが40〜55%でも、長期（30分〜8時間）では25%前後、超長期（8時間超）では20%前後まで下がる。例外はStreamingTOM（超長期34.2%）で、量子化して退避する方法が超長期に効く。4択で偶然は25% |
| [TeleEgo](https://arxiv.org/abs/2510.23981) | MiniCPM-o（唯一のStreaming対応）。VideoChat-Online、Qwen2.5-VL、Qwen2.5-Omniは1秒ずつ渡す擬似的なStreaming | MiniCPM-oは1分ごとにセッションを切ると最高（54.1%）で、10分では30.2%に下がる。記憶の持続時間（MPT）は、適したモデルがないとして報告していない |
| [EgoMemReason](https://arxiv.org/abs/2605.09874) | StreamingVLM（メモリを持つAgentとしてWorldMMも評価） | StreamingVLMは24.2%（5択なら偶然は20%）。最高はGemini-3-Flashの39.6%。評価自体はオフライン |
| [OVO-Bench](https://openaccess.thecvf.com/content/CVPR2025/papers/Niu_OVO-Bench_How_Far_is_Your_Video-LLMs_from_Real-World_Online_Video_CVPR_2025_paper.pdf)（参考） | Flash-VStream、VideoLLM-online、Dispider | Backward Tracingの平均は17.7〜36.1% |
| [StreamingBench](https://arxiv.org/abs/2411.03628)（参考） | VideoLLM-online、Flash-VStream | 文脈理解は24〜27% |

### 3-2. 手法の論文が、上のベンチマークで評価しているもの

| 手法 | 質問の扱い | 評価したベンチマーク | 結果の要点 |
| --- | --- | --- | --- |
| [ReMem](https://arxiv.org/abs/2610.05940) | 後から来る（質問を知らずにメモリを作り、質問で読み出す） | StreamingBench文脈理解、OVO-Bench Backward Tracing、EgoSchema、Video-MME | Qwen2.5-VL-7BでStreamingBench ACUが24.8→44.8、OVO-Bench Backward Tracingが41.3→44.9 |
| [VST](https://arxiv.org/abs/2603.12262) | Streamingで考えながら見る | LongVideoBench（**オフラインとして評価**） | 58.0%（TimeChat-Onlineより+2.6） |
| QueryStream（ICLR 2026） | 最初から知っている | LongVideoBench、StreamingBench、OVO-Bench | [2026-10-18 引用の追跡](2026-10-18-query-known-online-video-citation-trace.md)を参照。LongVideoBenchでの質問の与え方は明記なし |
| [StreamAgent](https://arxiv.org/abs/2508.01875) | 明記なし | LongVideoBench（「オフラインでは動画全体を入力する」と記載） | 57.9%。元のQwen2.5-VL-7B（61.5%）より低く、TimeChat-Online（57.7%）と同程度 |
| [StreamingVLM](https://arxiv.org/abs/2510.09608)（ICLR 2026） | 明記なし | LongVideoBench（評価方法の記載なし） | 54.7→59.0%（元のQwen2.5-VL-7Bから+4.3） |
| [LiveVLM](https://arxiv.org/abs/2505.15269) | 届いた後に質問 | LongVideoBench（「オフライン評価」と記載） | 56.1%。元のLLaVA-OneVision-7Bは55.6%、ReKVは55.8%、StreamMemは54.4% |
| SVMemAgent、Watch-Think-Interact、ThinkStream | 未確認 | LongVideoBench | 未確認（[分類メモ（2回目）](2026-10-17-agent-role-classification-round2.md)の4.3節より） |

**LongVideoBenchについて（確認した3本）：** どれもLongVideoBenchを「オフラインのベンチマーク」として扱い、全体の正答率だけを出している。オンライン処理の手法としてどう処理したかは書かれておらず、Referring Reasoningや動画の長さ別の結果もない。元のモデルからの改善は0.5〜4ポイント程度で、元のモデルより下がる例もある。

**間隔を意図して設定したベンチマーク（EgoProbe、EGOSTREAM）で、自分の手法を提案して評価している論文は見つからなかった。**

### 3-3. 本文を読めなかった・一部しか読めなかった論文

いずれもarXivのHTMLを要約ツールで読んだ。数値は原文で確認し直す必要がある。

| 論文 | 状態 | 理由 |
| --- | --- | --- |
| EGOSTREAM | 前半（約53%）のみ | PDFは大きすぎて取得できず、HTMLは前半だけ読めた。考察や付録の結果は未確認 |
| HERBench | arXiv HTMLの約78%のみ | 会議のページは403で開けなかった。会議版との差は未確認 |
| EgoMemReason | arXiv HTMLの約78%のみ | 後半（付録）は未読 |
| EgoProbe | arXiv HTMLの約92%のみ | 末尾は未読 |
| LongVideoBench | 未読 | 今回は検索結果の要約だけ。原論文がStreamモデルを評価しているかは未確認 |
| S-EMBER、EgoMonth、TeleEgo | 読めた | 採録の有無は、arXivのページで記載がないことだけ確認 |
| QueryStream | 本文はPDFで確認済み（[引用の追跡](2026-10-18-query-known-online-video-citation-trace.md)） | OpenReviewのページは認証画面で開けない |

## 4. 個別のメモ

### EgoProbe（arXiv 2610.17128）
- Ego4DとEgoLifeを元にしている。思い出すまでの間隔は約32秒〜約139時間。
- 結果（要約ツールの読み取りによる。要確認）：Streamingモデルで最も高いのはStreamForest。どのモデルも12時間以上の間隔で最も低く、Streamingモデルは28〜40%。大まかな質問には答えられても、対象の出来事の細部を答える2段目で大きく落ちる（VSTは1段目95%、2段目34%程度）。
- 手法の提案はなく、ベンチマークとデータ作成の仕組みが主な貢献。

### ReMem（arXiv 2610.05940）
- 学習なしで使えるオンラインのメモリ。各時刻でメモリを更新し、質問が来たら質問との類似度でメモリを読み出す。**質問は後から来る設定**（質問を知らない）。
- 評価：StreamingBench（SQA、MCU、ACU）、OVO-Bench Backward Tracing（EPM、ASI、HLD）、EgoSchema、Video-MME、Visual Haystacksを使った針探しの調査。
- 結果（Qwen2.5-VL-7B、1 fps）：StreamingBench ACUで24.8→44.8、OVO-Bench Backward Tracing平均で41.3→44.9。

## 5. 私たちの推論

1. 「離れていることを保証したベンチマーク」は、オフライン（EgoMemReason、EgoMonth）とStreaming（EgoProbe、EGOSTREAM、TeleEgo）の両方にある。HERBenchは複数の証拠を求めるが、時間の隔たりの保証は弱い。ただし、**それを主な評価に使ってオンライン手法を提案している論文**は、今回の検索では見つからなかった。ここは空いている可能性がある。
2. EgoProbeは、間隔ごとの正答率を出せるため、「離れた証拠に強いか」を示す評価先の候補になる。ただし、質問は到着時刻に初めて見せる設定なので、私たちの「質問を最初から知っている」設定とは合わない（[2026-10-18 引用の追跡](2026-10-18-query-known-online-video-citation-trace.md)を参照）。
3. LongVideoBenchは、すでに私たちの最初のデータセットとして使っている（[2026-09-23 データセット選定](2026-09-23-long-videoqa-dataset-selection.md)）。（訂正）Streaming系の手法7本が結果を報告しているので、比較相手はいる。ただし、どれもオフラインのベンチマークとして全体の正答率を出しているだけで、「離れた証拠を、届く順の処理でどれだけ拾えるか」は示していない。Referring Reasoningの部分や、証拠からの間隔ごとに結果を分ければ、既存の報告と違う見せ方ができる可能性がある。

### 5-1. なぜ手法の論文が少ないのか（2026-10-18、林との相談）

林の問い：空いているのは、難しさのせいで需要が少ないからか。

推論（今回の検索結果だけに基づく）：

- **需要はむしろ増えている。** 間隔を保証したStreamingベンチマークが、TeleEgo（2025-10）、EgoMemReason・EGOSTREAM（2026-05）、S-EMBER（2026-07）、EgoMonth（2026-08）、EgoProbe（2026-10）と続けて出ている。「長時間の記憶が必要なのに、既存のStreamingモデルでは解けない」という問題意識が広がっていると考えられる。
- **手法の論文が少ない理由の候補：**
  1. 時期：ベンチマークが出たばかりで、それを主な評価にした手法はこれから出てくる段階。
  2. 主流の評価先が短い：オンライン手法の多くはStreamingBenchやOVO-Benchで遅延やメモリ量を競っており、長い間隔に特化する動機が弱かった。
  3. 評価の費用：数時間〜数日の動画を届く順に処理する評価は重い。
  4. 難しさ：EgoProbeでは12時間以上で28〜40%、EGOSTREAMでは8時間超で20%前後と低く、改善を示しにくい。
  5. オフライン手法が先に強い：全体を見られるRAGやAgentの手法（Ego-R1、EgoRAGなど）が先に成果を出している。
- **位置づけ：** 「空いているが需要がない」より、「ベンチマークがそろい、これから手法が出てくる時期」と見る方が近い。新規性は説明しやすいが、同じ時期に他のグループも取り組んでいる可能性が高いので、最近のarXivをこまめに確認する必要がある。
- これらのベンチマークは「質問を後から出す」前提なので、私たちの「質問を最初から知っている」設定とは合わない点は残る。

## 6. 次の判断・未確認

- [x] EgoProbeの本文で、間隔ごとの結果と評価したモデル名を確認する（表3-1。要約ツール経由なので数値は要再確認）
- [x] EGOSTREAMで、どの手法を評価しているか、オンライン手法を提案しているかを確認する（既存のメモリ管理の比較で、手法の提案はなし。後半は未読）
- [x] TeleEgo、S-EMBER（arXiv 2607.02689）、EgoMonth（arXiv 2608.13113）で、オンライン手法を評価しているかを確認する（TeleEgoのみ。表3-1）
- [ ] HERBenchをオンライン処理で解いた論文がないか、引用の追跡で確認する
- [x] LongVideoBenchをオンライン処理で解いた論文がないか確認する（7本が報告。3本を確認。表3-2）
- [ ] SVMemAgent、Watch-Think-Interact、ThinkStreamで、LongVideoBenchをどう評価したかを確認する
- [ ] EGOSTREAM、HERBench、EgoMemReason、EgoProbeの未読部分を読む（表3-3）
- [ ] LongVideoBenchの原論文で、Streamモデルを評価しているかを確認する
- [ ] EgoMemReasonのCOLM 2026の論文ページを探してリンクを差し替える
- [x] 手順を決めて体系的に数え直した（2026-10-18）：該当9本（強い0本、弱い9本。すべてLongVideoBenchの全体正答率のみ）、オンラインか不明17本 → [体系的な調査](2026-10-18-long-range-evidence-online-methods-systematic-search.md)

## 出典

- [EgoProbe (arXiv 2610.17128)](https://arxiv.org/html/2610.17128)
- [EGOSTREAM (arXiv 2605.31557)](https://arxiv.org/pdf/2605.31557)
- [TeleEgo (arXiv 2510.23981)](https://arxiv.org/abs/2510.23981)
- [EgoMemReason (arXiv 2605.09874)](https://arxiv.org/html/2605.09874v2)
- [S-EMBER (arXiv 2607.02689)](https://arxiv.org/pdf/2607.02689)
- [EgoMonth (arXiv 2608.13113)](https://arxiv.org/pdf/2608.13113)
- [HERBench (arXiv 2512.14870)](https://arxiv.org/abs/2512.14870)、[CVPR 2026版PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Ami_HERBench_A_Benchmark_for_Multi-Evidence_Integration_in_Video_Question_Answering_CVPR_2026_paper.pdf)
- [LongVideoBench (arXiv 2407.15754)](https://arxiv.org/abs/2407.15754v1)、[NeurIPS 2024のページ](https://neurips.cc/virtual/2024/poster/97862)
- [OVO-Bench (arXiv 2501.05510)](https://arxiv.org/abs/2501.05510)、[CVPR 2025版PDF](https://openaccess.thecvf.com/content/CVPR2025/papers/Niu_OVO-Bench_How_Far_is_Your_Video-LLMs_from_Real-World_Online_Video_CVPR_2025_paper.pdf)
- [StreamingBench (arXiv 2411.03628)](https://arxiv.org/abs/2411.03628)
- [EgoMemReason プロジェクトページ](https://egomemreason.github.io/)、[EGOSTREAM プロジェクトページ](https://saroo25.github.io/Egostream/)
- [ReMem (arXiv 2610.05940)](https://arxiv.org/html/2610.05940)
- [Video Streaming Thinking / VST (arXiv 2603.12262)](https://arxiv.org/pdf/2603.12262)
