---
date: 2026-10-14
project: agentic-streaming-videoqa
source_todo: "2026-09-11 MTG: Agent系研究とMemory表現の関連研究調査"
topic: memory-literature-review-tree-strategy
status: exploratory
tags: [brainstorm, literature-review, streaming-videoqa, memory, research-method]
---

# 関連研究の読み方：1本の精読から研究地図（木）へ

## 出発点
- ユーザーはStreamForestの短期時空間Memory、meta-event生成、長期Event Forestまで逐一理解しようとしていたが、「木を作りたいのに一点で終わる」ことを懸念。
- 本質的な問いは「今回のMTGの期待は内部実装の完全理解か、Memory形式の分類と研究差分の探索か」「関連研究をどう連鎖的に掘るか」「効率的に何を省略できるか」。
- 本文は思考整理と調査方針の探索メモであり、研究方針・spec・実装の確定事項ではない。

## 読み込んだ現在の文脈・Authority
- 2026-09-11 MTG決定: Agent系Streaming VideoQAを幅広く調べ、既存手法のできること/できないこと、text/KV/feature等のMemory表現、chunkの可変化やmulti-timescale Memory等の差分候補を検討。必要な専門用語を自分で説明できること。future frameにアクセスしないchunk-level causal、Queryはt=0既知を初期設定とする。
- 2026-09-25 MTG: 興味を持ったイベントをテキスト+時刻等を含むJSONで残す設計案を議論。ただし先行研究の調査対象をテキスト限定にする指示ではない。
- 現行project README: Agent系手法の可能・不可能とMemory表現の分類が未完了マイルストーン。直近の実装状況と文献調査のAuthorityは区別する。
- 2026-09-16 literature-review-depth-guidanceと2026-10-13 streamagent-centered-literature-review-strategyは探索記録。前者はLevel 1/2/3、後者は基準論文から比較軸別に引用をたどる案。
- 2026-10-14 anticipation-and-text-memory-literatureと2026-10-13 awesome-streaming-memory-paper-priorities（10/14追記）にはtext Memoryの既存例とtext+KVのStreamAgent分類訂正がある。
- 最新のGitHub mainでは組織文書の保存ルートは旧 .company/ ではなく .research/ 。AGENTS.mdと.secretary/AGENTS.mdを現在の保存場所の根拠とする。

## 中心の整理
- 最終目的: 個別Methodの完全再現ではなく、「研究設定が同程度で、何を保存し、どう更新し、誰が判断し、何が検証されたか」を比較し、未解決の研究問いを特定する。
- 手段として「分類（全体像の幹）→重要論文の比較（枝）→差分の根拠になる箇所だけ精読（葉）」を使う。精読をやめるのではなく、問いに紐付けて深さを選ぶ。
- Memory保存**媒体**、Memory**構造**、**更新操作/ポリシー**、**処理設定**は直交している。論文が複数分類に入るのは正常。樹形図は探索索引、比較の正本は多軸matrixとする。

## ツリー案（探索用、排他的分類ではない）
1. 保存媒体: text (global rewrite summary / append-only event records), visual features/tokens, KV cache, raw frame/video, latent/recurrent states, graph/structured DB, hybrids。
2. 構造・時間尺度: recent vs long-term、episodic/event vs continuous、hierarchical/tree、multi-timescale、flat chronology。
3. 保存・更新・検索: append、rewrite、merge、compress、discard、retrieve/revisit。判定が規則・similarity・attention・Agent・query-conditionedのどれか。
4. Streaming条件・研究目的: Query t0/途中/未知、future access、raw video revisitの可否、incremental computation、GPU/CPU Memory budget、回答タイミング、遅延、正解率、情報脱落。

## 一次比較の候補（形式と機構を混同しない）
- StreamForest: event-level hierarchical **visual** Memory; frame/event境界とevent mergeによる長期保存。Event Memoryの「形式/構造」の代表。meta-event内部手順のすべてを調べる前に既存類型として置ける（https://arxiv.org/abs/2509.24871）。
- StreamAgent: compact recurrent **text** m_t と、詳細補完用の長期KV cache/selective recallを併用。Agentは将来のtask-related evidence予測とperception計画も担当（https://arxiv.org/html/2508.01875）。
- OneStreamer: 時刻付きの局所captionと完了event summaryからなる階層的**text** Memory + recent visual window。event-level textual recordの直接比較候補（https://arxiv.org/abs/2610.01762）。
- Lando et al.: online egocentric videoをtext descriptionとして蓄積してMCQ回答。text baseline候補（https://arxiv.org/abs/2506.16450）。
- StreamMem/StreamingVLMなど: visual/KV memory budgetを扱う補助候補。ただし本文確認までは保存操作の詳細や未対応事項を断定しない。

