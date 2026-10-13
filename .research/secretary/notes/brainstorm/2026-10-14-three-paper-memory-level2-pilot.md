---
date: 2026-10-14
project: agentic-streaming-videoqa
source_todo: "2026-10-09 MTG: 過去映像情報をどうMemoryとして維持するかの関連研究調査"
topic: three-paper-memory-level2-pilot
status: exploratory
tags: [brainstorm, literature-review, level2, memory, streaming-videoqa]
---

# Level 2試験調査：OneStreamer・EventMemAgent・OASIS

## 範囲と判断
- ユーザーはStreamAgentとStreamForestを既に一定程度理解しているため除外。OneStreamer / EventMemAgent / OASISを「方法の入力からMemory維持・回答時利用まで」を説明できる深さでまとめる。
- 「過去の映像情報をどうMemoryとして維持するか」に対して3つの異なる回答を比較する。イベントという名称が共通でも、同じ表現/操作ではない。
- 2026-10-14時点の公開情報。最新の学会採録を優先: EventMemAgentはECCV2026 LNCSの正式論文集、OASISはCVPR2026 CVF Open Access。OneStreamerは2026-10-01 arXiv公開で今回、学会採択情報は確認していない。
- 原典PDF/著者公開概要で確認できた記述と、そこからの研究上の解釈を分離する。論文の全実装・全benchmarkを網羅した監査ではない。

## OneStreamer
- 論文: OneStreamer: Unifying Perception, Memory, and Proactive Response in Streaming Video Interaction
- arXiv: https://arxiv.org/abs/2610.01762
- 著者コード: https://github.com/MCG-NJU/OneStreamer

### 目的
動画の将来質問が未知でも、古い映像の必要な証拠を再利用できるようにする。現在映像の理解を圧迫せず、十分な証拠が集まった時点での応答も統一的に学習する。

### Memory処理フロー（Level 2）
1. 映像ストリームの最近Nフレーム（論文比較の設定はRecent-16）をvisual tokensとして維持。
2. モデルが観測した短い区間の詳細な内容を `</Observe>` captionとして生成し、完了したイベント/区間の情報を `</Summary>` として生成する。いずれも時刻に対応づける。
3. 作成されたcaption/summaryを生成順でText履歴へ追加。過去のvisual tokensがrecent windowから外れても記述は残る。過去のvisual featuresを外部検索で再取得する前提はない。
4. Queryが来たとき、Text履歴と現在のvisual windowを利用する。別途PSTLによってSilence/Standby/Responseの制御状態を学習し応答タイミングを扱う。

### Evidence
- arXiv Abstractと著者コードによるPHCMの説明。
- PHCM（Recent-16 + captions）対FIFO（Recent-16のみ）のOVOBench-Backward ASI：71.6対63.5（論文Table 2）。リアルタイム認識指標は同等以上。ただし全履歴Visualを使うFullが一部の指標でPHCMを上回る。
- 限界と留保: Captionが必ず真実とは確認できない、無期限のtext history budget/削除政策は今回未確認、Question=t0既知と未来Query未知の前提差、回答段階のみの速度計測をstream全体の速度と混同しない。

## EventMemAgent
- 論文: EventMemAgent: Hierarchical Event-Centric Memory for Online Video Understanding with Adaptive Tool Use
- ECCV2026 Springer公式論文集 Part XXVIII（pp.318–334）: https://link.springer.com/book/10.1007/978-3-032-37624-4?page=1
- arXiv版（v2）: https://arxiv.org/abs/2602.15329
- 著者コード: https://github.com/lingcco/EventMemAgent

### 目的
無限長の動画を有限のcontextで扱いつつ、古い出来事を構造化して後の質問に使う。過去の情報の単純な固定間隔切出しでは出来事が途切れる問題と、固定的なツール利用の限界に対処。

### Memory処理フロー（Level 2）
1. 1 FPSで到着したフレームを短期Memory（STM、最大32フレーム）へ。STMは最近の複数eventの集合で末尾eventが伸びる。
2. 新フレームと現在eventのグレースケールhistogramをPearson相関で比べ、外観の不一致に基づきイベント境界を検出。意味理解そのものによる境界検出ではない。
3. STM容量が埋まった際、複数eventなら最古の完了eventを長期Memory（LTM）へ移す。長時間続く同一eventだけが容量を占めた場合、event内部のフレームをreservoir samplingで保持する。
4. LTMにはeventごとに、最初の代表フレーム（visual anchor）、MLLMが作成したcaption、検索用embedding、連続event間の変化のlogを構造化保存。
5. 質問時刻に存在する最近フレームと、必要時の検索結果を利用。AgentはSearch Memory（時間条件/意味類似）、OCR、Object Detectionを適応的に選択。Qwen3-VL-8Bを用いたAgentic RL/GRPOでこの判断の方針を学習する。

