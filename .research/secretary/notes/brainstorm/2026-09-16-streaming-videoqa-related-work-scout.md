---
date: 2026-09-16
project: agentic-streaming-videoqa
source_todo: "2026-09-11 MTG: Agent系、Memory、動的chunk、予測とAgent actionの先行研究調査"
topic: streaming-videoqa-related-work-scout
status: exploratory
tags: [brainstorm, literature-survey, streaming-videoqa]
---

# 9/11 MTG由来の先行研究一次調査（2026-09-16）

## 位置づけ・調査範囲

9/11議事録と9/15 approved text-memory specを踏まえた、関連論文の**存在確認と概要レベルのスクリーニング**。各論文の抄録・公開概要を中心に確認した。数式、評価条件の統一、実装コード、future accessの実装監査は未実施。以下の「類似する」は問題設定まで同一という主張ではない。

本研究の比較基準: Queryがt=0から既知、入力は時間順、future chunkへアクセスしない。現在approvedの実装specは1 frame + previous text memoryからnew text memoryを生成し、Memory容量最適化、動的chunk、multi-timescale、専用予兆Memory、計算モデル切替はscope外。参考: `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-11-mtg.md`、同`specs/2026-09-15-streaming-text-memory-spec.md`。

## 1. Agent系のVideo理解・VideoQA: 何を判断するか

- **StreamAgent** (arXiv:2508.01875): 質問と過去観測から将来の関連時間帯・領域を予測して観測を計画し、対象領域への注視・追跡、WAIT/回答を判断。textの逐次更新Memoryと、CPUへ退避したKVの選択的再読込を併用。論文の問題設定は質問が時刻tに与えられるケースで、必ずしもt=0固定ではない。https://arxiv.org/abs/2508.01875
- **EventMemAgent** (arXiv:2602.15329、2026-09-11改訂): 短期イベント区切り+イベント単位サンプリング、長期イベント蓄積を持つonline agent。複数粒度の知覚ツールを反復利用。https://arxiv.org/abs/2602.15329
- **Response-G1** (arXiv:2605.07575): streaming clipから質問に沿うscene graphをオンライン生成→関連過去グラフを検索→根拠充足に応じて回答/沈黙を決定。Agentのツール探索そのものより応答判定に重点。https://arxiv.org/abs/2605.07575
- **Active Video Perception (AVP)** (arXiv:2512.05774 / CVPR Findings 2026): planner→observer→reflectorが、質問に足りない証拠を選んで再観測する。長動画をインタラクティブに探索する設計のため、未来未到着を禁止する厳格なstreamとは区別。https://arxiv.org/abs/2512.05774
- **QueryStream** (ICLR 2026): Queryと時間的な新規性を基に視覚tokenを削除し、関連性と情報密度を見て発話を起動する。Agentと呼称されなくてもQuery-aware KEEP/DROPと判断器の直接比較対象。https://proceedings.iclr.cc/paper_files/paper/2026/hash/0b17d256cf1fe1cc084922a8c6b565b7-Abstract-Conference.html

一次解釈: 「Agentが判断する」「Queryで捨てる」単独では新規性を主張できない。Agentのactionが観測/回答なのか、Memory write / summarize / deleteなのか、Queryがいつから使用可能かを区別する。

## 2. Memoryの実体、時間幅、重要イベント

- **StreamAgent**: 要約・更新するtextual memory とKV cacheの階層退避/選択的再読込を併用。単一のtext stateを逐次更新する設計が、古い証拠の脱落に関する比較の出発点。https://arxiv.org/abs/2508.01875
- **StreamMem** (arXiv:2508.15717): 実Query未取得でも汎用Query tokenとのattentionでKVを圧縮し固定長保持。text memoではない。https://arxiv.org/abs/2508.15717
- **StreamForest** (arXiv:2509.24871): 最近の細かい知覚窓と、時刻距離・類似度などでイベントを木状に統合する長期visual memory。https://arxiv.org/abs/2509.24871
- **EventMemAgent**: 短期バッファでイベント境界検出/イベント単位サンプリング、長期にイベントごとに蓄積。https://arxiv.org/abs/2602.15329
- **LatentStream** (2026-09-03, arXiv:2609.04131): Query未知でshort/mid/long 3階層の視覚履歴を固定予算で整理し、Query到着後に関連情報を固定長latent memoryへ内在化。textの複数要約とは異なる。https://arxiv.org/abs/2609.04131
- **SAVEMem** (arXiv:2605.07897): 疑似質問集合を使ってQuery未知のMemory作成段階から意味的重要度を反映、Query到着後にshort/mid/longの検索範囲を調整。https://arxiv.org/abs/2605.07897
- **SelectStream** (arXiv:2606.16353): 意外性で書込窓を調整し、優先度を保って統合、固定容量の潜在的なmemory graphからQuery条件付き検索。https://arxiv.org/abs/2606.16353
- **FOLIO** (arXiv:2607.13298): 注目するentity/出来事の詳細は厚く、周辺文脈は短く、短期視覚バッファと長期semantic memory/視覚証拠cacheを連結。https://arxiv.org/abs/2607.13298

