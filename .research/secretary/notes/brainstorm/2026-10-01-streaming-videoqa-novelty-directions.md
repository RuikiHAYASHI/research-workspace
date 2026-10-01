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


## 2026-10-01 19:xx 追加壁打ち: 実装起点ではなく Online × Agent × LongVideoQA から探索

ユーザー指示により、現在のWorkbench実装を前提に新規性を考えるのではなく、
**Online（未来参照なしの逐次処理）× Agent（観測・記憶・判断を自律制御）× LongVideoQA（長時間動画質問応答）**
というタスク自体から研究空間を広げて検討する。

### 1. 消去法Agent / 仮説検証Agent

ユーザー案: 選択肢を順に消去して問題を解くAgent。

近い既存研究:
- MM-PoE (2024): multimodal MCQでProcess of Eliminationを導入。
- VideoHV-Agent / Think, Then Verify (CVPR 2026): 各候補回答を検証可能なhypothesisへ変換し、必要なclueを導出してvideo evidenceで検証。

したがって「選択肢を消去する」だけでは新規性が弱い。

ただしOnline条件では未解決余地がある。

候補:
**Online Hypothesis Elimination Agent**
- t=0で各選択肢を検証可能な仮説へ変換。
- stream到着ごとに各仮説を support / contradiction / unknown で更新。
- どの選択肢を区別するために何を見るべきかをAgentが決める。
- 未来へseekせず、到着するstreamに対する観測budgetだけを変える。
- 一度消去した選択肢を、後続証拠で復活可能にするかも研究軸。

重要な差別化候補は、offline retrievalではなく、**選択肢間の識別に必要な証拠を逐次管理しながら観測戦略を変えること**。

### 2. 質問からchunk秒数・frame数を決めるAgent

近い既存研究:
- Adaptive Keyframe Sampling (CVPR 2025): prompt relevance + coverageでkeyframe selection。
- ReQuest (2026): question-aware / uncertainty-driven adaptive frame selection。
- StreamAgent: question semanticsとhistoryから将来のtask-relevant temporal/spatial focusを予測してperception actionを変更。

したがってquestion-aware sampling単独では競合が強い。

一方、Streaming VideoQAで
- chunk duration
- frames per chunk
- frame density
- observation frequency
を**明示的なAgent action**として逐次選択し、
accuracy / compute / latencyのtrade-offを最適化する研究は検討価値がある。

特に、質問の種類によって初期policyを変える案:
- 物体有無 -> 粗い長chunk / 少frame
- 瞬間的行動 -> 短chunk / 高密度frame
- 長期的状態変化 -> 長chunk + memory重視
- 順序・因果 -> 中密度 + event boundary重視

さらに、stream中に候補選択肢が絞れたら観測粒度も変える。

### 3. Online LongVideoQA向けの高難度Dataset / Benchmark

既存の関連benchmark:
- 1H-VideoQA: 40–90分の動画、hour-long long-context能力。
- HLV-1K: 約1時間動画、frame / within-event / cross-event / long-term reasoning。
- LSDBench: 平均45.39分、短い重要actionを高sampling密度で見つける必要がある。
- HERBench: k>=3の時間的に離れた証拠を統合しないと解けないmulti-evidence QA。
- SportsTime (ECCV 2026): 分単位に離れた複数eventをChain-of-Timeで統合するtemporal compositional reasoning。
- VideoZeroBench (2026): 正答だけでなくspatio-temporal evidence groundingまで要求。

したがって「動画が長い」「証拠が離れている」だけでは既存benchmarkがある。

Online特有の難しさを定義すると研究余地がある。

