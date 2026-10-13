---
date: 2026-10-14
project: agentic-streaming-videoqa
source_todo: null
topic: 予習AgentとText Memoryのオンライン動画理解・Memory形式の探索
status: exploratory
tags: [brainstorm, literature-review, streaming, anticipation, text-memory]
---

# 予習AgentとText Memoryの文献調査・探索メモ

## 背景と問い

- 研究はQuestionを動画開始時に既知とするchunk-level causal streaming VideoQAで、Situation -> Summary -> Answerのテキスト累積要約方式を最小baselineとしている。
- MTGではテキストMemoryをまず実装する一方、KV/visual featureも区別して先行研究調査することを確認済み。
- 直近MTGには、Summaryで重要イベントを消さない別記憶、および学習データの質問傾向を先に学んで重要情報を予習するAgentという未決の提案がある。
- 今回はテンプレや固定評価軸の設定ではなく、これらの発想に近い論文を具体的に調査した。

## 予習の意味

- A: 将来起きるイベント・時間・領域を予測し、次の観測に反映するfuture-event anticipation。
- B: 将来質問されそうな意味情報を予め想定・学習し、質問未到着の段階から重要内容を記憶するfuture-query anticipation / query-distribution prior。
- AとBは異なる。さらにQueryが既知のときの観測計画とも区別する。

## 予習に特に近い論文

- **SAVEMem**, https://arxiv.org/abs/2605.07897 (2026-05): モデル開始時に設定した固定5 pseudo-questions（物体、数、動作・イベント、シーン変化、位置関係）を意味priorとして使い、visual tokensを短中長の三層に保管/選別する。現実のquery到着時にread-only retrievalする。質問傾向の事前活用に近いが、質問をAgentが生成するわけではない。**論文Appendix A.4はpseudo-streaming評価であり、実時間の各フレーム推論遅延は測定していないと明示**。Appendix Bに5問が掲載。固定質問のドメイン適応は今後の課題と著者が明記。
- **SVMemAgent**, https://arxiv.org/abs/2609.18540 (2026-09): 多様なVideoQAペアからGRPO報酬で、質問未知時でもフレームをkeep/replace/discardするAgent方策を学ぶ。問いの分布を学ぶ発想は教師の予習Agentと近い。ただし結果はvisual frame memoryであってtext event memoryではない。
- **StreamAgent**, https://arxiv.org/abs/2508.01875 (2025初稿/2026改訂): 過去text m_t + video observationから未来のtemporal/spatial task evidenceを予測、Reactive/Proactive/Speculative計画を比較し、cropや追跡などを制御。将来イベント予測Aであり実際のqueryが前提。
- **Em-Garde**, https://arxiv.org/abs/2603.19054 (2026): 既知queryを視覚proposalsに変換しストリーム中に軽量照合して応答。Query予測ではなくquery-aware前処理。
- **ProVideLLM**, https://arxiv.org/abs/2504.13915 (ICCV2025): Procedural action anticipationとplanningに関連。長期言語化＋短期visual tokens。
- **Memento**, https://proceedings.iclr.cc/paper_files/paper/2026/hash/3b5f4587a0bdb81ecc6ce9d82320a5c2-Abstract-Conference.html (ICLR2026): 全日動画のproactive assistant、dynamic memoryとquery-related selection、質問予測Agentそのものではない。
- **FutureOmni**, https://proceedings.mlr.press/v306/chen26ad.html (ICML2026): multimodal future-event forecastingの近傍研究。Agentの記憶制御までは対象外。

## オンライン動画でText Memoryを持つ重要な論文

