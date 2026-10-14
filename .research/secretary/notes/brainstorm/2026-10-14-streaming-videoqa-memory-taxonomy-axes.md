---
date: 2026-10-14
project: agentic-streaming-videoqa
source_todo: "Memoryに関する先行研究を観点別に整理する"
topic: streaming-videoqa-memory-taxonomy-axes
status: exploratory
tags: [brainstorm, literature-review, memory, taxonomy, streaming-videoqa]
---

# 長時間・Streaming VideoQAのMemory分類軸：軸の設計フェーズ

## 出発点と目的
2026-10-14のMTG後の相談において、論文本数を固定せず、長時間動画理解におけるMemoryを大枠テーマとして調査する。ユーザーが提示した「扱う情報 × 表現形式」の多軸対応表のような分類を最終目標とするが、**今回は個々の論文を分類する前に、どんな比較軸があるか整理する段階**。本分類は提案であり、確定した学術taxonomy、approved spec、実装指示ではない。

## 根拠の位置付け
- 2026-09-11 MTG: text / KV / feature、逐次処理、複数時間尺度Memory、古い記憶の希釈を調査する。
- 2026-10-09 MTG: 累積Summaryの情報脱落懸念、重要イベントの別保存、Memoryの保存/更新/検索方針を比較する。
- 2026-10-14 memory-literature-review-tree-strategy: 媒体、構造、更新操作、処理設定は異なる軸であり、一論文の複数所属を許容する。
- 公開一次研究の例: StreamForest（視覚イベント階層、https://arxiv.org/abs/2509.24871）、OASIS（階層イベントとon-demand retrieval、https://openaccess.thecvf.com/content/CVPR2026/html/Liang_OASIS_On-Demand_Hierarchical_Event_Memory_for_Streaming_Video_Reasoning_CVPR_2026_paper.html）、MuKV（複数粒度のKV cache圧縮と検索、https://openaccess.thecvf.com/content/CVPR2026/html/Xiao_MuKV_Multi-Grained_KV_Cache_Compression_for_Long_Streaming_Video_Question-Answering_CVPR_2026_paper.html）。
- 上記の例は軸の必要性を示すための参照であり、全論文について全軸の分類を実証済みという意味ではない。

## 7軸（ユーザー未承認の暫定案）
| 軸 | 質問 | 暫定分類の例 |
| --- | --- | --- |
| I: 記憶する情報 | 何を覚える？ | Scene / Entity / State / Action / Event / Temporal relations / Uncertainty・hypothesis |
| R: 表現形式 | どんなデータとして覚える？ | Free text / Structured text / Graph / Raw frame / Visual feature-token / KV cache / Latent state |
| G: 単位・区切り | 何を一件の記録として扱う？ | Frame / Chunk / Event / Entity history / Video-global |
| S: 構造・時間尺度 | どこにどう配置する？ | Recent buffer / Flat chronological log / Short+long / Hierarchical tree / Indexed archive |
| W: 保存選択 | 何を保持/破棄する？ | All / Periodic / Change / Similarity・novelty / Query relevance / Semantic importance・anticipation |
| U: 更新・維持 | 新情報で何を変える？ | Append / Rewrite / Edit / Merge / Compress / Evict / Promote |
| Q: 読み出し | 回答時にどう使う？ | Entire memory / Time-based / Semantic retrieval / Query-based / Hierarchical / Evidence revisit |

### 軸1: I（記憶する情報）
| 仮コード | 小分類 | 例 |
| --- | --- | --- |
| I1 | Scene context | 場所、背景、全体状況 |
| I2 | Entity identity / properties | 人物、物体、同一ID、属性 |
| I3 | State / state change | 開閉、所持、位置、変化前後 |
| I4 | Action / interaction | 持つ、注ぐ、移動する、人物-物体の作用 |
| I5 | Event / episode | 一まとまりの出来事、開始/終了、出来事の説明 |
| I6 | Temporal / causal relation | 順序、前後、繰り返し、因果関係 |
| I7 | Uncertainty / hypothesis / task status | 未確認事項、予測、質問に必要な証拠の充足状況 |

注意: 「質問に関連するか」は情報の内容ではなく**保存選択W**の条件にもなる。I軸では内容の種類を記し、query-awareな選別方法はWへ分ける。Event I5とAction I4の同時タグを許す。

### 軸2: R（表現形式）
| 仮コード | 小分類 | 例 |
| --- | --- | --- |
| R1 | Free-form text | Caption、累積Summary、自然言語イベント |
| R2 | Structured text | JSON event records、entity-state fields、Timestamp付き記録 |
| R3 | Graph / relation structure | Event graph、entity graph、node/edge |
| R4 | Raw / sampled visual | フレーム、Keyframe、Clip画像列 |
| R5 | Visual feature / token / embedding | 画像特徴、Visual token、Event embedding |
| R6 | KV cache retained across time | 過去視覚入力のkey/value、検索可能なKV |
| R7 | Other latent / recurrent state | hidden state、learned memory slot、圧縮された非言語状態 |

注意: Text+KV、Text+Visualのようなhybridは独立した排他的カテゴリーにせずR1/R6等の**複数所属**で示す。標準推論中だけの一時KVを自動的に「長期記憶」とは数えない。

