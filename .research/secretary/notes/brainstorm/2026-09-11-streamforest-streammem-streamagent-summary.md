---
date: 2026-09-11
project: null
source_todo: "Awesome-Streaming-Video-Understanding（https://github.com/Yang011013/Awesome-Streaming-Video-Understanding）を調査する"
topic: StreamForest / StreamMem / StreamAgent の詳細整理
status: exploratory
tags: [brainstorm, research]
---

# StreamForest / StreamMem / StreamAgent の詳細整理

## 出発点

2026-09-11 MTG用Notionで、すでに詳しく整理したStreamingVLMと同じ粒度に、残りのA候補3件（StreamForest / StreamMem / StreamAgent）を整理する。

今回の観点は、Dataset / 学習 / streaming時の処理 / Memory機構 / Queryの扱い / 今回の研究への示唆 / 注意点。

## StreamForest

### 確認済み事実

- NeurIPS 2025 Spotlight。公式repoは `MCG-NJU/StreamForest`。
- 構成はFine-grained Spatiotemporal Window（FSTW）とPersistent Event Memory Forest（PEMF）。current付近を高密度に保持し、古い履歴をevent単位の階層memoryへ移す。
- evaluation時は1 FPS。代表設定ではreal-time perceptionに729 visual tokens、short-term memoryに18 frames × 128 tokensを割り当てる。
- FSTWを超えた履歴はframe間similarityの局所最小点でmeta-event化し、PEMFへ送る。long-term memory上限を超えると、content similarity / merge count / temporal distanceのpenaltyでevent nodeをmergeし、ToMeでvisual tokensを圧縮する。
- OnlineIT-generalは既存dataを含む40万件超のinstanceで、32Kの高品質streaming training instancesを新規整備。OnlineIT-driveは89K streaming QA。
- 学習はSigLIP-so400M + MLP + Qwen2-7B。5-stageで、Stage 1-3はoffline pretraining/SFT、Stage 4がstreaming fine-tuning、任意Stage 5がdriving fine-tuning。論文では32 A100 GPUを使用。
- online evaluationはStreamingBench / OVBench / OVO-Bench / ODV-Bench。ODV-Benchは1,190 driving clips、5-90秒、6,348 QA。
- online benchmarkはcurrent timestampより後の映像を使わない。ただし公開evaluation wrapperにはprefixをまとめて推論する経路があるため、information-access causalityとpersistent compute incrementalityは分ける。

### 解釈

StreamForestの主要な示唆は、recentとlong-termを同じ粒度で保持せず、古いvideoをevent構造へ段階的に圧縮すること。Query semanticを直接使ったmemory retentionではないので、今回のQuery-aware Agent Memoryではevent化後のKEEP / DELETEをQueryで制御する拡張が考えられる。

## StreamMem

### 確認済み事実

- training-free / query-agnosticな固定サイズKV memory方式。
- incoming frame batchを順番に取得し、similarity filter -> encode -> proxy-query attentionでold/new KVのimportance計算 -> fixed budgetを超えたKVのprune -> frame-level prototype merge -> next clip、というincremental loop。
- 標準的な実験設定は0.5 FPS、1 incoming clip=8 frames。代表的なKV budgetは6K tokens。
- proxy queryにはchat template中のassistant開始token等を用い、実際のuser queryを必要とせずvisual token importanceを評価する。
- weighted frame-wise KV mergingで各frameの代表情報も残す。
- offline long-video benchmarkはMLVU / EgoSchema / VideoMME、streaming QAはRVS-Ego / RVS-Movie。
- LLaVA-OneVision-7B / Qwen2-VL-7B / Qwen2.5-VL-3Bなどに追加学習なしで適用する。
- true user queryをcompressionに使うablationはquery-agnostic方式より高く、特にmulti-detail taskで差が大きい。
- positionは単純reindexせずoriginal temporal consistencyを保つ方向で、長いpositionへYaRNを利用する。StreamingVLMのContiguous RoPEとは対照的。
- 今回の監査では公式GitHub実装を特定できていないためcode-level reader/cache auditは未確認。

### 解釈

Queryがt=0から既知の今回には、StreamMemのtrue-query ablationが重要なEvidenceになる。固定memory budgetを同じにした上でquery-agnostic / query-awareを比較するbaseline設計へ直接つながる。

## StreamAgent

### 確認済み事実

- Queryとhistoryから、今後task-relevant情報が現れそうな時間区間・空間領域をanticipateし、perception actionを変えるagentic streaming VideoQA。
- future anticipationはfuture pixels/featuresを先読みする意味ではなく、現在までの情報から将来の観測対象を予測する。
- inputは224×224、1 FPS。planning/tool coordinationにQwen2.5-VL-3B、precise interactionにQwen2.5-VL-7Bを使用。
- StreamingBench / OVO-Bench / OVBenchを主なstreaming benchmarkとして評価し、MLVU / LongVideoBench / VideoMME等のlong-video benchmarkも使用する。
- video clipを順番にencodeし、過去clip KVをlong-term memoryとして保持。GPU threshold超過後はCPUへoffloadし、Query時にlayer-adaptiveなattention scoreで関連KVだけをSelective RecallしてGPUへ戻す。
- default α=3、maximum retrieval=256。
- clip内のchunk-wise incremental prefillはactivation memory削減のための実装であり、frame-level observation causalityの証拠にはしない。
- 標準問題設定ではQueryがstream途中のtimestampで来る場合もある。今回の設定はQuery=t0なので、最初のchunkからmemory decisionへQueryを使える点が異なる。
- 現行論文の中心はpretrained Qwen2.5-VLを使ったplanning / prompting / tool orchestrationとstreaming KV機構で、StreamForestのような明示的multi-stage streaming fine-tuning recipeは主手法として提示されていない。Future Workではagent workflowからdataを構築しfine-tuneする方向を述べる。

### 解釈

4本の中では今回のQuery-aware Agent Memoryに最も概念的に近い。ただし、最初からsemantic memory + KV selective recall + active toolsをすべて再現すると寄与が混ざるため、初期実験では `Query + current chunk + External Memory -> KEEP / SUMMARIZE / DELETE / WAIT` に簡略化し、Agent decision自体の効果を分離する案が自然。

## 3本を並べたときの整理

- StreamForest: **event structureで古い履歴を圧縮**。
- StreamMem: **fixed KV budget内でquery-agnosticに重要tokenを選ぶ**。
- StreamAgent: **Query semanticsを使い、観測・待機・retrievalをagentが決める**。

StreamingVLMのrecency-oriented bounded KVと合わせると、今回の候補systemは `recent detail / event-semantic summary / query-aware selection` をどの層で組み合わせるか、という比較軸に整理できる。

## 未確認点

- StreamMemの公式code-level streaming reader / sampler / cache_position。
- StreamAgentの公式code公開有無、およびtoolが実際にアクセスできるvideo範囲のcode-level確認。
- StreamForest公開eval pathでpersistent stateをwall-clock間にどこまで再利用するかの完全な実装監査。

## Notion同期

2026-09-11 MTGページのStreamForest / StreamMem / StreamAgent各sectionへ、StreamingVLMと同様の粒度で同期した。

- https://app.notion.com/p/3d777f89f3cd80dab6c5f6efc924e337