- **Lando et al.**, https://arxiv.org/abs/2506.16450 (2025): streaming egocentric videosをMLLM descriptorで軽量なtext-only historical memoryへ変換し、LLM reasonerがmultiple-choiceを解く。QAEgo4D-Closedで56%と3.6kB/minは著者報告。自研究のテキストMemory baselineとの直接比較候補。
- **Lando/Forte et al. Edge**, https://arxiv.org/abs/2602.22455 (2026): 逐次textual descriptor threadと非同期QA thread。8GB GPUで動く本当のオンライン推論速度・遅延を調査。text historical memoryを中心に据える。
- **Think While Watching**, https://arxiv.org/abs/2603.11896 (ECCV2026): 逐次segment-level textual memory notesでイベント等を引き継ぎ、causal maskとdual KV cacheでwatching/thinkingを並行。歴史記憶はtext notesだが、runtimeにKVは存在する。
- **OneStreamer**, https://arxiv.org/abs/2610.01762 (2026-10-01): Proactive Hierarchical Caption Memory (PHCM)で時間情報付き局所captionと完成イベントsummaryを出力し、過去の視覚特徴を見直さずrecent visual windowと併用する。**イベントをテキストで別途残す案との最重要先行例**。
- **Watch-Think-Interact**, https://arxiv.org/abs/2609.37035 (2026-09): 観測時間範囲付き自然言語memory entriesを使い、回答できなければ該当する過去の視覚証拠を再取得して再検討する。raw過去映像再アクセスを許すためstreaming protocolに注意。
- **StreamAgent**, https://arxiv.org/html/2508.01875 (§3.1): text recurrent m_tをcaption updateし、劣化補償にはKV Cache selective recall。
- **ProVideLLM**, https://openaccess.thecvf.com/content/ICCV2025/html/Chatterjee_Streaming_VideoLLMs_for_Real-Time_Procedural_Video_Understanding_ICCV_2025_paper.html: 長期のverbalized text tokens＋短期visual tokens。
- **EventMemAgent**, https://arxiv.org/abs/2602.15329 (ECCV2026): イベントごとのcaption+first frame+semantic embedding+change logsを長期に保存し、Agentがretrieval/OCR等のtoolsを利用。
- **Retrieval-Augmented Online Textual Memory for Episodic Memory Video Question Answering** (CBMI2026)は研究者のpublication listで存在だけ確認。論文本文は今回未確認、詳細を断定しない。

## Memory表現の整理（直交する観点）

表現媒体には以下がある。
1. text record / append-only event notes / global summary
2. raw image/frame/video segments
3. image encoder由来のvisual feature / visual token
4. LLMのattention KV Cache
5. latent/recurrent state (LatentStream https://arxiv.org/abs/2609.04131 やVideoLLaMB)
6. 物体・イベントの構造化graph/database（中身がtext node/feature node等を組み合わせる）
7. inference時にパラメータとして保持するdynamic parametric memory（OVG-HQ-Unify https://openaccess.thecvf.com/content/ICCV2025/papers/Zeng_OVG-HQ_Online_Video_Grounding_with_Hybrid-modal_Queries_ICCV_2025_paper.pdf）。最後はVideoQAではなくonline grounding。

混合方式はtext+visual、text+KV、text+image+embedding、visual+KV、latent+featuresなど任意に存在する。「KVを通常の推論で使う」と「KVを長期Memoryとして保存・再呼出する」は異なる。

「重要event/summary/multi-timescale/短期長期/階層」は保存対象の構造と運用の話で、媒体の分類とは違う。「Agent」は何を保持し統合・検索するか決定するpolicyであり保存媒体そのものではない。

## 今回の研究上の検討

- 「text memory自体が新しい」「イベント要約を記録するだけで新しい」という主張は成立しない。OneStreamer / TWW / Lando / EventMemAgent等を比較すべき。
- Query=t0既知の自研究と、質問未到着を前提にしたSAVEMem・SVMemAgentは条件が異なる。質問傾向の事前学習に加え、その動画で既知の個別質問にどう適応するかは検討余地だが、実現・新規性は未検証。
- 2026新論文OneStreamerのEvent Summaryと、現行累積Summaryの書換劣化、独立Event Ledger、Evidence/Grounding維持の違いを精読する価値が高い。
- SAVEMemのAppendix A.4はpseudo-streamingとtrue streamingの違いを丁寧に書いており、今後の論文比較時も必須の留保。
- これは探索記録であり、実装方針の決定・spec化・評価による裏付けではない。

## 非固定の次の読書候補

- 予習: SAVEMem と SVMemAgent の事前質問priorを対比し、StreamAgentの未来イベント予測とどう結び付けるか検討。
- テキスト記憶: Lando2025 -> OneStreamer -> TWW/WTI -> EventMemAgent のいずれかから問いを発展させる。
- この順序は推奨であり、読みながら自由に変えてよい。