候補difficulty axes:
- **Evidence latency**: 質問提示から最後の必須証拠が現れるまでの時間。
- **Evidence span**: 最初の必須証拠から最後の必須証拠までの時間幅。
- **Evidence gap**: 必須証拠どうしの最大時間間隔。
- **Evidence sparsity**: 長時間の中で必要情報が占める割合。
- **Distractor duration**: 誤答を支持しそうな無関係区間の長さ。
- **Reversal risk**: 前半だけ見ると誤答がもっともらしいが、後半証拠で反転する度合い。
- **Memory horizon**: 正答に必要な最古情報までの時間距離。
- **Answerability time**: 初めて正答可能になる動画時刻。
- **Cross-event composition depth**: 何個の離れた出来事を順序づけ・統合する必要があるか。

特に「前半だけでは誤答が合理的に見えるが、数十分後の証拠で覆る」問題はOnline性を強く評価できる。

### 4. Hallucination × Online Processing

関連benchmark:
- VideoHallucer: intrinsic / extrinsic video hallucination。
- HAVEN: hallucination原因・対象・質問形式を多軸評価。
- ELV-Halluc: long-video特有のSemantic Aggregation Hallucination (SAH)。frame-level認識が正しくても、複数eventを集約すると誤った意味へ統合される現象。
- VideoSEAL (ICML 2026): agentic long-video QAでanswerとretrieved evidenceが一致しないEvidence Misalignmentを分析し、plannerとanswer authorityを分離。

ユーザー仮説:
Online処理では、一度に動画全体を圧縮・集約するのではなく、逐次eventを確定しながら進むため、long-video hallucination、特にSemantic Aggregation Hallucinationを減らせる可能性がある。

これは現時点で有望な研究問い。

例:
**Does causal online aggregation reduce long-video hallucination?**
- Offline full-video / sparse global sampling
- Sliding-window recent-only
- Online incremental event memory
- Online hypothesis-tracking agent
を同じbackbone・同程度budgetで比較。

見る指標:
- final QA accuracy
- hallucination rate
- evidence grounding
- contradiction consistency
- event order errors
- answer-evidence alignment

重要なのは「Onlineだから良い」と仮定せず、offline方法よりhallucinationが減る条件・増える条件を分析すること。
逐次誤りがmemoryへ蓄積して逆にhallucinationが増える可能性も反例として重要。

### 5. 現時点で統合しやすい研究案

#### 案A: Online Hypothesis Elimination VideoQA

各選択肢を仮説として保持し、stream到着ごとにsupport / contradiction / unknownを更新する。
Agentは残った仮説を最も区別できるよう次の観測粒度を決める。

研究問い:
- 選択肢全体を毎回直接回答するより、逐次消去の方がlong-horizon reasoningに強いか。
- distractorや遠隔証拠に強くなるか。
- hallucinationが減るか。

#### 案B: Question-Adaptive Online Perception Agent

質問の種類・現在の仮説状態に応じてchunk duration / frame countを動的選択。

研究問い:
- 固定samplingより少ないcomputeで同等以上の精度を出せるか。
- evidence sparsity / gap / latency別にどのpolicyが有効か。

#### 案C: Online-Hard LongVideoQA Benchmark

Online特有のdifficulty axesをannotationし、単純な動画長ではなく
「どれだけ長く覚え、どれだけ待ち、どれだけ離れた証拠を統合する必要があるか」を評価する。

#### 案D: Online Processing as Hallucination Mitigation

逐次観測・逐次memory・仮説検証がlong-video hallucinationを抑えるかを研究する。
特にELV-HallucのSemantic Aggregation Hallucinationと相性が良い可能性。

### 6. 現時点の強い組み合わせ仮説

単独より、以下の組み合わせが研究ストーリーとして強い可能性がある。

**Hypothesis-Driven Adaptive Online VideoQA**

1. 質問と選択肢から仮説を作る。
2. 各仮説を区別するために必要な証拠を定義する。
3. Online streamを未来参照なしで処理する。
4. 現在残っている仮説に応じてchunk長 / frame数を変える。
5. 証拠が来るたびに仮説を支持・反証・保留へ更新する。
6. 十分に識別できたら回答する。

評価はaccuracyだけでなく、
- compute
- answer timing
- evidence grounding
- hallucination
- evidence gap / span別性能
まで見る。

