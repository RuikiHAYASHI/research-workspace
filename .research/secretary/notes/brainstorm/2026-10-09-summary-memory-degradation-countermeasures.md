---
date: 2026-10-09
project: agentic-streaming-videoqa
source_todo: null
topic: summary-memory-degradation-countermeasures
status: exploratory
tags: [brainstorm, summary, memory, degradation, streaming]
---

# 累積Summaryの情報劣化に対する対策候補

## 出発点

現行baselineは各windowで

```text
Summary_t = LLM(Summary_{t-1}, Situation_t)
```

として累積Summary全体を書き直す。

初期Behavior実験では、

- 同じ場面の説明が繰り返される例
- 後半Summaryから前半の記述が抜ける例
- Summary max_new_tokensへ頻繁に到達する条件
- max_new_tokensへ到達していないW8でもSummary内容が初期から変化する例

が観察されている。

したがって、出力上限だけでなく、過去のmodel生成文を繰り返し入力して再生成するrecursive rewrite自体が情報劣化へ寄与している可能性がある。

## 原因仮説

### 1. Iterative compression

各更新で過去情報が再圧縮されるため、一度落ちた情報は後続windowで復元できない。

### 2. Self-conditioning / error propagation

過去のSummaryに含まれた誤り・曖昧化・言い換えを次のSummaryが正本として受け取り、後続更新へ伝播させる。

### 3. Recency bias

長いprevious summaryとcurrent situationを統合すると、新しいSituationが相対的に強くなり、古い詳細が消える可能性がある。

### 4. Redundancy amplification

previous summaryの文章構造を引き継ぎながら新しいSituationを追加することで、既存記述を再掲するだけの更新が起きる。

### 5. Undefined salience

SummaryはQuestion非依存で、Promptは `important facts and changes` の保持のみを指示する。
何が後のQAに重要かをモデルは知らないため、服装、物体属性、短い行動等を不要と判断して落とす可能性がある。

## 対策候補

### A. Append-only baseline

診断用の最小ablation。

```text
memory = Situation_1 + Situation_2 + ... + Situation_t
```

または各windowを一度だけ短くlocal summaryし、そのdeltaをappendする。

累積memory全体をLLMで再生成しない。

利点:
- iterative rewriteによる情報消失をほぼ除去できる。
- 現行baselineとの因果比較が明確。

欠点:
- 長尺になるほどtoken数が単調増加する。
- 重複も蓄積する。

最終方式ではなく、「recursive rewriteが劣化原因か」を切り分けるablationとして有力。

### B. Immutable Situation log + Chapter Summary

最有力候補。

```text
Situation 1 ┐
Situation 2 ├─> Chapter 1 Summary ─┐
Situation 3 ┘                      │
                                   ├─> Answer / final synthesis
Situation 4 ┐                      │
Situation 5 ├─> Chapter 2 Summary ─┘
Situation 6 ┘
```

各Situationはimmutableに保存する。
例えば4〜8 windowごとに、そのchapter内のSituationだけを一度まとめる。
完成したChapter Summaryは後続windowで書き直さない。

利点:
- 同じ古い情報を毎window再生成しない。
- 1 factsが受けるcompression回数を限定できる。
- Summary callの入力長を一定範囲に保ちやすい。
- Question非依存のonline observationという現行方針を維持できる。
- chapter単位でどこで情報が落ちたか追跡しやすい。

EOFでは、
- Chapter Summary群をAnswerへ渡す
- Chapter Summary群を1回だけfinal synthesisする
- 必要なら階層的にさらにまとめる
の候補がある。

### C. Periodic checkpoint / refresh

通常はrolling summaryを使うが、N windowごとにimmutable Situation logからSummaryを作り直す。

利点:
- 現行構造との差分が小さい。

欠点:
- refreshまでの間はrecursive degradationが残る。
- 全Situationから再生成するとcontext / computeが増える。

### D. Stable event/fact ledger

Narrative Summaryだけでなく、

- timestamp
- person/entity
- appearance/state
- action
- state change

等をappend/updateするevent/fact memoryを持つ。

自然文Summaryは表示・Answer用projectionとして扱い、事実の正本をledgerにする。

利点:
- 服装変化や状態変化を保持しやすい。
- 同じ事実を毎回自然文で再生成しなくてよい。

欠点:
- schemaとupdate規則が増え、現行minimal baselineより複雑。
- model出力の構造validationが再び必要になる。

Company README上、2026-09-25には追記型観測・イベント台帳・上限超過時の章圧縮に近い構成を実装した経験があるため、将来案としては既存知見を参照できる。

### E. Answer-time retrieval

Situation log / Chapter Summaryをimmutableに保持し、EOFでQuestionを使って関連する時間帯だけを選びAnswerへ渡す。

利点:
- online Situation / memory構築はQuestion非依存のままにできる。
- 全情報を1本のFinal Summaryへ押し込む必要がない。

欠点:
- 現行の「Answerはfinal summaryだけを見る」契約を変更する。
- retrievalの失敗という新しいerror sourceが増える。

## Promptだけでできる低コスト対策

構造変更前に、Summary Promptへより具体的な保持規則を追加する案。

例:
- preserve distinct events and state changes
- do not remove earlier facts merely to shorten the summary
- merge duplicate descriptions instead of repeating them
- preserve person identity, appearance changes, object interactions, location changes, and temporal order
- never treat a later observation as a replacement for an earlier event unless it explicitly changes state

ただし、全文recursive rewrite自体は残るため、根本対策ではなく低コストmitigationとみなす。

## 推奨する検証順序

### Step 1: 劣化を定量化する

既存traceで早期windowのfactが後続Summaryのどこまで残るかを追跡する。

例:
- fact survival length
- repetition count
- contradiction introduction
- max-token hitとの関係

### Step 2: Append-only ablation

同じSituation outputsを使い、
rolling rewriteをせずappendしたmemoryと現行Final Summaryを比較する。

新たなvideo/Qwen Situation推論を行わず、保存済みSituation textだけから可能なoffline diagnosticとする案もある。

### Step 3: Chapter Summary比較

W4等1条件で、
- current rolling Summary
- append-only
- fixed-K chapter summaries
を比較する。

見るもの:
- early fact retention
- duplicate rate
- token growth
- summary model calls / time
- final QA evidence retention

## 現在の収束

研究・実装候補としては、

**immutable Situation log + fixed-size Chapter Summary**

が最有力。

理由:
- iterative rewrite回数を直接減らす。
- source observationを失わない。
- Question非依存の逐次認識を維持する。
- full event ledgerほど複雑でない。
- append-onlyより長尺へ拡張しやすい。

ただし現時点では採用決定ではない。
まず既存artifactでrecursive rewriteによるfact lossを確認し、append-onlyまたはchapter化で改善するかをablationするのが次のEvidence候補。

## 未解決

- chapter sizeをwindow数 / 秒 / token数のどれで決めるか。
- EOF Answerへchapter summariesを直接渡すか、final synthesisを1回行うか。
- long videoでchapter summaries自体が増えた場合の第2階層compressionが必要か。
- question-independent summaryだけで将来の任意QAに必要な細部をどこまで保持できるか。
