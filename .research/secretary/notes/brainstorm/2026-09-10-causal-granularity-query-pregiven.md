---
date: 2026-09-10
project: null
source_todo: "Awesome-Streaming-Video-Understanding（https://github.com/Yang011013/Awesome-Streaming-Video-Understanding）を調査する"
topic: causal granularity と query 事前提示を考慮した Streaming VideoQA 調査
status: exploratory
tags: [brainstorm, research]
---

# causal granularity と query 事前提示を考慮した Streaming VideoQA 調査

## 今回の前提更新

- Query は動画開始前から既知とする。
- Query を用いた query-aware な frame/memory 選別は許容する。
- ただし Query を使って future frame を探索したり、full video から関連 frame を事前取得することは禁止する。
- Streaming の因果性は単純な Yes/No ではなく、最小アクセス単位まで確認する。

## causal の調査軸

### Observation causality

- Frame-level causal: frame t の処理時に利用できるのは frame <= t のみ。
- Chunk/clip-level causal: chunk k が到着した時点で chunk 内全体は利用可能だが、future chunk は利用不可。
- Offline / non-causal: whole-video sampling、全動画 feature 抽出、future-aware segmentation 等を先に行う。

### Internal attention causality

- Causal attention: token i が future token を attend しない。
- Full/bidirectional within unit: 同じ chunk/clip 内では future token を参照できる。

Observation causality と internal attention causality は分けて記録する。LLM が autoregressive causal mask を持つだけでは、動画入力が causal である証拠にはしない。

## A候補4件の一次見直し

- StreamingVLM: inference は新規 visual input と既存 KV を逐次利用する streaming。長時間機構の参考として強い。一方、training は overlapped chunk 内で full attention を使うため、training causality と inference causality を分ける。論文は contiguous position IDs / RoPE の扱いも streaming 安定化の重要要素として報告する。
- StreamForest: online path は current frame、short-term window、event memory の構造で frame-level causal に近い。正確な causal granularity と hidden preprocessing は code audit が必要。
- StreamMem: incoming clip を単位として継続処理し、clip 内の連続 frame を filtering/encoding するため、安全な表現は clip-level causal。原手法は query-agnostic だが、論文 ablation では ground-truth query を使った KV compression が特に multi-detail task で有利と報告されるため、Query 事前既知の今回では query-aware 版が重要な baseline 候補。
- StreamAgent: video clip を sequential に処理し、clip 内では chunk-wise incremental prefill。question semantics を stream 中の予測・選択・selective recall に利用するため、Query 事前提示条件との整合性が高い。frame-level causal か、clip/token chunk が最小単位かは code で確認する。

## 実装調査で追加して追う項目

`video reader -> sampler -> clip/chunk construction -> attention mask -> position_ids/RoPE -> cache_position -> KV update -> evaluation`

特に確認する:

- chunk/clip の生成前に future frame を読んでいないか。
- chunk 内でどの token/frame まで相互 attention 可能か。
- Query が online memory write / retrieval にどう使われるか。
- KV eviction/compression 後に position ID、RoPE、cache position がどう整合されるか。
- visual token span と multimodal special token の対応を壊さず KV を操作しているか。
- evaluation 時に Query を使って未来動画へ random seek していないか。

## 今回の研究への示唆

候補構成は `Query(t=0) + Sequential Loader + Frozen VLM + Query-aware Agent Memory`。

Query が最初から既知なので、Agent は各 chunk 到着時に質問との関連性を用いて KEEP / SUMMARIZE / DROP を判断できる。query-agnostic にすべてを公平に保存する必要はなく、memory budget を質問に関係する情報へ集中できる可能性がある。一方、Query-aware であることと future-aware であることは別であり、loader/access policy 側で future frame へのアクセスを禁止する必要がある。

## 未確認点

- 各A候補の実装上の最小 causal 単位。
- visual token block 内の attention mask の実際の形。
- Qwen2.5-VL 系で visual KV を削除・圧縮した際の position_ids / mRoPE / cache_position の具体的処理。
- Query 事前提示を前提にすると、従来A/B/Cランキングがどこまで変わるか。全Modelsを同じ基準で再スクリーニングする必要がある。

## 関連

- https://app.notion.com/p/3d777f89f3cd80338e21d0ec7e68f349
- https://arxiv.org/abs/2510.09608
- https://arxiv.org/abs/2509.24871
- https://arxiv.org/abs/2508.15717
- https://arxiv.org/abs/2508.01875