この方向は、消去法、adaptive sampling、long-range difficulty、hallucinationという今回のユーザー案を一つの研究テーマへ統合できる。

まだresearch-specへは昇格せず、探索候補として保持する。


## 2026-10-01 20:25 追加壁打ち: マルチスケール・Online消去法・premature answer・新規性

### MTGでの「マルチスケール」の意味

Company議事録を再確認。

2026-09-18 MTG原文:
- 「マルチスケール - 短い～長い範囲を見るか」
- Chunkは実装上ロードする単位。

したがって、このMTGでの第一義は **temporal multi-scale chunk（時間幅の異なるchunkを使うこと）**。
例:
- 数秒の短chunk: 瞬間的な行動・細かい状態変化。
- 数十秒〜数分の長chunk: 文脈・流れ・長期変化。

2026-09-11 MTGでは別に:
- 「要約のTime Scaleをマルチスケールにする」
- multi-timescale memory
も議論されている。

よってCompany上では「マルチスケール」は少なくとも
1. chunkの時間幅のmulti-scale
2. memory / summaryの時間スケールのmulti-scale
の2文脈がある。
直近9/18の発言は1が中心。

### ユーザー仮説: Online処理は直感に反する展開を追いやすいか

ユーザーが意図したのは一般的なhallucinationより、
「前半では人間の常識・直感上もっともらしい解釈があるが、後半の予想外の出来事でその解釈が覆る動画」に対して、
offline一括処理よりonline逐次処理の方が時系列に沿ってbeliefを更新しやすいのでは、という仮説。

この問題は **defeasible reasoning（新証拠で既存仮説を撤回・修正する推論） / belief revision（信念更新）** と見る方が近い。

関連:
- Black Swan (CVPR 2025): unpredictable eventsに対するabductive / defeasible video reasoning。新しいvisual informationが既存hypothesisを変更するtaskを含む。

研究問い候補:
**Does causal incremental belief revision help video models reason through counter-intuitive event reversals?**

比較:
- Offline one-shot: 全動画を一括入力 / global sampling。
- Online incremental: 順番に入力し、各時点のhypothesis/beliefを更新。
- Online + explicit hypothesis tracking: 候補仮説ごとにsupport / contradiction / unknownを更新。

注意:
offlineは情報量としてはonline以上を見られるため、「onlineだから情報的に有利」ではない。
差が出るなら、order-preserving processing / state update / aggregation mechanismが原因。
同一backbone・同程度visual/token budgetで比較し、処理方式の差として主張する必要がある。

### Online消去法VideoQAの直接先行研究

2026-10-01時点で重点検索した範囲では、
**strict online / future inaccessibleなvideo streamで、MCQ選択肢を時系列にsupport/contradiction/unknownへ更新し、候補を逐次消去しながら回答する**
ことを中心にした論文は確認できなかった。

近いもの:
- MM-PoE (2024/2025): multimodal multiple-choiceでprocess of elimination。ただしimage中心でstreaming videoではない。
- VideoHV-Agent / Think, Then Verify (CVPR 2026): long-video候補回答をtestable hypothesisに変換して検証。ただしoffline long-video searchで、全動画空間へのretrieval/localizationが可能。
- PACE / Finding the Right Evidence (2026-08): option-discriminative evidenceをcandidate answersから導出し、offline long-video indexから証拠取得。
- TreeReasoner (CVPRW 2026): hypothesis-verification + temporal zoom/jump/slide。ただしoffline video navigation。

したがって、**Online Hypothesis Elimination（逐次仮説消去）** は探索価値がある。ただし「論文が存在しない」と断定せず、現検索範囲で直接一致を未確認とする。

### 根拠前のpremature answerを直接調べる研究

かなり明確に存在。

- StreamReady (CVPR 2026):
  - supporting visual evidenceが現れる前の回答をspeculationとして問題化。
  - answer evidence windowとAnswer Readiness Scoreを導入。