一次解釈: multi-timescale、重要イベント優先、固定budget、query-aware selectionは先例あり。ただしこれらの多くはvisual/KV/latent表現、Query後着の設定であり、「t=0 Queryで更新可能な説明可能なtext recordをKEEP/SUMMARIZE/DELETE」まで同一かは未監査。Memory更新による古い事実の消失を具体的QAで検証する比較が必要。

## 3. chunkの長さとイベント単位

- **VideoScaffold** (arXiv:2512.22226): 到着映像に対し予測誘導でイベント境界を調整し、関係するsegmentを段階的に統合。可変長のイベント表現であり、「Agentが次の取得chunkの秒数を指示する」のと同義ではない。https://arxiv.org/abs/2512.22226
- **EventMemAgent**: event boundary検出とイベント単位のreservoir samplingで固定長バッファを動的運用。https://arxiv.org/abs/2602.15329
- **StreamForest**: 類似度・時間距離等でframeをevent-level treeへ統合。入力loaderのchunk長をAgentが変える提案かは未確認。https://arxiv.org/abs/2509.24871
- **Q-Frame** (arXiv:2506.22139): 質問と動画内容に応じてframe選択と解像度配分を変えるが、長動画の通常QAであり厳格な未来未到着条件とは別。https://arxiv.org/abs/2506.22139

一次解釈: 動的な時間粒度自体には先例がある。「入力chunk長」「frame sampling密度」「イベント区切り」「過去Memory統合粒度」を混同しないこと。Agentが未来未到着の次chunk長そのものを決める先例は、この調査だけでは確証なし。

## 4. 将来予測、知覚行動、モデル/計算切替

- **StreamAgent**: 過去と質問から将来の関連時刻・空間領域を見積もり、後続frameで注視・追跡・zoomなどの知覚actionを選ぶ。未来画像そのものを見ることではない。https://arxiv.org/abs/2508.01875
- **VideoScaffold**: 予測をイベント境界の修正に利用。予測の目的は長期イベントのcaption予想ではなく分割粒度調整。https://arxiv.org/abs/2512.22226
- **R3-Streaming** (arXiv:2605.17921): Queryごとに古いMemoryを圧縮→回答準備完了判定→難しい質問なら強いモデルへ計算routing。『encoderの切替』が記載されているわけではなくモデルroutingの例。https://arxiv.org/abs/2605.17921
- **Q-Frame**: Queryに応じてframeと解像度を選び視覚token/計算budgetを配分。ただしoffline long-video系で、未来予測を利用するstreaming Agentとは異なる。https://arxiv.org/abs/2506.22139

一次解釈: anticipation、将来に備えた観測選択、難易度に応じたモデルroutingはそれぞれ先例あり。「長期anticipation → 未来未到着のchunk長 / encoder / Memory書込方針を同時制御」の厳密な一体化は未確認で、新規性の確定ではない。

## まとめと次の調査判断（未承認候補）

確認済み: 4観点とも関連先行研究あり。特に **StreamAgent / QueryStream / EventMemAgent / VideoScaffold / SelectStream / R3-Streaming** が直接比較先として浮上。2026年5–9月の新しい論文を加えると、「Query-awareなMemory処理は未研究」とは言えない。

未解決: 各論文のQuery提供時点・future access禁止・過去raw video再読込可否、実際のwrite/keep/delete action、Memory型、時間幅変更の対象、予測 horizon、latency・budget・評価protocol、実装再現性。厳密な新規性・優劣は未判断。

次の候補: (a) StreamAgent/QueryStream/SelectStreamをQuery timingと書込規則で比較、(b) StreamForest/EventMemAgent/LatentStreamをMemory型と消失防止で比較、(c) VideoScaffoldとR3を動的制御の対象別に比較。TODOへの自動反映なし。既存approved specおよびコードに変更なし。
