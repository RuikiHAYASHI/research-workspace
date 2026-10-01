---
date: 2026-10-01
project: agentic-streaming-videoqa
source_todo: null
topic: streaming-videoqa-novelty-directions
status: exploratory
tags: [brainstorm, research, novelty, streaming-videoqa, active-perception, memory, early-answer]
---

# Streaming VideoQA 新規性候補の初期壁打ち

## 出発点

2026-10-01、現在は研究基盤を整備している段階であり、ここから研究として新規性を出す方向を検討したいという相談。

本メモは探索記録であり、spec・実装許可ではない。

## 読み込んだ現在文脈

- Project README: `.research/lab/projects/agentic-streaming-videoqa/README.md`
- 直近MTG: `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-25-mtg.md`
- implemented spec: `.research/lab/projects/agentic-streaming-videoqa/specs/2026-09-30-workbench-agent-modes-and-readable-memory-spec.md`
- 階層記憶spec: `.research/lab/projects/agentic-streaming-videoqa/specs/2026-09-25-workbench-target-stream-and-hierarchical-memory-spec.md`
- 初回Qwen実験: `.research/lab/projects/agentic-streaming-videoqa/experiments/2026-09-24-longvideobench-qwen3vl-initial-run.md`
- Workbench main README: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main`

2026-10-01時点でCompanyにはWorkbench Stage 5--7のapproved implementation specが存在するが、これらは主にpreview、翻訳、設定/Prompt UX、結果可視化であり、研究アルゴリズムの新規性そのものではない。

## 確認済み事実

現在の研究アルゴリズムは概ね以下。

1. Queryは動画開始時から既知。
2. future chunkへアクセスしないstrict causalな逐次処理。
3. 固定window / 固定framesで現在chunkを読む。
4. Situation Agentがwindow-level観測とunresolvedを生成。
5. Memory Agentが根拠付きevent ledgerとbounded text narrativeを更新。
6. Answer AgentはEOF後のみ実行。
7. frame ID / timestamp / event ID / narrative versionまで根拠追跡可能。
8. current video clipへprevious text memoryを渡す/渡さない比較軸がある。
9. 実Qwenで現行video_clip + memory構成を十分に比較評価したEvidenceはまだない。

現在の実装は、新しい研究制御器を追加する前の観測・記憶・証跡基盤としてはかなり整っている。

## 先行研究との衝突確認

### StreamAgent (2025)
https://arxiv.org/abs/2508.01875

質問意味と過去観測から未来のtask-relevant interval/regionをanticipateし、perception actionとresponse timingを変える。text memoryとstreaming KV-cacheも扱う。

したがって「Agentが次に見る場所/時間を予測する」「十分なら答える」だけでは新規性が弱い。

### OVO-Bench (2025)
https://arxiv.org/abs/2501.05510

Backward tracing / real-time understanding / forward active respondingを評価し、情報が足りるまで回答を遅延する能力自体が既に明示的な研究課題。

したがってearly answer / wait-or-answerだけでは十分ではない。

### Active Video Perception (2025)
https://arxiv.org/abs/2512.05774

long-form videoをinteractive environmentとして扱い、plan-observe-reflectでquery-relevant evidenceを反復取得し、sufficiencyを判定して停止する。

ただしoffline long-video settingが中心で、strict streaming causal条件とは差がある。

### OASIS (2026)
https://arxiv.org/abs/2604.17052

hierarchical event memoryとuncertainty-driven on-demand retrievalを組み合わせる。

したがって「階層Memoryを作る」「必要時だけ過去をretrieveする」だけでは新規性が弱い。

### SimpleStream (2026)
https://arxiv.org/abs/2604.02317

recent N framesだけの単純baselineが複雑なstreaming memory法に匹敵/優越する場合があり、perception-memory trade-offを報告する。

したがってMemoryを複雑化する場合は、recent-onlyの単純baselineを必ず上回る設計・比較が必要。

## 新規性候補

### 候補A: Evidence-Sufficiency based Causal Early Answer

現在のevent ledger / unresolved / answer evidence traceを使い、各chunk後に「今答えてよいか」を判定する。

単なるconfidenceではなく、例えば次を判定対象にする。

- 現在の候補回答を直接支持するevidenceがあるか。
- 競合する選択肢を支持する未解決仮説が残っているか。
- future evidenceによって現在回答が反転する余地が大きいか。
- 根拠eventが十分に独立しているか。

出力例:

```text
ANSWERABLE / CONTINUE
candidate_answer
supporting_event_ids
remaining_counter_evidence
unresolved_questions
stability_score
```

新規性仮説:
「strict causal streamingで、explicit evidence ledgerとcounter-evidenceを用いて回答安定性を判定する」こと。

単純なwait/answerは既存研究と被るため、counterfactualなanswer stabilityや根拠追跡を中心に据える必要がある。

### 候補B: Uncertainty-Driven Causal Temporal Zoom

現在は全区間を固定window / fixed framesで処理する。

Memoryの`unresolved`やSituationのcertaintyから、次windowの観測密度を変える。

例:

- 変化なし・質問無関係 -> windowを長く / frameを減らす。
- 重要状態変化・uncertainty上昇 -> windowを短く / frameを増やす。
- 特定entityの状態が未解決 -> 直近数秒を高密度観測。
- answerabilityに近づいた -> 証拠確認用に一時的に高密度化。

重要な制約:
futureへseekせず、現在以降に到着するstreamに対するbudget allocationだけを変える。

新規性仮説:
offline keyframe searchではなく「strict causal online budget allocation」を、explicit unresolved/evidence stateで制御する。

ただしStreamAgent等と近いため、単なるtask-driven anticipationではなく、観測密度・chunk粒度の制御とanswer stabilityを明確に結び付ける必要がある。

### 候補C: Contradiction-Preserving Evidence Memory

現在のMemoryはevent ledger + bounded narrative。

ここを単なるsummaryではなく、回答判断に必要な状態として分離する。

```text
supported facts
contradicted facts
unresolved hypotheses
entity states
answer-changing evidence
```

特に古い情報を圧縮するとき、
「要約として重要」ではなく
「現在の回答を変え得るか」
で保持優先度を決める。

新規性仮説:
answer-decision utilityをmemory admission / compressionの基準に使う。

ただしevent memory自体は競合が多く、これ単独よりA/Bとの組み合わせの方が研究主張を作りやすい。

### 候補D: Answerability-Time Benchmark / Protocol

現在のWorkbenchはframe timestampと根拠eventを厳密に保存できる。

これを利用し、

- Queryはt=0から既知。
- futureは禁止。
- いつ最初に正答可能になったか。
- modelがいつ回答したか。
- それまでに何frame / token / wall timeを使ったか。

を同時に測る評価protocolを作る。

評価候補:

```text
final accuracy
answer time / delay
frames consumed
VLM calls
input/output tokens
evidence precision
premature-answer rate
unnecessary-wait rate
```

既存OVO-Bench等との差分を精査する必要はあるが、現在のWorkbenchの証跡構造とは非常に相性がよい。

## 現時点で相性が良い組み合わせ

単独機能より、次の一つの研究仮説としてまとめる方が強い。

**Evidence-Adaptive Streaming VideoQA**

各chunkで
Situation -> Evidence Memory -> Sufficiency Controller
を回し、

- evidenceが十分なら早く回答。
- 不十分ならunresolved / counter-evidenceに応じて次の観測budgetを変更。
- 全判断をevent/frame/timestampへtrace可能にする。

つまり、

```text
固定sampling + EOF回答
        ↓