- PhoStream (ICML 2026):
  - Forward taskでrequired visual/audio cuesがまだ出ていない段階のEarly Responseを明示評価。
  - forward performance低下の主因がearly response。
- ProactiveBench (2026-09):
  - 適切なevent前に応答するpremature responseを評価。
  - 6 system中4つでpremature responseがmissed responseを上回ると報告。
- OVO-Bench (CVPR 2025):
  - sufficient future informationまで回答をdelayするForward Active Responding。

したがって「根拠が出る前に答えてしまう」は既に独立したfailure modeとして研究されている。

### Hypothesis-Driven Adaptive Online VideoQAの新規性再評価

名前・大枠だけでは新規性は不十分。

既存要素:
- hypothesis verification: VideoHV-Agent, TreeReasoner
- process of elimination: MM-PoE
- option-discriminative retrieval: PACE
- question-adaptive frame selection: ReQuest, AKS
- online perception / response timing: StreamAgent, StreamReady, OVO-Bench, PhoStream

一方、次の組み合わせは直接一致する研究を現検索範囲では確認できていない:

**Strict-Online Discriminative Hypothesis Tracking**
1. t=0でanswer choicesをtestable hypothesesへ変換。
2. future access禁止。
3. stream到着ごとに各hypothesisをsupport / contradiction / unknownで更新。
4. remaining hypothesesを最も区別するため、次のchunk duration / frames-per-chunk / observation densityをAgent actionとして選択。
5. 仮説消去は必要ならreversibleにし、新証拠によるbelief revisionを許す。
6. final answerだけでなくhypothesis trajectoryとevidence timestampを評価。

特に新規性候補は:
**「質問関連性」ではなく「残存仮説間の識別に必要な証拠」を使って、future-inaccessible streamの観測粒度をオンライン制御すること。**

これはPACEのoption-discriminative evidenceという発想と近いため、offline index retrievalとの差を明示する必要がある。

さらにBlack Swan型のcounter-intuitive / defeasible videoを評価対象にすると、
- 早期消去の誤り
- 後続証拠による仮説復活
- belief revision
を定量化でき、Onlineである意味が強くなる。

現時点では「新規性あり」と断定せず、**有望だが、PACE / VideoHV-Agent / StreamAgentとの境界をさらに精査すればmethod contributionとして成立する可能性がある**とする。


## 2026-10-01 20:xx 追加壁打ち: 仮説trajectory評価とOnline Agent研究のDataset / Model動向

### 仮説が時間とともにどう変化するかの既存評価

既存video研究ではcontinuous hypothesis trajectoryを直接標準評価するものはまだ少ない。
近い評価骨格:

- BlackSwanSuite (CVPR 2025)
  - Forecaster: 前半のみで未来仮説を生成。
  - Detective: post-eventを追加して、既存仮説をvalidate / invalidate。
  - Reporter: main eventまで含めて再度仮説をvalidate / invalidateし、最終説明。
  - Y/N variantでは各hypothesisが新しいvisual evidenceでvalid / invalidになったかを直接評価。
  - したがって「新証拠後に仮説を正しく更新できるか」を段階的に評価するvideo benchmarkとして近い。

- Belief-R (EMNLP 2024, text reasoning)
  - tとt+1の2段階でbelief revisionを評価。
  - BU-Acc (Belief Update Accuracy): 更新すべきとき正しく更新できるか。
  - BM-Acc (Belief Maintain Accuracy): 更新不要なとき元のbeliefを維持できるか。
  - BREU: BU-AccとBM-Accの平均。

Online VideoQAへ応用する場合、既存評価に近い最小設計として:
- timestampごとにanswer hypothesis stateを記録。
- update-required区間とmaintain-required区間をannotation。
- 正しい仮説更新率 / 不要なflip率 / update delayを測る。
が考えられる。

これは提案であり、video側で標準化済みのmetricではない。