### 軸3: G（記憶の単位）
| 仮コード | 小分類 | 例 |
| --- | --- | --- |
| G1 | Frame / patch | 個々のフレーム・パッチ |
| G2 | Chunk / clip / fixed interval | 4秒間など区間単位 |
| G3 | Event / variable interval | 行動・視覚変化で切る出来事単位 |
| G4 | Entity history / track | 一人・一物体の履歴 |
| G5 | Global / video level | 動画全体までの累積状態 |

G3の区切り方（固定時間、視覚類似度、prediction error、意味的状態変化、Agent決定）は補助フィールド`boundary_rule`で保持。複数粒度はG1+G3等の複数所属とS階層構造で示す。

### 軸4: S（構造・時間尺度）
| 仮コード | 小分類 |
| --- | --- |
| S1 | 最近情報だけのsliding/recent buffer |
| S2 | 時刻順に並ぶflat / event ledger |
| S3 | Short-term + long-termの役割分担 |
| S4 | Hierarchical / tree / multi-timescale |
| S5 | Indexed external archive / database |

### 軸5: W（保存対象の選択）
| 仮コード | 小分類 |
| --- | --- |
| W1 | 全観測を保存 |
| W2 | 固定間隔・予算に応じて保存 |
| W3 | 変化やevent boundaryで保存 |
| W4 | 類似度・新規性・冗長性に応じて保存 |
| W5 | Question relevanceに応じて保存 |
| W6 | 意味的重要度・未確実性・将来予測に応じて保存 |

`decision_maker`（rule / trainable module / LLM Agent / mixed）をWとは別にメタデータで記録する。基準と判断主体を混同しない。入力段階のframe samplingとMemory書込選択も分ける。

### 軸6: U（更新・維持）
| 仮コード | 小分類 |
| --- | --- |
| U1 | Append-only（追記） |
| U2 | Recurrent rewrite（累積記憶全体の再生成） |
| U3 | Local edit / upsert（局所訂正） |
| U4 | Merge / aggregation（複数記録を統合） |
| U5 | Summarization / compression（圧縮要約） |
| U6 | Prune / evict / discard（削除・退避） |
| U7 | Promote / archive（長期側へ移管） |

Appendは全記録保存と同義ではない（選択したものだけappendも可能）。RewriteとCompressは重なるが、前者は更新範囲、後者は操作目的として区別。

### 軸7: Q（読み出し・利用）
| 仮コード | 小分類 |
| --- | --- |
| Q1 | 全文・現在stateを毎回渡す |
| Q2 | 時刻・区間・IDで選択する |
| Q3 | Embedding similarity等で検索する |
| Q4 | Question-conditioned / semantic reasoningで選ぶ |
| Q5 | 階層的に粗→細で検索する |
| Q6 | 保存根拠（frame、KV、イベント）を再訪・詳細化する |

`revisit_raw_video`は研究設定によって禁止もあり得るため、過去生動画へのseek/再観測と保存Memoryの取り出しを区別する。

## 別管理の共通比較条件（Memoryの下位分類ではない）
- Query timing: t=0既知 / 動画途中 / 未知
- Future access: 未到着フレーム禁止 / 動画全体を閲覧可能
- Past raw video revisit: 可 / 不可 / 不明
- Incremental state reuse: 既存計算を再利用 / 毎回prefixから再計算
- Budget / evaluation: Memory容量・token数・GPU/CPU、遅延、QA精度、fact保持など
- Evidence: 著者の主張 / Methodに明記 / 実験による裏付け / 今回未確認

## 複数軸の例（仮想例であり特定論文の実装ではない）
「コップを取る → 水を注ぐ → 机に置く」を一連のイベントとして時刻付きJSONに追記し、回答時は時刻で検索する場合：
I4/I5/I6、R2、G3、S2、W3、U1、Q2。
一論文一行の対応表は次のフェーズ。未確認は空欄でなく`未確認`とする。

## 収束案・未決
- 今回の採用候補: I/R/G/S/W/U/Qの7軸を暫定の研究地図として使う。
- 第一回の整理で優先する軸: I（何を覚える）、R（どう表現）、U（どう更新）; 実験や新規性と結び付きやすい。
- 保留: 7軸を固定した排他的なtaxonomyにすること。追加論文によって分類を統合・分割可能にする。
- 棄却寄り: Text/Visual/KVだけで全てを分類し、Event、更新、検索、query設定を捨てること。
- 次の判断: まずI/Rをユーザー例のA〜D, R1〜R10相当の粒度まで詳細化するか、先に既知の3論文で7軸の分類しやすさを試すか。
- 本書はexploratory。論文への正式なラベル付け、TODO登録、研究spec化、コード変更は行っていない。

## Companyの関連文書
- [9/11 MTG](../../../lab/projects/agentic-streaming-videoqa/meetings/2026-09-11-mtg.md)
- [10/9 MTG](../../../lab/projects/agentic-streaming-videoqa/meetings/2026-10-09-mtg.md)
- [Memory tree strategy](2026-10-14-memory-literature-review-tree-strategy.md)