根拠状態に応じた観測budget + 回答時刻の共同制御
```

を研究対象にする。

主張候補:
「同じaccuracyをより少ないframe / VLM call / delayで達成できるか」
または
「同じcompute budgetでaccuracyを改善できるか」。

## 重要な反例・リスク

- SimpleStreamのようなrecent-only baselineに負ける可能性。
- Controller自体のLLM callが増え、節約したvisual computeを相殺する可能性。
- answerability判定が自己confidenceだけだとcalibration不良でpremature answerが増える可能性。
- adaptive samplingが質問依存情報だけを追い、question-independentな後続証拠を落とす可能性。
- LongVideoBenchはoffline QA由来のため、early-answer時刻のground truthがない可能性がある。
- StreamAgentとの違いを「実装が違う」だけでなく問題設定・controller signal・評価軸で明確にする必要がある。

## 次に壁打ちすべき問い

1. 新規性の中心を「いつ答えるか」と「どれだけ見るか」のどちらへ置くか。
2. answerabilityを何で定義するか。
3. adaptive samplingをfuture anticipationで制御するか、現在のuncertainty/evidenceだけで制御するか。
4. benchmarkはLongVideoBench中心か、OVO-Bench / StreamingBenchも含めるか。
5. 研究貢献をmethod中心にするか、strict-causal evaluation protocolも含めるか。

## 現在の方向性

採用ではなく初期有力候補として、
**Evidence-Sufficiency Controller + Uncertainty-Driven Causal Temporal Zoom**
の組み合わせを優先して次の壁打ち対象とする価値が高い。

research-specへの昇格はまだ行わない。


## 2026-10-01 19:14 追加調査: 途中回答・応答時刻を直接扱う研究

ユーザーの「StreamAgentも途中で終了して答えを返すのではないか」という確認を受けて、response timing / proactive responseを直接扱う研究を追加調査した。

### StreamAgent (2025)

StreamAgentの定式化では、各timestampでdecision functionがWAIT/RESPONDを判断し、十分な情報が集まった時点または動画終端で回答する。したがって、query単位で動画終端より前に回答する理解は正しい。

ただし「回答後にシステム全体がstream監視を終了する」とは限らず、active interactionの文脈ではqueryへの応答とstream処理継続は区別する必要がある。

### OVO-Bench (2025)

Forward Active Respondingとして、質問時点では情報不足の場合にfuture情報が十分になるまで回答を遅延する能力を評価する。

### Dispider (2025)

Perception / Decision / Reactionを分離し、軽量なstreaming処理が適切なinteraction timingを判定する。interaction中も非同期でstream監視を継続するため、「一問に答えたらstreamを終了」とは異なる。

### ProactiveVideoQA (2025)

動画再生中にmodel自身がmulti-turn responseの時刻を決めるproactive interactionを評価するbenchmark。response timingを含むPAUC metricを提案。

### MMDuet2 (2025)

各turnでrespond / remain silentを判断し、precise response-time annotationなしでmulti-turn reinforcement learningによりtimely responseを学習する。

### LiveStar (2025)

response-silence decodingによりproactive response timingを決定するalways-on streaming assistant。回答後もstream継続を前提とする。

### StreamReady / ProReady-QA (CVPR 2026)

「What to answer and When」を直接主題化している。supporting evidenceが現れた時刻範囲をannotateし、早すぎる回答と遅すぎる回答を非対称に罰するAnswer Readiness Scoreを提案。learnable readiness mechanismがevidence sufficientになったかを判定して回答をgateする。

このため、「十分なevidenceが集まったらearly answer」という単独アイデアは新規性として成立しにくい。

### ProactiveBench (2026-09)

standing requestを受け、1秒ごとにstreamを監視し、target event後の適切なintervalだけで応答し、それ以外はsilenceを保つ能力を評価する。premature responseが大きな失敗要因であることを報告。

### REVEAL (2026-08)

offline/long-video寄りだが、explicit evidence sufficiency verificationを導入し、単なるretrieval relevanceではなく「temporal / causal / fine-grained evidenceが本当に揃っているか」を検証して不足情報を再取得する。training-free agentic long-video QA。

## 新規性候補の更新

追加調査により、以下は単独では競合が強い。

- WAIT / ANSWERの導入。
- evidence sufficiency判定。
- readiness score。
- response timing metric。
- proactive / silence decision。
- hierarchical memory + sufficiency。
- precise response-time annotationなしのtraining。

したがって、現在の研究で新規性を狙うなら「途中回答」を中心機能として主張するのではなく、現在のWorkbenchが既に持つexplicit event ledger / unresolved / frame timestamp / evidence traceを利用した、より限定的な未解決問題へ寄せる必要がある。

現時点の探索候補:

1. **Counter-evidence-aware stopping**
   - supporting evidenceだけでなく、現在回答を反転させ得るcounter-evidence / unresolved hypothesisを明示追跡する。
   - 「証拠がある」ではなく「反証候補が十分に潰れた」を停止条件にする。

2. **Strict-causal evidence verification**
   - REVEALのようなfull-videoへのtargeted re-retrievalは許さず、到着済みstreamだけでevidence sufficiencyを検証する。
   - past artifactの再参照は可能だがfuture seekは禁止。
   - この差分が研究主張として十分かはさらに文献調査が必要。

3. **Joint observation-cost / response-time control**
   - when to answerだけでなく、回答までのframe budget / VLM call / token cost自体もcontrollerが調整する。
   - accuracy + timing + computeの3軸で評価する。
   - StreamAgentとの重複を避けるため、future event anticipationではなくcurrent evidence gap / contradictionをcontrol signalにする案を検討する。

4. **Unanswerable / never-answer streaming QA**
   - StreamReady自身がexplicit unanswerability modelingをfuture workとして挙げている。
   - 動画を最後まで見ても答えられない質問、根拠が一度も十分にならない質問を含め、「いつ答えるか」だけでなく「最後まで答えないべきか」を扱う。
   - ただしProactiveBench等のsilence taskとの重複確認が必要。

この追加調査により、前節の「Evidence-Sufficiency Controller単体を有力候補」とする評価は弱める。現在は **counter-evidence / strict causal / compute-aware / unanswerability** のいずれかを加えないと新規性主張は難しいと判断する。