### Online / Streaming + Agent研究のDataset動向

2024-2026の代表的研究では、次が頻出。

1. StreamingBench
   - 900 videos / 4,500 QA。
   - 各videoに異なるtimestampの5 question。
   - real-time visual / omni-source / contextual understanding。
   - Streaming系の共通比較先として定着。

2. OVO-Bench
   - 644 videos / 約2,800 timestamp annotation。
   - Backward Tracing / Real-Time Understanding / Forward Active Responding。
   - 「過去を思い出す・今を見る・未来証拠を待つ」の3軸。
   - StreamAgent / StreamReady / Dispider / StreamForest等で頻出。

3. OVBench / VStream-QA
   - Streaming/long-contextの補助評価として使用例が多い。

4. Offline long-video benchmarksも併用
   - VideoMME, MLVU, MVBench, EgoSchema, ActivityNet-QA等。
   - Streaming専用性能だけでなく、一般LongVideo理解を壊していないかを見る。

5. 新しい応用特化benchmark
   - ProReady-QA: evidence window / answer timing。
   - PhoStream: mobile-centric streaming、audio-visual、Forward task。
   - ODV-Bench: autonomous driving。
   - LiveProBench: standing request、1秒ごとのproactive response。
   - OVO-S-Bench: streaming spatial intelligence。

Training data側ではEgo4D、COIN、BEHAVIOR等の連続・手順動画が頻出し、offline annotationをstreaming dialogue / instructionへ変換する流れもある。

### Model動向

- 7B〜8B級open-source Video-LLM / MLLMが主流。
- Qwen系列が非常に多い。
  - Qwen2-VL-7B
  - Qwen2.5-VL-7B
  - Qwen3-VL-8B
  - Qwen2.5-Omni / Qwen3-Omni
- LLaVA-OneVision 7B、InternVL 7B/8B、MiniCPM-V/O 8B、Gemma系も比較対象。
- proprietary baselineとしてGPT-4o / Gemini系を併記することが多い。

Agent/system設計では、複数の巨大VLMを何個も常時回すより:
- small decision / trigger / readiness module
- 7B前後のmain reaction / reasoning VLM
- streaming KV cache / event memory
- asynchronous perception / decision / response
という分業が多い。

例:
- Dispider: compact Qwen2-1.5BでPerception-Decision、Qwen2-7BでReaction。
- StreamReady: Qwen-2-VL 7B backbone。Oryx-1.5-7B / LLaVA-OneVision 7Bでもbackbone ablation。
- PhoStream: Qwen2.5-Omni-7B, Qwen3-VL-8B/30B, Qwen3-Omni-30BとGemini/Doubao等を比較。
- VideoLLM-online: Llama-3-8B + SigLIP、Ego4D streaming data。repoでは後にQwen2.5-VL-Instructへの適用も推奨。
- newer systems still largely 7B-scale online models, with 1 fps前後のstream処理が共通設定になっている例が多い。

### 研究トレンドとしての解釈

現在のStreaming Agent研究は、大きく:
1. 何を覚えるか（memory / KV cache）
2. いつ応答するか（trigger / readiness / proactive response）
3. どこを見るか（task-driven perception / anticipation）
4. どれだけ効率よく見るか（token compression / 1fps / low latency）
5. audioを含むomnimodal化
へ広がっている。

一方、**answer choices / hypotheses自体の時系列trajectoryを中心評価対象にする研究は相対的に薄い**。
ただしこれは現時点の調査所見であり、新規性確定ではない。

### 今後の探索を狭める示唆

「全部入り」ではなく、一つの核に絞るなら候補は:
- Online belief revision for VideoQA
  - いつ仮説を変えるべきか / 変えないべきか。
- Adaptive observationは後段のmethod候補として分離。
- Early answer / multi-scale / memoryは主貢献ではなくablation / extensionへ回す。

これなら「仮説が時間とともにどう変化するか」という一つの問題設定で研究を立てやすい。