### Evidence
- ECCV2026公式論文集収載確認。原著arXiv v2 Fig.1・Sec.3.2・3.3、Table 3。
- OVO-Bench Overall 60.75、StreamingBench Overall 77.00（著者報告）。固定30秒区切りMemoryでは58.27/75.09に低下（同条件の比較）。したがって固定区間よりイベントベースがこの評価条件で有利という根拠はあるが、全情報が損失なく保持できるわけではない。
- 限界と留保: 動画のsemantic action境界を厳密に認識する保証なし、古いイベントからは最初の画像等に依存する可能性、RL・外部ツールも寄与するため全体精度をMemory単独の効果と解釈しない。

## OASIS
- 論文: OASIS: On-Demand Hierarchical Event Memory for Streaming Video Reasoning
- CVPR2026正式CVF: https://openaccess.thecvf.com/content/CVPR2026/html/Liang_OASIS_On-Demand_Hierarchical_Event_Memory_for_Streaming_Video_Reasoning_CVPR_2026_paper.html
- arXiv: https://arxiv.org/abs/2604.17052
- 著者コード: https://github.com/Solus-sano/OASIS

### 目的
動画履歴を無制限に入力するのも全履歴を強く圧縮するのも問題で、質問に必要な「少数の歴史的証拠」を探せるようにする。現在の認識を古い記憶で妨げない。

### Memory処理フロー（Level 2）
1. 高密度なshort windowと、広い範囲を低密度に見るmedium bufferを保持（論文実験はshort 8秒/2FPS、medium 32秒/1FPS）。
2. 中期bufferの区間をMLLMでテキスト要約し、時刻範囲・keyframes・summary・embedding・階層深度を持つEvent Forestのleaf root nodeに保存。ここでのleaf生成は基本的に到着した一定区間を扱うもので、EventMemAgentのヒストグラムによる意味境界検出とは異なる。
3. root node数が上限を越えたら、時間的に隣接するroot同士を類似度と階層depthで比較してmerge。親nodeへkeyframes（再サンプリング）とsummaryを引き継ぎ、古い子nodeも階層的に利用できる。
4. 質問が来たら現在/中期frame、上位root summaries、過去QA summaryだけでcoarse reasoning。証拠が足りない時だけ検索へ。
5. Fine reasoningでは元の質問をそのまま検索するのでなく、「何が確認できれば答えられるか」という意味的検索意図をMLLMが生成。Event Forestのnode（およびQA履歴）から関連するkeyframes・Textを検索し、回答する。方法はtraining-freeで既存MLLMに付加できる。

### Evidence
- CVPR2026公開論文、Fig.3、Sec.3.1, 3.2, 4.4–4.5、Tables 1, 4, 5。
- OVO-Bench Qwen3-VL-8B: Perception Avg 66.79 → 78.14、Backward Avg 51.19 → 57.21（著者再実験条件の差分）。同条件でFlat Memoryとw/o RAGを除いた時に低下。Memoryの階層性と読出し方の両方が寄与する。
- 限界と留保: leafの要約/代表frame生成は情報を圧縮するので全細部の保持保証はない。検索が当たらない場合の失敗は残る。QAは質問到着時刻までを使い、質問が初めから既知の本研究baselineとは違う。評価用の疑似逐次実行と常時リアルタイム処理の区別には追加評価が必要。

## 横断比較と研究への解釈

| 観点 | OneStreamer | EventMemAgent | OASIS |
| --- | --- | --- | --- |
| 主な長期Memory | 時刻付Text captions + event summaries | event tuple（visual anchor+caption+embedding+change log） | 階層Event Forest（time/keyframes/text summary/embedding） |
| 写像のタイミング | 観測時にcaptionを生成し追加 | STMのeventが追い出されるとLTM化 | medium bufferの区間を要約しroot nodeへ |
| 保存単位 | 短区間captionと完了event要約 | 外観変化によって区切ったevent | 時間区間nodeを段階的にmerge |
| 古いMemoryの管理 | Text履歴へ追加、古いvisualはrecent windowから消える | event単位アーカイブ + 長時間event内reservoir | root数budgetを維持し、隣接nodeをmerge |
| 回答で使う | Text履歴とrecent visuals、外部検索なし | Agentによるevent検索/OCR/物体検出 | Coarse→必要時のみ意図に基づくevent検索 |
| 研究上の焦点 | 観測時の証拠の書込み | どの映像をeventとして維持するか、Agentのtool選択 | 既存の履歴から必要な証拠を選び出す |

**今回の問いへの回答（探索レベル）**: 映像情報のMemory維持には、局所Captionの追記、短期frameから長期event tupleへの移管、階層要約と検索など別の設計が存在。単にeventと言っても、保存媒体、切出し単位、更新方法、質問時利用は異なる。

**反例/未解決**: どの方式も「古いすべての重要factが必ず残る」ことは未証明。自研究の累積Summaryの劣化原因を、単にevent化すれば解決すると結論しない。OneStreamerのQuery未知と、他論文の途中Queryと、現研究のQuery=t0は別の実験設定。

**次の深掘り候補**: text historyの容量と削除政策、event境界の品質、event LTMの詳細の損失、plan-based retrievalの失敗率、各手法のEnd-to-End streaming計算時間。これらはspecや実装許可ではない。
