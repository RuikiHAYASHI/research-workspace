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

## 2026-09-10 17:08 JST 再監査結果

A候補4件を、`Future-content access / Observation unit / Causal granularity / Within-unit visibility / Compute incrementality / Query=t0適合性` の6観点で再監査した。

### StreamingVLM

- 公開実装 `streaming_vlm/inference/inference.py` では既定 `chunk_duration=1 sec`、`window_size=16 sec`。
- 時間方向に1秒ずつ進むloopで現在の1秒区間だけをreaderから取得し、`past_key_values` を次roundの `model.generate()` に渡すため、compute-incremental streamingはcodeで確認できた。
- Queryは最初のchunkでのみ明示的にpromptへ入り、その後はpast stateとともに保持される。今回のQuery事前提示条件に直接近い。
- 古いvision/text KVをtoken range単位で削除し、`pos_mode=shrink` とcontiguous 3D RoPEでpositionを再整合する。
- 安全なcausal表現は **1-second chunk-level causal**。current 1秒chunk内の各frameを厳密に逐次不可視にしているframe-level causalityまでは確認しない。

### StreamForest

- 論文設計とonline training設定は1 FPS、`local_num_frames=1`、`mm_pos_num_frames=1`、`dynamic_fps1` でframe-oriented。
- OVO-Bench evaluationではsampleの `start/end` をvideo loaderへ渡し、「過去〜現在」の区間だけを入力できるためfuture-contentを除くprefix-causal accessは確認できる。
- 一方、公開 `lmms_eval/models/streamforest.py` のgeneration wrapperは、その時点までに選ばれたframesをまとめてpreprocessし1回のgenerationへ渡す経路を持つ。そのため、**information-access causality** と **persistent compute incrementality** を同一視しない。
- 現時点の表現は「paperはframe-oriented、公開eval pathはprefix-causal、wall-clock間のpersistent state更新は部分確認」とする。

### StreamMem

- 論文Algorithmはincoming frame batchを順に取得し、similarity filter、encode、KV budget超過時prune、retained KVへappendするincremental構造。
- 実験既定は0.5 FPS、1 incoming clip=8 framesであり、安全なcausal表現は **8-frame clip-level causal**。
- 原方式はquery-agnosticだが、ground-truth user queryをKV importance計算に使うablationがquery-agnostic方式より高性能。Queryがt=0から既知の今回では、query-aware bounded KVを主要baseline候補にする。
- Position処理は、圧縮後に単純reindexするより元のtemporal position consistencyを保ち、YaRNで長文脈へ拡張する方向。
- 今回、公式GitHub codeを確認できなかったためreader/cache-positionのcode-level監査は未確認。

### StreamAgent

- 問題設定はvideo clip `v_t` が時刻順に到着し、future clipは到着するまで利用しないため、observation levelは **clip-level causal**。
- clip内の`chunk-wise incremental prefill`はvisual token sequenceを分割するactivation-memory最適化であり、frame-level causalの根拠にはしない。
- question semanticsを観測方針、予測、KV selective recallへ用いるため、Queryがt=0から既知の今回との概念的一致度が最も高い。
- 今回、公式GitHub codeを確認できなかったためreader/sampler/cache-positionのcode-level監査は未確認。

### 収束した研究条件

今回の研究条件は **query-known, chunk-causal, compute-incremental streaming VideoQA** と表現するのがよい。

```text
q = known at t=0
M_0 = init()
for t = 1..T:
    x_t = loader.next_chunk()  # future chunk unavailable
    M_t = update(M_{t-1}, x_t, q)
answer = decode(q, M_T)
```

Query-aware selectionはcausal性を壊さない。一方、Queryを用いて未来frame、future feature、whole-video由来のsampling index、future-aware scene boundaryを取得することは禁止する。

### 初期baseline案

1. current chunk only
2. query-agnostic bounded memory
3. query-aware bounded memory
4. query-aware agent memory

この順で比較すれば、streaming access contract、memory、query-aware selection、agentic decisionの寄与を分離しやすい。

### KV研究へ進む場合の追加監査

KVを直接削除・圧縮する場合は `position_id / RoPE / attention_mask / cache_position / multimodal special token` を必ずセットで追う。StreamingVLMのcontiguous/shrink positionと、StreamMemのoriginal temporal position保持+YaRNは対照的な設計軸として扱う。

詳細はNotion「Awesome Streaming Video Understanding調査」の `2026-09-10 再監査：Causal粒度 × Query事前提示` に同期した。

## 2026-09-10 17:20 JST 明日MTGに持参したい論点

MTGでは調査ログの列挙ではなく、`Evidence / Interpretation / Ask` の順で説明する。

### Evidenceとして持っていく

- Awesome-Streaming-Video-UnderstandingのA候補4件の比較表。
- StreamingVLMの公開実装で確認した `1 sec chunk -> past_key_values再利用 -> KV eviction -> contiguous 3D RoPE` の処理フロー。
- StreamMemは8-frame clip-level causal、StreamAgentはclip-level causal、StreamForestはpaper上frame-orientedだが公開eval pathはprefixをまとめて推論する場合がある、というcausal粒度の差。
- Queryはt=0から既知という今回の前提。

### Interpretationとして持っていく

- 今回の研究条件は `query-known, chunk-causal, compute-incremental streaming VideoQA` と置くと整理しやすい。
- Sequential Loaderの役割は速度最適化よりも、future chunkへのアクセスを禁止するinformation-access contract。
- Queryが最初から既知なので、query-aware memory selectionはcausal性を壊さず利用できる。
- 最初からVLM内部KVを改造するより、Frozen VLM + external query-aware memoryから始めると研究寄与を分離しやすい。

### Askとして先生に相談したい候補

1. causal条件はframe-levelまで要求するか、chunk-levelを正式条件としてよいか。
2. 初期研究の中心をKV cache改造ではなく、Sequential Loader + Query-aware Agent Memoryに置いてよいか。
3. baselineを `current chunk only -> query-agnostic bounded memory -> query-aware bounded memory -> query-aware agent memory` とするか。
4. 次の実験対象datasetと、長時間動画の最低durationをどこに置くか。

### MTG前にあると強い最小追加情報

- 1枚で分かる研究構成図: `Query(t=0) -> Sequential Loader -> Frozen VLM -> Query-aware Memory -> Answer`。
- A候補4件の比較表に `causal granularity / compute incrementality / query timing / memory` の4列。
- 可能ならSequential Loaderの現在実装がfuture accessをどこまで禁止できているかの確認。これは既存研究との差分を説明するために重要。