## 読み方・引用のたどり方
1. 最初に問題を1文にする（例「古い重要情報が累積summary更新によって失われることをどう防ぐ？」）。「どうmeta-eventを実装？」はこの下位問いにする。
2. まず5〜10本をScan（タイトル、Abstract、Introduction、中心図、Conclusion）し、媒体/更新/Agentの有無/Query時点/未確認箇所だけ短く記録。
3. そのうち直接比較3〜5本をExtract（Method、Experiments、Ablation）し、「できること」と「論文で未対応/自分が未確認」を厳密に分ける。
4. 必要な1〜2本だけDeep Read（数式、Supplement、Code）。たとえば「StreamForestはどのイベントをいつmergeし古い情報の精度にどう影響？」が真の比較点になったらmeta-event分割やpenalty計算を掘る。
5. Related Workの表題全体から芋づる式に読むのではなく、自分の欠けた枝を埋める論文に限り引用（backward）、引用元（forward）を辿る。1論文から次候補は最大2〜3本程度を推奨。複数論文が同じ機構を説明する場合は重複を減らす。
6. 実験・Ablationから本当に検証されている機能と精度・遅延・memory budgetのトレードオフを確認する。オンライン性の主張と実行環境の評価は区別する。
7. 比較セルが埋まり、追加論文で新しい枝や異なる機構がほぼ増えなくなったら一次調査を一旦止める。

## 最小記録フォーマット
論文 | 何を解決する | Memory媒体（複数可）| Memory構造 | write/update/retrieve | Agentの判断 | Query時点・future可否 | 本文に書かれたlimitation | 自研究との差分候補 | 根拠URL/図/節 | 未確認事項

- 最初のScanでは媒体、更新、Agent、設定、仮差分の5軸程度に縮めてもよい。未読欄は「未確認」でよい。
- 全論文に統一テンプレートを埋めること自体を目的としない。

## 評価・収束
評価軸: 9/11 MTGへの適合、research gapの発見、設定の比較可能性、投入時間、次回MTGでの説明しやすさ。
- 最有力: 枝を分けた俯瞰図 + 1枚の比較表を先に作り、疑問が生まれた箇所だけ精読。
- 保留: StreamForestのmeta-event生成の細部、閾値・merge penaltyの完全追跡。Event segmentation/mergeが独自性に直接関係すると判明したら再開。
- 棄却寄り: 全論文の数式・実装を順番に網羅、単一の論文のRelated Workを全件消化、Memoryを単純にtext vs visualの排他2分割にする方法。
- 注意: Event text記録もmulti-timescaleも既存研究があり、それだけで新規性を主張しない。

## 未解決・次に判断すべきこと
- 主軸を「累積text summaryの古い重要情報の脱落」「query-awareな保存・削除」「Agentによる未来観測の計画」「動的chunk」のどれに置くかは未決。
- Question=t0既知の既存研究と質問未到着前提研究は直接比較できるか、protocolを確認する必要がある。
- 暫定の次アクション候補: (a) StreamForestを一旦1行に要約 (b) StreamAgent/OneStreamer/Landoの比較セルを埋める (c) メモリの媒体と更新方針の両方について各1-2本引用を深掘り (d) 未解決の問いを次回MTGへ持参する。
- これらは候補であり、新規TODO・spec・コード変更を承認したものではない。

## 関連文書
- .research/lab/projects/agentic-streaming-videoqa/README.md
- .research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-11-mtg.md
- .research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-25-mtg.md
- .research/secretary/notes/brainstorm/2026-09-16-literature-review-depth-guidance.md
- .research/secretary/notes/brainstorm/2026-10-13-streamagent-centered-literature-review-strategy.md
- .research/secretary/notes/brainstorm/2026-10-14-anticipation-and-text-memory-literature.md


## 2026-10-14 追記：次回MTG前の探索スタイルについてのユーザー意向

- ユーザーは明日のMTGまでは、論文の分類・仕分け・技術的な完全理解を先行させず、自分が選んだ観点（まずText Memory論文、Visual Memory論文）について**広く浅く論文を探す**ことを優先したい。
- この段階では体系的な分類表や論文間比較を作ることを目標にしない。Abstract・中心図・必要ならConclusion程度を見て、論文名、URL、どんなMemoryを扱うかの短い一言だけ記録する方針を推奨。
- Text+KV等のハイブリッドなMemoryは厳密な二分をせずそのままメモする。個別論文の深掘り、分類軸の確定、どの方向を研究の主軸にするかはMTG後に決める。
- 本追記は探索の作業方法の整理であり、研究方向やspecの採択ではない。新規TODO作成や既存README更新も行わない。
